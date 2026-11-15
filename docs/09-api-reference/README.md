# Document 09 --- API Reference and Backend Integration

## 1. Purpose

This document describes the HTTP API currently exposed by the Federated
Healthcare Research backend for health checks, experiment discovery,
dashboard summaries, experiment details, and experiment metrics.

It also explains how the React frontend consumes these endpoints and how
the backend's router, service, repository, ORM, and response-schema
layers fit together.

This reference documents the read-only dashboard API that has been
implemented and verified in the project context. It does not invent
request bodies, query parameters, response fields, authentication
requirements, or write operations that have not been established.

## 2. API Overview

The backend is implemented with FastAPI. The versioned API prefix used
by the frontend is:

``` text
/api/v1
```

The frontend uses an Axios client configured with `/api/v1` as its base
URL. During local development, Vite proxies `/api` requests to the
backend at:

``` text
http://127.0.0.1:8000
```

This keeps frontend requests on the Vite origin while forwarding API
traffic to the FastAPI development server.

### Implemented endpoints

  -----------------------------------------------------------------------------------------------
  Method                  Endpoint                                        Purpose
  ----------------------- ----------------------------------------------- -----------------------
  GET                     `/api/v1/health`                                Backend health check

  GET                     `/api/v1/health/database`                       Database connectivity
                                                                          health check

  GET                     `/api/v1/experiments`                           List recorded
                                                                          experiments

  GET                     `/api/v1/experiments/summary`                   Retrieve dashboard
                                                                          summary information

  GET                     `/api/v1/experiments/{experiment_id}`           Retrieve one experiment

  GET                     `/api/v1/experiments/{experiment_id}/metrics`   Retrieve metrics
                                                                          associated with one
                                                                          experiment
  -----------------------------------------------------------------------------------------------

The endpoints above are read operations. The documented dashboard
integration does not trigger model training or create new experiments
through HTTP.

## 3. Local Development Request Flow

``` mermaid
flowchart LR
    A[React page or component] --> B[Axios API client]
    B --> C[Vite /api proxy]
    C --> D[FastAPI application]
    D --> E[Versioned API router]
    E --> F[Endpoint router]
    F --> G[Experiment service]
    G --> H[Experiment repository]
    H --> I[SQLAlchemy models]
    I --> J[(PostgreSQL)]
    J --> H
    H --> G
    G --> K[Pydantic response schemas]
    K --> F
    F --> B
    B --> A
```

The frontend does not query PostgreSQL directly. It calls the backend
API, and the backend owns database access and response construction.

## 4. Health Endpoints

### 4.1 Backend health

``` http
GET /api/v1/health
```

**Purpose:** Provides a basic health endpoint for checking whether the
API process is responding.

The exact response JSON shape is not reproduced here because it was not
captured in the verified endpoint notes. Use the running service's
FastAPI OpenAPI documentation for the authoritative response schema.

### 4.2 Database health

``` http
GET /api/v1/health/database
```

**Purpose:** Checks database connectivity from the backend.

This endpoint is useful during local setup because the API process can
be running even when its database connection is not healthy.

The exact response JSON shape and status-code mapping should be
confirmed from the current route implementation or OpenAPI document
before being copied into an external API contract.

## 5. Experiment List Endpoint

``` http
GET /api/v1/experiments
```

**Purpose:** Returns the recorded experiments available to the
dashboard.

The frontend uses this endpoint to populate experiment lists and
identify experiment records for detailed metric requests.

The current project includes these experiment types:

-   `centralized`
-   `fedavg`
-   `dp_fedavg`
-   `local_training`

The exact set of serialized experiment fields should be taken from the
current `ExperimentRead` schema and the live OpenAPI output. This
document does not assume undocumented filters, pagination parameters, or
sorting parameters.

### Frontend integration

The frontend API module exposes:

``` ts
getExperiments()
```

React Query components use this function to load the experiment
collection and render experiment lists, filters, and selection controls.

## 6. Dashboard Summary Endpoint

``` http
GET /api/v1/experiments/summary
```

**Purpose:** Returns aggregate information used by the dashboard
overview.

The frontend API module exposes:

``` ts
getDashboardSummary()
```

The dashboard uses the summary data for its top-level KPIs and
experiment overview.

The currently displayed overview includes:

-   Number of recorded experiments.
-   Best recorded accuracy.
-   Configured client count.
-   Latest/final privacy epsilon represented by the available DP
    experiment data.

The displayed values are sourced from persisted experiment data. They
are not hard-coded demonstration values.

The precise JSON property names and calculation rules should be read
from `DashboardSummary` and the backend summary service. They are not
guessed in this reference.

## 7. Experiment Detail Endpoint

``` http
GET /api/v1/experiments/{experiment_id}
```

**Purpose:** Retrieves the metadata for one experiment identified by its
UUID.

Example using a recorded experiment identifier:

``` http
GET /api/v1/experiments/b0de2782-d703-4148-b9ea-cef21f5cda45
```

The detail view uses experiment metadata to explain which algorithm ran
and which configuration was recorded.

Relevant configuration concepts include:

-   Algorithm.
-   Dataset.
-   Client count.
-   Communication rounds.
-   Local epochs.
-   Partition strategy.
-   Differential-privacy configuration.
-   Secure-aggregation configuration.
-   Experiment status and timestamps.

The authoritative serialized field set is defined by the current
`ExperimentRead` response schema.

## 8. Experiment Metrics Endpoint

``` http
GET /api/v1/experiments/{experiment_id}/metrics
```

**Purpose:** Retrieves the stored metrics associated with a particular
experiment.

This endpoint is the main data source for the experiment detail pages
and several analytics views.

The response model is:

``` text
ExperimentMetricsResponse
```

The response includes the metric groups represented by the following
schemas:

  Schema                       Data represented
  ---------------------------- -------------------------------------------
  `CentralizedMetricRead`      Centralized baseline evaluation
  `FederatedRoundRead`         Per-round federated evaluation metrics
  `PrivacyMetricRead`          Per-round privacy-accounting measurements
  `ClientTrainingMetricRead`   Per-client local training measurements

The service retrieves client-training metrics by experiment ID and
includes them in the metrics response. The repository orders
client-training records by creation time.

### Example experiment IDs

  Experiment type        Experiment ID
  ---------------------- ----------------------------------------
  Local training         `a0c0696f-35fd-429e-b86c-cc202e075381`
  Centralized baseline   `ca672b33-5b23-420b-99b4-78ac8322ffc9`
  Standard FedAvg        `bdaf2928-fed6-4ae3-9767-7a5e75427d8f`
  DP-FedAvg              `b0de2782-d703-4148-b9ea-cef21f5cda45`

These identifiers refer to the currently recorded research runs. A local
database may contain different IDs if experiments are recreated.

## 9. Response Schema Responsibilities

The backend uses response schemas to define the data returned by its
API. The established schema names include:

-   `ExperimentRead`
-   `CentralizedMetricRead`
-   `FederatedRoundRead`
-   `PrivacyMetricRead`
-   `ClientTrainingMetricRead`
-   `ExperimentMetricsResponse`
-   `ExperimentPerformance`
-   `DashboardSummary`

The purpose of these schemas is to keep API responses explicit and
separate from ORM persistence models.

A schema name alone does not establish every field, type, default, or
nullability rule. For an exact field-by-field contract, inspect the
current `app/experiments/schemas.py` file and the FastAPI-generated
OpenAPI document.

### Nullable measurements

Some experiment paths do not produce every possible metric. For example,
DP-FedAvg persisted round rows intentionally leave `training_loss` and
`training_accuracy` as `NULL`.

Frontend code should preserve that distinction:

-   `null` means the value was not recorded or is not available for that
    metric.
-   `0` is a real numeric value and must not be used as a substitute for
    missing data.

## 10. Backend Layer Responsibilities

The API is structured into distinct layers.

### 10.1 FastAPI application and router registration

The application entry point creates the FastAPI app and includes the
versioned API router. The versioned router groups the health and
experiment routers under the `/api/v1` prefix.

### 10.2 Endpoint routers

The health and experiment routers define the HTTP paths and connect
incoming requests to backend logic.

The experiment router exposes the list, summary, detail, and metrics
read paths.

### 10.3 Service layer

The experiment service coordinates retrieval and constructs the response
data expected by the API schemas.

For experiment metrics, it gathers the relevant metric groups, including
client-training records.

### 10.4 Repository layer

The experiment repository performs database queries. This keeps query
logic out of the HTTP route functions and allows the service layer to
work with a defined persistence interface.

### 10.5 ORM and database layer

SQLAlchemy models represent persisted experiments and their metrics.
Database configuration and session handling are centralized under
`app/core`.

### 10.6 Response schemas

Pydantic response schemas define the API output shape and provide a
boundary between internal persistence models and frontend-facing data.

## 11. Frontend API Client

The frontend centralizes HTTP access in:

``` text
frontend/src/lib/api.ts
```

The Axios client uses the base URL:

``` ts
baseURL: '/api/v1'
```

The API module provides these functions:

``` ts
getDashboardSummary()
getExperiments()
getExperimentMetrics(experimentId)
getHealth()
```

The functions are used by the React pages rather than duplicating Axios
request configuration inside every component.

The module also defines TypeScript interfaces used by the UI, including:

-   `Experiment`
-   `ExperimentPerformance`
-   `DashboardSummary`
-   `FederatedRound`
-   `PrivacyMetric`
-   `ExperimentMetrics`

These TypeScript interfaces should remain aligned with the backend's
actual Pydantic response schemas. If a backend response field changes,
update the corresponding frontend type and the components that consume
it.

