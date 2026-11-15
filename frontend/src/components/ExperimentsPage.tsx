import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowLeft,
  CalendarDays,
  ChevronRight,
  FlaskConical,
  LockKeyhole,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  getExperiments,
  getExperimentMetrics,
  type Experiment,
} from "../lib/api";

import "../App.css";

function percentage(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

function ExperimentsPage() {
  const [search, setSearch] = useState("");
  const [algorithm, setAlgorithm] = useState("all");
  const [status, setStatus] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: getExperiments,
  });

  const experiments = experimentsQuery.data ?? [];

  const filteredExperiments = experiments.filter((experiment) => {
    const matchesSearch =
      experiment.name.toLowerCase().includes(search.toLowerCase()) ||
      experiment.dataset_name.toLowerCase().includes(search.toLowerCase());

    const matchesAlgorithm =
      algorithm === "all" ||
      (algorithm === "dp-fedavg"
        ? experiment.algorithm === "fedavg" && experiment.differential_privacy
        : experiment.algorithm === algorithm && !experiment.differential_privacy);

    const matchesStatus =
      status === "all" || experiment.status === status;

    return matchesSearch && matchesAlgorithm && matchesStatus;
  });

  const selectedExperiment = experiments.find(
    (experiment) => experiment.id === selectedId,
  );

  const metricsQuery = useQuery({
    queryKey: ["experiment-metrics", selectedId],
    queryFn: () => getExperimentMetrics(selectedId!),
    enabled: Boolean(selectedId),
  });

  const metrics = metricsQuery.data;

  return (
    <div className="experiments-page">
      <div className="experiments-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            RESEARCH WORKSPACE
          </div>
          <h1>{selectedExperiment ? "Experiment Details" : "Experiments"}</h1>
          <p>
            {selectedExperiment
              ? "Inspect experiment configuration, evaluation results, and privacy metrics."
              : "Explore and compare your persisted federated learning research runs."}
          </p>
        </div>

        {selectedExperiment && (
          <button
            className="experiment-back-button"
            onClick={() => setSelectedId(null)}
          >
            <ArrowLeft size={16} />
            All Experiments
          </button>
        )}
      </div>

      {!selectedExperiment && (
        <>
          <div className="experiment-overview-cards">
            <div className="experiment-overview-card">
              <FlaskConical size={20} />
              <div>
                <strong>{experiments.length}</strong>
                <span>Total experiments</span>
              </div>
            </div>
            <div className="experiment-overview-card">
              <ShieldCheck size={20} />
              <div>
                <strong>
                  {experiments.filter((item) => item.differential_privacy).length}
                </strong>
                <span>DP experiments</span>
              </div>
            </div>
            <div className="experiment-overview-card">
              <Users size={20} />
              <div>
                <strong>
                  {experiments.reduce(
                    (maximum, item) => Math.max(maximum, item.client_count),
                    0,
                  )}
                </strong>
                <span>Maximum configured clients</span>
              </div>
            </div>
          </div>

          <div className="panel experiment-list-panel">
            <div className="experiment-toolbar">
              <div className="experiment-search">
                <Search size={17} />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search experiments or datasets..."
                />
              </div>

              <select
                value={algorithm}
                onChange={(event) => setAlgorithm(event.target.value)}
                aria-label="Filter by algorithm"
              >
                <option value="all">All algorithms</option>
                <option value="centralized">Centralized</option>
                <option value="fedavg">FedAvg</option>
                <option value="dp-fedavg">DP-FedAvg</option>
                <option value="local_training">Local Training</option>
              </select>

              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                aria-label="Filter by status"
              >
                <option value="all">All statuses</option>
                <option value="completed">Completed</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="created">Created</option>
              </select>
            </div>

            {experimentsQuery.isLoading && (
              <div className="experiment-empty-state">
                Loading experiments from the database...
              </div>
            )}

            {experimentsQuery.isError && (
              <div className="experiment-empty-state">
                Unable to load experiments.
                <button
                  className="text-button"
                  onClick={() => void experimentsQuery.refetch()}
                >
                  Retry
                </button>
              </div>
            )}

            {!experimentsQuery.isLoading &&
              !experimentsQuery.isError &&
              filteredExperiments.length === 0 && (
                <div className="experiment-empty-state">
                  No experiments match your filters.
                </div>
              )}

            <div className="experiment-list">
              {filteredExperiments.map((experiment) => (
                <ExperimentCard
                  key={experiment.id}
                  experiment={experiment}
                  onSelect={() => setSelectedId(experiment.id)}
                />
              ))}
            </div>

            <div className="experiment-list-footer">
              Showing {filteredExperiments.length} of {experiments.length} experiments
            </div>
          </div>
        </>
      )}

      {selectedExperiment && (
        <div className="experiment-detail">
          <div className="experiment-detail-header panel">
            <div>
              <span className="algorithm-label">
                {selectedExperiment.differential_privacy
                  ? "DP-FedAvg"
                  : selectedExperiment.algorithm}
              </span>
              <h2>{selectedExperiment.name}</h2>
              <p>{selectedExperiment.description || "No description provided."}</p>
            </div>
            <span className="completed-status">
              <i />
              {selectedExperiment.status}
            </span>
          </div>

          <div className="experiment-config-grid">
            <ConfigItem label="Dataset" value={selectedExperiment.dataset_name} />
            <ConfigItem label="Partition strategy" value={selectedExperiment.partition_strategy.toUpperCase()} />
            <ConfigItem label="Configured clients" value={String(selectedExperiment.client_count)} />
            <ConfigItem label="Communication rounds" value={String(selectedExperiment.num_rounds)} />
            <ConfigItem label="Local epochs" value={String(selectedExperiment.local_epochs)} />
            <ConfigItem label="Learning rate" value={String(selectedExperiment.learning_rate)} />
            <ConfigItem label="Differential privacy" value={selectedExperiment.differential_privacy ? "Enabled" : "Disabled"} />
            <ConfigItem label="Secure aggregation" value={selectedExperiment.secure_aggregation ? "Enabled" : "Disabled"} />
          </div>

          {metricsQuery.isLoading && (
            <div className="panel experiment-empty-state">
              Loading evaluation and privacy metrics...
            </div>
          )}

          {metricsQuery.isError && (
            <div className="panel experiment-empty-state">
              Unable to load experiment metrics.
              <button className="text-button" onClick={() => void metricsQuery.refetch()}>
                Retry
              </button>
            </div>
          )}

          {metrics && (
            <>
              {metrics.centralized && (
                <div className="experiment-section">
                  <h3>Evaluation Results</h3>
                  <div className="experiment-result-grid">
                    <ResultItem label="Test accuracy" value={percentage(metrics.centralized.test_accuracy)} />
                    <ResultItem label="Precision" value={percentage(metrics.centralized.precision)} />
                    <ResultItem label="Recall" value={percentage(metrics.centralized.recall)} />
                    <ResultItem label="F1 score" value={percentage(metrics.centralized.f1_score)} />
                    <ResultItem label="ROC-AUC" value={metrics.centralized.roc_auc.toFixed(4)} />
                    <ResultItem label="Training loss" value={metrics.centralized.training_loss.toFixed(4)} />
                  </div>
                </div>
              )}

              {metrics.federated_rounds.length > 0 && (
                <div className="panel experiment-data-panel">
                  <div className="panel-header">
                    <div>
                      <h3>Federated Round Metrics</h3>
                      <p>Evaluation results recorded after each communication round</p>
                    </div>
                    <Activity size={20} />
                  </div>
                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>ROUND</th>
                          <th>CLIENTS</th>
                          <th>ACCURACY</th>
                          <th>PRECISION</th>
                          <th>RECALL</th>
                          <th>F1 SCORE</th>
                          <th>ROC-AUC</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.federated_rounds.map((round) => (
                          <tr key={round.round_number}>
                            <td>Round {round.round_number}</td>
                            <td>{round.client_count}</td>
                            <td className="accuracy-cell">{percentage(round.test_accuracy)}</td>
                            <td>{percentage(round.precision)}</td>
                            <td>{percentage(round.recall)}</td>
                            <td>{percentage(round.f1_score)}</td>
                            <td>{round.roc_auc.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {metrics.privacy_accounting.length > 0 && (
                <div className="panel experiment-data-panel">
                  <div className="panel-header">
                    <div>
                      <h3>Privacy Accounting</h3>
                      <p>Recorded differential privacy budget per round</p>
                    </div>
                    <LockKeyhole size={20} />
                  </div>
                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>ROUND</th>
                          <th>EPSILON</th>
                          <th>DELTA</th>
                          <th>NOISE</th>
                          <th>SENSITIVITY</th>
                          <th>STEPS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.privacy_accounting.map((item) => (
                          <tr key={item.round_number}>
                            <td>Round {item.round_number}</td>
                            <td className="accuracy-cell">{item.epsilon.toFixed(4)}</td>
                            <td>{item.delta}</td>
                            <td>{item.noise_multiplier}</td>
                            <td>{item.sensitivity.toFixed(4)}</td>
                            <td>{item.steps}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="privacy-note">
                    <LockKeyhole size={17} />
                    <span>
                      Privacy accounting reflects the recorded experiment configuration.
                      Secure aggregation is not implemented in this experiment.
                    </span>
                  </div>
                </div>
              )}

              {metrics.client_training_metrics.length > 0 && (
                <div className="panel experiment-data-panel">
                  <div className="panel-header">
                    <div>
                      <h3>Client Training Metrics</h3>
                      <p>Locally recorded simulated client training results</p>
                    </div>
                    <Users size={20} />
                  </div>
                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>CLIENT</th>
                          <th>PARTITION</th>
                          <th>SAMPLES</th>
                          <th>TRAINING LOSS</th>
                          <th>ACCURACY</th>
                          <th>EPOCHS</th>
                        </tr>
                      </thead>
                      <tbody>
                        {metrics.client_training_metrics.map((item) => (
                          <tr key={`${item.client_id}-${item.created_at}`}>
                            <td>{item.client_id}</td>
                            <td>{item.partition_strategy}</td>
                            <td>{item.sample_count}</td>
                            <td>{item.training_loss.toFixed(4)}</td>
                            <td>{percentage(item.training_accuracy)}</td>
                            <td>{item.epochs_completed}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!metrics.centralized &&
                metrics.federated_rounds.length === 0 &&
                metrics.client_training_metrics.length === 0 && (
                  <div className="panel experiment-empty-state">
                    No evaluation metrics have been recorded for this experiment yet.
                  </div>
                )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function ExperimentCard({
  experiment,
  onSelect,
}: {
  experiment: Experiment;
  onSelect: () => void;
}) {
  const algorithm = experiment.differential_privacy
    ? "DP-FedAvg"
    : experiment.algorithm === "local_training"
      ? "Local Training"
      : experiment.algorithm === "centralized"
        ? "Centralized"
        : "FedAvg";

  return (
    <button className="experiment-card" onClick={onSelect}>
      <div className="experiment-card-icon">
        <FlaskConical size={20} />
      </div>
      <div className="experiment-card-main">
        <div className="experiment-card-title">
          <strong>{experiment.name}</strong>
          <span className="algorithm-label">{algorithm}</span>
        </div>
        <p>{experiment.description || experiment.dataset_name}</p>
        <div className="experiment-card-meta">
          <span><Users size={14} /> {experiment.client_count} clients</span>
          <span><Activity size={14} /> {experiment.num_rounds} rounds</span>
          <span><CalendarDays size={14} /> {new Date(experiment.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      <div className="experiment-card-right">
        <span className={`experiment-status status-${experiment.status}`}>
          {experiment.status}
        </span>
        <ChevronRight size={19} />
      </div>
    </button>
  );
}

function ConfigItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="experiment-config-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ResultItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="experiment-result-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default ExperimentsPage;
