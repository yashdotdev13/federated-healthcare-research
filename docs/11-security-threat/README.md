# Document 11 --- Security, Threat Model and Privacy Limitations

## 1. Purpose and Scope

This document describes the security and privacy boundaries of the
Federated Healthcare Research prototype. It identifies the system
components, the assets and trust boundaries relevant to the current
implementation, the threats considered by the research design, and the
protections that are currently implemented versus those that remain
future work.

The project is a research prototype for implementing and evaluating
federated learning and privacy techniques. It is not a production
healthcare system, is not clinically validated, and must not be used to
make patient-care decisions.

This document distinguishes: - **Implemented behavior:** functionality
present in the current prototype. - **Research design considerations:**
threats and mitigations that motivate the architecture. - **Future
work:** protections that are not yet implemented or verified.

## 2. System Security Context

The prototype contains the following principal components:

-   A React/Vite frontend that displays experiment and metric
    information.
-   A FastAPI backend that exposes health and experiment-read APIs.
-   A PostgreSQL database that stores experiment metadata and metrics.
-   PyTorch training code that runs centralized and federated
    experiments.
-   Simulated clients that perform local training and return model
    updates.
-   A coordinator that aggregates client updates and advances federated
    rounds.
-   A central differential-privacy mechanism and privacy accountant used
    by the DP-FedAvg experiment.

The dataset used in the recorded experiments is the public Wisconsin
Diagnostic Breast Cancer (WDBC) benchmark. The three client identities
represent simulated institutions, not connected hospitals.

## 3. Assets to Protect

The relevant assets in this prototype include:

  -----------------------------------------------------------------------
  Asset                               Why it matters
  ----------------------------------- -----------------------------------
  Training data partitions            They are the local inputs used by
                                      simulated clients

  Client model updates                Updates can contain information
                                      influenced by local training data

  Global model parameters             They represent the result of the
                                      federated training process

  Experiment metadata                 It identifies the configuration and
                                      provenance of a run

  Evaluation metrics                  They describe the measured model
                                      behavior

  Privacy-accounting records          They document the claimed DP
                                      parameters and cumulative privacy
                                      bound

  Database credentials                They provide access to persisted
                                      experiment information

  Backend configuration and secrets   They can contain sensitive
                                      connection or runtime settings

  Source code and experiment          They determine the actual behavior
  configuration                       and reproducibility of the
                                      prototype
  -----------------------------------------------------------------------

No real patient records are intended to be stored or processed by this
project.

## 4. Trust Boundaries

### 4.1 Client-to-coordinator boundary

Each simulated client trains locally and sends a model update to the
coordinator. In the current central-DP workflow, the coordinator
receives individual client updates before clipping, aggregation, and
noise addition are completed.

This is a significant trust boundary. Central differential privacy does
not prevent the coordinator from inspecting the individual updates it
receives.

### 4.2 Coordinator and privacy mechanism boundary

The coordinator applies the update-clipping and Gaussian-noise workflow
used by DP-FedAvg. The privacy guarantee depends on the correctness of
this implementation, the sensitivity calculation, the
neighboring-dataset definition, and the accountant's assumptions.

The current prototype does not independently prove that the coordinator
is trusted or that its execution is tamper-resistant.

### 4.3 Backend-to-database boundary

The FastAPI backend connects to PostgreSQL through SQLAlchemy. Database
credentials and connection settings must remain outside committed source
code.

The frontend does not connect directly to PostgreSQL. It retrieves
experiment information through the backend API.

### 4.4 Browser-to-backend boundary

The React frontend calls the backend through the `/api/v1` API prefix.
In local development, Vite proxies `/api` requests to the FastAPI
server.

The local development proxy is not, by itself, a production security
architecture. Deployment must separately configure network exposure,
transport security, access control, and secret management.

## 5. Threat Model

