# 07 - UI/UX Plan

---

## 1. Design Direction: Dark Luxury with Data Depth

**Style**: Dark theme with rich data visualizations, glassmorphism cards, subtle gradients. Think Bloomberg Terminal meets modern SaaS dashboard.

**Why**: Event planning is data-heavy. A dark, dense interface signals professionalism and lets colorful data visualizations pop. This avoids the "generic template" trap.

**Palette:**
```css
:root {
  --bg-primary: oklch(12% 0.02 260);        /* Deep navy-black */
  --bg-surface: oklch(18% 0.02 260);        /* Card backgrounds */
  --bg-elevated: oklch(22% 0.02 260);       /* Elevated surfaces */
  --accent-primary: oklch(70% 0.20 250);    /* Electric blue */
  --accent-success: oklch(72% 0.18 155);    /* Green for completed */
  --accent-warning: oklch(78% 0.16 80);     /* Amber for in-progress */
  --accent-error: oklch(65% 0.22 25);       /* Red for errors */
  --text-primary: oklch(95% 0 0);           /* Near-white */
  --text-secondary: oklch(65% 0 0);         /* Muted gray */
}
```

**Typography**: Inter (body) + JetBrains Mono (data/numbers)

---

## 2. User Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Landing    │ →   │   Event      │ →   │   Agent      │ →   │   Full       │
│   Page       │     │   Wizard     │     │   Dashboard  │     │   Plan       │
│              │     │  (4 steps)   │     │  (real-time) │     │  (results)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                              ┌──────────┐ ┌──────────┐ ┌──────────┐
                              │Simulation│ │ Outreach │ │  Export  │
                              │Dashboard │ │  Center  │ │  (PDF/   │
                              │          │ │          │ │   CSV)   │
                              └──────────┘ └──────────┘ └──────────┘
```

---

## 3. Screen-by-Screen Specification

### 3.1 Landing Page

**Purpose**: Explain the product, capture user intent, start the wizard.

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  [Logo: Srishti]              [Try Demo] [Docs] │
├─────────────────────────────────────────────────┤
│                                                  │
│    "AI-Powered Event Intelligence"               │
│    Plan conferences, festivals, and sporting     │
│    events with autonomous AI agents.             │
│                                                  │
│    [Start Planning →]                            │
│                                                  │
├─────────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ 7 AI   │  │ 220+   │  │ Real-  │            │
│  │ Agents │  │ Events │  │ time   │            │
│  │        │  │ Data   │  │ Collab │            │
│  └────────┘  └────────┘  └────────┘            │
│                                                  │
│  [How it works - scrolly section]               │
│  Step 1: Configure → Step 2: Agents work →      │
│  Step 3: Get your plan                          │
└─────────────────────────────────────────────────┘
```

### 3.2 Event Configuration Wizard (4 Steps)

**Step 1 - Domain & Category**
```
┌─────────────────────────────────────┐
│  What type of event?                │
│                                     │
│  ┌───────────┐ ┌───────────┐       │
│  │ Conference │ │  Music    │       │
│  │    🎤      │ │ Festival  │       │
│  │  [Active]  │ │    🎵     │       │
│  └───────────┘ └───────────┘       │
│  ┌───────────┐                     │
│  │ Sporting  │                     │
│  │  Event    │                     │
│  │    ⚽     │                     │
│  └───────────┘                     │
│                                     │
│  Category: [AI ▼] [Web3] [Climate] │
│  Sub-theme: [________________]     │
│                                     │
│              [Next →]               │
└─────────────────────────────────────┘
```

**Step 2 - Location & Dates**
```
┌─────────────────────────────────────┐
│  Where and when?                    │
│                                     │
│  Geography: [India ▼]              │
│  City (optional): [Bangalore ▼]    │
│                                     │
│  Start Date: [📅 Sep 15, 2026]     │
│  End Date:   [📅 Sep 17, 2026]     │
│                                     │
│  [← Back]           [Next →]       │
└─────────────────────────────────────┘
```

