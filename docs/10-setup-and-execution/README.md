# Document 10 --- Project Setup, Installation and Execution Guide

## 1. Purpose

This guide explains how to prepare the local development environment,
configure PostgreSQL, install backend and frontend dependencies, start
the research prototype, and verify that the dashboard can retrieve
experiment data.

The instructions reflect the project's known Windows development
environment and current architecture: a Python/FastAPI/PyTorch backend,
PostgreSQL persistence, and a React/Vite/TypeScript frontend.

Some environment-specific values and the exact FastAPI ASGI module path
must be taken from the current checkout. They are marked clearly rather
than guessed.

## 2. Project Structure

The project root is:

``` text
federated-healthcare-research/
├── backend/
│   ├── .venv/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── experiments/
│   │   └── ml/
│   ├── alembic/
│   ├── tests/
│   └── ...
└── frontend/
    ├── node_modules/
    ├── src/
    │   ├── components/
    │   ├── lib/
    │   ├── App.tsx
    │   ├── App.css
    │   ├── index.css
    │   └── main.tsx
    ├── package.json
    ├── package-lock.json
    └── vite.config.ts
```

The root directory may contain additional local files created during
development. The structure above highlights the main application
directories and is not intended as a complete listing of every file.

## 3. Prerequisites

Install or prepare the following tools:

  Tool                 Purpose
  -------------------- -----------------------------------------------------
  Windows PowerShell   Run the documented local commands
  Python 3.13.14       Backend runtime used in the development environment
  Node.js and npm      Frontend runtime and dependency management
  PostgreSQL           Relational database
  Git                  Source control
  PyCharm or VS Code   Optional development environment

The frontend uses Vite, React, TypeScript, Tailwind CSS, React Query,
Axios, React Router, Recharts, and Lucide icons.

The backend uses FastAPI, SQLAlchemy, Alembic, PyTorch, and pg8000 for
PostgreSQL connectivity in the documented Windows setup.

Use the Python and Node versions recorded by the project when
reproducing an existing environment. If the repository later adds
version pinning files, treat those as authoritative.

## 4. Clone or Open the Project

If the project is already present locally, open its root directory:

``` text
E:\projects\federated-healthcare-research
```

If setting it up from source control, clone the repository using its
actual remote URL:

``` powershell
git clone <repository-url>
cd federated-healthcare-research
```

The repository URL is intentionally shown as a placeholder because it
was not established in the project notes used for this guide.

## 5. PostgreSQL Setup

### 5.1 Start PostgreSQL

Ensure the PostgreSQL service is installed and running.

Create a development database and a database user, or use an existing
local development role with the required permissions.

Example SQL (adapt the database name and credentials to the local
environment):

``` sql
CREATE DATABASE federated_healthcare;
```

The database name above is an example. The actual database name,
username, and password must match the backend configuration.

### 5.2 Configure the connection

The backend uses centralized configuration under:

``` text
backend/app/core/config.py
backend/app/core/database.py
```

Set the database connection value expected by the current settings
implementation. The documented Windows environment uses the SQLAlchemy
`pg8000` dialect, with a connection URL in this form:

``` text
postgresql+pg8000://<username>:<password>@<host>:<port>/<database>
```

Do not commit real credentials to source control. Use the project's
supported environment-variable or local configuration mechanism.

### 5.3 Windows SQLAlchemy compatibility setting

The documented development environment used this setting because of a
Windows Application Control restriction affecting compiled SQLAlchemy
extensions:

``` powershell
$env:DISABLE_SQLALCHEMY_CEXT = "1"
```

This is a development-environment workaround. It is not a requirement of
PostgreSQL itself.

## 6. Backend Environment Setup

Open PowerShell and move into the backend directory:

``` powershell
cd E:\projects\federated-healthcare-research\backend
```

### 6.1 Create a virtual environment

If the existing `.venv` is not present, create it:

``` powershell
py -3.13 -m venv .venv
```

Activate it:

``` powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation due to the current execution policy,
follow the machine's approved policy for running local
virtual-environment activation scripts. Do not change system policy
without understanding the security implications.

### 6.2 Confirm Python

``` powershell
python --version
```

The documented development environment used Python 3.13.14.

### 6.3 Install dependencies

Use the dependency manifest committed in the current backend checkout,
if present. For a `requirements.txt` file:

``` powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the project uses a different dependency-management file, follow that
file's installation instructions instead. Do not create a second
dependency list that can drift from the actual project.

The documented backend dependency set includes FastAPI, SQLAlchemy,
Alembic, PyTorch, Pydantic-related FastAPI dependencies, and pg8000. The
exact pinned versions should be read from the current dependency
manifest.