The following table describes relevant threat scenarios and the current
implementation status.

  -----------------------------------------------------------------------
  Threat                  Potential impact        Current status
  ----------------------- ----------------------- -----------------------
  Curious coordinator     Updates may reveal      Not prevented by
  inspects individual     information about local current central DP
  client updates          training data           

  Inference from released An observer may infer   Central DP is intended
  model updates or        information about       to bound client-level
  outputs                 training contributions  influence on the noisy
                                                  aggregate, subject to
                                                  its assumptions

  Malicious or anomalous  Global model quality or Robust aggregation and
  client sends            training stability may  malicious-client
  manipulated updates     be degraded             experiments are not
                                                  implemented

  Network interception    Data in transit may be  Production
                          exposed or modified     transport-security
                                                  configuration is not
                                                  established by the
                                                  current prototype notes

  Unauthorized API access Experiment information  Authentication and
                          or operational          authorization behavior
                          endpoints may be        for the documented read
                          accessed                APIs is not established
                                                  here

  Database credential     An attacker may access  Credentials must be
  exposure                or modify persisted     kept out of source
                          experiment records      control; production
                                                  secret management is
                                                  future work

  Database compromise     Experiment records and  No database-hardening
                          configuration may be    or production backup
                          read or altered         design is established
                                                  here

  Frontend or API input   Service availability or Production security
  abuse                   data integrity may be   testing and
                          affected                rate-limiting coverage
                                                  are not established
                                                  here

  Incorrect privacy       Reported privacy        The implementation uses
  accounting              guarantees may be       an RDP accountant, but
                          invalid or overstated   its assumptions and
                                                  finite order grid must
                                                  be documented and
                                                  reviewed
  -----------------------------------------------------------------------

This is a research threat model, not evidence that the system has been
penetration-tested or independently security-audited.

## 6. Differential Privacy as a Protection

The DP-FedAvg experiment implements central differential privacy around
the weighted aggregate of clipped client updates.

The recorded configuration is:

  Parameter                               Value
  ------------------------ --------------------
  Privacy unit                     Client-level
  Neighboring relation       Replace-one-client
  L2 clipping bound                         1.0
  Noise multiplier                          1.0
  Recorded sensitivity                    (2/3)
  Delta                              (10\^{-5})
  Communication rounds                        5
  Final reported epsilon              13.256463

The experiment uses three equally weighted simulated clients, each with
152 training examples. The recorded sensitivity calculation is based on
clipped updates and fixed public sample weights:

\[ `\Delta`{=tex}\_f `\leq `{=tex}2C`\max`{=tex}\_k p_k
=2(1.0)`\left`{=tex}(`\frac{1}{3}`{=tex}`\right`{=tex})
=`\frac{2}{3}`{=tex}. \]

The Gaussian mechanism adds noise to the weighted aggregate. The privacy
accountant composes the per-round privacy loss and reports epsilon at
the configured delta.

### 6.1 What this guarantee means

The reported guarantee is client-level under the replace-one-client
adjacency definition and the assumptions used by the implemented
accountant.

It is not a patient-level or individual-record-level guarantee. The
privacy unit is a simulated client contribution, not one patient record.

### 6.2 Accounting assumptions

The recorded experiment uses: - Full client participation in each
round. - Fixed public client weights. - No subsampling amplification. -
A finite configured grid of RDP orders. - Five composed communication
rounds.

The reported epsilon is the accountant's converted bound over its
configured order grid. It should not be presented as an exact
continuous-order optimum.

## 7. Central DP Does Not Equal Secure Aggregation

Differential privacy and secure aggregation address different risks.

-   **Central differential privacy** adds calibrated random noise to a
    result so that the released aggregate has a bounded dependence on a
    protected unit, under a defined adjacency relation.
-   **Secure aggregation** is intended to prevent the coordinator from
    learning individual client updates while still allowing it to obtain
    an aggregate.

The current DP-FedAvg experiment implements central DP. Secure
aggregation is disabled/not implemented.

