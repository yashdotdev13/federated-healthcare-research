# FedHealth --- Research Overview

## 1. Introduction

FedHealth is a privacy-focused federated learning research platform for
investigating collaborative machine learning across multiple simulated
healthcare institutions without collecting their local training datasets
in one centralized repository.

The project explores **Federated Learning (FL)** and **Differential
Privacy (DP)** in a healthcare-oriented binary-classification research
scenario. It provides an environment for executing, recording,
comparing, and analyzing centralized training, standard Federated
Averaging (FedAvg), and Differentially Private Federated Averaging
(DP-FedAvg).

In conventional centralized machine learning, training datasets are
collected in one location. In distributed healthcare settings,
transferring records can create data-governance, privacy, and security
challenges. Federated Learning offers an alternative: clients train
locally and communicate model updates to a coordinator, rather than
sending their raw training records.

Federated Learning alone does not guarantee that model updates cannot
reveal information about local training data. FedHealth therefore also
investigates a central Differential Privacy mechanism based on update
clipping and Gaussian noise.

> **Research-prototype boundary:** FedHealth is an academic and
> engineering research prototype. It is not a production healthcare
> application, a clinically validated diagnostic system, or a platform
> connected to real hospitals. The healthcare institutions shown in the
> application are simulated clients, and the experiments use a public
> benchmark dataset.

## 2. Research Problem

Machine learning models may benefit from data distributed across
multiple healthcare institutions. However, centralizing those datasets
can introduce challenges:

-   Institutional data-sharing restrictions may limit the transfer of
    sensitive records.
-   Moving records outside their original environment increases
    exposure.
-   Institutions may need to retain control over locally maintained
    datasets.
-   A centralized repository can become a target for unauthorized
    access.
-   Privacy requirements constrain the design of collaborative learning
    systems.

Federated Learning addresses part of this problem by keeping training
data at participating clients and communicating model updates instead of
raw records. However, model updates themselves may still reveal
information about local training data.

The research problem explored by FedHealth is therefore twofold: how to
train a shared model across distributed clients without transferring
their raw training datasets, and how an additional privacy mechanism
affects model performance.

## 3. Research Motivation

### 3.1 Decentralized Data Ownership

Participating clients retain their local training partitions. The
coordinator does not need to collect the original training records to
perform the federated aggregation workflow.

### 3.2 Collaborative Model Training

Multiple clients independently train the same model architecture using
their respective local data. Their updates are sent to a coordinator,
which combines them using Federated Averaging to produce a global model.

### 3.3 Additional Privacy Protection

Federated updates can contain information related to local training
data. Differential Privacy provides a mathematical framework for
limiting the influence of individual contributions. In the current
prototype, update clipping and a Gaussian noise mechanism are used in
the DP-FedAvg experiment.

## 4. Research Objectives

The objectives are:

1.  Implement a simulated multi-client federated learning environment
    representing distributed healthcare institutions.
2.  Perform local machine learning training independently at each
    simulated client.
3.  Implement Federated Averaging to combine locally trained model
    updates.
4.  Implement centralized training as a comparative baseline.
5.  Integrate Differential Privacy through update clipping and Gaussian
    noise addition.
6.  Record privacy-accounting information, including epsilon and delta,
    across federated rounds.
7.  Evaluate trained models using classification metrics.
8.  Compare centralized learning, standard FedAvg, and DP-FedAvg.
9.  Provide a frontend dashboard for visualizing experiments, model
    performance, client training information, and privacy metrics.
10. Establish a foundation for further investigation into secure
    aggregation, non-IID client distributions, and robust aggregation.

## 5. Research Questions

### RQ1 --- Federated Learning

Can simulated healthcare clients collaboratively train a global model
without transferring their raw local training datasets to the
coordinator?

### RQ2 --- Model Performance

How does standard FedAvg compare with a centralized baseline under the
current dataset, model architecture, and training configuration?

### RQ3 --- Differential Privacy

How does incorporating a Gaussian noise mechanism into federated
aggregation affect the resulting model performance?

### RQ4 --- Privacy Accounting

How does the recorded privacy budget epsilon evolve across successive
federated rounds under the configured accounting assumptions?

### RQ5 --- Privacy and Utility

What differences in accuracy, precision, recall, F1-score, and ROC-AUC
are observed between standard FedAvg and DP-FedAvg?

These questions are investigated through the experiments implemented in
this prototype. Conclusions are limited to the configurations and
observations actually recorded.

