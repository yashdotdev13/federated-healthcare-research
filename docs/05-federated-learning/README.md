# FedHealth --- Federated Learning Workflow and Mathematical Foundations

## 1. Purpose of This Document

This document explains the Federated Learning workflow implemented in
FedHealth, with particular focus on simulated clients, local model
training, communication rounds, coordinator responsibilities, and
Federated Averaging (FedAvg).

It connects the conceptual federated learning process to the current
research prototype and explains the mathematical notation used to
describe sample-weighted model aggregation.

The document also distinguishes standard FedAvg from the separately
implemented Differentially Private Federated Averaging workflow.

> **Implementation boundary:** The current prototype uses three
> simulated clients and IID partitions of the public WDBC training
> subset. It is not connected to real healthcare institutions. Secure
> aggregation, non-IID partition experiments, and Byzantine-robust
> aggregation are not implemented.

------------------------------------------------------------------------

## 2. What Is Federated Learning?

Federated Learning is a collaborative machine learning approach in which
multiple participants train a shared model while keeping their local
training datasets at their respective clients.

In a conventional centralized workflow, the training records are
collected into one location. In a federated workflow, each participant
trains a local copy of the model and communicates model parameters or
updates to a coordinator.

The coordinator combines the client contributions to produce an updated
global model. The updated global model can then be distributed to
clients for another round of local training.

The central idea is to coordinate model learning without requiring the
original client training records to be transferred to the coordinator.

Federated Learning reduces the need to centralize raw training data, but
it does not by itself guarantee that communicated model updates reveal
no information about the training data. That is why FedHealth also
investigates Differential Privacy in a separate experiment.

## 3. Federated Learning in FedHealth

FedHealth uses a simulated cross-silo-style arrangement in which a
central coordinator manages three simulated healthcare clients.

The clients are identified as:

-   `hospital-1`
-   `hospital-2`
-   `hospital-3`

These names represent software clients in the research environment. They
are not real hospitals, independent hospital deployments, or live
network participants.

### 3.1 Roles in the Workflow

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  Dataset preparation                 Loads and prepares the WDBC
                                      benchmark

  Client partitioner                  Divides the training subset among
                                      simulated clients

  Simulated client                    Holds a local training partition
                                      and performs local training

  Local trainer                       Optimizes a local copy of the model

  Coordinator                         Orchestrates federated rounds and
                                      collects client updates

  FedAvg aggregator                   Combines client model updates using
                                      sample-count weights

  Evaluator                           Measures the global model on the
                                      held-out test subset

  Persistence layer                   Stores experiment configuration and
                                      result records
  -----------------------------------------------------------------------

### 3.2 High-Level Workflow

``` mermaid
flowchart TD
    A[Load and Prepare WDBC Dataset]
    B[Create Training and Test Subsets]
    C[Partition Training Subset]
    D[Initialize Global Model]
    E[Coordinator Distributes Global Parameters]
    F[Clients Perform Local Training]
    G[Clients Return Local Model Updates]
    H[Coordinator Performs FedAvg]
    I[Update Global Model]
    J[Evaluate Global Model]
    K[Persist Round Results]
    L{More Rounds?}
    M[Complete Experiment]

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K --> L
    L -->|Yes| E
    L -->|No| M
```

This sequence describes the standard federated training workflow. The
DP-FedAvg experiment adds privacy processing to the update aggregation
path, as described later in this document.

------------------------------------------------------------------------

## 4. Dataset Preparation for Federated Training

### 4.1 Public Benchmark Dataset

The current experiments use the Wisconsin Diagnostic Breast Cancer
(WDBC) dataset.

  Property                      Value
  -------------------------- --------
  Total records                   569
  Numerical input features         30
  Training records                456
  Test records                    113
  Classification task          Binary

The dataset is split into training and testing subsets using a
stratified 80:20 split. Feature standardization is fitted using the
training subset and then applied to the test subset.

### 4.2 Client Partitioning

The 456 training records are divided equally across three simulated
clients in the current IID experiment.

  Client         Local training records   Share of training data
  ------------ ------------------------ ------------------------
  hospital-1                        152                      1/3
  hospital-2                        152                      1/3
  hospital-3                        152                      1/3
  **Total**                     **456**                 **100%**

Each client trains using its own assigned partition.

### 4.3 Meaning of IID

IID stands for Independent and Identically Distributed.

In the current experiment, the client partitions are constructed to have
approximately the same underlying class distribution as the overall
training subset. This creates a controlled starting point for studying
the federated training workflow.