Therefore: - The coordinator can see individual updates before noise is
added. - The DP mechanism does not cryptographically conceal those
updates from the coordinator. - The project must not claim that secure
aggregation is complete. - The combined DP-plus-secure-aggregation
architecture remains future work.

## 8. Malicious Clients and Robustness

A client may be malicious, compromised, misconfigured, or simply produce
an anomalous update. Such an update could attempt to disrupt training,
bias the global model, or introduce a backdoor.

Clipping limits the L2 magnitude of an update. It does not establish
that the update is honest, correctly trained, or free from adversarial
behavior.

The current recorded experiments do not implement or validate robust
aggregation against malicious clients. No Byzantine-fault-tolerance or
poisoning-resistance claim should be made.

Potential future work includes: - Defining explicit malicious-client
threat scenarios. - Simulating model-update poisoning and anomalous
updates. - Evaluating robust aggregation methods. - Measuring
clean-model utility and attack success separately. - Studying the
interaction between robust aggregation and DP.

These are proposed research directions, not completed features.

## 9. Network and Transport Security

The development setup uses a local Vite proxy and a FastAPI backend. The
available implementation notes do not establish a production TLS
deployment, certificate-management workflow, mutual TLS, or a hardened
client-to-coordinator transport protocol.

Before any deployment outside a controlled research environment, the
system would need a reviewed transport-security design. Depending on the
deployment, this may include: - HTTPS for browser-to-backend traffic. -
Authenticated and encrypted client-to-coordinator communication. -
Certificate and key lifecycle management. - Network segmentation and
restricted service exposure. - Secure handling of connection
credentials.

These controls are not claimed as implemented merely because the system
can run locally.

## 10. API and Application Security

The documented experiment and health endpoints are read-only. The
current project notes do not establish a verified authentication or
authorization contract for these endpoints.

Before exposing the API beyond a local research environment, evaluate: -
Authentication for users and services. - Authorization for experiment
and administrative operations. - Input validation and consistent error
handling. - Rate limiting and abuse controls. - CORS and reverse-proxy
configuration. - Dependency vulnerability management. - Security logging
that avoids exposing secrets or sensitive payloads.

Do not assume that a local development API is safe to expose publicly.

## 11. Database and Secret Management

The backend uses PostgreSQL through SQLAlchemy. Local connection
settings must be configured outside committed source code.

Recommended operational practices include: - Keep passwords, API keys,
and connection strings out of Git. - Use environment variables or a
dedicated secret manager. - Apply least-privilege database roles. -
Restrict database network access. - Back up experiment metadata and
migration files. - Protect database backups and local development
dumps. - Avoid storing real patient data in the prototype.

The project notes do not establish a production secret manager,
backup/restore procedure, database encryption policy, or database audit
configuration. These should be treated as future deployment
requirements.

## 12. Privacy Limitations and Interpretation Rules

The following distinctions are essential when describing the current
prototype:

  -----------------------------------------------------------------------
  Topic                               Accurate statement
  ----------------------------------- -----------------------------------
  Privacy unit                        Client-level replace-one-client
                                      adjacency

  Patient-level DP                    Not implemented or established

  DP mechanism                        Central Gaussian noise on the
                                      weighted aggregate

  Coordinator visibility              Individual client updates are
                                      visible to the coordinator before
                                      noise addition

  Secure aggregation                  Disabled/not implemented

  Client participation                Full participation; no subsampling
                                      amplification

  Client weights                      Fixed public sample weights in the
                                      recorded experiment

  Privacy accounting                  RDP-based accounting over a finite
                                      order grid

  Dataset                             Public WDBC benchmark

  Real hospitals                      Not connected; clients are
                                      simulated

  Real patient data                   Not used

  Privacy-utility study               One recorded DP configuration; no
                                      systematic sweep or multi-seed
                                      study
  -----------------------------------------------------------------------

