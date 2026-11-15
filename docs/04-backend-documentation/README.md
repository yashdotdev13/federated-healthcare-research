# FedHealth --- Backend Documentation

## 1. Purpose and Scope

This document describes the backend implementation of FedHealth, a
research prototype for experimenting with centralized machine learning,
Federated Averaging (FedAvg), and Differentially Private Federated
Averaging (DP-FedAvg) in a healthcare-oriented classification scenario.

The backend is responsible for the application's API, experiment
retrieval, machine learning workflows, evaluation, privacy processing,
and persistence of experiment results.

The backend is implemented as a Python application using FastAPI,
PyTorch, SQLAlchemy, Alembic, and PostgreSQL.

This document focuses on the responsibilities and interactions of the
implemented backend components. It does not describe the system as a
production healthcare platform.

> **Research boundary:** The current implementation uses the public
> Wisconsin Diagnostic Breast Cancer (WDBC) benchmark and simulated
> clients. It is not connected to real hospitals, does not process real
> patient records, and is not clinically validated.

------------------------------------------------------------------------

## 2. Backend Technology Stack

  Technology    Role in the backend
  ------------- ------------------------------------------------------------
  Python 3.13   Main implementation language
  FastAPI       HTTP API framework
  Pydantic      Data schemas and response validation
  SQLAlchemy    ORM and database interaction
  Alembic       Database schema migration management
  PostgreSQL    Persistent relational database
  pg8000        PostgreSQL database driver used in the project environment
  PyTorch       Neural-network definition and model training
  Pytest        Automated backend tests

The backend separates HTTP request handling, application-level
coordination, data access, machine learning execution, and database
persistence.

------------------------------------------------------------------------

## 3. Backend Responsibilities

The backend has the following principal responsibilities:

1.  Load and prepare the public research dataset.
2.  Create training and test subsets.
3.  Partition training data across simulated clients for federated
    experiments.
4.  Define and train the diagnostic classification model.
5.  Execute centralized training.
6.  Execute local client training.
7.  Coordinate federated communication rounds.
8.  Aggregate client updates using FedAvg.
9.  Apply update clipping and Gaussian noise in the DP-FedAvg workflow.
10. Evaluate model predictions.
11. Calculate and record privacy-accounting information.
12. Persist experiment configurations and results.
13. Expose experiment and health information through REST APIs.

The backend is the authoritative source for the experiment records
displayed by the frontend.

------------------------------------------------------------------------

## 4. Backend Project Organization

The backend is organized into application, API, experiment-management,
machine-learning, and migration areas.

The principal implementation areas include:

``` text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── health/
│   │       └── experiments/
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── experiments/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── router.py
│   │   ├── federated_models.py
│   │   ├── centralized_models.py
│   │   └── privacy_models.py
│   └── ml/
│       ├── aggregation/
│       │   └── fedavg.py
│       ├── clients/
│       │   └── hospital_client.py
│       ├── data/
│       │   ├── dataset.py
│       │   └── partitioner.py
│       ├── evaluation/
│       │   └── evaluator.py
│       ├── federation/
│       │   └── coordinator.py
│       ├── models/
│       │   └── diagnostic_model.py
│       ├── privacy/
│       │   ├── update_clipper.py
│       │   ├── gaussian_mechanism.py
│       │   └── privacy_accountant.py
│       └── training/
│           ├── local_trainer.py
│           ├── run_local_experiment.py
│           ├── run_fedavg_experiment.py
│           ├── run_centralized_experiment.py
│           └── run_dp_fedavg_experiment.py
├── alembic/
├── tests/
└── ...
```

This tree highlights the principal modules discussed in the
implementation. Supporting files such as package initializers,
environment files, migration revisions, and individual test modules are
omitted for readability.

------------------------------------------------------------------------

## 5. Application Core

### 5.1 Configuration --- `app/core/config.py`

The configuration module centralizes backend settings used by the
application.

Its role is to keep environment-dependent settings separate from
business logic and individual API handlers.