## 6. Platform Overview

FedHealth has two principal application layers:

-   **Backend research and machine learning engine:** performs data
    preparation, training, aggregation, privacy processing, evaluation,
    experiment management, and persistence.
-   **Frontend research dashboard:** communicates with the backend
    through REST APIs and presents experiment information.

### 6.1 Backend Responsibilities

The backend is responsible for:

-   Loading and preprocessing the public benchmark dataset.
-   Creating simulated client dataset partitions.
-   Performing centralized training and client-local training.
-   Coordinating federated rounds.
-   Aggregating client model updates.
-   Applying the configured Differential Privacy mechanism.
-   Evaluating trained models.
-   Calculating and recording privacy-accounting metrics.
-   Persisting experiment configurations and results.
-   Exposing experiment information through REST APIs.

### 6.2 Frontend Responsibilities

The frontend contains five main sections:

1.  **Overview Dashboard:** summarizes experiment activity, model
    performance, privacy information, and backend health.
2.  **Experiments:** displays recorded experiments, configurations,
    training results, federated rounds, and client metrics.
3.  **Model Analytics:** compares training approaches and visualizes
    evaluation results.
4.  **Hospital Clients:** presents simulated clients, local dataset
    partitions, and recorded local training performance.
5.  **Privacy & Security:** presents Differential Privacy configuration,
    privacy-accounting progression, and the implementation status of
    security mechanisms.

The frontend does not execute machine learning training independently.
It retrieves and visualizes information produced and persisted by the
backend.

## 7. Research Dataset

The current implementation uses the public **Wisconsin Diagnostic Breast
Cancer (WDBC)** dataset as a benchmark for binary classification.

### 7.1 Dataset Characteristics

  Property           Value
  ------------------ ------------------------------------
  Dataset            Wisconsin Diagnostic Breast Cancer
  Total records      569
  Input features     30 numerical features
  Classification     Binary
  Benign class       0
  Malignant class    1
  Training records   456
  Test records       113

### 7.2 Data Preparation

The dataset is divided into training and testing subsets using a
stratified 80:20 split. Feature standardization uses statistics
calculated from the training subset; the same transformation is applied
to the test subset. This prevents test data from influencing the
feature-scaling parameters.

### 7.3 Federated Client Distribution

The 456 training records are distributed equally across three simulated
clients in the current IID experiment.

  Simulated Client     Training Samples Partition
  ------------------ ------------------ -----------
  hospital-1                        152 IID
  hospital-2                        152 IID
  hospital-3                        152 IID
  **Total**                     **456** 

Each client maintains its own local training partition. The current
implementation uses IID partitioning. Non-IID partitioning is a planned
extension, not an implemented experiment.

## 8. Machine Learning Approaches

### 8.1 Centralized Training

Centralized training serves as a baseline. The training dataset is used
in a conventional single-model workflow, and the resulting model is
evaluated against the held-out test subset. This provides a reference
for the federated approaches.

### 8.2 Federated Averaging

Federated Averaging (FedAvg) is the aggregation algorithm used in the
standard federated experiment:

1.  The coordinator initializes the global model.
2.  The global model parameters are distributed to participating
    clients.
3.  Each client trains locally using its own dataset partition.
4.  Clients return their locally updated model parameters.
5.  The coordinator calculates a sample-weighted average of the received
    parameters.
6.  The resulting global model is evaluated.
7.  The process continues for the configured number of communication
    rounds.

The aggregation weights reflect the number of local training samples
represented by each client.

### 8.3 Differentially Private Federated Averaging

DP-FedAvg extends the federated workflow with update clipping and
Gaussian noise. The current implementation performs **central
Differential Privacy processing** during aggregation.

Client updates are clipped using a configured norm bound. Gaussian noise
is added to the aggregated update according to the configured noise
multiplier and sensitivity calculation. Privacy-accounting information
is recorded across rounds.

**Implementation distinction:** the coordinator receives individual
client updates before the central noise mechanism is applied. The
current prototype does not implement secure aggregation that
cryptographically hides individual client updates from the coordinator.

## 9. Model Architecture

The classification model is a feed-forward neural network implemented
using PyTorch.

``` text
Input Layer
    |
    | 30 input features
    v
Fully Connected Layer
    |
    | 32 neurons
    v
Fully Connected Layer
    |
    | 16 neurons
    v
Output Layer
    |
    | 2 output classes
    v
Classification Result
```