The final DP-FedAvg run reports epsilon 13.256463 at delta (10\^{-5})
after five rounds. This value is meaningful only with the stated privacy
unit, adjacency relation, clipping, noise, participation, weighting, and
accounting assumptions.

## 13. Security Testing Status

The backend test suite had 62 passing tests at the documented project
stage. Those tests support the correctness of the covered application
behavior.

They do not establish: - A completed penetration test. - A formal
security audit. - Resistance to all model-inference attacks. - Secure
aggregation correctness. - Malicious-client robustness. -
Production-grade authentication and authorization. - Production-grade
network or database hardening.

Security assurance requires dedicated tests and reviews aligned with the
actual threat model.

## 14. Recommended Security and Privacy Roadmap

The following work is recommended before considering a broader
deployment or making stronger research claims.

### Priority 1 --- Clarify and validate the privacy implementation

1.  Review clipping and Gaussian-noise code against the documented
    sensitivity derivation.
2.  Add tests for clipping norms and noise-scale configuration.
3.  Verify accountant inputs, composition behavior, and finite-order
    conversion.
4.  Persist the privacy assumptions and configuration with every DP
    experiment.
5.  Clearly label client-level privacy in the API and frontend.

### Priority 2 --- Improve the coordinator trust boundary

1.  Design and implement secure aggregation.
2.  Verify that the coordinator cannot inspect individual client updates
    under the selected protocol.
3.  Test protocol failure cases and client dropout behavior.
4.  Measure communication and computation overhead.

### Priority 3 --- Evaluate malicious-client behavior

1.  Define reproducible poisoning and anomalous-update scenarios.
2.  Add robust aggregation methods as separate experimental
    configurations.
3.  Compare clean utility, attack success, and robustness across runs.
4.  Study interactions with DP rather than assuming clipping alone
    provides robustness.

### Priority 4 --- Harden application and infrastructure

1.  Define authentication and authorization requirements.
2.  Add TLS and secure service-to-service communication.
3.  Add secret management and least-privilege database access.
4.  Add security-focused API and dependency tests.
5.  Establish logging, backup, recovery, and incident-response
    procedures.

### Priority 5 --- Strengthen experimental evidence

1.  Repeat experiments across multiple random seeds.
2.  Evaluate multiple noise multipliers and clipping bounds.
3.  Add non-IID client partitions.
4.  Document dataset provenance and preprocessing.
5.  Report uncertainty and limitations alongside performance metrics.

## 15. Safe Research Claims

### Claims supported by the current prototype

-   The prototype runs centralized training and federated experiments on
    a public benchmark.
-   It simulates three clients with local training partitions.
-   It implements standard FedAvg.
-   It implements a central-DP FedAvg experiment with update clipping
    and Gaussian noise.
-   It records an RDP-based client-level privacy-accounting result under
    stated assumptions.
-   It persists experiment and metric records for dashboard inspection.

### Claims that should not be made

-   The system guarantees patient-level differential privacy.
-   The coordinator cannot see individual client updates.
-   Secure aggregation is implemented.
-   The system is resistant to malicious or Byzantine clients.
-   The platform is production-ready for hospitals.
-   The model is clinically validated or suitable for diagnosis.
-   The recorded metrics generalize to real hospital populations.
-   A single DP run establishes a general privacy-utility trade-off.

## 16. Conclusion

The current prototype demonstrates a research workflow for centralized
learning, standard FedAvg, and central-DP FedAvg using a public dataset
and simulated clients. Its privacy mechanism clips client updates, adds
Gaussian noise to the weighted aggregate, and tracks a client-level
privacy budget using an RDP accountant.

The implementation has important boundaries. The coordinator sees
individual client updates before noise is added; secure aggregation is
not implemented; patient-level DP is not established; and
malicious-client robustness is not validated. Network, API, database,
and deployment hardening also require separate implementation and
verification.

These boundaries should remain explicit in project documentation,
demonstrations, research reports, and any future presentation of
results.