**Step 3 - Audience & Budget**
```
┌─────────────────────────────────────┐
│  Scale and budget                   │
│                                     │
│  Target Audience Size:              │
│  [━━━━━━━●━━━━━━━] 2,000           │
│  500          5,000        20,000   │
│                                     │
│  Budget Range (INR):                │
│  Min: [50,00,000]                   │
│  Max: [80,00,000]                   │
│                                     │
│  [← Back]           [Next →]       │
└─────────────────────────────────────┘
```

**Step 4 - Review & Launch**
```
┌─────────────────────────────────────┐
│  Review your event                  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ AI Conference                │   │
│  │ Bangalore, India             │   │
│  │ Sep 15-17, 2026              │   │
│  │ 2,000 attendees              │   │
│  │ Budget: ₹50L - ₹80L         │   │
│  └─────────────────────────────┘   │
│                                     │
│  [← Edit]     [🚀 Launch Agents]   │
└─────────────────────────────────────┘
```

### 3.3 Agent Dashboard (Main Screen)

**This is the hero screen -- where agents work in real-time.**

```
┌────────────────────────────────────────────────────────────────┐
│  Srishti │ AI Summit India 2026              [Simulation] [Export]│
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                      │
│ Agents   │   ┌─────────────────────────────────────────────┐   │
│          │   │        Agent Collaboration Graph              │   │
│ ✅Sponsor│   │                                               │   │
│ ✅Speaker│   │    [Sponsor]──┐                               │   │
│ ✅Venue  │   │       ✅      │                               │   │
│ ✅Exhib  │   │               ▼                               │   │
│ ⏳Pricing│   │    [Speaker]→[Pricing]                        │   │
│ ⏳GTM    │   │       ✅      ⏳ 67%                          │   │
│ 🔒Ops    │   │               ▲                               │   │
│          │   │    [Venue]───┘  [Exhibitor]→[GTM]             │   │
│          │   │       ✅           ✅        ⏳ Queued         │   │
│          │   │                                               │   │
│          │   │              [Ops Agent]                       │   │
│          │   │                🔒 Waiting                     │   │
│          │   │                                               │   │
│          │   │   Progress: ████████████░░░░░  68%            │   │
│          │   └─────────────────────────────────────────────┘   │
│          │                                                      │
│          │   ┌─────────────────────────────────────────────┐   │
│          │   │        Activity Log                          │   │
│          │   │ 12:45:15 Pricing Agent: Analyzing 47 venues  │   │
│          │   │ 12:45:12 Speaker Agent: ✅ 28 speakers found │   │
│          │   │ 12:45:08 Sponsor Agent: ✅ 25 sponsors ready │   │
│          │   └─────────────────────────────────────────────┘   │
│          │                                                      │
├──────────┴─────────────────────────────────────────────────────┤
│  [Sponsors] [Speakers] [Venues] [Exhibitors] [Pricing] [GTM]  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sponsor Results (25 found)                    [Export CSV]     │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ #1 Google Cloud          Title    Score: 0.92        │      │
│  │    Industry relevance: 0.95 │ History: 0.90          │      │
│  │    "Strong presence at Indian AI events..."          │      │
│  │    [View Details] [Generate Outreach] [Remove]       │      │
│  ├──────────────────────────────────────────────────────┤      │
│  │ #2 Microsoft Azure       Title    Score: 0.89        │      │
│  │    ...                                               │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.4 Simulation Dashboard

```
┌────────────────────────────────────────────────────────────────┐
│  Simulation Dashboard                         [Reset] [Save]   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Pricing Simulator ──────────────────────────────────┐    │
│  │                                                         │    │
│  │  Early Bird:  ₹2,999  [━━━━●━━━━━] ──→ 400 tickets     │    │
│  │  Regular:     ₹5,999  [━━━━━━●━━━] ──→ 800 tickets     │    │
│  │  VIP:         ₹14,999 [━━━━━━━●━━] ──→ 200 tickets     │    │
│  │  Student:     ₹1,499  [━━●━━━━━━━] ──→ 600 tickets     │    │
│  │                                                         │    │
│  │  Projected Revenue: ₹85,00,000                          │    │
│  │  Projected Attendees: 2,000                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── Break-Even Analysis ────────┐ ┌─── Revenue Breakdown ──┐ │
│  │                                │ │                         │ │
│  │  Revenue ────────/             │ │  [Pie Chart]            │ │
│  │  Costs ────────/               │ │  Tickets: 55%           │ │
│  │              /                 │ │  Sponsors: 35%          │ │
│  │           ● Break-even: 850   │ │  Exhibitors: 10%        │ │
│  │          /  Current: 2000     │ │                         │ │
│  │        /   Margin: 57.5%     │ │                         │ │
│  └────────────────────────────────┘ └─────────────────────────┘ │
│                                                                 │
│  ┌─── What-If Scenarios ──────────────────────────────────┐    │
│  │                                                         │    │
│  │  [+] New Scenario    Current  │ Scenario A │ Scenario B │    │
│  │  ──────────────────────────────────────────────────────│    │
│  │  Avg Ticket Price   ₹5,999   │ ₹4,999     │ ₹7,999    │    │
│  │  Attendance          2,000   │ 2,400      │ 1,500     │    │
│  │  Ticket Revenue     ₹85L    │ ₹82L       │ ₹78L      │    │
│  │  Total Revenue      ₹1.2Cr  │ ₹1.15Cr    │ ₹1.1Cr    │    │
│  │  Profit Margin       23%    │ 20%        │ 18%       │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.5 Outreach Center