Database connection configuration and other application settings should
be obtained through the central configuration mechanism rather than
being duplicated throughout the codebase.

Secrets and environment-specific credentials should be supplied through
the local environment and must not be committed to source control.

### 5.2 Database Setup --- `app/core/database.py`

The database module provides the SQLAlchemy database setup used by the
backend.

Its responsibilities include:

-   Establishing the database engine.
-   Providing the session-management mechanism used by application
    components.
-   Supporting database access through SQLAlchemy.
-   Keeping database initialization separate from API and
    machine-learning logic.

The project uses PostgreSQL for persistent experiment information.

The development environment uses the `pg8000` PostgreSQL driver.
SQLAlchemy is configured to use the pure-Python implementation in the
Windows environment where native-extension loading was restricted.

------------------------------------------------------------------------

## 6. API Architecture

### 6.1 FastAPI Application

FastAPI provides the HTTP interface through which the frontend retrieves
backend information.

The API is versioned under the `/api/v1` prefix. The health and
experiment routers are included in the application.

The API layer is responsible for:

-   Receiving HTTP requests.
-   Resolving the requested endpoint.
-   Invoking the relevant application logic.
-   Returning structured responses.
-   Reporting request failures through appropriate HTTP responses.

The API layer should not contain the implementation of neural-network
training or database query logic directly. Those responsibilities belong
to the relevant application and machine-learning components.

### 6.2 Health Endpoints

  Endpoint                        Responsibility
  ------------------------------- --------------------------------------------
  `GET /api/v1/health`            Returns backend service health information
  `GET /api/v1/health/database`   Checks database connectivity

The general health endpoint indicates that the backend health route is
responding. The database health endpoint checks a separate dependency.

A successful health response is not a complete production-readiness or
security assessment.

### 6.3 Experiment Endpoints

  ---------------------------------------------------------------------------------------
  Endpoint                                            Responsibility
  --------------------------------------------------- -----------------------------------
  `GET /api/v1/experiments`                           Retrieves the recorded experiment
                                                      list

  `GET /api/v1/experiments/summary`                   Retrieves aggregate information
                                                      used by the dashboard

  `GET /api/v1/experiments/{experiment_id}`           Retrieves a particular experiment

  `GET /api/v1/experiments/{experiment_id}/metrics`   Retrieves the experiment and its
                                                      associated metric records
  ---------------------------------------------------------------------------------------

These endpoints support the frontend's Overview, Experiments, Model
Analytics, Hospital Clients, and Privacy & Security sections.

### 6.4 Experiment List

The experiment-list endpoint returns the experiment records available in
the database.

The frontend uses this information to display experiment names,
algorithms, dataset details, configuration, and status.

### 6.5 Dashboard Summary

The summary endpoint provides aggregate information for the overview
dashboard.

The response schema includes fields for:

-   Total experiment count.
-   Completed experiment count.
-   Participating/configured client count.
-   Best accuracy.
-   Latest epsilon and delta, where available.
-   Experiment performance records.

The summary is a compact representation of stored experiment
information. Detailed values should be inspected through the individual
experiment metrics endpoint.

### 6.6 Experiment Metrics

The experiment metrics endpoint is the principal detailed read endpoint.

It returns the selected experiment together with the metric collections
associated with that experiment, including:

-   Centralized evaluation information.
-   Federated round metrics.
-   Privacy-accounting records.
-   Client local-training metrics.

The service and repository layers assemble the data required for this
response.

------------------------------------------------------------------------

## 7. Experiment Management Layer

The experiment-management area separates persistence models, response
schemas, database queries, and application-level coordination.

### 7.1 Models --- `app/experiments/models.py`

The model definitions represent the persisted experiment-related
entities using SQLAlchemy.

They provide the mapping between Python objects and relational database
records.

The experiment data model supports storing the experiment identity and
configuration, while related metric models represent the outcomes of
different experiment types.

### 7.2 Schemas --- `app/experiments/schemas.py`

The schema module defines the structured data returned by the API.

