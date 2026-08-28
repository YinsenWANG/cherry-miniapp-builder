# High-stakes domain boundaries

Read this for medical, mental-health, financial, legal, employment, industrial-safety, critical-infrastructure, education-assessment, insurance, or public-sector apps.

## Product boundary

Build decision support, education, organization, simulation, and draft assistance. Do not present the mini app as a licensed professional, make irreversible decisions automatically, or conceal uncertainty.

- Keep deterministic rules and calculations in code with visible formulas and source dates.
- Make inputs, assumptions, exclusions, and jurisdiction or policy version explicit.
- Separate observed facts, user-entered facts, computed results, and AI-generated interpretation.
- Require a human confirmation before exports, notifications, or external submissions.
- Provide correction and deletion paths for sensitive records.
- Use fictional sample data. Never ship real patient, employee, student, customer, or citizen data.
- Minimize retention and permissions. Avoid network access unless the workflow cannot work without an identified service.
- Do not embed credentials, regulated datasets, proprietary policy text, or personal data in the package.

## Domain-specific minimums

### Health and medicine

State that output is informational, not diagnosis or treatment. Escalate emergency symptoms to local emergency services. Cite user-supplied or bundled sources, expose uncertainty, and avoid dosage or triage automation unless the user explicitly supplies an authoritative protocol and accepts responsibility for review.

### Finance and insurance

Label estimates and market-data timestamps. Keep formulas reproducible. Do not promise returns, approve credit, set prices, or make suitability decisions. Scenario tools must expose assumptions and adverse cases.

### Legal and compliance

Identify jurisdiction and effective date. Produce checklists and drafts, not legal conclusions. Preserve source references and mark clauses or requirements that need professional review.

### Employment and education

Do not infer protected or sensitive traits. Keep compensation, performance, admissions, grading, and hiring decisions reviewable. Explain scoring criteria and provide an appeal or correction path.

### Industrial and critical systems

Keep the app advisory and offline from control loops. Never directly operate machinery, clinical devices, vehicles, utilities, or safety systems. Require operator verification, surface stale readings, and provide safe-stop guidance from an authoritative procedure only.

### Public sector

Avoid eligibility or enforcement decisions without a human owner, traceable rules, accessibility, correction channels, and jurisdiction-specific policy review.
