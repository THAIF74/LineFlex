# LineFlex

### Manufacturing Flexibility & Second-Source Readiness

LineFlex is an early-stage project exploring how manufacturers can prepare for production changes and supplier disruption through structured capability information, scenario planning, and second-source qualification tracking.

> **Current status:** Working local Factory Capability Registry with Streamlit, SQLite and a FastAPI backend.

## What works today

- Register factories and their locations.
- Record stated monthly production capacity and units.
- Record machines, processes, materials and certifications.
- Search and view factory records.
- Edit factory details and capability entries.
- Delete factory records and their associated capabilities.
- Access factory records through REST API endpoints.
- Validate required fields and positive finite capacity values.

## Technology

- Python 3.11
- Streamlit
- FastAPI
- SQLite
- Pandas
- Pytest
- Uvicorn

## Run locally

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the Streamlit application:

```powershell
python -m streamlit run app.py
```

Start the API in a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api:app --reload
```

Open:
- Streamlit: http://localhost:8501
- API documentation: http://127.0.0.1:8000/docs

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Health check |
| POST | /factories | Create factory |
| GET | /factories | List and search factories |
| GET | /factories/{factory_id} | Read factory |
| PUT | /factories/{factory_id} | Update factory |
| DELETE | /factories/{factory_id} | Delete factory |

## Tests

Run:

```powershell
python -m pytest tests -v
```

The current local test run passed all 17 tests, covering API operations, database CRUD, search and validation.

## Planned modules

- Production Flexibility Planner
- Second-Source Readiness
- Qualification Workspace
- Activation Workflow

## Current limitations

- Factory capacity and capabilities are user-entered and unverified.
- No automatic engineering compatibility assessment is performed.
- No supplier or certification claims are independently verified.
- No authentication, roles or multi-user access.
- No production deployment or customer approval workflow.
- Market demand and willingness to pay remain unvalidated.

LineFlex is a planning and record-keeping prototype, not a certification or engineering approval system. Real production transfers require appropriate technical checks and customer approvals.

See [docs/ROADMAP.md](docs/ROADMAP.md) for project progress.

## Factory data review metadata

The API also supports factory-level provenance and review labels:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /factories/{factory_id}/review | Read source and review metadata |
| PUT | /factories/{factory_id}/review | Save source, status, evidence reference and reviewer label |

Review statuses are user-entered labels: Unverified, Self-declared, Evidence attached, and Reviewed. An evidence reference is a text reference only; the prototype does not upload, inspect, authenticate or independently verify documents. A Reviewed label records a user's declaration, not LineFlex certification.
