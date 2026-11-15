# FedHealth --- Frontend Documentation

## 1. Purpose and Scope

This document describes the frontend application of FedHealth, a
research dashboard for inspecting the results of centralized, federated,
and differentially private federated learning experiments.

The frontend is implemented with React and TypeScript and communicates
with the FastAPI backend through REST endpoints. Its responsibility is
to retrieve, organize, and visualize experiment information. Model
training, federated aggregation, privacy processing, evaluation, and
persistent experiment storage are performed by the backend.

The current application contains five principal research sections:

1.  Overview Dashboard
2.  Experiments
3.  Model Analytics
4.  Hospital Clients
5.  Privacy & Security

This document explains the purpose of each section, the meaning of its
visible information, the data flow behind it, and the technologies used
to render it.

> **Research boundary:** The frontend presents a research prototype. The
> hospital clients are simulated participants, the dataset is a public
> benchmark, and the application is not a clinical diagnostic tool or a
> production healthcare system.

------------------------------------------------------------------------

## 2. Frontend Technology Stack

  -----------------------------------------------------------------------
  Technology                          Responsibility
  ----------------------------------- -----------------------------------
  React                               Component-based user interface

  TypeScript                          Static typing for components and
                                      API data

  Vite                                Development server and production
                                      build tooling

  Tailwind CSS                        Styling utilities and CSS
                                      integration

  React Query                         Server-state fetching, caching, and
  (`@tanstack/react-query`)           refetching

  Axios                               HTTP communication with the backend

  Recharts                            Charts and graphical data
                                      presentation

  Lucide React                        Interface icons
  -----------------------------------------------------------------------

### 2.1 Application Entry Point

The frontend entry point is `src/main.tsx`.

It:

-   Imports the global stylesheet.
-   Creates a React Query `QueryClient`.
-   Configures default query behaviour.
-   Mounts the root React application.
-   Wraps the application in `QueryClientProvider`.

The current query defaults include a 30-second stale time, refetching
when the browser window regains focus, and one retry for failed queries.

These settings apply to queries unless an individual query overrides
them.

### 2.2 Main Application Component

`src/App.tsx` provides the application shell and primary navigation.

Its responsibilities include:

-   Rendering the sidebar and shared application header.
-   Tracking the selected dashboard section.
-   Displaying the selected page component.
-   Rendering the overview dashboard when the Overview section is
    selected.
-   Providing the shared visual structure used by the five research
    sections.

The selected page is maintained as React component state. Selecting a
sidebar item updates that state and causes the corresponding page
content to render.

The current navigation is an in-application page-selection mechanism; it
should not be described as a separately configured URL route for each
section.

------------------------------------------------------------------------

## 3. Frontend Architecture and Data Flow

### 3.1 Logical Structure

``` text
frontend/
├── src/
│   ├── components/
│   │   ├── ExperimentsPage.tsx
│   │   ├── ModelAnalyticsPage.tsx
│   │   ├── HospitalClientsPage.tsx
│   │   └── PrivacySecurityPage.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── App.tsx
│   ├── App.css
│   ├── index.css
│   └── main.tsx
├── index.html
├── package.json
└── vite.config.ts
```

The overview dashboard is rendered by the main `App.tsx` component. The
other four dedicated sections are implemented as page components under
`src/components/`.

### 3.2 Frontend-to-Backend Request Flow

``` mermaid
sequenceDiagram
    actor User
    participant Page as React Page
    participant RQ as React Query
    participant API as Axios API Helper
    participant Vite as Vite Proxy
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    User->>Page: Open a dashboard section
    Page->>RQ: Execute query
    RQ->>API: Call typed API helper
    API->>Vite: Request /api/v1/...
    Vite->>BE: Proxy request to backend
    BE->>DB: Retrieve persisted data
    DB-->>BE: Return records
    BE-->>Vite: JSON response
    Vite-->>API: Forward response
    API-->>RQ: Return typed data
    RQ-->>Page: Provide query result
    Page-->>User: Render cards, charts, and tables
```

The frontend does not connect directly to PostgreSQL. It receives data
through the backend API.

### 3.3 API Client

The shared API client is defined in `src/lib/api.ts`.

The Axios instance uses:

-   Base URL: `/api/v1`
-   Content type: `application/json`
-   Request timeout: 10,000 milliseconds

The relative API base URL is used with the Vite development proxy. The
proxy forwards requests beginning with `/api` to
`http://127.0.0.1:8000`.