## 12. React Query Integration

The frontend wraps the application in a `QueryClientProvider`.

The configured default query behavior includes:

-   A 30-second stale time.
-   Refetching when the browser window regains focus.
-   One retry for failed queries.

Dashboard pages use React Query hooks to load summary data, experiment
lists, and experiment metrics.

This provides a shared cache and avoids each component independently
implementing loading and request state.

### UI states

Each data-driven page should distinguish:

1.  **Loading:** the request is still in progress.
2.  **Success with data:** render the values returned by the API.
3.  **Success with no records:** show an appropriate empty state.
4.  **Error:** show a useful failure message rather than silently
    presenting stale or invented values.

The precise UI treatment can vary by page, but missing or failed data
should not be represented as a successful zero-valued result.

## 13. Vite Development Proxy

The Vite configuration forwards API paths to the local backend:

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

This configuration supports local development when the FastAPI server
listens on port `8000` and Vite serves the frontend on its development
port.

The proxy is a development convenience. A deployed environment needs an
equivalent reverse-proxy or deployment configuration so that the
frontend's `/api` requests reach the correct backend service.

## 14. Running and Inspecting the API Locally

### 14.1 Start the backend

From the backend directory, activate the project's virtual environment
and start the FastAPI application using the project's configured ASGI
entry point.

The exact module path and command should be taken from the current
backend run configuration. Do not assume a module name if the
application entry point has changed.

The development API is expected at:

``` text
http://127.0.0.1:8000
```

### 14.2 Open interactive API documentation

FastAPI normally exposes interactive OpenAPI documentation at:

``` text
http://127.0.0.1:8000/docs
```

The generated OpenAPI schema is the authoritative runtime reference for:

-   Exact response fields.
-   Field types and nullability.
-   Path parameter definitions.
-   Response status codes.
-   Validation behavior.
-   Error response schemas.

Use the live documentation to verify exact contracts before integrating
a new client or publishing a formal API specification.

### 14.3 Verify health and experiment reads

The following paths can be opened or called from an HTTP client while
the backend is running:

``` text
GET http://127.0.0.1:8000/api/v1/health
GET http://127.0.0.1:8000/api/v1/health/database
GET http://127.0.0.1:8000/api/v1/experiments
GET http://127.0.0.1:8000/api/v1/experiments/summary
```

For a known experiment, call its detail and metrics paths using the UUID
from the local database or experiment list.

## 15. API Error and Contract Considerations

The exact error payloads and status-code behavior should be confirmed
from the live FastAPI route and exception-handling configuration. This
document does not prescribe an error envelope that has not been
verified.

Frontend integration should account for common cases:

-   Backend unavailable.
-   Database unavailable.
-   Experiment ID not found.
-   Experiment exists but has no metric records.
-   Optional metric values are `null`.
-   Network request fails or times out.

The frontend should show a useful message and should not substitute
fabricated experiment data.

## 16. Security and Scope Boundaries

The documented endpoints provide read access to research experiment
information. The current implementation notes do not establish an
authentication or authorization contract for these routes, so this
document does not claim that the endpoints are protected by a particular
authentication scheme.

The prototype uses a public benchmark dataset and simulated clients. It
is not intended to expose patient records, clinical data, or diagnostic
decisions.

Transport security, deployment authentication, authorization, rate
limiting, audit logging, and production hardening require separate
verification before any deployment beyond the research environment.

## 17. Current API Limitations and Future Improvements

The current API is sufficient for the frontend's experiment dashboard
and analytics pages. Potential follow-up improvements include:

1.  Publish a versioned OpenAPI specification as part of the project
    documentation.
2.  Add pagination if experiment history grows substantially.
3.  Add documented filters for algorithm, status, and dataset if
    required by the UI.
4.  Define a consistent error response format.
5.  Add API integration tests for missing IDs, empty metrics, and
    nullable values.
6.  Add authentication and authorization if the deployment context
    requires them.
7.  Add explicit API contract tests to detect drift between Pydantic
    schemas and TypeScript interfaces.
8.  Add a controlled experiment-submission API only if remote experiment
    execution becomes a deliberate product requirement.

These are recommendations, not claims that the features are already
implemented.

## 18. Summary

The current FastAPI backend exposes health checks and read-only
experiment APIs under `/api/v1`. The experiment endpoints provide
recorded experiment metadata, dashboard summaries, individual experiment
details, and the associated centralized, federated-round, privacy, and
client-training metrics.

The React frontend consumes these endpoints through a centralized Axios
module and React Query. The backend owns database access through
SQLAlchemy repositories and services, while Pydantic schemas define the
response boundary.

For exact field-level contracts and status codes, the live FastAPI
OpenAPI documentation and current source schemas remain authoritative.
This reference intentionally documents only the endpoints and
integration behavior established in the current prototype.
