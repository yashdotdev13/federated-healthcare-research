# Document 07 --- Experimental Methodology and Results Analysis

## 1. Purpose

This document describes how the current Federated Healthcare Research
prototype is evaluated, how its experiments are configured, what results
have been recorded, and what conclusions can and cannot be drawn from
those results.

The project is a research prototype for studying federated learning and
privacy mechanisms. It is not a production healthcare system and is not
intended to diagnose patients or support clinical decisions.

## 2. Research Evaluation Objectives

The current evaluation is designed to investigate four practical
questions:

1.  How does a centralized training baseline perform on the selected
    public benchmark?
2.  How does standard Federated Averaging (FedAvg) perform when the same
    training data is distributed across simulated clients?
3.  How do model utility and privacy-accounting values behave when
    central differential privacy is added to FedAvg?
4.  Can the prototype persist and expose experiment configurations,
    round metrics, client metrics, and privacy metrics for inspection?

The current implementation provides an initial experimental comparison.
It does not yet establish statistically general conclusions about
federated healthcare systems.

## 3. Dataset and Task

### 3.1 Dataset

The experiments use the public Wisconsin Diagnostic Breast Cancer (WDBC)
benchmark.

  Property                   Value
  ------------------------ -------
  Total records                569
  Numeric input features        30
  Training records             456
  Test records                 113
  Classification classes         2

The target encoding used by the prototype is:

-   `0`: benign
-   `1`: malignant

This is a benchmark classification task only. The prototype's outputs
are experimental model predictions and must not be interpreted as
clinical diagnoses.

### 3.2 Preprocessing

The dataset is divided into training and test partitions using a
stratified 80/20 split:

-   456 records are used for training.
-   113 records are held out for evaluation.

Feature standardization uses statistics calculated from the training
partition only. The test partition is transformed using the
training-derived mean and standard deviation. This avoids fitting
preprocessing statistics on the held-out test data.

### 3.3 Client partitioning

The 456 training records are distributed evenly among three simulated
clients:

  Client         Training samples Partition
  ------------ ------------------ -----------
  hospital-1                  152 IID
  hospital-2                  152 IID
  hospital-3                  152 IID
  **Total**               **456** 

The names represent simulated institutions in the experiment. They do
not represent connected hospitals or real healthcare organizations.

The current recorded federated experiments use IID partitions. Non-IID
partition experiments remain future work.

## 4. Model and Training Setup

The prototype uses a feed-forward neural network implemented in PyTorch.

The model architecture is:

\[ 30 `\rightarrow 32`{=tex} `\rightarrow 16`{=tex}
`\rightarrow 2`{=tex} \]

-   Input layer: 30 numeric features.
-   Hidden layer 1: 32 units.
-   Hidden layer 2: 16 units.
-   Output layer: 2 class logits.

The training implementation uses:

-   PyTorch.
-   Stochastic Gradient Descent (SGD).
-   Cross-entropy loss.
-   Local training on each simulated client for federated experiments.

The centralized and federated experiments have different training
procedures and recorded configurations. Their results should be read as
the current prototype's experimental runs, not as a fully controlled
benchmark study.

## 5. Experiment Groups

Three principal experiment types are currently persisted.

### 5.1 Centralized baseline

The centralized experiment trains one model using the complete training
partition in a single training process.

  Setting                                               Value
  ------------------ ----------------------------------------
  Training samples                                        456
  Epochs                                                   25
  Experiment ID        `ca672b33-5b23-420b-99b4-78ac8322ffc9`

This run provides a reference point for the model's performance when
training is not distributed among simulated clients.

### 5.2 Standard FedAvg

The standard federated experiment distributes training data across three
clients. Each client trains locally, then the coordinator combines
client updates using sample-weighted Federated Averaging.

  Setting                                                     Value
  ------------------------ ----------------------------------------
  Clients                                                         3
  Samples per client                                            152
  Communication rounds                                            5
  Local epochs per round                                          5
  Partition type                                                IID
  Differential privacy                                     Disabled
  Experiment ID              `bdaf2928-fed6-4ae3-9767-7a5e75427d8f`

