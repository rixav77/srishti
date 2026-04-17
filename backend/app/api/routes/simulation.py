"""Simulation engine — pricing, break-even, and revenue projections.

PDF says simulation dashboard is "particularly valued" for extra points.
Supports what-if scenarios: adjust tier prices, see impact on revenue + attendance.
"""

from __future__ import annotations

import math

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# ── request / response models ────────────────────────────────────────────────


class TierInput(BaseModel):
    name: str
    price: float
    allocation_pct: float = Field(..., ge=0, le=100)


class PricingSimulationRequest(BaseModel):
    tiers: list[TierInput]
    total_target_audience: int = 1000
    fixed_costs: float = 500000
    variable_cost_per_attendee: float = 500
    sponsor_revenue: float = 0
    exhibitor_revenue: float = 0
    price_elasticity: float = 1.2


class TierResult(BaseModel):
    name: str
    price: float
    allocation_pct: float
    estimated_sales: int
    revenue: float


class SimulationResult(BaseModel):
    tiers: list[TierResult]
    total_ticket_revenue: float
    total_revenue: float
    total_costs: float
    profit: float
    margin_pct: float
    break_even_attendees: int
    estimated_total_attendees: int
    safety_margin_pct: float
    revenue_breakdown: dict


class SensitivityPoint(BaseModel):
    price_change_pct: int
    attendance_change_pct: float
    revenue: float
    profit: float


class SensitivityResult(BaseModel):
    points: list[SensitivityPoint]
    optimal_price_change_pct: int
    optimal_revenue: float


# ── core simulation logic ────────────────────────────────────────────────────


def _simulate(req: PricingSimulationRequest) -> SimulationResult:
    """Run pricing + revenue simulation with price-elasticity demand model."""
    tiers: list[TierResult] = []
    total_ticket_revenue = 0.0
    total_attendees = 0

    for tier in req.tiers:
        seats = int(req.total_target_audience * tier.allocation_pct / 100)
        # Apply simple demand adjustment: higher price → lower fill rate
        # fill_rate = 1 / (1 + elasticity * (price / baseline_price - 1))
        baseline = sum(t.price * t.allocation_pct for t in req.tiers) / max(
            sum(t.allocation_pct for t in req.tiers), 1
        )
        if baseline > 0:
            price_ratio = tier.price / baseline
            fill_rate = min(1.0, 1.0 / (1 + req.price_elasticity * max(0, price_ratio - 1)))
        else:
            fill_rate = 0.85

        estimated_sales = max(1, int(seats * fill_rate))
        revenue = estimated_sales * tier.price
        total_ticket_revenue += revenue
        total_attendees += estimated_sales

        tiers.append(TierResult(
            name=tier.name,
            price=tier.price,
            allocation_pct=tier.allocation_pct,
            estimated_sales=estimated_sales,
            revenue=round(revenue, 2),
        ))

    total_revenue = total_ticket_revenue + req.sponsor_revenue + req.exhibitor_revenue
    total_costs = req.fixed_costs + (req.variable_cost_per_attendee * total_attendees)
    profit = total_revenue - total_costs
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    # Break-even: total_costs = ticket_revenue_per_attendee * N + sponsor + exhibitor
    avg_ticket = total_ticket_revenue / max(total_attendees, 1)
    net_per_attendee = avg_ticket - req.variable_cost_per_attendee
    if net_per_attendee > 0:
        break_even = math.ceil(
            (req.fixed_costs - req.sponsor_revenue - req.exhibitor_revenue) / net_per_attendee
        )
        break_even = max(0, break_even)
    else:
        break_even = req.total_target_audience  # can't break even

    safety = ((total_attendees - break_even) / max(break_even, 1)) * 100 if break_even > 0 else 0

    return SimulationResult(
        tiers=tiers,
        total_ticket_revenue=round(total_ticket_revenue, 2),
        total_revenue=round(total_revenue, 2),
        total_costs=round(total_costs, 2),
        profit=round(profit, 2),
        margin_pct=round(margin, 1),
        break_even_attendees=break_even,
        estimated_total_attendees=total_attendees,
        safety_margin_pct=round(safety, 1),
        revenue_breakdown={
            "tickets": round(total_ticket_revenue, 2),
            "sponsors": round(req.sponsor_revenue, 2),
            "exhibitors": round(req.exhibitor_revenue, 2),
        },
    )


# ── API endpoints ────────────────────────────────────────────────────────────


@router.post("/pricing", response_model=SimulationResult)
async def simulate_pricing(request: PricingSimulationRequest):
    """Run a full pricing simulation with the given tiers and cost structure."""
    return _simulate(request)


@router.post("/sensitivity", response_model=SensitivityResult)
async def sensitivity_analysis(request: PricingSimulationRequest):
    """
    Run -30% to +30% price sensitivity analysis.
    Shows how revenue and profit change with uniform price adjustments.
    """
    points: list[SensitivityPoint] = []
    best_revenue = 0.0
    best_change = 0

    for delta_pct in range(-30, 35, 5):
        adjusted = request.model_copy(deep=True)
        factor = 1 + delta_pct / 100
        adjusted.tiers = [
            TierInput(name=t.name, price=round(t.price * factor, 2), allocation_pct=t.allocation_pct)
            for t in request.tiers
        ]
        result = _simulate(adjusted)

        # Attendance change vs baseline
        baseline_result = _simulate(request)
        att_change = (
            (result.estimated_total_attendees - baseline_result.estimated_total_attendees)
            / max(baseline_result.estimated_total_attendees, 1) * 100
        )

        points.append(SensitivityPoint(
            price_change_pct=delta_pct,
            attendance_change_pct=round(att_change, 1),
            revenue=result.total_revenue,
            profit=result.profit,
        ))

        if result.total_revenue > best_revenue:
            best_revenue = result.total_revenue
            best_change = delta_pct

    return SensitivityResult(
        points=points,
        optimal_price_change_pct=best_change,
        optimal_revenue=round(best_revenue, 2),
    )


@router.post("/breakeven")
async def breakeven_analysis(request: PricingSimulationRequest):
    """Return break-even point and chart data."""
    result = _simulate(request)
    avg_ticket = result.total_ticket_revenue / max(result.estimated_total_attendees, 1)

    # Generate chart data points (attendees vs revenue vs cost)
    chart_data = []
    for n in range(0, int(request.total_target_audience * 1.2), max(1, request.total_target_audience // 20)):
        revenue = (n * avg_ticket) + request.sponsor_revenue + request.exhibitor_revenue
        cost = request.fixed_costs + (request.variable_cost_per_attendee * n)
        chart_data.append({
            "attendees": n,
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "profit": round(revenue - cost, 2),
        })

    return {
        "break_even_attendees": result.break_even_attendees,
        "projected_attendees": result.estimated_total_attendees,
        "safety_margin_pct": result.safety_margin_pct,
        "chart_data": chart_data,
    }
