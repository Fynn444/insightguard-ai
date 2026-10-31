# Architecture overview

The platform is organised into a small set of service layers to keep the application understandable and extensible:

- Presentation: Streamlit dashboard and navigation
- Workspace: workspace registry and dashboard-selected SQL filters; authentication, ownership, and authorization are not implemented
- Persistence: SQLite schema and repository helpers
- Data layer: synthetic data generator and validation utilities
- SQL analytics: reusable SQL scripts and query execution helpers
- ML layer: churn model training, evaluation, and prediction
- AI insights layer: provider-neutral request/response service, structured business context, and an explicitly simulated local mock
- Snwolley boundary: reserved for a future official provider; no endpoint, SDK, authentication, or payload contract is assumed
- Reporting: PDF and dashboard reporting
- Configuration: environment files and logging

A high-level flow is: workspace -> database -> SQL analytics -> ML model -> structured insights context -> configured insight provider -> report generation. The local mock is the only implemented provider until Npontu supplies the official Snwolley toolkit contract.

Dashboard SQL queries bind the selected workspace ID and scope customers, labels, usage, payments, segment findings, and KPI totals. This is query scoping only; there is no authenticated identity or server-side ownership check, so the current workspace selector is not a security boundary. The PDF report is rendered in memory and downloaded by the browser; report text is escaped before PDF markup parsing.

See [Snwolley integration boundary](snwolley_integration.md) for the provider interface, validation behavior, and outstanding requirements.