For client (k), the aggregation weight is based on its number of
training examples:

\[ p_k=`\frac{n_k}{\sum_j n_j}`{=tex}. \]

The global model update is formed from the weighted client updates.
Since the three clients have equal sample counts in this run, each has
weight (1/3).

### 5.3 DP-FedAvg

The DP-FedAvg experiment adds central differential privacy to the
weighted federated aggregation workflow.

  Setting                                                                      Value
  ----------------------------------------- ----------------------------------------
  Clients                                                                          3
  Communication rounds                                                             5
  Local epochs per round                                                           5
  Partition type                                                                 IID
  DP clipping bound                                                              1.0
  Noise multiplier                                                               1.0
  Delta                                                                   (10\^{-5})
  Recorded replace-one-client sensitivity                                      (2/3)
  Secure aggregation                                        Disabled/not implemented
  Experiment ID                               `b0de2782-d703-4148-b9ea-cef21f5cda45`

The experiment clips client updates, aggregates them using fixed public
sample weights, adds Gaussian noise to the aggregate, and records
privacy-accounting results per round.

The coordinator receives individual updates before noise is added.
Therefore, this experiment does not hide individual client updates from
the coordinator.

## 6. Evaluation Metrics

The prototype records common binary-classification metrics.

### 6.1 Accuracy

Accuracy is the fraction of predictions that are correct:

\[ `\text{Accuracy}`{=tex}=`\frac{TP+TN}{TP+TN+FP+FN}`{=tex}. \]

It gives an overall correctness measure but can hide differences between
classes.

### 6.2 Precision

Precision measures the proportion of positive predictions that are
correct:

\[ `\text{Precision}`{=tex}=`\frac{TP}{TP+FP}`{=tex}. \]

In this experiment, the positive class is malignant (`1`).

### 6.3 Recall

Recall measures the proportion of actual positive examples that are
identified:

\[ `\text{Recall}`{=tex}=`\frac{TP}{TP+FN}`{=tex}. \]

For the benchmark's positive class, recall measures the share of
malignant-labelled test examples predicted as positive.

### 6.4 F1-score

The F1-score is the harmonic mean of precision and recall:

\[ F1=2`\cdot`{=tex}`\frac{\text{Precision}\cdot\text{Recall}}`{=tex}
{`\text{Precision}`{=tex}+`\text{Recall}`{=tex}}. \]

It combines the two metrics into one value, while still requiring the
reader to inspect precision and recall separately.

### 6.5 ROC-AUC

ROC-AUC summarizes the model's ability to rank positive examples above
negative examples across classification thresholds. It measures ranking
discrimination rather than performance at only one fixed threshold.

### 6.6 Privacy epsilon

For DP-FedAvg, epsilon is recorded per communication round at the
configured delta. It represents the accountant's cumulative privacy
bound under the experiment's adjacency definition and accounting
assumptions. It is not a model-accuracy metric.

## 7. Centralized Baseline Results

The centralized baseline produced the following recorded results:

  Metric                    Result
  ------------------- ------------
  Training loss             0.3759
  Training accuracy         91.38%
  Test accuracy         **94.69%**
  Precision                 95.00%
  Recall                    90.48%
  F1-score                  0.9268
  ROC-AUC                   0.9916

The run provides a strong initial reference for the chosen benchmark and
model architecture. It should not be treated as a clinical performance
claim or as evidence of generalization to other datasets or populations.

## 8. Standard FedAvg Results

The standard FedAvg experiment recorded these test metrics after each
communication round:

    Round     Accuracy     Precision   Recall     F1-score      ROC-AUC
  ------- ------------ ------------- -------- ------------ ------------
        1       83.19%        92.59%   59.52%       0.7246       0.9292
        2       81.42%       100.00%   50.00%       0.6667       0.9584
        3       81.42%       100.00%   50.00%       0.6667       0.9681
        4       82.30%       100.00%   52.38%       0.6875       0.9740
        5   **86.73%**   **100.00%**   64.29%   **0.7826**   **0.9789**