```
┌────────────────────────────────────────────────────────────────┐
│  Outreach Drafts                     [Generate All] [Export]   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Filter: [All ▼]  [Sponsors] [Speakers] [Exhibitors] [Comms]  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ To: Google Cloud (Sponsor - Title Tier)               │      │
│  │ Channel: [Email ▼]                                    │      │
│  │                                                        │      │
│  │ Subject: Google Cloud x AI Summit India 2026          │      │
│  │                                                        │      │
│  │ Hi [Name],                                            │      │
│  │                                                        │      │
│  │ I noticed Google Cloud's strong presence at GTC India │      │
│  │ 2025 and DevFest Bangalore — your commitment to the   │      │
│  │ Indian AI ecosystem is impressive...                  │      │
│  │                                                        │      │
│  │ [Edit Draft] [Copy to Clipboard] [Mark as Sent]       │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ To: Dr. Andrej Karpathy (Speaker - Keynote)           │      │
│  │ ...                                                    │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.6 Dataset Explorer

```
┌────────────────────────────────────────────────────────────────┐
│  Event Dataset Explorer              [Download CSV] [JSON]     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Domain: [All ▼]  Year: [2025 ▼] [2026 ▼]  Category: [All ▼] │
│  Search: [________________________]                            │
│                                                                 │
│  220 events loaded │ Sources: 8 │ Last updated: Apr 10, 2026  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ Name          │ Date    │ Location │ Category │ Att. │      │
│  │───────────────│─────────│──────────│──────────│──────│      │
│  │ NeurIPS 2025  │ Dec '25 │ San Diego│ AI/ML    │16000 │      │
│  │ ICML 2026     │ Jul '26 │ Vienna   │ AI/ML    │ 8000 │      │
│  │ Coachella '26 │ Apr '26 │ Indio,CA │ Music    │125K  │      │
│  │ IPL 2026      │ Mar '26 │ India    │ Cricket  │ 40K  │      │
│  │ ...           │         │          │          │      │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Responsive Strategy

| Breakpoint | Layout |
|-----------|--------|
| Desktop (1440+) | Full dashboard with sidebar |
| Laptop (1024-1440) | Condensed sidebar |
| Tablet (768-1024) | Stacked layout, collapsible panels |
| Mobile (320-768) | Not primary target for hackathon, basic scroll layout |

Priority: Desktop-first. The judges will view this on laptops/desktops.

---

## 5. Key Interactive Elements

1. **Agent Collaboration Graph** (React Flow) -- live animated, shows data flow between agents
2. **Pricing Sliders** (custom range inputs) -- drag to adjust prices, see real-time updates
3. **Break-Even Chart** (Recharts) -- interactive line chart with tooltip at intersection
4. **Scenario Comparison Table** -- side-by-side comparison of what-if scenarios
5. **Outreach Editor** -- inline editing of AI-generated drafts
6. **Dataset Table** -- sortable, filterable, searchable data explorer