Real institutions may have different patient populations, data
collection processes, and class distributions. Such differences can
produce non-IID client datasets.

The current prototype does not include non-IID partitioning experiments.
Therefore, the current results should not be used to make claims about
performance under heterogeneous client distributions.

------------------------------------------------------------------------

## 5. Model Shared Across Clients

The centralized and federated experiments use the same feed-forward
neural-network architecture as their classification model.

``` text
Input Layer
  30 features
      |
      v
Fully Connected Layer
  32 neurons
      |
      v
Fully Connected Layer
  16 neurons
      |
      v
Output Layer
  2 classes
```

The model is implemented with PyTorch.

The training objective uses Cross Entropy Loss, and Stochastic Gradient
Descent (SGD) is used as the optimizer.

In federated training, each client receives the current global model
parameters and performs local optimization using the same model
architecture.

The clients do not need to share their original training records to
perform this local optimization.

------------------------------------------------------------------------

## 6. Local Training

### 6.1 What Happens Locally?

Local training is the process in which a client optimizes its own copy
of the global model using its assigned local dataset.

For a given communication round:

1.  The client receives the current global model parameters.
2.  The client initializes or updates its local model state using those
    parameters.
3.  The local trainer processes the client's training partition.
4.  The optimizer updates the model parameters over the configured local
    epochs.
5.  The client makes its resulting model parameters available to the
    coordinator.

The local trainer is responsible for the optimization process. The
coordinator is responsible for orchestrating the participation of
clients and the round sequence.

### 6.2 Local Epochs

An epoch is one complete pass through the local training dataset.

The current standard FedAvg experiment uses five local epochs per client
per communication round.

The number of local epochs affects how much optimization each client
performs before returning its model update. Changing the local epoch
count changes the training configuration and can affect the resulting
global model.

### 6.3 Local Training Metrics

The initial local-training experiment records client-level information.

The recorded values are:

  Client         Samples   Training loss   Training accuracy   Epochs
  ------------ --------- --------------- ------------------- --------
  hospital-1         152          0.6477              81.45%        5
  hospital-2         152          0.6490              80.39%        5
  hospital-3         152          0.6535              79.34%        5

These are local training metrics from the initial local-training
experiment. They are not the global model's held-out test metrics and
should not be interpreted as such.

------------------------------------------------------------------------

## 7. Communication Rounds

Federated training proceeds through communication rounds.

A communication round is one cycle in which the coordinator distributes
the current global model, clients perform local training, and the
coordinator aggregates their returned updates.

### 7.1 Round Lifecycle

``` mermaid
sequenceDiagram
    participant C as Coordinator
    participant H1 as hospital-1
    participant H2 as hospital-2
    participant H3 as hospital-3

    C->>H1: Global model parameters
    C->>H2: Global model parameters
    C->>H3: Global model parameters

    H1->>H1: Local training
    H2->>H2: Local training
    H3->>H3: Local training

    H1-->>C: Updated model parameters
    H2-->>C: Updated model parameters
    H3-->>C: Updated model parameters

    C->>C: Weighted aggregation
    C->>C: Update global model
```

The sequence repeats for the configured number of rounds.

### 7.2 Current Standard FedAvg Configuration

The recorded standard FedAvg experiment uses:

  Configuration                 Value
  ------------------------ ----------
  Simulated clients                 3
  Communication rounds              5
  Local epochs per round            5
  Partition strategy              IID
  Differential Privacy       Disabled

The configuration describes the recorded experiment. A different run may
use different settings and produce different results.

------------------------------------------------------------------------

## 8. Federated Averaging (FedAvg)

### 8.1 Purpose

Federated Averaging is the aggregation algorithm used to combine locally
trained model parameters into an updated global model.

Clients may have different local sample counts. FedAvg accounts for this
by weighting each client's model parameters according to the number of
local training samples represented by that client.

### 8.2 Mathematical Formulation

Let:

-   \(K\) denote the number of participating clients.
-   (n_k) denote the number of training samples held by client (k).
-   \(N\) denote the total number of training samples across
    participating clients.
-   (w_t) denote the global model parameters at the beginning of round
    (t).
-   (w\_{t+1}\^{(k)}) denote the locally updated parameters returned by
    client (k) after local training in round (t).
-   (w\_{t+1}) denote the new global model parameters after aggregation.

The total number of samples is:

\[ N = `\sum`{=tex}\_{k=1}\^{K} n_k \]

The aggregation weight for client (k) is:

\[ p_k = `\frac{n_k}{N}`{=tex} \]

The sample-weighted FedAvg update is:

\[ w\_{t+1} = `\sum`{=tex}*{k=1}\^{K} p_k w*{t+1}\^{(k)} \]

Equivalently:

\[ w\_{t+1} = `\sum`{=tex}*{k=1}\^{K} `\frac{n_k}{N}`{=tex}
w*{t+1}\^{(k)} \]

The resulting global model is a weighted average of the locally updated
model parameter states.

### 8.3 Weight Calculation in the Current Experiment

The current experiment has three clients with 152 samples each.

Therefore:

\[ N = 152 + 152 + 152 = 456 \]

Each client receives the same aggregation weight:

\[ p_1 = p_2 = p_3 = `\frac{152}{456}`{=tex} = `\frac{1}{3}`{=tex} \]

For this equal-sized IID partition, the weighted aggregation assigns
one-third of the total weight to each client.

If clients had different sample counts, their aggregation weights would
differ accordingly.

### 8.4 Conceptual Aggregation Example

Suppose three clients return locally updated parameter values for one
particular model parameter:

-   Client 1 returns (a_1).
-   Client 2 returns (a_2).
-   Client 3 returns (a_3).

With equal sample counts, the aggregated value for that parameter is:

\[ a\_{`\mathrm{global}`{=tex}} = `\frac{a_1 + a_2 + a_3}{3}`{=tex} \]

This example illustrates the arithmetic for one parameter. A neural
network contains many parameter tensors, and the aggregation operation
is applied to the corresponding model parameters.

### 8.5 Why Sample-Weighted Aggregation?

A simple unweighted average would assign equal importance to every
client regardless of how many samples each client represents.

FedAvg's sample-count weighting accounts for the size of each local
dataset.

The weighting does not guarantee that all client distributions are
identical or that every client has equal influence in every possible
sense. It defines how local model parameter states contribute to the
aggregate under the selected weighting rule.

------------------------------------------------------------------------

## 9. Coordinator Responsibilities

The coordinator is the orchestration component of the federated
workflow.

Its responsibilities include:

1.  Maintaining the current global model state.
2.  Starting a federated communication round.
3.  Making the global model parameters available to participating
    clients.
4.  Coordinating local training.
5.  Collecting client model updates.
6.  Invoking the aggregation implementation.
7.  Updating the global model state.
8.  Supporting evaluation and recording of round results.
9.  Repeating the workflow until the configured round count is reached.

The coordinator and aggregator have different responsibilities:

-   The **coordinator** manages the workflow.
-   The **aggregator** performs the mathematical model-combination
    operation.

This separation helps keep round orchestration distinct from the FedAvg
calculation.

------------------------------------------------------------------------

## 10. Global Model Evaluation

After aggregation, the updated global model is evaluated using the
held-out test subset.

The test subset contains 113 records in the current dataset split.

The evaluator calculates classification metrics including:

-   Accuracy.
-   Precision.
-   Recall.
-   F1-score.
-   Sensitivity.
-   Specificity.
-   ROC-AUC.

The resulting values are associated with the corresponding federated
round and persisted for later inspection.

### 10.1 Why Evaluate After Aggregation?

Client-local training metrics describe how each local model performed on
its own training partition.

The global model evaluation measures the aggregated model against the
held-out test subset.

These measurements answer different questions:

  -----------------------------------------------------------------------
  Measurement             Data used               What it describes
  ----------------------- ----------------------- -----------------------
  Client training         Client's local training Local model performance
  accuracy                partition               on local training data

  Global test accuracy    Held-out test subset    Performance of the
                                                  aggregated global model
                                                  on test data
  -----------------------------------------------------------------------

They should not be treated as interchangeable.

------------------------------------------------------------------------

## 11. Recorded Standard FedAvg Results

The current standard FedAvg experiment used three clients, five rounds,
five local epochs, and IID partitions.

The final recorded round produced:

  Metric            Final recorded value
  --------------- ----------------------
  Test accuracy                   86.73%
  Precision                      100.00%
  Recall                          64.29%
  F1-score                        0.7826
  ROC-AUC                         0.9789

These values are observations from one recorded run. They are not
statistical estimates across multiple random seeds and do not establish
general performance for other datasets or client distributions.

### 11.1 Interpretation

The final round's precision of 100% means that, for the evaluated test
predictions in that run, the positive predictions were correct.

The recall of 64.29% indicates that the model identified 64.29% of the
actual positive test samples.

The difference between precision and recall illustrates why several
metrics are needed to understand classification behaviour.

The results should be interpreted in the context of the dataset, class
labels, model, training configuration, and test split.

------------------------------------------------------------------------