The response structures include:

  -----------------------------------------------------------------------
  Schema                              Responsibility
  ----------------------------------- -----------------------------------
  `ExperimentRead`                    Represents experiment metadata and
                                      configuration

  `CentralizedMetricRead`             Represents centralized training and
                                      evaluation results

  `FederatedRoundRead`                Represents one federated round's
                                      recorded metrics

  `PrivacyMetricRead`                 Represents a round-wise
                                      privacy-accounting record

  `ClientTrainingMetricRead`          Represents local training metrics
                                      for a simulated client

  `ExperimentMetricsResponse`         Combines an experiment with its
                                      associated metric collections

  `ExperimentPerformance`             Represents evaluation metrics used
                                      in performance comparisons

  `DashboardSummary`                  Represents aggregate dashboard
                                      information
  -----------------------------------------------------------------------

Pydantic schemas define the expected response structure and support
serialization of application data into API responses.

### 7.3 Repository --- `app/experiments/repository.py`

The repository layer encapsulates database access for experiment
information.

Its responsibilities include retrieving experiment records and related
metric records from PostgreSQL.

The experiment metrics response requires several related collections.
Repository functions retrieve the relevant records so that the service
layer can assemble the complete response.

The client-training metric query retrieves records for the selected
experiment and orders them by creation time.

### 7.4 Service --- `app/experiments/service.py`

The service layer coordinates experiment retrieval and response
construction.

It uses repository operations to obtain the experiment and related
metrics, then prepares the response expected by the API.

For the detailed metrics response, the service includes the
client-training metric records alongside centralized metrics, federated
rounds, and privacy-accounting records.

This separation keeps endpoint handlers focused on HTTP concerns and
places application-level coordination in the service layer.

### 7.5 Router --- `app/experiments/router.py`

The experiment router exposes the experiment endpoints.

It connects HTTP requests to the service layer and returns the
corresponding response models.

The router is responsible for endpoint-level behaviour, while the
repository remains responsible for database access.

### 7.6 Experiment-Specific Model Modules

The experiment package also contains modules for different result
categories:

-   `federated_models.py`
-   `centralized_models.py`
-   `privacy_models.py`

These modules organize model definitions associated with the respective
experiment result types.

The exact fields and relationships are defined by the implementation and
database schema. The frontend-facing response structure is described by
the Pydantic schemas.

------------------------------------------------------------------------

## 8. Dataset and Data Preparation

### 8.1 Dataset Module --- `app/ml/data/dataset.py`

The dataset module is responsible for loading and preparing the research
dataset used by the experiments.

The current implementation uses the public Wisconsin Diagnostic Breast
Cancer (WDBC) benchmark.

The dataset contains 569 records and 30 numerical input features for a
binary classification task.

### 8.2 Train/Test Split

The current experiment preparation uses a stratified 80:20 split:

  Subset        Records
  ----------- ---------
  Training          456
  Testing           113
  **Total**     **569**

Stratification preserves the class distribution across the training and
test subsets.

### 8.3 Feature Standardization

Feature standardization is fitted using the training subset. The
training-derived mean and standard deviation are then used to transform
the test subset.

This avoids using test-subset statistics when preparing the training
transformation.

### 8.4 Client Partitioner --- `app/ml/data/partitioner.py`

The partitioner distributes the training data among simulated federated
clients.

The current federated experiment uses three equal IID partitions:

  Client         Samples
  ------------ ---------
  hospital-1         152
  hospital-2         152
  hospital-3         152
  **Total**      **456**

IID means the client partitions are created to have approximately the
same underlying class distribution as the overall training subset.

Non-IID partitioning experiments have not been implemented in the
current prototype.

------------------------------------------------------------------------

## 9. Machine Learning Model

### 9.1 Diagnostic Model --- `app/ml/models/diagnostic_model.py`

The diagnostic model is a feed-forward neural network implemented with
PyTorch.

Its architecture is:

``` text
Input: 30 features
       |
       v
Fully Connected Layer: 32 neurons
       |
       v
Fully Connected Layer: 16 neurons
       |
       v
Output Layer: 2 classes
```