### 3.4 API Data Types

The API module defines TypeScript interfaces for the principal response
structures.

  -----------------------------------------------------------------------
  Interface                           Meaning
  ----------------------------------- -----------------------------------
  `Experiment`                        Experiment identity, algorithm,
                                      dataset, training configuration,
                                      privacy flags, and status

  `ExperimentPerformance`             Evaluation metrics associated with
                                      an experiment

  `DashboardSummary`                  Aggregate dashboard counts, best
                                      accuracy, latest privacy values,
                                      and performance records

  `FederatedRound`                    Evaluation and training information
                                      for a federated round

  `PrivacyMetric`                     Per-round privacy-accounting
                                      information

  `ExperimentMetrics`                 Experiment configuration plus
                                      centralized, federated, privacy,
                                      and client metric records
  -----------------------------------------------------------------------

The interfaces make the expected API response shape explicit to
TypeScript components. They do not themselves perform validation of the
JSON received at runtime.

### 3.5 API Helper Functions

  --------------------------------------------------------------------------------------
  Function                     Endpoint                          Purpose
  ---------------------------- --------------------------------- -----------------------
  `getDashboardSummary()`      `GET /experiments/summary`        Retrieves aggregate
                                                                 dashboard information

  `getExperiments()`           `GET /experiments`                Retrieves the
                                                                 experiment list

  `getExperimentMetrics(id)`   `GET /experiments/{id}/metrics`   Retrieves the
                                                                 configuration and
                                                                 detailed metrics for
                                                                 one experiment

  `getHealth()`                `GET /health`                     Retrieves backend
                                                                 health information
  --------------------------------------------------------------------------------------

All paths are relative to the Axios base URL `/api/v1`.

### 3.6 React Query

Page components use React Query's `useQuery` hook to request backend
data.

This separates asynchronous data retrieval from visual rendering. Query
results expose information such as:

-   Returned data.
-   Loading state.
-   Error state.
-   Cached query data.

The pages use these states to render their content, loading messages, or
error/empty states.

------------------------------------------------------------------------

## 4. Shared Application Shell

The shared shell provides consistent navigation and identity across the
research dashboard.

### 4.1 Sidebar

The sidebar contains the FedHealth identity and the primary navigation
items:

-   Overview
-   Experiments
-   Model Analytics
-   Hospital Clients
-   Privacy & Security

It also includes preference or supporting navigation entries such as
Settings and Documentation.

The selected research section receives an active visual treatment. This
helps the user understand which section is currently displayed.

### 4.2 Header

The shared header displays the current workspace context and selected
section. It also contains the search presentation and
account/notification interface elements visible in the application
shell.

The presence of a visual control should not be interpreted as proof of a
fully implemented backend search, notification, or account-management
workflow unless that behaviour is separately implemented.

### 4.3 Visual Language

The application uses a dark research-dashboard visual style with:

-   A dark navy page and sidebar background.
-   Contrasting panel surfaces.
-   Purple accents for primary research visualizations.
-   Green accents for successful or implemented states.
-   Amber accents for disabled or not-implemented capabilities.
-   Muted text for descriptions and supporting metadata.
-   Cards, tables, charts, and section headings to organize information.

The shared stylesheet is `src/App.css`, while global base styling is
defined in `src/index.css`.

------------------------------------------------------------------------

## 5. Section One --- Overview Dashboard

### 5.1 Purpose

The Overview Dashboard is the entry point to the FedHealth frontend. It
provides a consolidated view of experiment activity, model performance,
privacy information, and backend health.

It is intended to answer high-level questions:

-   How many experiments have been recorded?
-   What is the best recorded model accuracy?
-   How many simulated clients are configured in the research
    experiments?
-   What is the latest available privacy-budget value?
-   How do the implemented training approaches compare?
-   Is the backend responding?

### 5.2 KPI Cards

The dashboard presents high-level metric cards. The values are obtained
from the dashboard summary API rather than being intended as manually
maintained labels.

  -----------------------------------------------------------------------
  KPI                     What it represents      Interpretation
  ----------------------- ----------------------- -----------------------
  Total Experiments       Number of experiment    Indicates the number of
                          records                 experiments registered
                                                  in the backend

  Best Accuracy           Highest accuracy        Identifies the best
                          represented in the      recorded accuracy among
                          returned performance    the summarized
                          data                    experiments

  Participating Clients / Client count            Refers to simulated
  Configured Clients      represented by the      federated clients, not
                          dashboard summary       real hospital
                                                  connections

  Latest Epsilon          Latest available        Provides a summary of
                          privacy-budget value    the most recently
                                                  represented DP
                                                  accounting result
  -----------------------------------------------------------------------