The final round has the highest recorded accuracy and F1-score in this
run. Precision is 100% at the reported final operating threshold, while
recall is 64.29%. This illustrates why accuracy or precision alone is
not sufficient to describe classifier behavior.

ROC-AUC rises over the five recorded rounds, indicating improved ranking
discrimination in this run. It does not imply that all
threshold-dependent metrics improve monotonically.

## 9. DP-FedAvg Results

The DP-FedAvg experiment recorded:

  ----------------------------------------------------------------------------------------
       Round     Accuracy   Precision       Recall     F1-score    ROC-AUC         Epsilon
  ---------- ------------ ----------- ------------ ------------ ---------- ---------------
           1       36.28%      14.29%       14.29%       0.1429     0.1813        5.378231

           2       60.18%      47.46%       66.67%       0.5545     0.6700        7.837642

           3       85.84%     100.00%       61.90%       0.7647     0.9574        9.837642

           4       73.45%      60.34%       83.33%       0.7000     0.7961       11.756463

           5   **82.30%**      68.97%   **95.24%**   **0.8000**     0.8806   **13.256463**
  ----------------------------------------------------------------------------------------

The final round has 82.30% accuracy, 68.97% precision, 95.24% recall, an
F1-score of 0.8000, and ROC-AUC of 0.8806.

The metrics vary between rounds. This is an observed property of this
particular run; it should not be interpreted as a universal pattern for
different privacy settings or datasets.

The epsilon value increases with the number of composed rounds. The
final reported value is 13.256463 at delta (10\^{-5}), under the current
client-level replace-one-client accounting assumptions.

## 10. Cross-Experiment Comparison

The final recorded results can be summarized as follows:

  Metric        Centralized baseline   Standard FedAvg    DP-FedAvg
  ----------- ---------------------- ----------------- ------------
  Accuracy                **94.69%**            86.73%       82.30%
  Precision                   95.00%       **100.00%**       68.97%
  Recall                      90.48%            64.29%   **95.24%**
  F1-score                **0.9268**            0.7826       0.8000
  ROC-AUC                 **0.9916**            0.9789       0.8806

### 10.1 Observations

-   The centralized run has the highest recorded accuracy and ROC-AUC
    among these three runs.
-   Standard FedAvg has the highest recorded precision, but its final
    recall is lower than the centralized and DP-FedAvg runs.
-   DP-FedAvg has the highest recorded recall and a slightly higher
    final F1-score than standard FedAvg in these particular runs.
-   DP-FedAvg's final ROC-AUC is lower than the values recorded for the
    other two runs.
-   These results are not sufficient to isolate the causal effect of
    differential privacy because the prototype has not yet performed a
    repeated, controlled multi-seed study.

### 10.2 Interpretation caution

The experiments are useful for demonstrating the implemented workflows
and recording an initial comparison. They do not yet constitute a
statistically controlled study. A single run per configuration cannot
quantify run-to-run variance or establish that one approach will
consistently outperform another.

## 11. Client-Level Training Metrics

The separate local-training experiment recorded the following client
metrics:

  Client         Samples   Local epochs   Training loss   Training accuracy
  ------------ --------- -------------- --------------- -------------------
  hospital-1         152              5          0.6477              81.45%
  hospital-2         152              5          0.6490              80.39%
  hospital-3         152              5          0.6535              79.34%

The mean recorded client training accuracy is approximately 80.39%.

These values describe the persisted local-training experiment. They
should not be confused with the global model's held-out test accuracy
after federated aggregation. The two measurements refer to different
stages and evaluation contexts.

## 12. Data Persistence and Experiment Traceability

The backend persists experiment metadata and metric records so the
frontend can retrieve historical results without rerunning model
training.

The API exposes read-only experiment information through endpoints
including:

-   `GET /api/v1/experiments`
-   `GET /api/v1/experiments/summary`
-   `GET /api/v1/experiments/{experiment_id}`
-   `GET /api/v1/experiments/{experiment_id}/metrics`