The model uses Cross Entropy Loss and Stochastic Gradient Descent (SGD).
The same model architecture forms the basis of centralized and federated
training, allowing the experiments to focus on differences in training
workflows.

## 10. Evaluation Methodology

  -----------------------------------------------------------------------
  Metric                              Purpose
  ----------------------------------- -----------------------------------
  Accuracy                            Proportion of correctly classified
                                      samples

  Precision                           Proportion of positive predictions
                                      that are correct

  Recall                              Proportion of actual positive
                                      samples correctly identified

  F1-score                            Harmonic mean of precision and
                                      recall

  ROC-AUC                             Measures the model's ability to
                                      distinguish between the classes

  Sensitivity                         True positive rate

  Specificity                         True negative rate
  -----------------------------------------------------------------------

These metrics provide complementary views of classification performance.
Accuracy alone is insufficient to characterize a binary classifier,
particularly when false-positive and false-negative errors have
different implications.

## 11. Differential Privacy Configuration

The current DP-FedAvg experiment uses the following recorded
configuration:

  Parameter              Recorded Configuration
  ---------------------- ------------------------
  Differential Privacy   Enabled
  Noise mechanism        Gaussian
  Noise multiplier       1.0
  Maximum update norm    1.0
  Delta                  0.00001
  Client participation   Full participation
  Adjacency definition   Replace-one-client
  Secure aggregation     Disabled

The privacy accountant uses an RDP-based Gaussian mechanism with full
participation. The reported epsilon is interpreted under the configured
client-level adjacency and accounting assumptions.

The final recorded privacy budget in the current five-round DP-FedAvg
experiment is approximately **epsilon = 13.2565 at delta = 10\^-5**.

This value describes the recorded experiment and its assumptions. It is
not a universal privacy guarantee for arbitrary configurations or
deployments.

## 12. Technology Stack

### Backend

-   Python 3.13
-   FastAPI
-   PyTorch
-   SQLAlchemy
-   Pydantic
-   Alembic
-   PostgreSQL
-   pg8000

### Frontend

-   React
-   TypeScript
-   Vite
-   Tailwind CSS
-   React Query
-   Axios
-   Recharts
-   Lucide React

### Development and Testing

-   Python virtual environments
-   Pytest
-   TypeScript compiler
-   Vite production build
-   REST API testing

## 13. Current Implementation Scope

### Implemented Capabilities

-   Centralized model training.
-   Simulated multi-client local training.
-   IID client data partitioning.
-   Federated Averaging.
-   Differentially Private Federated Averaging.
-   Update clipping.
-   Gaussian noise addition.
-   RDP-based privacy accounting.
-   Model evaluation and metric persistence.
-   Experiment management and retrieval APIs.
-   Frontend visualization of experiment and privacy data.

### Not Implemented in the Current Prototype

-   Cryptographic secure aggregation.
-   Non-IID client partitioning experiments.
-   Byzantine or malicious-client robust aggregation.
-   Production authentication and deployment controls.
-   Integration with real healthcare institutions.
-   Clinical validation or diagnostic deployment.

These capabilities are possible extensions and must remain clearly
distinguished from the existing implementation.

## 14. Research Significance

FedHealth provides an experimental foundation for studying the
interaction between federated machine learning and privacy protection in
a healthcare-oriented classification scenario.

By implementing centralized training, standard FedAvg, and DP-FedAvg,
the platform enables comparative evaluation of different training
strategies under a common dataset and model architecture. It also
provides persistent experiment management and a dashboard for examining
training performance, client-level metrics, and privacy-accounting
results.

The implementation is intended to support further engineering and
research, including investigation of non-IID client distributions,
secure aggregation, robust aggregation, and broader privacy-utility
analysis.

Results from the current prototype are experimental observations, not
evidence of clinical effectiveness or production-level privacy security.

## 15. Document Scope

This document introduces the research motivation, objectives, platform
capabilities, dataset, machine learning approaches, privacy
configuration, and current implementation boundaries.

The following documentation areas provide detailed technical
explanations:

-   System architecture and component interactions.
-   Frontend architecture and individual dashboard sections.
-   Backend modules, services, repositories, and API implementation.
-   Federated learning workflow and aggregation mathematics.
-   Differential Privacy mechanisms and privacy accounting.
-   Database schema and persistence design.
-   Experimental methodology and recorded results.
-   Development environment, setup, and execution procedures.