The exact value displayed depends on the records returned by the
backend. A KPI is a summary, not a substitute for inspecting an
individual experiment.

### 5.3 Model Performance Comparison

The model-performance visualization compares the evaluation results of
the available training approaches.

The comparison is intended to show how centralized training, standard
FedAvg, and DP-FedAvg performed under their recorded configurations.

The principal metrics include:

-   Accuracy
-   Precision
-   Recall
-   F1-score
-   ROC-AUC

The chart should be interpreted as a comparison of recorded experimental
results, not as a universal ranking of the algorithms. The experiments
may differ in training configuration and stochastic behaviour, and a
single run does not establish statistical significance.

### 5.4 Differential Privacy Training Visualization

The dashboard includes a visualization of the DP-FedAvg experiment's
recorded round-wise behaviour.

The round number identifies a communication round. Evaluation values
describe the global model after the corresponding round, while privacy
values describe the accounting result recorded for that round.

The detailed per-round privacy accounting is available in the Privacy &
Security section.

### 5.5 Recent Experiments

The recent-experiments area provides a compact view of experiment
records, including information such as experiment name, algorithm,
status, and configuration summary.

It helps users identify which experiments have been completed and
provides context for deeper inspection in the Experiments section.

### 5.6 Backend/System Health

The dashboard requests backend health through the health API.

A successful health response indicates that the backend health endpoint
responded. It should not be interpreted as a complete assessment of
every dependency, every machine learning component, or production
operational readiness.

The backend database health endpoint is a separate check.

------------------------------------------------------------------------

## 6. Section Two --- Experiments

### 6.1 Purpose

The Experiments section is the detailed inspection area for recorded
research runs.

It allows the user to browse experiments, narrow the visible list,
select an experiment, and inspect its configuration and persisted
results.

### 6.2 Experiment List

The list is populated from `GET /api/v1/experiments`.

Each experiment record can include:

-   Experiment ID.
-   Name and description.
-   Algorithm.
-   Dataset name.
-   Partition strategy.
-   Client count.
-   Number of federated rounds.
-   Local epochs.
-   Learning rate.
-   Differential Privacy configuration.
-   Secure aggregation setting.
-   Status.
-   Creation timestamp.

The experiment list provides the entry point for selecting an individual
run.

### 6.3 Search and Filters

The page includes controls for searching and filtering the experiment
list.

Their purpose is to help users locate experiments by the available
descriptive or algorithm/status information without manually scanning
every record.

Filtering changes which experiment records are shown in the interface;
it does not alter the persisted experiment or rerun training.

### 6.4 Experiment Details

After an experiment is selected, the page requests its detailed metrics
through:

`GET /api/v1/experiments/{experiment_id}/metrics`

The response includes the experiment configuration and related metric
collections.

The details area presents configuration information such as:

-   Algorithm.
-   Dataset.
-   Client count.
-   Partition strategy.
-   Communication rounds.
-   Local epochs.
-   Learning rate.
-   Differential Privacy enabled/disabled state.
-   Noise multiplier and maximum gradient norm, where available.
-   Secure aggregation configuration.

These values describe the selected experiment's recorded configuration.

### 6.5 Centralized Metrics

For a centralized experiment, the response can include the centralized
evaluation record.

The displayed fields include:

-   Sample count.
-   Training loss.
-   Training accuracy.
-   Test accuracy.
-   Precision.
-   Recall.
-   F1-score.
-   Sensitivity.
-   Specificity.
-   ROC-AUC.

Training metrics describe optimization on the training data. Test
metrics describe evaluation on the held-out test subset. They should not
be treated as interchangeable.

### 6.6 Federated Round Metrics

For a federated experiment, the page presents the round-wise records.

A federated round record can include:

  Field               Meaning
  ------------------- --------------------------------------------------------
  Round Number        Position of the communication round in the experiment
  Client Count        Number of clients represented in the round
  Total Samples       Number of training samples represented
  Training Loss       Recorded training loss, when available
  Training Accuracy   Recorded training accuracy, when available
  Test Accuracy       Global model accuracy on the test subset
  Precision           Positive predictive value
  Recall              True positive rate
  F1-score            Harmonic mean of precision and recall
  Sensitivity         True positive rate
  Specificity         True negative rate
  ROC-AUC             Area under the receiver operating characteristic curve

