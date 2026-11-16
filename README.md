# Federated Healthcare Research

### A Privacy-Aware Federated Learning Research Prototype for Healthcare Diagnosis

[![Python](https://img.shields.io/badge/Python-3.13.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-To%20Be%20Defined-lightgrey)](#license)

**Explore federated model training, privacy-aware aggregation,
experiment tracking, and evaluation through an interactive research
dashboard.**
:::

------------------------------------------------------------------------

## Overview

**Federated Healthcare Research** is a research prototype that explores
how machine-learning models can be trained across simulated healthcare
institutions without centralizing their local training datasets.

The project implements and evaluates three training paths:

1.  **Centralized training** --- a baseline model trained using the
    complete training partition.
2.  **Federated Averaging (FedAvg)** --- simulated clients train locally
    and send model updates to a coordinator for weighted aggregation.
3.  **Differentially Private FedAvg (DP-FedAvg)** --- a central
    differential-privacy mechanism clips client updates and adds
    Gaussian noise to the aggregated update, with privacy accounting
    recorded across communication rounds.

The platform includes a Python backend, PostgreSQL persistence, and a
React dashboard for inspecting experiment configurations, model
performance, client training metrics, federated rounds, and
privacy-accounting results.

> **Research prototype only.** This project is not a production
> healthcare system, is not clinically validated, and must not be used
> for diagnosis or patient-care decisions. Experiments use a public
> benchmark dataset and simulated clients---not real hospital
> connections or real patient records.

## Research Goals

-   Demonstrate centralized and federated model-training workflows.
-   Compare centralized training, standard FedAvg, and DP-FedAvg.
-   Explore client-level differential privacy in a federated setting.
-   Persist experiment configurations and evaluation results.
-   Visualize model utility and privacy-accounting progression.
-   Provide a reproducible foundation for future studies of non-IID
    data, secure aggregation, and robust federated learning.

## Current Implementation

  -----------------------------------------------------------------------
  Area                                Current implementation
  ----------------------------------- -----------------------------------
  Dataset                             Public Wisconsin Diagnostic Breast
                                      Cancer (WDBC) benchmark

  Input features                      30 numeric features

  Classification                      Binary classification: benign (`0`)
                                      and malignant (`1`)

  Data split                          Stratified 80/20 split: 456
                                      training records and 113 test
                                      records

  Simulated clients                   3 clients, 152 training samples
                                      each

  Client partition                    IID for the currently recorded
                                      federated experiments

  Model                               PyTorch feed-forward network:
                                      `30 → 32 → 16 → 2`

  Federated algorithm                 Sample-weighted Federated Averaging
                                      (FedAvg)

  DP mechanism                        Central Gaussian mechanism with
                                      update clipping

  Backend                             Python, FastAPI, SQLAlchemy,
                                      Alembic, PyTorch

  Database                            PostgreSQL

  Frontend                            React, TypeScript, Vite, Tailwind
                                      CSS

  Data visualization                  Recharts

  Client-side data fetching           Axios and TanStack React Query
  -----------------------------------------------------------------------

## Architecture

``` mermaid
flowchart TB
    subgraph UI["Frontend — React / TypeScript"]
        DASH["Research Dashboard"]
        EXP["Experiments & Analytics"]
        PRIV["Privacy & Client Views"]
    end

    subgraph API["Backend — FastAPI"]
        ROUTER["Versioned REST API"]
        SERVICE["Experiment Service"]
        REPO["Repository Layer"]
    end

    subgraph ML["Federated Learning — PyTorch"]
        DATA["Dataset & Client Partitioner"]
        CLIENTS["Simulated Training Clients"]
        COORD["Federation Coordinator"]
        FEDAVG["Weighted FedAvg"]
        DP["Clipping + Gaussian Noise"]
        EVAL["Model Evaluation"]
    end

    DB[("PostgreSQL")]
    DASH --> ROUTER
    EXP --> ROUTER
    PRIV --> ROUTER
    ROUTER --> SERVICE --> REPO --> DB
    DATA --> CLIENTS --> COORD --> FEDAVG --> DP --> EVAL
    EVAL --> DB
    COORD --> DB
```

### Main components

-   **Frontend:** dashboard pages for overview, experiments, model
    analytics, simulated clients, and privacy/security.
-   **Backend API:** health checks and read-only endpoints for
    experiment metadata and persisted metrics.
-   **ML layer:** dataset preparation, client partitioning, local
    training, FedAvg aggregation, DP mechanisms, and evaluation.
-   **Persistence:** experiment metadata, centralized metrics,
    federated-round metrics, privacy metrics, and client-training
    metrics.

## Recorded Experimental Results

The following values are from the currently recorded prototype runs.
They are individual run results, not multi-seed averages.

  Metric            Centralized baseline   Standard FedAvg    DP-FedAvg
  --------------- ---------------------- ----------------- ------------
  Test accuracy               **94.69%**            86.73%       82.30%
  Precision                       95.00%       **100.00%**       68.97%
  Recall                          90.48%            64.29%   **95.24%**
  F1-score                    **0.9268**            0.7826       0.8000
  ROC-AUC                     **0.9916**            0.9789       0.8806

### DP-FedAvg configuration

  Parameter                                   Recorded value
  ----------------------------------------- ----------------
  Simulated clients                                        3
  Communication rounds                                     5
  Local epochs per round                                   5
  L2 clipping bound                                      1.0
  Noise multiplier                                       1.0
  Delta                                           (10\^{-5})
  Recorded replace-one-client sensitivity              (2/3)
  Final reported epsilon                       **13.256463**

The reported privacy budget is based on client-level replace-one-client
adjacency, fixed public client weights, full client participation, and
the implemented RDP accountant's configured finite order grid. It is
**not** a patient-level differential-privacy guarantee.

### How to interpret these results

-   Results represent one recorded run per principal configuration.
-   No multi-seed statistical comparison or systematic privacy-noise
    sweep has been completed.
-   The current federated partitions are IID; non-IID experiments remain
    future work.
-   Central DP does not hide individual client updates from the
    coordinator before noise is added.

## Dashboard

The frontend currently provides these main views:

  -----------------------------------------------------------------------
  View                                What it shows
  ----------------------------------- -----------------------------------
  Overview                            Experiment KPIs, model-performance
                                      comparison, DP training
                                      progression, and recent experiments

  Experiments                         Experiment search and filtering,
                                      configuration details, round
                                      metrics, privacy records, and
                                      client metrics

  Model Analytics                     Model comparison, convergence
                                      trends, evaluation metrics, and
                                      privacy-utility observations

  Hospital Clients                    Simulated client sample counts,
                                      local training metrics, and
                                      client-level comparisons

  Privacy & Security                  DP configuration, epsilon
                                      progression, privacy-accounting
                                      records, and implementation caveats
  -----------------------------------------------------------------------

The "Hospital Clients" view represents simulated clients; it does not
show live hospital integrations.

## Documentation

The `docs/` directory contains the detailed project documentation. Each
document is stored in its own numbered folder.

  -------------------------------------------------------------------------------------------------------------
                            \# Document                                                   Description
  ---------------------------- ---------------------------------------------------------- ---------------------
                            01 [Research Overview](docs/01-research-overview/README.md)   Research motivation,
                                                                                          problem statement,
                                                                                          objectives, dataset,
                                                                                          scope, and project
                                                                                          overview

                            02 [System                                                    High-level
                               Architecture](docs/02-system-architecture/README.md)       architecture,
                                                                                          frontend/backend/ML
                                                                                          components, data
                                                                                          flow, and system
                                                                                          boundaries

                            03 [Frontend                                                  Dashboard structure,
                               Documentation](docs/03-frontend-documentation/README.md)   pages, cards, charts,
                                                                                          tables, and frontend
                                                                                          data flow

                            04 [Backend                                                   Backend modules, API
                               Documentation](docs/04-backend-documentation/README.md)    layers, experiment
                                                                                          services, ML
                                                                                          components, and
                                                                                          persistence
                                                                                          responsibilities

                            05 [Federated Learning                                        Client training, data
                               Workflow](docs/05-federated-learning/README.md)            partitioning, FedAvg,
                                                                                          communication rounds,
                                                                                          and workflow

                            06 [Differential                                              DP foundations,
                               Privacy](docs/06-differential-privacy/README.md)           clipping,
                                                                                          sensitivity, Gaussian
                                                                                          mechanism, RDP
                                                                                          accounting, and
                                                                                          measured privacy
                                                                                          budget

                            07 [Database Design](docs/07-database-design/README.md)       Persistence model,
                                                                                          metric records,
                                                                                          relationships,
                                                                                          migrations, and data
                                                                                          access

                            08 [Experimental Methodology and                              Dataset methodology,
                               Results](docs/08-experimental-methodology/README.md)       experiment
                                                                                          configurations,
                                                                                          measured results,
                                                                                          interpretation, and
                                                                                          limitations

                            09 [API Reference](docs/09-api-reference/README.md)           REST endpoints,
                                                                                          backend integration,
                                                                                          response schemas, and
                                                                                          frontend API client

                            10 [Setup and Execution                                       Local prerequisites,
                               Guide](docs/10-setup-and-execution/README.md)              backend/frontend
                                                                                          setup, database
                                                                                          configuration,
                                                                                          migrations, and
                                                                                          verification

                            11 [Security and Threat                                       Trust boundaries,
                               Model](docs/11-security-threat/README.md)                  threat model, privacy
                                                                                          limitations, security
                                                                                          status, and future
                                                                                          roadmap
  -------------------------------------------------------------------------------------------------------------

## Getting Started

The detailed, environment-specific instructions are in the [Setup and
Execution Guide](docs/10-setup-and-execution/README.md). The high-level
workflow is:

1.  Install Python, Node.js/npm, and PostgreSQL.
2.  Configure the backend database connection using the local settings
    expected by the backend.
3.  Create and activate the backend virtual environment.
4.  Install backend dependencies from the project's dependency manifest.
5.  Check and apply Alembic migrations.
6.  Start the FastAPI backend.
7.  Install frontend dependencies from the `frontend/` lockfile.
8.  Start the Vite development server.
9.  Open the frontend and verify that it can retrieve experiment data
    from the API.

### Local development addresses

  Service                        Address
  ------------------------------ --------------------------------------------
  FastAPI backend                `http://127.0.0.1:8000`
  FastAPI interactive API docs   `http://127.0.0.1:8000/docs`
  Frontend                       Use the local URL printed by `npm run dev`

The Vite development proxy forwards `/api` requests to
`http://127.0.0.1:8000`.

> **Migration note:** At the documented project state,
> `client_training_metrics` was created manually and was not yet
> represented in Alembic migration history. Verify and reconcile this
> table with migrations before expecting a fresh database to be created
> completely from the migration chain.

## API Endpoints

The backend currently exposes these read-oriented endpoints:

  -----------------------------------------------------------------------------------------------
  Method                  Endpoint                                        Purpose
  ----------------------- ----------------------------------------------- -----------------------
  `GET`                   `/api/v1/health`                                Backend health check

  `GET`                   `/api/v1/health/database`                       Database connectivity
                                                                          check

  `GET`                   `/api/v1/experiments`                           List experiments

  `GET`                   `/api/v1/experiments/summary`                   Dashboard summary

  `GET`                   `/api/v1/experiments/{experiment_id}`           Experiment details

  `GET`                   `/api/v1/experiments/{experiment_id}/metrics`   Experiment metrics
  -----------------------------------------------------------------------------------------------

Use the running FastAPI `/docs` page as the authoritative source for
exact response fields and status codes.

## Current Scope and Limitations

The following distinctions are important when evaluating or presenting
the project:

### Implemented

-   Centralized baseline training.
-   Three simulated federated clients.
-   Standard sample-weighted FedAvg.
-   Central-DP FedAvg with update clipping and Gaussian noise.
-   RDP-based client-level privacy accounting for the recorded DP run.
-   PostgreSQL persistence for experiment and metric records.
-   Dashboard views for experiment and metric inspection.

### Not yet implemented or not yet validated

-   Secure aggregation.
-   Non-IID client partition experiments.
-   Malicious-client and Byzantine-robust aggregation experiments.
-   Patient-level differential privacy.
-   Multi-seed evaluation and confidence intervals.
-   A systematic privacy-utility sweep across clipping/noise settings.
-   Production authentication, authorization, transport security, and
    deployment hardening.

## Research Safety and Responsible Use

-   Use public or synthetic datasets only.
-   Do not upload or store real patient records in this prototype.
-   Do not interpret predictions as medical advice or clinical
    diagnoses.
-   Do not describe simulated clients as real hospitals.
-   State the privacy unit and assumptions whenever reporting epsilon.
-   Distinguish implemented protections from proposed future work.

## Technology Stack

  -----------------------------------------------------------------------
  Layer                               Technologies
  ----------------------------------- -----------------------------------
  Language                            Python, TypeScript

  Machine learning                    PyTorch

  Backend API                         FastAPI

  ORM and migrations                  SQLAlchemy, Alembic

  Database                            PostgreSQL

  PostgreSQL driver                   pg8000 in the documented Windows
                                      development environment

  Frontend                            React, Vite

  Styling                             Tailwind CSS

  Data fetching                       Axios, TanStack React Query

  Charts                              Recharts

  Icons                               Lucide React
  -----------------------------------------------------------------------

## Project Structure

``` text
federated-healthcare-research/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── experiments/
│   │   └── ml/
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── 01-research-overview/
│   ├── 02-system-architecture/
│   ├── 03-frontend-documentation/
│   ├── 04-backend-documentation/
│   ├── 05-federated-learning/
│   ├── 06-differential-privacy/
│   ├── 07-database-design/
│   ├── 08-experimental-methodology/
│   ├── 09-api-reference/
│   ├── 10-setup-and-execution/
│   └── 11-security-threat/
└── README.md
```

## Testing and Quality

The backend test suite had **62 passing tests** at the documented
development stage. Run the current test suite from the backend
environment using the project's configured test command (the documented
command is `python -m pytest`).

The frontend production build is configured as:

``` powershell
npm run build
```

Passing tests and builds validate only the code paths they cover. They
do not establish clinical validity, production security, or completion
of the future research items listed above.

## Reproducibility

For stronger experimental reproducibility, future experiment records
should consistently capture:

-   Random seed.
-   Dataset version and provenance.
-   Train/test split and client partition identifiers.
-   Preprocessing configuration.
-   Model and optimizer configuration.
-   Federated round and local epoch settings.
-   DP clipping, noise, adjacency, and accounting configuration.
-   Source-code revision and runtime environment.

The current prototype persists important experiment and metric
information, but a complete reproducibility and multi-run statistical
evaluation workflow remains future work.

## Contributing

Contributions that improve correctness, reproducibility, documentation,
testing, or the research implementation are welcome.

Before proposing a change:

1.  Read the relevant documentation under [`docs/`](docs/).
2.  Keep implementation claims aligned with the actual code.
3.  Add or update tests for changed behavior.
4.  Document experimental assumptions and configuration.
5.  Avoid including credentials, private data, or real patient
    information.

For substantial changes, describe the research motivation,
implementation approach, validation performed, and any limitations.

## License

A project license has not been specified in the current project
information. Until a license is added to the repository, do not assume
that the source code is available for unrestricted reuse. Add an
appropriate `LICENSE` file before publishing the repository with an
explicit open-source licensing claim.

------------------------------------------------------------------------

::: {align="center"}
**Built as a research prototype to explore federated learning and
privacy-aware model training.**
:::