The experiment metrics response includes relevant centralized,
federated-round, privacy, and client-training records when available.

Persisting configurations and results supports traceability. For a
rigorous research report, each run should also be associated with its
code version, random seed, exact data partition, preprocessing
configuration, and environment details. Not all of those reproducibility
controls have been established as a complete experiment-tracking system
yet.

## 13. Threats to Validity and Current Limitations

### 13.1 Dataset scope

The evaluation uses one public benchmark dataset. Results do not
establish performance on other datasets, hospitals, populations, imaging
systems, or clinical workflows.

### 13.2 IID-only federated partitions

The recorded federated runs use IID client partitions with equal sample
counts. Real-world cross-silo data can be heterogeneous. Non-IID
experiments are not yet implemented.

### 13.3 Limited repetitions

The recorded comparison contains one run for each principal
configuration. There are no multi-seed confidence intervals or
statistical significance tests.

### 13.4 No privacy-budget sweep

Only one DP configuration is recorded for the current DP-FedAvg
experiment. The prototype has not yet measured a privacy-utility curve
across multiple clipping bounds or noise multipliers.

### 13.5 Central DP trust boundary

The coordinator receives individual client updates before noise is
added. Secure aggregation is disabled/not implemented, so the current
implementation does not protect those individual updates from the
coordinator.

### 13.6 Client-level privacy definition

The reported DP accounting uses replace-one-client adjacency. It is not
a patient-level differential-privacy guarantee.

### 13.7 Robustness and malicious clients

Malicious-client and robust-aggregation experiments are not implemented
in the current recorded results. No claim of Byzantine robustness should
be made.

### 13.8 Prototype-only scope

This project is a research prototype, not a production healthcare
platform. It does not use real patient records and must not be presented
as a clinically validated diagnostic system.

## 14. Recommended Follow-Up Evaluation Plan

The following work would strengthen the research evidence:

1.  **Repeat each experiment across multiple seeds.** Report mean,
    standard deviation, and suitable confidence intervals.
2.  **Control comparisons.** Keep data splits, model initialization
    policy, optimizer settings, and training budgets consistent where
    the comparison requires it.
3.  **Run a DP noise sweep.** Compare multiple noise multipliers and
    record both utility and epsilon.
4.  **Vary clipping bounds.** Examine how clipping affects update
    distortion and model performance.
5.  **Add non-IID partitions.** Test label-skew and other documented
    client-distribution scenarios.
6.  **Evaluate class-specific behavior.** Include confusion matrices,
    sensitivity, specificity, and threshold analysis.
7.  **Add calibration analysis.** Evaluate whether predicted
    probabilities are calibrated, rather than relying only on
    discrimination metrics.
8.  **Implement and evaluate secure aggregation.** Measure its
    communication and computation overhead separately from DP.
9.  **Test robustness mechanisms.** Define malicious-client scenarios
    and evaluate suitable robust aggregation methods.
10. **Improve reproducibility metadata.** Store seeds, code revision,
    preprocessing details, and partition identifiers with each
    experiment.

These are proposed next steps; they should not be represented as
completed features.

## 15. Conclusion

The current prototype demonstrates three experiment paths on the WDBC
public benchmark: centralized training, standard FedAvg across three
simulated clients, and central-DP FedAvg. It records classification
metrics, client training metrics, federated-round results, and per-round
privacy accounting.

The current runs show a centralized test accuracy of 94.69%, a final
standard FedAvg accuracy of 86.73%, and a final DP-FedAvg accuracy of
82.30%. The DP-FedAvg run reports epsilon 13.256463 at delta (10\^{-5})
after five rounds under a client-level replace-one-client definition.

These measurements are preliminary. The current evidence is limited to
one public dataset, IID partitions, one run per principal configuration,
and one DP setting. Secure aggregation, non-IID evaluation,
malicious-client robustness, and a systematic privacy-utility study
remain future work.
