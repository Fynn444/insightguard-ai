# Submission Implementation and Validation Report

## Scope note

The original Npontu practical-assignment brief was not present in the project files inspected for this report. The matrix below audits capabilities visible in the repository and the finalization checklist; it is not a claim that these rows reproduce every formal assignment requirement. Attach the original brief before making a final requirement-by-requirement certification.

## Project Capability Matrix

| Capability | Status | Evidence / limitation |
|---|---|---|
| Synthetic telecom data | Implemented | Reproducible generator includes missing, inconsistent, and outlier values. |
| SQLite persistence and seeding | Implemented | Workspace, customer, usage, payment, subscription, and churn data are seeded. |
| SQL analytics and data quality | Implemented | SQL resources are allowlisted; dashboard queries use bound workspace parameters. Existing SQL tests plus workspace-isolation tests pass. |
| Workspace-scoped dashboard | Partial | Selecting a workspace filters SQL summaries and segments. It is not secure tenant isolation because authentication and ownership checks are absent. |
| Authentication / authorization | Not implemented | No registration, login, password storage, user identity, or access-control checks exist. Do not use this prototype with private multi-tenant data. |
| Churn ML | Implemented | Logistic regression and random forest comparison; validation F1 selects the model; independent test metrics, saved pipeline, unseen-record inference, and permutation interpretation are covered by tests. |
| AI business insights | Implemented as development mock | Context is built from SQL and model results. Mock responses are validated and visibly labelled simulated. |
| Official Snwolley integration | Blocked | Npontu has not supplied official toolkit documentation or credentials. No endpoint, SDK method, auth flow, or payload format is invented. See `snwolley_integration.md`. |
| PDF reporting | Implemented | Dashboard downloads an in-memory PDF with workspace-scoped aggregate metrics, model findings, and available AI evidence/recommendations; report text is escaped. |
| Production readiness | Partial | Prototype uses synthetic data. Authentication, authorization, migrations, deployment hardening, and real provider integration remain outstanding. |

## Security and Repository Hygiene

- `.env.example` contains an empty Snwolley key and no fake endpoint. No `.env` file was present during this audit.
- SQL values are bound parameters; SQL resource names are allowlisted.
- Report download filenames are sanitized and PDFs are rendered in memory. ReportLab text is escaped.
- Insight-provider error logs omit exception contents and credentials.
- `.gitignore` excludes virtual environments, `.env` files, SQLite databases, generated data CSVs, model artifacts, PDFs, and temporary files.
- The requested `git status --short --untracked-files=all` command was attempted with the resolved Git executable and returned `fatal: not a git repository`. The workspace has no `.git` directory, so there are no Git staging/tracking records to inspect. Local databases and model artifacts match ignore patterns.
- Only load trusted local joblib model artifacts; deserialization formats based on pickle can execute code.

## Validation Results

Fresh full-suite run from the project root using `.venv\Scripts\python.exe`: **29 passed, 0 failed, 0 skipped**, pytest exit code **0**. The run collected and passed `tests/test_submission_workflow.py`; that workflow exercises synthetic seeding, workspace-scoped SQL, model persistence/training, unseen-record prediction, business-context construction, and mock insights. The full captured output is at `C:\Users\FYNN JOACHIM JUNIOR\AppData\Local\Temp\insightguard-final-submission-pytest.txt` (last written 2026-10-31 09:27:22 UTC).

Final Streamlit startup was rechecked at `http://localhost:8502`; the health endpoint returned **HTTP 200 `ok`** on 2026-10-31. The final dashboard AppTest completed without script exceptions.

The final test run reported 4,256 warnings, primarily existing `datetime.utcnow()` deprecations, a scikit-learn solver warning, Altair deprecation, and ReportLab's Python AST deprecation. These warnings did not fail tests.

## Remaining Blockers

1. Obtain the original assignment brief to certify formal requirements rather than this repository capability inventory.
2. Obtain the official Snwolley package/version, authentication and credential specification, client operations, request/response schema, documented errors/retries, data governance constraints, and sandbox procedure.
3. Implement authentication, user ownership, and authorization before storing private data or claiming tenant isolation.