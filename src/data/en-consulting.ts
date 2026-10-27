// Shared content for the English consulting pages.

export const services = [
  {
    id: 'energy',
    icon: 'fa-bolt',
    title: 'Power systems & energy',
    summary: 'Optimization studies for grids, storage and renewables.',
    points: [
      'Unit commitment and economic dispatch',
      'DC and AC optimal power flow',
      'Battery storage siting and sizing',
      'Hosting capacity for loads, EV charging and renewables',
      'Robust and stochastic planning under uncertainty',
    ],
  },
  {
    id: 'scheduling',
    icon: 'fa-calendar-check',
    title: 'Scheduling & workforce rostering',
    summary: 'Production schedules and staff rosters that respect every rule.',
    points: [
      'Production and job-shop scheduling',
      'Shift rostering with labour rules, rest and fairness',
      'Resource-constrained project scheduling',
      'Constraint programming with Google OR-Tools CP-SAT',
    ],
  },
  {
    id: 'routing',
    icon: 'fa-truck-fast',
    title: 'Routing & logistics',
    summary: 'Fleet routes that cut distance, time and cost.',
    points: [
      'Vehicle routing with capacities and time windows',
      'Split deliveries and multi-depot fleets',
      'Dynamic re-optimization when new orders arrive',
      'Electric-vehicle and field-service routing',
    ],
  },
  {
    id: 'supply-chain',
    icon: 'fa-network-wired',
    title: 'Supply chain & network design',
    summary: 'Where to locate facilities and how goods should flow.',
    points: [
      'Facility location and multi-echelon network design',
      'Production and inventory planning',
      'Supplier selection and order allocation',
      'Closed-loop and reverse logistics',
    ],
  },
  {
    id: 'healthcare',
    icon: 'fa-house-chimney-medical',
    title: 'Healthcare operations',
    summary: 'Better use of staff, rooms and supplies in care delivery.',
    points: [
      'Physician and nurse rostering',
      'Operating room and appointment scheduling',
      'Patient transport and home-care routing',
      'Pharmacy and blood inventory management',
    ],
  },
  {
    id: 'model-review',
    icon: 'fa-stethoscope',
    title: 'Model review & solver performance',
    summary: 'Fix models that are infeasible, wrong or too slow.',
    points: [
      'Diagnosis of infeasible and unbounded models',
      'Reformulation for faster solve times',
      'Solver selection and tuning',
      'Migration of GAMS models to Python (Pyomo)',
    ],
  },
];

export const engagements = [
  {
    title: 'Fixed-scope pilot',
    text: 'One well-defined problem, your data, and a working model with a short report. The fastest way to test whether optimization pays off for you.',
  },
  {
    title: 'Model review',
    text: 'An independent review of an existing model or codebase: what is wrong, why, and how to fix or speed it up.',
  },
  {
    title: 'Ongoing advisory',
    text: 'Regular support for an internal team that builds and maintains optimization models.',
  },
  {
    title: 'Team training',
    text: 'Hands-on workshops in mathematical modeling, Pyomo and OR-Tools, built around your own problems.',
  },
];

export const process = [
  { title: 'Discovery call', text: 'We discuss the decision you need to make, the data you have and what a good result looks like.' },
  { title: 'Scoping proposal', text: 'A written proposal with scope, deliverables, timeline and price.' },
  { title: 'Build & validate', text: 'The model is built and validated against your rules and data, with regular check-ins.' },
  { title: 'Handover', text: 'Documented code, a results report and a walkthrough, so your team can run and extend the model.' },
];

export const credentials = [
  { icon: 'fa-briefcase', text: 'Leads optimization and OR projects at EirGrid' },
  { icon: 'fa-building-columns', text: 'Nearly a decade on the faculty of University College Dublin' },
  { icon: 'fa-book', text: 'Author, Power System Optimization Modeling in GAMS (Springer, 2017)' },
  { icon: 'fa-certificate', text: 'IEEE Senior Member' },
  { icon: 'fa-trophy', text: 'INFORMS ENRE Young Researcher Prize (2013)' },
];

export const tools = ['Python', 'Pyomo', 'Google OR-Tools', 'CP-SAT', 'GAMS', 'HiGHS', 'Gurobi', 'IPOPT'];

// Demonstration projects published on optexpert.org (Persian write-ups).
export const projects = [
  {
    slug: 'load-hosting',
    title: 'Load hosting capacity of a transmission network',
    domain: 'Power systems',
    text: 'Estimates how much additional load each bus of the IEEE 24-bus system can host, using a DC optimal power flow model, and maps the results across the network.',
    tools: ['Pyomo'],
  },
  {
    slug: 'bess-allocation',
    title: 'Battery siting to reduce renewable curtailment',
    domain: 'Power systems',
    text: 'Chooses where to place energy storage on a transmission network so that less wind and solar output is curtailed, tested on standard IEEE test systems.',
    tools: ['Pyomo', 'GAMS'],
  },
  {
    slug: 'hc-ev-chargers',
    title: 'EV charging hosting capacity of a distribution feeder',
    domain: 'Power systems',
    text: 'Finds the maximum EV charging load each bus of a distribution feeder can take under several adoption scenarios and charging profiles, without violating voltage or thermal limits.',
    tools: ['Pyomo'],
  },
  {
    slug: 'community-energy-v2g-system',
    title: 'Community energy management with solar, storage and V2G',
    domain: 'Energy',
    text: 'Optimal dispatch of rooftop solar, household and shared batteries, and bidirectional EV charging in a 75-home community, within the feeder capacity and with peak reduction.',
    tools: ['Pyomo'],
  },
  {
    slug: 'energy-water-system',
    title: 'Integrated energy–water system design and operation',
    domain: 'Energy',
    text: 'Sizes and schedules hourly operation of a wind, solar, battery and desalination system over a five-year horizon, minimizing cost and carbon emissions.',
    tools: ['Pyomo'],
  },
  {
    slug: 'dynamic-vrp-reoptimization',
    title: 'Dynamic vehicle routing with real-time re-optimization',
    domain: 'Logistics',
    text: 'When a new order arrives or data changes, only the remaining part of each route is re-planned, quickly enough to use during operations.',
    tools: ['OR-Tools'],
  },
  {
    slug: 'hospital-doctor-shift-scheduling',
    title: 'Hospital physician shift scheduling',
    domain: 'Healthcare',
    text: 'Rosters physicians and residents with full shift coverage, rest after night shifts, limits on working days, fair distribution of nights and continuity of care.',
    tools: ['OR-Tools', 'CP-SAT'],
  },
  {
    slug: 'hiring-training-optimization',
    title: 'Hiring and training plan under budget and deadline',
    domain: 'Workforce',
    text: 'Assigns candidates to positions and schedules training to close skill gaps, within hiring and training budgets and a readiness deadline.',
    tools: ['OR-Tools', 'CP-SAT'],
  },
];
