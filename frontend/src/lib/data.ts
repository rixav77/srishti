export interface Project {
  id: string;
  name: string;
  category: string;
  geography: string[];
  city?: string;
  audienceSize: number;
  customizationEnabled: boolean;
  agentInstructions: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface Sponsor {
  name: string;
  tier: string;
  matchScore: number;
  reasoning: string;
  estimatedBudget: string;
}

export interface Speaker {
  name: string;
  topic: string;
  influence: string;
  pastTalks: number;
  matchScore: number;
}

export interface Venue {
  name: string;
  city: string;
  capacity: number;
  pricePerDay: string;
  rating: number;
}

export const CATEGORIES = ["AI / ML", "Web3", "Music & Arts", "FinTech", "HealthTech", "Gaming", "Climate"];
export const GEOGRAPHIES = ["North America", "Europe", "Asia Pacific", "Middle East", "Latin America"];

export const MOCK_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "AI Summit 2026",
    category: "AI / ML",
    geography: ["North America", "Europe"],
    audienceSize: 2400,
    customizationEnabled: false,
    agentInstructions: {},
    createdAt: "2026-03-15",
    updatedAt: "2026-04-10",
  },
  {
    id: "proj-2",
    name: "Web3 Connect Dubai",
    category: "Web3",
    geography: ["Middle East"],
    audienceSize: 1200,
    customizationEnabled: false,
    agentInstructions: {},
    createdAt: "2026-02-20",
    updatedAt: "2026-04-08",
  },
  {
    id: "proj-3",
    name: "HealthTech Forum Europe",
    category: "HealthTech",
    geography: ["Europe"],
    audienceSize: 800,
    customizationEnabled: false,
    agentInstructions: {},
    createdAt: "2026-01-10",
    updatedAt: "2026-04-05",
  },
];

export function getSponsorsForProject(project: Project): Sponsor[] {
  const sponsorSets: Record<string, Sponsor[]> = {
    "AI / ML": [
      { name: "NVIDIA", tier: "Platinum", matchScore: 96, reasoning: "Leading GPU provider with strong AI conference presence. Sponsored 14 AI events in 2025.", estimatedBudget: "$150K–$250K" },
      { name: "Google DeepMind", tier: "Gold", matchScore: 91, reasoning: "Active in AI research community. High brand alignment with ML-focused audiences.", estimatedBudget: "$100K–$180K" },
      { name: "Microsoft Azure", tier: "Gold", matchScore: 88, reasoning: "Enterprise AI platform targeting developer audiences. Strong ROI from past AI events.", estimatedBudget: "$80K–$150K" },
      { name: "Anthropic", tier: "Silver", matchScore: 85, reasoning: "Emerging AI safety leader seeking visibility in the AI conference circuit.", estimatedBudget: "$50K–$90K" },
    ],
    "Web3": [
      { name: "Polygon Labs", tier: "Platinum", matchScore: 94, reasoning: "Major L2 network actively sponsoring Web3 events globally.", estimatedBudget: "$120K–$200K" },
      { name: "Coinbase", tier: "Gold", matchScore: 89, reasoning: "Top exchange with strong event marketing budget for 2026.", estimatedBudget: "$80K–$140K" },
      { name: "Chainlink", tier: "Silver", matchScore: 83, reasoning: "Oracle network with developer-focused sponsorship strategy.", estimatedBudget: "$40K–$80K" },
    ],
    default: [
      { name: "AWS", tier: "Platinum", matchScore: 90, reasoning: "Broad tech sponsorship across verticals.", estimatedBudget: "$100K–$200K" },
      { name: "Salesforce", tier: "Gold", matchScore: 85, reasoning: "Enterprise reach with event marketing focus.", estimatedBudget: "$60K–$120K" },
    ],
  };
  return sponsorSets[project.category] || sponsorSets.default;
}