Some fields may be null depending on the experiment and what was
persisted. In particular, the DP-FedAvg experiment intentionally stores
null training loss and training accuracy in its federated-round records;
the frontend should not invent values for them.

### 6.7 Privacy Accounting Records

When the selected experiment has privacy-accounting data, the page
presents the recorded privacy metrics.

The detailed meaning of epsilon, delta, noise multiplier, sensitivity,
adjacency, and accounting method is explained in the Privacy & Security
and Differential Privacy documentation.

### 6.8 Client Training Records

The experiment details can include local client training records.

These records describe each simulated client's local training outcome,
including:

-   Client identifier.
-   Partition strategy.
-   Local sample count.
-   Training loss.
-   Training accuracy.
-   Completed local epochs.
-   Record timestamp.

They are useful for understanding differences between client-local
training results. They do not indicate live hospital activity.

------------------------------------------------------------------------

## 7. Section Three --- Model Analytics

### 7.1 Purpose

Model Analytics provides a comparative view of the recorded model
evaluation results.

It is intended to help the researcher examine the performance of the
implemented approaches rather than merely view a single accuracy value.

### 7.2 Performance Comparison

The comparison uses the available experiment performance records
retrieved from the dashboard summary and experiment APIs.

The displayed metrics include:

-   Accuracy.
-   Precision.
-   Recall.
-   F1-score.
-   ROC-AUC.

Each metric provides a different view of model behaviour.

**Accuracy** measures the fraction of predictions that are correct.

**Precision** measures how many positive predictions are correct.

**Recall** measures how many actual positive samples are identified.

**F1-score** balances precision and recall through their harmonic mean.

**ROC-AUC** measures the model's ability to rank positive examples above
negative examples across classification thresholds.

A higher value is not automatically sufficient to establish that one
model is preferable for every use case. Metric interpretation depends on
the task, error costs, test data, and experimental configuration.

### 7.3 Federated Convergence / Round Progression

The analytics section uses federated round records to visualize how
evaluation metrics change over communication rounds.

The horizontal axis represents the round number. The plotted metric
represents the global model's recorded evaluation result for that round.

This allows the researcher to inspect whether the observed metric
improves, declines, or fluctuates during training.

A short run with five rounds is not sufficient to establish general
convergence behaviour across all datasets or configurations.

### 7.4 Evaluation Metrics Table

The evaluation table presents the numeric results used in the
comparison.

It makes it possible to inspect exact values rather than relying solely
on visual chart differences.

### 7.5 Privacy--Utility Interpretation

The page can present observations about the performance of DP-FedAvg
relative to standard FedAvg.

These observations must be tied to the actual recorded experiment. A
single DP run does not establish a general privacy-utility curve or
prove how performance changes across different noise levels.

No privacy-budget sweep or multi-seed statistical analysis has been
completed in the current experiment set.

### 7.6 Dataset Context

The analytics view provides context about the benchmark used in the
experiments: the public WDBC dataset, its binary classification task,
and the experimental split.

The dataset context is important because the reported performance
applies to this benchmark and configuration. It should not be
generalized to real-world hospital populations or clinical deployment.

------------------------------------------------------------------------

## 8. Section Four --- Hospital Clients

### 8.1 Purpose

Hospital Clients presents the simulated participants used in the
local-training experiment.

The section is intended to make the federated client model visible: each
simulated institution has a local partition and a recorded local
training result.

The word "hospital" is used as a research-domain label. The clients are
simulated software participants, not real healthcare institutions
connected to the application.

### 8.2 Data Source

The page retrieves the experiment list, identifies the completed
local-training experiment, and requests its detailed metrics.

The client cards and table are populated from the
`client_training_metrics` collection returned by the experiment metrics
API.

### 8.3 Summary Cards

The page presents four summary values.

  -----------------------------------------------------------------------
  Summary                             Meaning
  ----------------------------------- -----------------------------------
  Recorded Clients                    Number of client training records
                                      represented

  Total Local Samples                 Sum of the local sample counts

  Average Training Accuracy           Mean of the recorded client
                                      training accuracies

  Local Training Epochs               Recorded local epoch count
  -----------------------------------------------------------------------