The model is used as the classification architecture for the centralized
and federated experiments.

### 9.2 Training Objective

The model uses Cross Entropy Loss for the binary classification task and
Stochastic Gradient Descent (SGD) as the optimizer.

The architecture and training settings form part of the experiment
configuration and should be interpreted alongside the recorded results.

------------------------------------------------------------------------

## 10. Local Training

### 10.1 Local Trainer --- `app/ml/training/local_trainer.py`

The local trainer performs model optimization using the training data
assigned to a client.

Its role in the federated workflow is to train a local copy of the model
using the client's partition.

Local training produces updated model parameters and training
information that can be used by the coordinator and recorded for
experiment inspection.

### 10.2 Simulated Hospital Client --- `app/ml/clients/hospital_client.py`

The hospital client represents one simulated participant in the
federated experiment.

A client is associated with its local training data and participates in
the local training workflow.

The client abstraction allows the coordinator to manage multiple
participants using a consistent interface.

The names `hospital-1`, `hospital-2`, and `hospital-3` are identifiers
for simulated clients. They do not represent real hospitals, real
hospital networks, or live external systems.

### 10.3 Local Training Experiment Runner

`app/ml/training/run_local_experiment.py` is the experiment runner
associated with the initial local-training workflow.

The local-training experiment records client-level information such as:

-   Client identifier.
-   Partition strategy.
-   Number of local samples.
-   Training loss.
-   Training accuracy.
-   Completed epochs.
-   Creation timestamp.

These records are used by the Hospital Clients frontend section.

------------------------------------------------------------------------

## 11. Centralized Training

### 11.1 Runner --- `run_centralized_experiment.py`

The centralized experiment runner executes the baseline training
workflow.

The general process is:

1.  Load and prepare the WDBC dataset.
2.  Create the stratified training and test subsets.
3.  Initialize the diagnostic model.
4.  Train the model using the centralized training subset.
5.  Evaluate the trained model on the held-out test subset.
6.  Persist the experiment configuration and evaluation metrics.

### 11.2 Purpose of the Baseline

The centralized experiment provides a reference result for comparison
with the federated experiments.

It uses the same research dataset and model foundation, while differing
in the training arrangement.

------------------------------------------------------------------------

## 12. Federated Learning Coordination

### 12.1 Coordinator --- `app/ml/federation/coordinator.py`

The coordinator manages the federated training workflow.

Its responsibilities include coordinating the participating clients and
the sequence of federated rounds.

At a high level, the coordinator:

1.  Maintains the current global model state.
2.  Distributes the global model parameters to participating clients.
3.  Coordinates local training.
4.  Collects client updates.
5.  Invokes the aggregation logic.
6.  Updates the global model.
7.  Supports evaluation and recording of round results.

The coordinator is an orchestration component. The mathematical
aggregation operation is implemented separately.

### 12.2 FedAvg Aggregation --- `app/ml/aggregation/fedavg.py`

The FedAvg module combines client model updates using a sample-weighted
average.

Let:

-   \(K\) be the number of participating clients.
-   (n_k) be the number of training samples held by client (k).
-   (N = `\sum`{=tex}\_{k=1}\^{K} n_k) be the total number of samples.
-   (w_k) be the locally updated model parameters returned by client
    (k).

The aggregated model parameters are:

\[ w\_{`\mathrm{global}`{=tex}} = `\sum`{=tex}\_{k=1}\^{K}
`\frac{n_k}{N}`{=tex} w_k \]

The weight assigned to each client is proportional to its local sample
count.

For the current experiment, all three clients hold 152 samples.
Therefore, their aggregation weights are equal.

### 12.3 FedAvg Experiment Runner

`app/ml/training/run_fedavg_experiment.py` executes the standard
federated experiment.

The current recorded standard FedAvg experiment uses:

-   Three simulated clients.
-   Five communication rounds.
-   Five local epochs per round.
-   IID client partitions.
-   No Differential Privacy mechanism.

The runner coordinates the federated workflow and records round-wise
evaluation information.

