# Document 06 --- Differential Privacy: Mathematical Foundations and Implementation

## 1. Purpose of This Document

This document explains the differential-privacy concepts used by the
Federated Healthcare Research prototype and connects the mathematics to
the implemented DP-FedAvg experiment.

The focus is the prototype's current configuration and measured run. It
does not claim that every privacy component proposed by the broader
research framework has been implemented. In particular, the current
experiment uses **central differential privacy** and does not enable
secure aggregation.

## 2. Differential Privacy in Federated Learning

Federated learning keeps each client's training examples local. Clients
train a model and send model updates to a coordinating server, which
combines those updates to produce a global model.

Federated learning alone does not guarantee privacy. A model update can
still reveal information about the data that influenced it. Differential
privacy (DP) provides a formal way to limit how much the released result
can depend on one protected unit.

For neighboring datasets (D) and (D'), a randomized mechanism (M) is
((`\varepsilon`{=tex},`\delta`{=tex}))-differentially private when, for
every measurable output set (S),

\[
`\Pr[M(D)\in S] `{=tex}`\leq `{=tex}e\^`\varepsilon`{=tex}`\Pr[M(D')\in S]`{=tex}+`\delta`{=tex}.
\]

The guarantee applies in both directions because the neighboring
relation is symmetric.

-   **Epsilon ((`\varepsilon`{=tex}))** controls the strength of the
    privacy guarantee. Smaller values generally provide stronger
    privacy, all else being equal.
-   **Delta ((`\delta`{=tex}))** is the approximate-DP slack parameter.
    It allows a small additive term in the privacy inequality; it is not
    a direct measurement of the probability that a particular record is
    exposed.

A privacy guarantee must always be interpreted together with its
neighboring-dataset definition, protected unit, mechanism, and
accounting assumptions.

## 3. Protected Unit: Client-Level, Not Patient-Level

The DP-FedAvg experiment is configured around **client-level replace-one
adjacency**.

Under this definition, two neighboring federated datasets differ in the
data contribution of one client: one client's contribution is replaced
by another admissible contribution, while the other clients remain
unchanged.

This is distinct from record-level (or patient-level) differential
privacy:

  -----------------------------------------------------------------------
  Privacy unit            What neighboring        What the guarantee
                          datasets differ in      protects
  ----------------------- ----------------------- -----------------------
  Record-level            One individual          The influence of one
                          example/record          record

  Client-level            One participating       The influence of one
                          client's contribution   client/institution
  -----------------------------------------------------------------------

The reported epsilon therefore must not be described as a patient-level
privacy guarantee. The current experiment does not establish that adding
or removing one patient has a bounded effect under a record-level
adjacency definition.

The three clients in this experiment are simulated institutions. They
are not live hospital connections.

## 4. The Implemented Central-DP Workflow

The current DP-FedAvg run follows this high-level sequence:

1.  The coordinator distributes the current global model to the
    participating clients.
2.  Each client trains locally using its own partition of the training
    data.
3.  Each client produces a model update.
4.  The coordinator receives the individual client updates.
5.  Client updates are clipped to a configured L2 norm bound.
6.  The coordinator forms the sample-weighted aggregate using the
    configured public client weights.
7.  Gaussian noise calibrated to the sensitivity is added to the
    aggregate.
8.  The resulting noisy aggregate is used to update the global model.
9.  The round is evaluated and the privacy accountant is advanced.

This is **central DP** because the noise is applied by the coordinating
server to the aggregate. It is not local DP: clients do not
independently randomize their updates before sending them.

### Important trust boundary

The coordinator sees individual client updates before the noise is
added. Consequently, this implementation does not hide each client's raw
model update from the coordinator.

Secure aggregation is disabled/not implemented in this experiment. The
current DP mechanism should not be described as secure aggregation or as
protection against an honest-but-curious coordinator inspecting
individual updates.

## 5. Update Clipping

### 5.1 Why clipping is necessary

Gaussian noise provides a formal privacy guarantee only when the
mechanism's sensitivity is bounded. If a client could submit an update
with an arbitrarily large norm, changing that client's contribution
could change the aggregate by an arbitrarily large amount.

Clipping limits the magnitude of each client update before aggregation.

For a client update vector (u_k), L2 clipping with bound (C) is:

\[ `\operatorname{clip}`{=tex}(u_k,C) =
u_k`\cdot `{=tex}`\min`{=tex}`\left`{=tex}(1,`\frac{C}{\lVert u_k\rVert_2}`{=tex}`\right`{=tex}).
\]

The clipped update satisfies:

\[ `\lVert `{=tex}`\operatorname{clip}`{=tex}(u_k,C)`\rVert`{=tex}\_2
`\leq `{=tex}C. \]

If the original update norm is already at most (C), it remains
unchanged. If it is larger, it is scaled down to the clipping bound.

### 5.2 Experiment setting

  Parameter                                           Value
  ------------------------- -------------------------------
  L2 clipping bound ((C))                               1.0
  Number of clients                                       3
  Samples per client                                    152
  Participation               Full participation each round

Clipping bounds update magnitude; it does not by itself provide
differential privacy. The privacy mechanism also requires calibrated
random noise and composition accounting.

## 6. Weighted FedAvg and Sensitivity

The experiment uses sample-weighted aggregation. For client (k), let
(n_k) be its sample count and let (N) be the total sample count. Its
aggregation weight is:

\[ p_k=`\frac{n_k}{N}`{=tex}. \]

The weighted aggregate of clipped client updates is:

\[ f(D)=`\sum`{=tex}\_{k=1}\^{K}p_k`\tilde{u}`{=tex}\_k, \]

where (`\tilde{u}`{=tex}\_k) is the clipped update and (K) is the number
of clients.

In the current experiment:

\[ n_1=n_2=n_3=152,`\qquad `{=tex}N=456, \]

so each fixed public weight is:

\[ p_k=`\frac{152}{456}`{=tex}=`\frac{1}{3}`{=tex}. \]

### 6.1 Replace-one-client sensitivity

Under replace-one-client adjacency, consider replacing client (j)'s
clipped update (`\tilde{u}`{=tex}\_j) with another admissible clipped
update (`\tilde{u}`{=tex}'\_j). All other client contributions and the
fixed public weights remain unchanged.

The aggregate difference is:

\[
```{=tex}
\begin{aligned}
\lVert f(D)-f(D')\rVert_2
&=p_j\lVert \tilde{u}_j-\tilde{u}'_j\rVert_2\\
&\leq p_j\left(\lVert\tilde{u}_j\rVert_2+
\lVert\tilde{u}'_j\rVert_2\right)\\
&\leq 2p_jC.
\end{aligned}
```
\]

Taking the maximum over the possible replaced client gives:

\[ `\Delta`{=tex}\_f `\leq `{=tex}2C`\max`{=tex}\_k p_k. \]

With (C=1.0) and (`\max `{=tex}p_k=1/3):

\[ `\Delta`{=tex}\_f
`\leq 2`{=tex}(1.0)`\left`{=tex}(`\frac{1}{3}`{=tex}`\right`{=tex})
=`\frac{2}{3}`{=tex}`\approx 0.6667`{=tex}. \]

The DP experiment records a sensitivity of **(2/3)**.

### 6.2 Assumptions behind this calculation

This sensitivity calculation relies on the experiment's stated setup:

-   Each client update is clipped to L2 norm at most (C=1.0).
-   The aggregation is a sample-weighted sum.
-   Client weights are fixed and public.
-   The neighboring relation replaces one client's contribution.
-   The client sample counts and weights are not treated as private
    values in this calculation.

If client weights, participation, or sample counts were private or
data-dependent under a different neighboring relation, the sensitivity
analysis would need to be revisited.

## 7. Gaussian Mechanism

The Gaussian mechanism adds a random Gaussian vector to a function's
output. For a function with L2 sensitivity (`\Delta`{=tex}\_f), a common
parameterization uses noise standard deviation:

\[ `\sigma`{=tex}=z`\Delta`{=tex}\_f, \]

where (z) is the noise multiplier.

The experiment configuration is:

  Parameter                                                                          Value
  --------------------------------------------------------------------------- ------------
  Noise multiplier ((z))                                                               1.0
  Recorded sensitivity ((`\Delta`{=tex}\_f))                                         (2/3)
  Implied Gaussian standard deviation ((`\sigma`{=tex}=z`\Delta`{=tex}\_f))          (2/3)
  Privacy delta ((`\delta`{=tex}))                                              (10\^{-5})

Thus, under this parameterization, the configured noise scale is:

\[
`\sigma=1.0`{=tex}`\times`{=tex}`\frac{2}{3}`{=tex}=`\frac{2}{3}`{=tex}.
\]

The noise is added to the aggregated update, not to each client's local
training data. The exact privacy guarantee also depends on the
accountant and the assumptions used to compose the per-round mechanism.

Increasing the noise multiplier generally strengthens privacy but can
make optimization less stable or reduce model utility. Decreasing it
generally reduces the amount of perturbation but weakens the privacy
guarantee.

## 8. Epsilon, Delta, and Composition Across Rounds

A federated training run releases information over multiple
communication rounds. The privacy cost therefore accumulates across
rounds; the final privacy guarantee cannot be inferred from the noise
multiplier alone.

The accountant tracks the privacy loss of the repeated Gaussian
mechanisms and converts that accumulated loss into an
((`\varepsilon`{=tex},`\delta`{=tex})) guarantee.

The prototype uses a Rényi Differential Privacy (RDP) accounting
approach. At a high level, RDP measures privacy loss at a collection of
Rényi orders (`\alpha`{=tex}), composes those losses across mechanisms,
and converts the result to approximate DP.

A commonly used conversion has the form:

\[ `\varepsilon`{=tex}(`\delta`{=tex}) =
`\min`{=tex}\_{`\alpha`{=tex}\>1} `\left[
D_\alpha+\frac{\log(1/\delta)}{\alpha-1}
\right]`{=tex}, \]

where (D\_`\alpha`{=tex}) represents the accumulated RDP bound at order
(`\alpha`{=tex}). The exact accounting implementation and its supported
order grid determine the reported numerical result.

### Accounting caveat

The prototype evaluates a finite grid of RDP orders. Its reported
epsilon is the minimum converted bound over that configured grid. It is
therefore a numerical upper bound produced by the implemented
accountant, not a claim that a continuous optimization over every
possible order was performed.

The experiment uses full participation and does not apply subsampling
amplification. It also uses fixed public client weights. These
assumptions are important when interpreting the reported epsilon.

## 9. Measured Privacy Budget Across the Five Rounds

The DP-FedAvg experiment uses:

-   Experiment ID: `b0de2782-d703-4148-b9ea-cef21f5cda45`
-   Clients: 3
-   Communication rounds: 5
-   Local epochs per client per round: 5
-   Clipping bound: 1.0
-   Noise multiplier: 1.0
-   Delta: (10\^{-5})
-   Secure aggregation: disabled/not implemented

The persisted privacy-accounting values are:

    Round         Epsilon        Delta
  ------- --------------- ------------
        1        5.378231   (10\^{-5})
        2        7.837642   (10\^{-5})
        3        9.837642   (10\^{-5})
        4       11.756463   (10\^{-5})
        5   **13.256463**   (10\^{-5})

The final reported privacy budget for this run is therefore:

\[ (`\varepsilon`{=tex},`\delta`{=tex})=(13.256463,10\^{-5}). \]

Epsilon increases as rounds are composed. The value is specific to this
configuration, accountant, adjacency definition, and run; it should not
be presented as a universal privacy value for the platform.

## 10. DP-FedAvg Utility Results

The model was evaluated after each global round. The recorded test
metrics are:

    Round   Accuracy   Precision   Recall   F1-score   ROC-AUC     Epsilon
  ------- ---------- ----------- -------- ---------- --------- -----------
        1     36.28%      14.29%   14.29%     0.1429    0.1813    5.378231
        2     60.18%      47.46%   66.67%     0.5545    0.6700    7.837642
        3     85.84%     100.00%   61.90%     0.7647    0.9574    9.837642
        4     73.45%      60.34%   83.33%     0.7000    0.7961   11.756463
        5     82.30%      68.97%   95.24%     0.8000    0.8806   13.256463

The final round reached 82.30% accuracy, 95.24% recall, 0.8000 F1-score,
and 0.8806 ROC-AUC in this run.

The round-to-round variation is visible in the measurements. The result
should not be reduced to a claim that adding DP always causes a fixed
amount of performance loss. Training is stochastic, and this prototype
has not yet run multiple random seeds or a systematic noise-multiplier
sweep.

## 11. Comparison With the Other Recorded Experiments

The current measured comparison is:

  Metric        Centralized baseline   Standard FedAvg   DP-FedAvg
  ----------- ---------------------- ----------------- -----------
  Accuracy                    94.69%            86.73%      82.30%
  Precision                   95.00%           100.00%      68.97%
  Recall                      90.48%            64.29%      95.24%
  F1-score                    0.9268            0.7826      0.8000
  ROC-AUC                     0.9916            0.9789      0.8806

These are results from the currently recorded runs, not a controlled
multi-seed statistical comparison. Differences can reflect training
configuration, stochasticity, and the injected noise. The table is
useful as an initial prototype comparison, but it is not sufficient to
establish a general privacy-utility curve or a statistically robust
conclusion.

## 12. What the Current DP Guarantee Does and Does Not Cover

### Covered by the current experiment's stated setup

-   A client-level replace-one-client adjacency definition.
-   Clipped client updates with an L2 bound of 1.0.
-   A central Gaussian mechanism applied to the weighted aggregate.
-   A reported RDP-based privacy accounting result at delta (10\^{-5}).
-   Composition across the five recorded communication rounds, under the
    accountant's configured assumptions.

### Not established by this experiment

-   Patient-level or individual-record-level differential privacy.
-   Hiding individual client updates from the coordinating server.
-   Secure aggregation or cryptographic protection of updates in transit
    or at the coordinator.
-   Protection against every malicious-client or inference attack.
-   Privacy amplification from client subsampling; the experiment uses
    full participation.
-   A general privacy-utility relationship across many noise multipliers
    and random seeds.
-   A guarantee for real hospital deployments or real patient data.

The WDBC dataset used here is a public benchmark. The experiment is a
research prototype and does not process real patient records.

## 13. Implementation Mapping

The privacy workflow is represented in the backend by the following
modules:

  -----------------------------------------------------------------------------------
  Module                                          Responsibility
  ----------------------------------------------- -----------------------------------
  `app/ml/privacy/update_clipper.py`              Applies the configured L2 clipping
                                                  bound to client updates

  `app/ml/privacy/gaussian_mechanism.py`          Implements Gaussian perturbation
                                                  for the aggregate

  `app/ml/privacy/privacy_accountant.py`          Tracks and converts privacy loss
                                                  across rounds

  `app/ml/federation/coordinator.py`              Coordinates federated rounds and
                                                  the aggregate update

  `app/ml/aggregation/fedavg.py`                  Performs weighted federated
                                                  aggregation

  `app/ml/training/run_dp_fedavg_experiment.py`   Runs the DP-FedAvg experiment and
                                                  persists its results
  -----------------------------------------------------------------------------------

The experiment records privacy metrics per round so that the dashboard
can display epsilon progression alongside model utility.

## 14. Recommended Next Research Experiments

The following are future experiments, not completed capabilities:

1.  **Noise-multiplier sweep:** run several values of (z) while keeping
    the data split and training configuration controlled.
2.  **Multiple random seeds:** repeat each configuration to estimate
    mean and variability for utility metrics.
3.  **Clipping-bound sensitivity study:** evaluate how different values
    of (C) affect update distortion, privacy accounting, and model
    quality.
4.  **Non-IID client partitions:** assess behavior when client data
    distributions differ.
5.  **Secure aggregation integration:** add a protocol that prevents the
    coordinator from inspecting individual client updates, then evaluate
    its communication and computation overhead.
6.  **Record-level DP study:** if patient-level protection is a research
    objective, define record-level adjacency and implement an
    appropriately calibrated mechanism and accountant.
7.  **Robust aggregation study:** separately evaluate malicious or
    anomalous client updates; robust aggregation is not part of the
    current DP experiment.

Each experiment should record its configuration, random seed, dataset
partition, metrics, and privacy assumptions so results can be reproduced
and compared.

## 15. Summary

The current prototype implements a central-DP extension to FedAvg. Each
client update is clipped to an L2 bound of 1.0, the coordinator forms a
fixed sample-weighted aggregate, and Gaussian noise is calibrated using
the recorded replace-one-client sensitivity of (2/3) with a noise
multiplier of 1.0. An RDP accountant reports a final epsilon of
13.256463 at delta (10\^{-5}) after five rounds.

This is a **client-level** privacy result under the experiment's
assumptions. It is not a patient-level guarantee, and it does not
prevent the coordinator from seeing individual updates before noise is
added. Secure aggregation remains outside the implemented scope. The
measured utility values are from one run and should be treated as
preliminary research observations rather than general conclusions.