These values summarize the initial local-training experiment, not
necessarily every federated experiment in the database.

### 8.4 Simulated Client Cards

Each client card presents:

-   Client identifier.
-   Recorded status.
-   Local sample count.
-   Training accuracy.
-   Training loss.
-   Partition strategy.

**Recorded** means that a local training metric record exists. It does
not mean the client is currently online, connected, or actively
training.

### 8.5 Client Training Accuracy Chart

The horizontal bar chart compares the recorded local training accuracy
of the simulated clients.

The category axis identifies the client. The numeric axis represents
training accuracy.

This visualization helps compare local training outcomes across the
three IID partitions.

It does not show global test accuracy. Local training accuracy and
global-model test accuracy describe different evaluations and must not
be compared as if they were the same measurement.

### 8.6 Client Training Records Table

The table presents the persisted local-training records, including:

-   Client ID.
-   Partition strategy.
-   Sample count.
-   Training loss.
-   Training accuracy.
-   Epochs completed.

The table is useful for inspecting the exact values behind the summary
cards and chart.

### 8.7 Data Provenance

The current client records belong to the initial local-training
experiment on the public WDBC benchmark.

The current experiment uses three equal IID partitions of 152 training
samples each, for a total of 456 training samples.

The records do not represent live hospital connections or actual patient
records.

------------------------------------------------------------------------

## 9. Section Five --- Privacy & Security

### 9.1 Purpose

Privacy & Security provides a focused view of the recorded DP-FedAvg
configuration, privacy-accounting progression, and the implementation
status of selected security mechanisms.

The page locates a completed experiment with Differential Privacy
enabled and retrieves its detailed privacy-accounting records.

### 9.2 Active Data Source

The experiment banner identifies the DP experiment used as the page's
data source.

It presents information such as:

-   Experiment name.
-   Algorithm.
-   Simulated client count.
-   Number of recorded privacy rounds.
-   Completion status.

This makes the origin of the displayed privacy metrics explicit.

### 9.3 Privacy Summary Cards

The page displays four principal privacy configuration values.

  -----------------------------------------------------------------------
  Card                                Meaning
  ----------------------------------- -----------------------------------
  Privacy Budget (epsilon)            Final recorded epsilon value in the
                                      selected experiment

  Delta                               Configured delta parameter

  Noise Multiplier                    Gaussian noise multiplier recorded
                                      for the privacy mechanism

  Gradient Clip (C)                   Configured maximum update/gradient
                                      norm bound
  -----------------------------------------------------------------------

The epsilon card displays the final available privacy-accounting value.
It should be interpreted together with delta and the accounting
assumptions, not as a standalone measure.

### 9.4 Privacy Budget Progression Chart

The line chart plots epsilon against federated round number.

-   Horizontal axis: federated round.
-   Vertical axis: recorded epsilon.
-   Each point: the privacy-accounting value persisted for that round.

The chart allows the researcher to inspect how the privacy budget
accumulates across the recorded rounds.

A rising epsilon indicates increasing cumulative privacy expenditure
under the configured accountant. The chart does not independently prove
a privacy guarantee; the guarantee depends on the mechanism and
accounting assumptions.

### 9.5 Privacy Configuration Panel

The configuration panel presents values recorded for the selected
experiment, including:

-   Algorithm.
-   Noise multiplier.
-   Maximum gradient norm.
-   Accounting method.
-   Adjacency definition.
-   Secure aggregation setting.

The accounting method and adjacency are especially important because
epsilon is meaningful only in the context of the privacy model and
accountant assumptions.

### 9.6 Round-wise Privacy Accounting Table

The table displays the persisted privacy record for each federated
round.

  Field             Meaning
  ----------------- ------------------------------------------------
  Round             Federated communication round
  Epsilon           Recorded privacy budget
  Delta             Delta parameter used for the accounting result
  Noise             Gaussian noise multiplier
  Sensitivity       Sensitivity value used by the implementation
  Max Update Norm   Recorded maximum update norm
  Steps             Accounting step count

The table exposes the numeric records behind the progression chart.

### 9.7 Security Controls