## 7. Database Migrations

The project uses Alembic for migration management.

With the backend virtual environment active and the working directory
set to `backend`, inspect the current migration state:

``` powershell
python -m alembic current
python -m alembic history
```

Apply migrations:

``` powershell
python -m alembic upgrade head
```

Check for model changes that are not reflected in migration scripts:

``` powershell
python -m alembic check
```

The project used `python -m alembic` in its Windows environment rather
than relying on an `alembic.exe` shim.

### Important migration caveat

At the documented project state, `client_training_metrics` had been
created manually and was not yet represented in Alembic migration
history. A developer database that already contains this table may work,
while a fresh database created only from migrations may not contain it.

Before treating a clean installation as reproducible, add the table to
the migration chain or otherwise reconcile the schema and migration
history. Verify the current repository before running migrations against
an existing database.

## 8. Start the Backend

The FastAPI application is exposed through an ASGI application object.
The exact import path depends on the current application entry point and
must be confirmed from the backend source.

Locate the file that creates the FastAPI instance and identify its
variable name (commonly `app`). Then start Uvicorn using the matching
module path:

``` powershell
python -m uvicorn <module_path>:<asgi_variable> --host 127.0.0.1 --port 8000 --reload
```

For example, only if the application object is `app` in `app.main`, the
command would be:

``` powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Do not use the example until the module path has been verified in the
current checkout.

The expected local backend address used by the frontend proxy is:

``` text
http://127.0.0.1:8000
```

## 9. Verify Backend Health

With the backend running, open these paths in a browser or call them
from an HTTP client:

``` text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/health/database
```

The first checks that the API responds. The second checks database
connectivity from the backend.

Open FastAPI's interactive API documentation:

``` text
http://127.0.0.1:8000/docs
```

Use this page to inspect the actual routes, request parameters, response
schemas, and status codes exposed by the running application.

## 10. Frontend Environment Setup

Open a second PowerShell terminal and move into the frontend directory:

``` powershell
cd E:\projects\federated-healthcare-research\frontend
```

Confirm Node.js and npm are available:

``` powershell
node --version
npm --version
```

Install dependencies from the committed lockfile:

``` powershell
npm ci
```

If the lockfile is not available or has intentionally changed, use:

``` powershell
npm install
```

The project frontend dependencies include:

-   React and React DOM.
-   TypeScript and Vite.
-   Tailwind CSS and the Vite Tailwind plugin.
-   Axios.
-   TanStack React Query.
-   React Router.
-   Recharts.
-   Lucide React.

The package manifest and lockfile in `frontend/` are the authoritative
dependency definitions.

## 11. Frontend API Proxy Configuration

The Vite configuration forwards `/api` requests to the local backend:

``` ts
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
}
```

The frontend Axios client uses:

``` ts
baseURL: '/api/v1'
```

Together, these settings allow a frontend request such as
`/api/v1/experiments` to be forwarded to the FastAPI server at
`127.0.0.1:8000`.

If the backend is running on a different host or port, update the Vite
proxy target accordingly.

## 12. Start the Frontend

From the `frontend` directory:

``` powershell
npm run dev
```

Vite prints the local development URL in the terminal. Open the
displayed address in a browser.

Keep the frontend and backend terminals running while using the
dashboard.

## 13. Recommended Startup Order

For a local development session, use this order:

1.  Start PostgreSQL.
2.  Activate the backend virtual environment.
3.  Set the required local environment variables.
4.  Confirm database configuration.
5.  Apply or verify Alembic migrations.
6.  Start the FastAPI backend on port `8000`.
7.  Verify the health and database-health endpoints.
8.  Start the Vite frontend.
9.  Open the dashboard in the browser.

This order makes it easier to distinguish database, backend, and
frontend startup problems.

## 14. Verify Experiment Data

After the API and frontend are running, verify the experiment endpoints:

``` text
GET /api/v1/experiments
GET /api/v1/experiments/summary
GET /api/v1/experiments/{experiment_id}
GET /api/v1/experiments/{experiment_id}/metrics
```

The project has recorded these experiment IDs in its development
database:

  Experiment             ID
  ---------------------- ----------------------------------------
  Local training         `a0c0696f-35fd-429e-b86c-cc202e075381`
  Centralized baseline   `ca672b33-5b23-420b-99b4-78ac8322ffc9`
  Standard FedAvg        `bdaf2928-fed6-4ae3-9767-7a5e75427d8f`
  DP-FedAvg              `b0de2782-d703-4148-b9ea-cef21f5cda45`

These are identifiers from the recorded development runs. They will only
be present in a database that contains those experiment records.

The dashboard should display persisted results, including the experiment
list, model comparisons, federated rounds, client training metrics, and
privacy accounting where records exist.

## 15. Run Backend Tests

The backend test suite had reached 62 passing tests at the documented
project stage.

With the backend virtual environment active and the current directory
set to `backend`, run:

``` powershell
python -m pytest
```

To run a specific test directory, use the path that exists in the
current checkout, for example:

``` powershell
python -m pytest tests
```

Use the actual test layout if it differs. A passing test suite validates
the covered behavior; it does not prove that every research feature
described in the broader project vision is implemented.

## 16. Build the Frontend

From the `frontend` directory:

``` powershell
npm run build
```

The configured build script runs TypeScript project checks and then
creates the Vite production bundle.

To preview the built frontend locally:

``` powershell
npm run preview
```

Use the URL printed by Vite. A production deployment also needs an
appropriate backend URL or reverse-proxy configuration.

## 17. Common Development Issues

### 17.1 Frontend cannot reach the API

Check:

-   Is the FastAPI backend running?
-   Is it listening on `127.0.0.1:8000`?
-   Does `vite.config.ts` point to the correct backend address?
-   Is the frontend request using `/api/v1`?
-   Does the browser's network panel show a proxy or backend error?

### 17.2 Database health check fails

Check:

-   Is PostgreSQL running?
-   Is the configured host and port correct?
-   Does the database exist?
-   Are the username and password correct?
-   Is the `pg8000` driver installed in the active virtual environment?
-   Does the connection URL use the expected SQLAlchemy dialect?

### 17.3 Alembic command is unavailable

Use:

``` powershell
python -m alembic current
```

rather than relying on a globally installed executable. Confirm the
backend virtual environment is activated and Alembic is installed.

### 17.4 SQLAlchemy compiled-extension restriction

In the documented Windows environment, set:

``` powershell
$env:DISABLE_SQLALCHEMY_CEXT = "1"
```

Then rerun the backend command in the same PowerShell session.

### 17.5 Frontend dependency mismatch

From `frontend`, use:

``` powershell
npm ci
```

to install from the lockfile. If dependencies were deliberately changed,
update and commit the package manifest and lockfile together.

### 17.6 Experiment list is empty

An empty experiment list may mean the database is reachable but does not
contain the recorded experiment rows. Check the configured database and
query the experiment endpoint before assuming the frontend is broken.

### 17.7 Client metrics are missing on a fresh database

Check whether the `client_training_metrics` table exists. At the
documented project state it was manually created and not yet included in
Alembic history, so a fresh migration-only database may not contain it.

## 18. Research and Data Safety Notes

-   Use the public WDBC benchmark or other appropriately licensed
    public/synthetic datasets.
-   Do not insert real patient records into this prototype.
-   Do not present the model as a clinical diagnostic tool.
-   The three client identities represent simulated institutions.
-   The DP-FedAvg result is client-level under the documented
    replace-one-client adjacency, not patient-level DP.
-   Secure aggregation, non-IID experiments, and malicious-client
    robustness are not part of the currently completed implementation.
-   Keep database credentials and local secrets out of Git.

## 19. Local Development Checklist

Use this checklist when preparing a development session:

-   [ ] PostgreSQL service is running.
-   [ ] Backend virtual environment is activated.
-   [ ] Backend dependencies are installed.
-   [ ] Database connection settings are configured.
-   [ ] Alembic migration state has been checked.
-   [ ] `client_training_metrics` schema availability has been verified.
-   [ ] Backend starts successfully.
-   [ ] Backend health endpoint responds.
-   [ ] Database health endpoint responds.
-   [ ] Frontend dependencies are installed.
-   [ ] Vite proxy points to the running backend.
-   [ ] Frontend starts successfully.
-   [ ] Experiment list and summary endpoints return expected data.
-   [ ] Dashboard pages render persisted experiment metrics.
-   [ ] Backend tests pass.
-   [ ] Frontend production build succeeds.

## 20. Summary

The research prototype runs locally as two application processes backed
by PostgreSQL: a FastAPI/PyTorch backend and a React/Vite frontend.
PostgreSQL stores experiment metadata and result records. The backend
exposes those records through read-only APIs, and the frontend retrieves
them through Axios and React Query.

The documented Windows setup uses Python 3.13.14, a backend virtual
environment, SQLAlchemy with the `pg8000` dialect, Alembic migrations,
and npm-managed frontend dependencies. The exact backend ASGI module
path, dependency manifest, environment-variable names, and database
credentials must be verified from the current checkout and local
environment.

One known setup caveat is that `client_training_metrics` was manually
created and had not yet been added to Alembic migration history at the
documented project state. Resolve that migration gap before relying on a
clean database installation.