------------------------------------------------------------------------

## 13. Differential Privacy Implementation

### 13.1 Privacy Module Organization

The privacy components are organized under `app/ml/privacy/`:

``` text
privacy/
├── update_clipper.py
├── gaussian_mechanism.py
└── privacy_accountant.py
```

The modules have distinct responsibilities in the DP-FedAvg workflow.

### 13.2 Update Clipping --- `update_clipper.py`

Update clipping constrains the norm of client updates using a configured
maximum norm bound.

The purpose is to bound the magnitude of an individual client's
contribution before the central noise mechanism is applied.

The current recorded DP-FedAvg configuration uses a maximum update norm
of 1.0.

### 13.3 Gaussian Mechanism --- `gaussian_mechanism.py`

The Gaussian mechanism adds noise to the aggregated update according to
the configured noise multiplier and sensitivity.

The current recorded DP-FedAvg configuration uses a noise multiplier of
1.0.

This is a central Differential Privacy implementation: the coordinator
receives individual client updates before clipping, aggregation, and
noise processing.

### 13.4 Privacy Accountant --- `privacy_accountant.py`

The privacy accountant records the cumulative privacy cost across
federated rounds.

The current implementation uses an RDP-based Gaussian accounting
approach with full client participation.

The recorded configuration uses:

  Parameter              Value
  ---------------------- --------------------
  Noise multiplier       1.0
  Maximum update norm    1.0
  Delta                  (10\^{-5})
  Adjacency              Replace-one-client
  Client participation   Full participation

The final recorded epsilon for the current five-round DP-FedAvg run is
approximately 13.2565 at delta (10\^{-5}).

This value is specific to the implemented experiment and accounting
assumptions. It is not a universal privacy value for the platform.

### 13.5 DP-FedAvg Runner

`app/ml/training/run_dp_fedavg_experiment.py` executes the
differentially private federated experiment.

The workflow extends federated aggregation with update clipping and
Gaussian noise and records privacy-accounting information across rounds.

### 13.6 Important Privacy Boundary

The current implementation does not include cryptographic secure
aggregation.

The coordinator receives individual client updates before the central
noise mechanism is applied. Therefore, the implementation must not be
described as hiding individual updates from the coordinator.

Secure aggregation and Byzantine or malicious-client robust aggregation
are not implemented.

------------------------------------------------------------------------

## 14. Model Evaluation

### 14.1 Evaluator --- `app/ml/evaluation/evaluator.py`

The evaluator calculates classification metrics using model predictions
and the corresponding ground-truth labels.

The metrics used by the research experiments include:

-   Accuracy.
-   Precision.
-   Recall.
-   F1-score.
-   Sensitivity.
-   Specificity.
-   ROC-AUC.

These metrics provide complementary information about classification
behaviour.

### 14.2 Evaluation Dataset

The current experiments evaluate against the held-out test subset of 113
records.

The test subset is separate from the training partitions used by the
clients.

The evaluation results apply to the WDBC benchmark and the recorded
experimental configuration. They should not be interpreted as clinical
performance claims.

### 14.3 Training Metrics Versus Evaluation Metrics

Training metrics and test metrics describe different stages:

-   **Training loss and training accuracy** describe the model's
    behaviour on training data.
-   **Test accuracy, precision, recall, F1-score, sensitivity,
    specificity, and ROC-AUC** describe evaluation on the held-out test
    subset.

The distinction is important when interpreting client-local results
alongside global-model evaluation results.

In the current DP-FedAvg records, training loss and training accuracy
are intentionally null in the federated-round result records. The
frontend should preserve their unavailable status rather than display
invented values.

------------------------------------------------------------------------

## 15. Experiment Persistence and Database Access

### 15.1 Persistence Objective

Experiment results are persisted so they can be retrieved after the
training workflow completes.

The frontend reads stored records through the experiment API rather than
directly accessing the machine learning runtime or database.

### 15.2 Persisted Information Categories