The page distinguishes implemented capabilities from research
extensions.

  -----------------------------------------------------------------------
  Capability              Current status          Explanation
  ----------------------- ----------------------- -----------------------
  Differential Privacy    Implemented             The DP-FedAvg
                                                  experiment applies
                                                  central Gaussian noise
                                                  and records
                                                  privacy-accounting
                                                  results

  Update Clipping         Implemented             Client updates are
                                                  clipped using the
                                                  configured norm bound

  Secure Aggregation      Not implemented         No cryptographic
                                                  protocol is implemented
                                                  to hide individual
                                                  client updates from the
                                                  coordinator

  Robust Aggregation      Not implemented         Byzantine or
                                                  malicious-client robust
                                                  aggregation is not
                                                  implemented
  -----------------------------------------------------------------------

The page must not imply that disabled or unimplemented mechanisms
provide protection.

### 9.8 Research Interpretation Notice

The page includes a research interpretation notice explaining that:

-   Epsilon and delta belong to the recorded DP-FedAvg experiment and
    its accounting assumptions.
-   Differential Privacy is applied centrally in the current
    implementation.
-   The coordinator receives individual client updates before noise is
    added.
-   Secure aggregation is disabled and not implemented.
-   The project uses a public benchmark in a research prototype, not a
    clinical system.

This notice is an important part of accurate presentation. It prevents
the privacy dashboard from overstating the guarantees of the current
implementation.

------------------------------------------------------------------------

## 10. Loading, Error, and Empty States

The pages use asynchronous API queries. Their UI should distinguish
among different data states.

### 10.1 Loading State

A loading state indicates that the frontend is waiting for an API
response. It is not evidence that an experiment is currently training.

### 10.2 Error State

An error state indicates that the relevant request failed. Possible
causes include an unavailable backend, a failed request, or an API
error.

An error should not be displayed as a valid zero-valued experiment
result.

### 10.3 Empty State

An empty state indicates that the API returned no relevant records for
the requested view. For example, the privacy page can explain that no
completed DP experiment is available.

An empty state is different from an API failure and should be presented
accordingly.

### 10.4 Null Metric Values

Some experiment metrics are optional and may be returned as `null`. The
frontend should represent unavailable values as unavailable rather than
converting them into fabricated zeros.

This is particularly relevant to the DP-FedAvg federated-round training
loss and training accuracy fields, which were intentionally persisted as
null in the current experiment.

------------------------------------------------------------------------

## 11. Frontend Configuration and Local Development

### 11.1 Vite Development Proxy

The Vite configuration proxies API requests beginning with `/api` to:

`http://127.0.0.1:8000`

This supports local frontend-backend development without hardcoding the
backend host in each component.

### 11.2 Run the Frontend

From the `frontend` directory:

``` powershell
npm install
npm run dev
```

The Vite development server prints the local URL in the terminal.

### 11.3 Production Build

Run:

``` powershell
npm run build
```

The build script executes TypeScript project compilation followed by the
Vite production build.

A successful build verifies that the current frontend source passes the
configured TypeScript build and Vite bundling process. It does not, by
itself, verify backend availability or correctness of every runtime API
response.

------------------------------------------------------------------------

## 12. Frontend Limitations and Interpretation Rules

1.  The frontend visualizes backend-produced data; it does not
    independently validate the scientific correctness of the
    experiments.
2.  The dashboard displays results from a public benchmark, not real
    hospital datasets.
3.  The hospital client names represent simulated clients.
4.  A recorded client is not necessarily an online client.
5.  Local training accuracy is not the same as global test accuracy.
6.  A single experiment run does not establish statistical significance.
7.  A single DP configuration does not establish a general
    privacy-utility curve.
8.  The privacy page reports the implemented central DP mechanism; it
    does not imply secure aggregation.
9.  Secure aggregation and robust aggregation are not implemented.
10. A successful backend health response is not a complete
    production-readiness assessment.
11. The frontend is a research dashboard, not a clinical
    decision-support interface.

------------------------------------------------------------------------

## 13. Summary

The FedHealth frontend is a React and TypeScript research dashboard that
retrieves experiment information from the FastAPI backend and presents
it through five sections.

The Overview Dashboard provides a consolidated status view. Experiments
supports detailed inspection of configurations and recorded results.
Model Analytics presents comparative evaluation information. Hospital
Clients exposes simulated local-training records. Privacy & Security
presents the configured Differential Privacy mechanism, round-wise
accounting data, and implementation boundaries.

Together, these sections provide a navigable interface for understanding
the current research prototype. Their purpose is to make the backend's
recorded experiments understandable and inspectable while preserving
clear distinctions between simulated capabilities, implemented privacy
mechanisms, and future research extensions.
