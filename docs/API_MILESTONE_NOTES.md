## Registry CRUD and API milestone

The registry now supports creating, reading, updating, searching, and deleting factory records. Capability entries are replaced together with factory details during an update and are removed when their factory is deleted.

### Run the Streamlit interface

```powershell
python -m streamlit run app.py
```

### Run the FastAPI backend

Open a second PowerShell terminal in the project folder, activate `.venv`, then run:

```powershell
python -m uvicorn api:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the interactive API documentation. The backend exposes `GET /health`, `POST /factories`, `GET /factories`, `GET /factories/{factory_id}`, `PUT /factories/{factory_id}`, and `DELETE /factories/{factory_id}`.

### Run all tests

```powershell
python -m pytest tests -v
```

The API and registry use the same local SQLite database. This is a local development prototype only; it has no authentication, role-based access, or production deployment configuration. Factory capability and capacity entries remain user-entered and unverified.