The API exposes the following categories of experiment information:

  -----------------------------------------------------------------------
  Category                            Information
  ----------------------------------- -----------------------------------
  Experiment metadata                 Name, algorithm, dataset,
                                      configuration, status, timestamp

  Centralized metrics                 Centralized training and test
                                      evaluation information

  Federated rounds                    Round number, client count, sample
                                      count, evaluation metrics

  Privacy accounting                  Epsilon, delta, noise, sensitivity,
                                      clipping information, accounting
                                      metadata

  Client training metrics             Client ID, partition, sample count,
                                      local loss, accuracy, epochs
  -----------------------------------------------------------------------

### 15.3 Repository Read Path

A typical experiment metrics request follows this sequence:

1.  FastAPI receives the experiment metrics request.
2.  The router invokes the experiment service.
3.  The service requests the experiment and related metric records.
4.  The repository queries the relevant SQLAlchemy models.
5.  The service assembles the response.
6.  The response schema defines the returned structure.
7.  FastAPI serializes the response as JSON.

``` mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as Experiment Router
    participant SVC as Experiment Service
    participant REP as Experiment Repository
    participant DB as PostgreSQL

    FE->>API: GET /experiments/{id}/metrics
    API->>SVC: Retrieve experiment metrics
    SVC->>REP: Get experiment and related records
    REP->>DB: Query experiment
    DB-->>REP: Experiment record
    REP->>DB: Query centralized/federated/privacy/client metrics
    DB-->>REP: Related records
    REP-->>SVC: Retrieved data
    SVC-->>API: Construct metrics response
    API-->>FE: JSON response
```

### 15.4 Database Migrations

Alembic manages database schema migration history.

The migration workflow allows schema changes to be represented as
revision files and applied to the configured database.

The project has used Alembic migration checks to verify that SQLAlchemy
model metadata and the current migration state do not report additional
pending schema operations at the time of the check.

A manually created table or database object should not be described as
migration-managed unless it is represented in the Alembic history.

------------------------------------------------------------------------

## 16. Experiment Records in the Current Research Environment

The current database contains four completed experiment records.

  ----------------------------------------------------------------------------
  Experiment    Algorithm              Clients           Rounds Main purpose
  ------------- ------------- ---------------- ---------------- --------------
  Initial       Local                        3                1 Inspect local
  Hospital      training                                        training
  Local                                                         behaviour
  Training                                                      across
                                                                simulated
                                                                clients

  Centralized   Centralized                  1                1 Establish a
  Baseline                                                      centralized
                                                                comparison
                                                                baseline

  Standard      FedAvg                       3                5 Evaluate
  FedAvg                                                        standard
                                                                federated
                                                                training

  DP-FedAvg     DP-FedAvg                    3                5 Evaluate
                                                                central
                                                                Differential
                                                                Privacy
                                                                processing
                                                                during
                                                                federated
                                                                aggregation
  ----------------------------------------------------------------------------

### 16.1 Centralized Baseline

The recorded centralized experiment achieved:

  Metric            Recorded value
  --------------- ----------------
  Test accuracy             94.69%
  Precision                 95.00%
  Recall                    90.48%
  F1-score                  0.9268
  ROC-AUC                   0.9916

### 16.2 Standard FedAvg

The final recorded round of the standard FedAvg experiment achieved:

  Metric            Recorded value
  --------------- ----------------
  Test accuracy             86.73%
  Precision                100.00%
  Recall                    64.29%
  F1-score                  0.7826
  ROC-AUC                   0.9789

### 16.3 DP-FedAvg

The final recorded round of the DP-FedAvg experiment achieved:

  Metric            Recorded value
  --------------- ----------------
  Test accuracy             82.30%
  Precision                 68.97%
  Recall                    95.24%
  F1-score                  0.8000
  ROC-AUC                   0.8806
  Epsilon                  13.2565
  Delta                 (10\^{-5})

These are the recorded outcomes of the current runs. They should not be
presented as statistically conclusive results. The current experiment
set does not include a multi-seed evaluation or a privacy-noise sweep.