export function getSpeakersForProject(project: Project): Speaker[] {
  const speakerSets: Record<string, Speaker[]> = {
    "AI / ML": [
      { name: "Dr. Fei-Fei Li", topic: "Human-Centered AI", influence: "Very High", pastTalks: 42, matchScore: 97 },
      { name: "Andrej Karpathy", topic: "Neural Network Training", influence: "Very High", pastTalks: 38, matchScore: 95 },
      { name: "Dario Amodei", topic: "AI Safety & Alignment", influence: "High", pastTalks: 22, matchScore: 90 },
      { name: "Yann LeCun", topic: "Self-Supervised Learning", influence: "Very High", pastTalks: 55, matchScore: 93 },
      { name: "Dr. Timnit Gebru", topic: "AI Ethics & Fairness", influence: "High", pastTalks: 30, matchScore: 88 },
    ],
    "Web3": [
      { name: "Vitalik Buterin", topic: "Ethereum & Decentralization", influence: "Very High", pastTalks: 60, matchScore: 98 },
      { name: "Balaji Srinivasan", topic: "Network States", influence: "High", pastTalks: 35, matchScore: 89 },
      { name: "Stani Kulechov", topic: "DeFi & Aave", influence: "High", pastTalks: 25, matchScore: 86 },
    ],
    default: [
      { name: "Tim Ferriss", topic: "Innovation & Growth", influence: "Very High", pastTalks: 70, matchScore: 85 },
      { name: "Sheryl Sandberg", topic: "Leadership", influence: "High", pastTalks: 45, matchScore: 82 },
    ],
  };
  return speakerSets[project.category] || speakerSets.default;
}

export function getVenuesForProject(project: Project): Venue[] {
  const regionVenues: Record<string, Venue[]> = {
    "North America": [
      { name: "Moscone Center", city: "San Francisco, CA", capacity: 5000, pricePerDay: "$45,000", rating: 4.8 },
      { name: "Javits Center", city: "New York, NY", capacity: 4000, pricePerDay: "$55,000", rating: 4.6 },
    ],
    "Europe": [
      { name: "ExCeL London", city: "London, UK", capacity: 6000, pricePerDay: "$38,000", rating: 4.7 },
      { name: "Fira Barcelona", city: "Barcelona, Spain", capacity: 3500, pricePerDay: "$32,000", rating: 4.5 },
    ],
    "Asia Pacific": [
      { name: "Marina Bay Sands Expo", city: "Singapore", capacity: 4500, pricePerDay: "$42,000", rating: 4.9 },
    ],
    "Middle East": [
      { name: "Dubai World Trade Centre", city: "Dubai, UAE", capacity: 3000, pricePerDay: "$35,000", rating: 4.7 },
    ],
    "Latin America": [
      { name: "Centro Citibanamex", city: "Mexico City, MX", capacity: 2800, pricePerDay: "$22,000", rating: 4.3 },
    ],
  };
  const venues: Venue[] = [];
  project.geography.forEach((geo) => {
    if (regionVenues[geo]) venues.push(...regionVenues[geo]);
  });
  return venues.length > 0 ? venues : [{ name: "Convention Center TBD", city: "TBD", capacity: 2000, pricePerDay: "$25,000", rating: 4.0 }];
}

export function getPricingForProject(project: Project) {
  const base = project.audienceSize > 2000 ? 350 : project.audienceSize > 1000 ? 250 : 180;
  return {
    earlyBird: `$${base - 80}`,
    standard: `$${base}`,
    vip: `$${base + 200}`,
    expectedAttendance: Math.round(project.audienceSize * 0.82),
    fillRate: "82%",
    revenueEstimate: `$${((project.audienceSize * 0.82 * base) / 1000).toFixed(0)}K`,
  };
}

export function getGTMForProject(project: Project) {
  return {
    channels: [
      { name: "LinkedIn Ads", reach: "45K professionals", cost: "$8,500", priority: "High" },
      { name: "Email Campaign", reach: "12K subscribers", cost: "$1,200", priority: "High" },
      { name: "Twitter/X Promoted", reach: "30K impressions", cost: "$4,000", priority: "Medium" },
      { name: "Partner Cross-Promo", reach: "20K via partners", cost: "$0", priority: "High" },
    ],
    timeline: [
      { phase: "Awareness", weeks: "12–8 weeks before", status: "Planned" },
      { phase: "Registration Push", weeks: "8–4 weeks before", status: "Planned" },
      { phase: "Last Call", weeks: "4–1 weeks before", status: "Planned" },
    ],
  };
}

export function getOpsForProject(project: Project) {
  return {
    checklist: [
      { task: "Venue contract finalization", status: "Pending", priority: "High" },
      { task: "AV equipment booking", status: "Pending", priority: "High" },
      { task: "Catering vendor selection", status: "Pending", priority: "Medium" },
      { task: "Registration system setup", status: "Pending", priority: "High" },
      { task: "Volunteer coordination", status: "Pending", priority: "Low" },
      { task: "Signage & branding production", status: "Pending", priority: "Medium" },
      { task: "Safety & compliance review", status: "Pending", priority: "High" },
    ],
    staffEstimate: Math.ceil(project.audienceSize / 100) + 5,
    daysToSetup: project.audienceSize > 2000 ? 3 : 2,
  };
}