## 12. Standard FedAvg Versus DP-FedAvg

Standard FedAvg and DP-FedAvg share the federated learning structure:

-   The coordinator distributes global parameters.
-   Clients train locally.
-   Clients return model updates.
-   The coordinator combines client contributions.
-   The global model is evaluated.

The DP-FedAvg workflow adds privacy processing to the aggregation path.

  Aspect                        Standard FedAvg                       DP-FedAvg
  ----------------------------- ------------------------------------- --------------------
  Local client training         Yes                                   Yes
  Federated coordinator         Yes                                   Yes
  Sample-weighted aggregation   Yes                                   Yes
  Update clipping               Not part of the standard experiment   Applied
  Gaussian noise                No                                    Applied centrally
  Privacy accounting            No DP accounting record               Recorded per round
  Secure aggregation            Not implemented                       Not implemented

The detailed privacy mechanism and its mathematical assumptions are
covered in the dedicated Differential Privacy documentation.

### 12.1 Central Privacy Processing Boundary

In the current DP-FedAvg implementation, the coordinator receives
individual client updates before central clipping, aggregation, and
Gaussian noise processing.

Therefore, the current implementation does not cryptographically hide
individual updates from the coordinator.

Federated Learning and Differential Privacy are implemented, but secure
aggregation is not.

------------------------------------------------------------------------

## 13. Experiment Persistence

The federated experiment workflow records information that can be
inspected through the backend API and frontend.

The persisted information includes:

-   Experiment configuration.
-   Federated round number.
-   Number of participating clients.
-   Total sample count.
-   Evaluation metrics.
-   Privacy-accounting records for DP experiments.
-   Client local-training metrics where recorded.

The frontend retrieves this information through the experiment metrics
endpoint.

Opening the Experiments, Model Analytics, Hospital Clients, or Privacy &
Security pages retrieves persisted information. It does not itself
initiate a new federated training run.

------------------------------------------------------------------------

## 14. Implementation Mapping

The main implementation areas associated with the federated workflow
are:

  Component                         File
  --------------------------------- -----------------------------------------------
  Dataset loading and preparation   `app/ml/data/dataset.py`
  Client partitioning               `app/ml/data/partitioner.py`
  Simulated client                  `app/ml/clients/hospital_client.py`
  Local training                    `app/ml/training/local_trainer.py`
  Federated coordinator             `app/ml/federation/coordinator.py`
  FedAvg aggregation                `app/ml/aggregation/fedavg.py`
  Diagnostic neural network         `app/ml/models/diagnostic_model.py`
  Evaluation                        `app/ml/evaluation/evaluator.py`
  Standard FedAvg runner            `app/ml/training/run_fedavg_experiment.py`
  Local training runner             `app/ml/training/run_local_experiment.py`
  DP-FedAvg runner                  `app/ml/training/run_dp_fedavg_experiment.py`

These paths identify the principal modules in the current backend
structure.

------------------------------------------------------------------------

## 15. Current Scope and Limitations

The current federated learning implementation has the following scope:

### Implemented

-   Three simulated clients.
-   Local training on client-specific data partitions.
-   IID partitioning.
-   A shared PyTorch model architecture.
-   Five-round standard FedAvg experiment.
-   Sample-count-weighted aggregation.
-   Global model evaluation.
-   Experiment and round metric persistence.
-   A separate DP-FedAvg experiment with central privacy processing.

### Not Implemented

-   Real hospital client connections.
-   Non-IID partitioning experiments.
-   Cryptographic secure aggregation.
-   Byzantine or malicious-client robust aggregation.
-   Client dropout and unreliable-network experiments.
-   A multi-seed statistical evaluation campaign.
-   Clinical validation.

The current prototype demonstrates the core federated workflow under
controlled conditions. It does not establish robustness under
heterogeneous, adversarial, or production network conditions.

------------------------------------------------------------------------

## 16. Summary

FedHealth implements a simulated federated learning workflow in which
three clients train a shared PyTorch classification model using separate
IID partitions of the WDBC training subset.

The coordinator distributes the current global parameters, clients
perform local optimization, and the FedAvg aggregator combines the
resulting model parameter states using weights proportional to local
sample counts.

The updated global model is evaluated against a held-out test subset,
and the resulting metrics are persisted for inspection through the
backend API and frontend dashboard.

The separate DP-FedAvg experiment extends this workflow with central
update clipping and Gaussian noise, together with privacy accounting.
Secure aggregation and robust aggregation remain unimplemented.

This workflow provides the foundation for understanding the federated
experiments currently available in FedHealth.