------------------------------------------------------------------------

## 17. Testing and Validation

### 17.1 Automated Tests

The backend test suite currently contains 62 passing tests, as recorded
during the development workflow.

Automated tests provide checks for implemented backend behaviour. They
do not, by themselves, establish the scientific validity of the research
methodology or guarantee production readiness.

### 17.2 API Validation

The health and experiment endpoints have been exercised through HTTP
requests during development.

The experiment metrics endpoint has been used to verify retrieval of:

-   Centralized metrics.
-   Federated round records.
-   Privacy-accounting records.
-   Client local-training metrics.

### 17.3 Database Validation

The database schema and migration state have been checked using Alembic.
The development workflow also verified that experiment result records
were persisted and could be retrieved through the API.

### 17.4 Frontend Build Validation

The frontend is built separately using its TypeScript and Vite build
script. A successful frontend build validates the frontend compilation
and bundling process, not the correctness of backend model training.

------------------------------------------------------------------------

## 18. Local Backend Execution

The following commands describe the established local development
workflow. Environment-specific database credentials and configuration
must be supplied locally.

### 18.1 Activate the Virtual Environment

From the backend directory in PowerShell:

``` powershell
.\.venv\Scripts\Activate.ps1
```

### 18.2 Configure the Database Environment

Ensure PostgreSQL is available and that the backend environment
configuration points to the intended development database.

Do not place database passwords or other secrets in committed
documentation or source files.

### 18.3 Run the Backend

Start the FastAPI application using the project's configured application
entry point and development server command.

The exact module path and command should be taken from the current
backend entry-point configuration rather than guessed if that
configuration changes.

### 18.4 Check Health

Once the backend is running, the health endpoints can be checked:

``` powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health/database"
```

### 18.5 Inspect Experiments

``` powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/experiments"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/experiments/summary"
```

For an individual experiment, use its actual UUID:

``` powershell
$experimentId = "REPLACE-WITH-ACTUAL-EXPERIMENT-UUID"

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/experiments/$experimentId/metrics"
```

The placeholder must be replaced with an experiment ID returned by the
experiment-list endpoint.

------------------------------------------------------------------------

## 19. Current Backend Limitations

The following limitations are important when describing the backend.

  -----------------------------------------------------------------------
  Area                                Current state
  ----------------------------------- -----------------------------------
  Dataset                             Public WDBC benchmark

  Client environment                  Simulated clients

  Client partitioning                 IID

  Centralized training                Implemented

  Local client training               Implemented

  Standard FedAvg                     Implemented

  Differentially private FedAvg       Implemented with central noise
                                      processing

  Update clipping                     Implemented

  Gaussian mechanism                  Implemented

  RDP privacy accounting              Implemented

  Secure aggregation                  Not implemented

  Non-IID experiments                 Not implemented

  Byzantine / malicious-client robust Not implemented
  aggregation                         

  Real hospital integration           Not implemented

  Clinical validation                 Not performed

  Production deployment and           Outside current prototype scope
  operational hardening               
  -----------------------------------------------------------------------

The backend should therefore be described as a research implementation
of selected federated learning and privacy mechanisms, not as a complete
production-grade privacy-preserving healthcare infrastructure.

------------------------------------------------------------------------

## 20. Summary

The FedHealth backend combines a FastAPI application layer,
experiment-management services, SQLAlchemy persistence, PostgreSQL
storage, and PyTorch-based research components.

The API layer exposes health and experiment information. The experiment
service and repository coordinate retrieval of persisted records. The
machine learning layer prepares the dataset, performs centralized or
client-local training, coordinates FedAvg rounds, applies the
implemented central Differential Privacy mechanism when configured, and
evaluates model performance.

The resulting experiment and metric records are stored in PostgreSQL and
exposed to the React frontend through versioned REST endpoints.

This architecture supports the current research prototype while
maintaining clear boundaries around its implemented capabilities. Secure
aggregation, non-IID experiments, robust aggregation, real hospital
integration, clinical validation, and production deployment are not part
of the current implementation.
