# Domain template index

The searchable catalog currently contains 200 patterns across 25 domain families. Run `python3 scripts/search_templates.py "<user need>"` and read only returned records. Use `--category <id> --limit 8` to inspect a whole family. A record's capabilities are possible capabilities (须按实际调用重推最小 leaf), never a permission grant.

Every result now carries four build decisions in addition to its domain workflow:

- one of twelve product archetypes from [archetypes.md](archetypes.md);
- concrete required capabilities for the core loop;
- optional capabilities that must fail gracefully;
- an AI mode: `core`, `enhancement`, or `none`.

These are opinionated one-shot defaults, not permissions inferred from a category. Re-check them against the exact requested workflow before packaging.

| Category id | Coverage |
|---|---|
| `data-analytics` | KPI, CSV profiling, cohort/funnel, anomaly, forecast, survey, experiment, narrative reporting |
| `office-admin` | meeting actions, documents, decisions, SOP, schedules, procurement, assets, workspace planning |
| `hr-payroll` | salary, headcount, shifts, leave, onboarding, skills, performance, compensation scenarios |
| `finance-accounting` | cash flow, budgeting, invoices, expenses, pricing, unit economics, tax preparation, close |
| `sales-crm` | pipeline, account plans, proposals, discovery, territory, renewals, forecasting, call coaching |
| `marketing-growth` | campaigns, content, SEO, experiments, personas, launches, attribution, community |
| `customer-support` | triage, knowledge, QA, incident communication, feedback, success plans, SLA, handoffs |
| `retail-ecommerce` | assortment, inventory, merchandising, returns, reviews, stores, promotions, marketplace ops |
| `hospitality-events` | itinerary, venue, restaurant, hotel, events, catering, guest service, local guide |
| `transport-travel` | fleet, route, trip cost, dispatch, maintenance, commute, travel risk, passenger information |
| `education-learning` | study plans, quizzes, tutoring, rubrics, language, labs, courses, parent communication |
| `research-science` | experiment design, literature, statistics, units, lab notebook, simulation, reproducibility, grants |
| `software-engineering` | API explorer, logs, releases, architecture, test data, regex, performance, incident review |
| `creative-media` | storyboards, brand kits, podcasts, photography, scripts, exhibitions, music practice, editorial |
| `games-interactive` | puzzles, trivia, strategy, simulation, tabletop, learning games, party games, wellness games |
| `manufacturing` | OEE, quality, maintenance, work instructions, SPC, changeover, energy, production scheduling |
| `construction-real-estate` | estimates, inspections, property analysis, punch lists, leases, site diaries, space, handover |
| `logistics-supply-chain` | shipment, warehouse, suppliers, demand, containers, cold chain, procurement risk, fulfillment |
| `agriculture-environment` | crops, irrigation, livestock, soil, biodiversity, waste, carbon, environmental sampling |
| `energy-utilities` | bills, solar, batteries, load, outages, audits, charging, utility field work |
| `healthcare-wellness` | symptom journaling, medication records, clinical education, rehab, nutrition, sleep, care coordination, public health |
| `legal-compliance` | contract review, policy mapping, privacy, evidence, obligations, licensing, audit, regulatory change |
| `security-risk` | threat modeling, vendor risk, phishing drills, access review, continuity, vulnerability triage, fraud, safety |
| `public-nonprofit` | grants, volunteers, cases, consultations, benefits navigation, community assets, emergency info, impact |
| `personal-family` | budgets, meals, habits, home inventory, family schedules, travel packing, reading, major decisions |

Catalog files live under `references/domains/`. The records are compact design seeds, not claims that every listed workflow is safe to automate. Apply [high-stakes-domains.md](high-stakes-domains.md) whenever applicable.
