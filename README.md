# InsightGuard AI

InsightGuard AI is a prototype for an AI-augmented machine learning analytics platform for telecom retention analysis. It includes a SQLite-backed Streamlit dashboard, SQL analytics, churn modeling, and a clearly labelled mock Snwolley Agent boundary. The original assignment brief was not present in the workspace, so formal requirement compliance should be checked against the supplied brief before submission.

## Architecture

- Presentation layer: Streamlit UI in `app.py`
- Workspace layer: `insightguard/workspace.py`
- Persistence layer: `insightguard/db/`
- Data generation: `insightguard/data/generator.py`
- Validation: `insightguard/data/validator.py`
- SQL analysis: `sql/*.sql` and `insightguard/analytics/sql_queries.py`
- Machine learning: `insightguard/ml/pipeline.py`
- AI insights: `insightguard/insights/` provider-neutral service and structured business context
- Snwolley boundary: `insightguard/snwolley/interface.py` (mock-only until official toolkit details are supplied)
- Reporting: `insightguard/reporting/report_generator.py`
- Configuration: `insightguard/config.py` and `.env.example`

## Project structure

```text
insightguard-ai/
├── app.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── data/
├── docs/
├── scripts/
├── sql/
├── tests/
└── insightguard/
    ├── __init__.py
    ├── analytics/
    ├── config.py
    ├── data/
    ├── db/
    ├── logging.py
    ├── ml/
    ├── reporting/
    ├── snwolley/
    └── use_cases/
```

## Windows setup

1. Open a terminal in the project folder.
2. Create a virtual environment:

```powershell
py -3.13 -m venv .venv
```

3. Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. Copy the example environment file and adjust values if needed:

```powershell
Copy-Item .env.example .env
```

6. Initialise the database and generate the synthetic dataset:

```powershell
python scripts\init_db.py
python scripts\generate_data.py
```

7. Run the app:

```powershell
streamlit run app.py
```

## Use case

The first implemented use case is customer churn prediction for a telecom business. The platform can be extended through the use-case registry in `insightguard/use_cases/registry.py`.

## Using the dashboard

- Select an existing workspace in the sidebar or enter a new workspace ID and create a synthetic demo workspace.
- Review workspace-scoped customer, churn, revenue, segment, and data-quality analytics.
- Review historical ML model comparison and held-out evaluation separately from the form for new-record churn predictions.
- Review the AI insights evidence and suggested actions. The local response is explicitly labelled as development mock output.
- Select **Download business report (PDF)** to export the currently selected workspace's aggregate metrics, model findings, and available insight text.

Workspace filters prevent accidental aggregation across workspaces in dashboard queries, but there is no login, workspace owner, or authorization check. Do not treat this selector as tenant security.

## Data and SQL

The synthetic data generator produces a telecom customer dataset with realistic imperfections, including missing values, inconsistent categories, and outlier values. SQL scripts in the `sql/` directory cover:

- segmentation and churn analysis
- revenue summary
- data-quality checks
- engagement decline analysis

The app uses the dataset and SQL outputs to ground the business analytics story.
SQL dashboard results are filtered to the selected workspace using bound parameters. This reduces accidental cross-workspace aggregation in the UI, but it is not an authorization boundary because the prototype has no login or user ownership model.

## Machine learning

The churn pipeline compares balanced logistic regression and random forest models using the same stratified train/validation/test split. Validation F1 selects the model; test metrics remain independent. The fitted preprocessing/model pipeline is saved under `data/models/`, and inference accepts new customer records without a churn label. Generated model files are ignored by Git.

## AI Insights and Snwolley

Business insight requests use a provider-neutral service contract and context built from the actual SQLite SQL summary and held-out ML findings. Local development uses a deterministic mock whose output is labelled as simulated in the dashboard. No real Snwolley API integration is implemented: the official toolkit documentation and credentials have not been provided. See [the integration boundary guide](docs/snwolley_integration.md) for details and the exact information needed before implementation.

## Testing

Run the automated checks from the project root:

```powershell
python -m pytest -q
```

## Report generation

Use **Download business report (PDF)** on the dashboard to download a report containing workspace-scoped KPI summaries, selected model results, and available AI evidence/recommendations. The report is generated in memory; text is escaped before it is passed to the PDF renderer. Reports identify synthetic data and simulated AI output.

## Limitations

- No real Snwolley API credentials or toolkit were provided in the workspace.
- Authentication, user ownership, and authorization are not implemented. Workspace selection scopes dashboard SQL only and must not be treated as secure tenant isolation.
- This is a prototype and not production-hardened security software.
- The app uses synthetic data only.

## Security and production notes

Before production deployment, the platform should add stronger authentication, RBAC, HTTPS, backup scheduling, audit logging, and migration tooling. The README intentionally keeps the prototype focused on a working demonstration.
