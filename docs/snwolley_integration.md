# Snwolley Integration Boundary

## Current status

InsightGuard AI has a provider-neutral insights service and a deterministic development mock. The mock consumes a structured context built from the SQLite dashboard summary, customer segments, revenue and data-quality results, and the trained model's validation/test findings. Dashboard output is labelled `DEVELOPMENT MOCK OUTPUT` and is not represented as a Snwolley response.

No official Snwolley endpoint, SDK, authentication scheme, or request/response schema has been implemented or assumed. When mock mode is disabled, the application fails safely with a clear configuration message and makes no network request. Credentials alone are not sufficient to enable an integration without the provider contract.

## Architecture

1. `build_business_context` in `insightguard/insights/context.py` selects and JSON-normalizes business KPIs, top churn segments, revenue/data-quality results, model comparison metrics, and validation-set feature importance.
2. `InsightService` in `insightguard/insights/service.py` accepts an `InsightProvider`, sends an `InsightRequest`, validates required response fields and provider provenance, logs failures, and raises typed errors.
3. `MockInsightsProvider` in `insightguard/insights/mock.py` builds cautious summaries and review actions from the supplied data. Its `provider` and `simulated` fields are validated by the service.
4. `SnwolleyClient` in `insightguard/snwolley/interface.py` remains a compatibility boundary. It uses the mock when explicitly configured and otherwise reports that official setup is unavailable.
5. `app.py` displays provider provenance, evidence, and recommendations; the SQL analytics and ML evaluation remain independent of provider availability. Downloaded PDF reports label synthetic data and simulated insights.

## Security notes

- The dashboard scopes its SQL queries to the selected workspace with bound parameters. This is not authorization: there is no user login, ownership relationship, or permission check.
- Insight context contains aggregate SQL and model findings, not customer-level records. Review Npontu's data handling requirements before any future provider receives data.
- Provider failures are logged without logging exception messages or credentials.
- Generated joblib models are local trusted artifacts. Do not load model files supplied by untrusted users because joblib/pickle-based formats can execute code during deserialization.

## Required from Npontu

Before adding an official provider, obtain and verify:

- Official toolkit/package name, supported version, installation instructions, and supported Python versions.
- Authentication method, credential names/format, secure storage guidance, and credential rotation expectations.
- Official client construction and operation names/signatures, including whether the toolkit is local or network-backed.
- Request schema, accepted context fields, size limits, and any required task/instruction format.
- Response schema, validation rules, confidence semantics, and documented error types.
- Timeout, retry, rate-limit, and availability guidance.
- Data retention, privacy, residency, and restrictions on sending synthetic or customer-level information.
- A minimal official example and sandbox/test procedure, plus any deployment/network requirements.

Until these details are supplied, keep `SNWOLLEY_USE_MOCK=true`. Do not populate invented base URLs or placeholder credentials; do not interpret mock output as model output or a real Snwolley response.