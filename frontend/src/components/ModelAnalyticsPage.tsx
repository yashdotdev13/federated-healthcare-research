import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Award,
  ChartNoAxesCombined,
  LockKeyhole,
  TrendingUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getDashboardSummary,
  getExperiments,
  getExperimentMetrics,
} from "../lib/api";

import "../App.css";

function percent(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

function ModelAnalyticsPage() {
  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: getExperiments,
  });

  const experiments = experimentsQuery.data ?? [];
  const performance = summaryQuery.data?.performance ?? [];

  const dpExperiment = experiments.find(
    (item) => item.algorithm === "fedavg" && item.differential_privacy,
  );

  const dpMetricsQuery = useQuery({
    queryKey: ["experiment-metrics", dpExperiment?.id],
    queryFn: () => getExperimentMetrics(dpExperiment!.id),
    enabled: Boolean(dpExperiment?.id),
  });

  const rounds = dpMetricsQuery.data?.federated_rounds ?? [];
  const privacy = dpMetricsQuery.data?.privacy_accounting ?? [];
  const latestPrivacy = privacy.at(-1);
  const latestRound = rounds.at(-1);

  const comparisonData = performance.map((item) => ({
    model: item.algorithm === "centralized"
      ? "Centralized"
      : item.name.toLowerCase().includes("dp")
        ? "DP-FedAvg"
        : "FedAvg",
    accuracy: item.test_accuracy * 100,
    precision: item.precision * 100,
    recall: item.recall * 100,
    f1: item.f1_score * 100,
    rocAuc: item.roc_auc * 100,
  }));

  const convergenceData = rounds.map((round) => ({
    round: `Round ${round.round_number}`,
    accuracy: round.test_accuracy * 100,
    f1: round.f1_score * 100,
  }));

  const bestModel = [...performance].sort(
    (a, b) => b.test_accuracy - a.test_accuracy,
  )[0];

  const isLoading = summaryQuery.isLoading || experimentsQuery.isLoading;
  const hasError = summaryQuery.isError || experimentsQuery.isError;

  return (
    <div className="analytics-page">
      <div className="analytics-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            MODEL EVALUATION
          </div>
          <h1>Model Analytics</h1>
          <p>
            Evaluate model performance, compare learning strategies,
            and inspect federated training behavior.
          </p>
        </div>
        <span className="panel-tag">WDBC BENCHMARK</span>
      </div>

      {hasError && (
        <div className="panel analytics-message">
          Unable to load model evaluation data. Check the backend connection.
          <button className="text-button" onClick={() => void summaryQuery.refetch()}>
            Retry
          </button>
        </div>
      )}

      <section className="analytics-kpi-grid">
        <AnalyticsKpi
          icon={<Award size={20} />}
          label="Best Test Accuracy"
          value={isLoading ? "..." : percent(bestModel?.test_accuracy)}
          detail={bestModel?.name ?? "No evaluation available"}
          color="purple"
        />
        <AnalyticsKpi
          icon={<ChartNoAxesCombined size={20} />}
          label="Models Compared"
          value={isLoading ? "..." : String(performance.length)}
          detail="With persisted evaluation results"
          color="blue"
        />
        <AnalyticsKpi
          icon={<Activity size={20} />}
          label="DP-FedAvg Final Accuracy"
          value={latestRound ? percent(latestRound.test_accuracy) : "—"}
          detail={rounds.length ? `${rounds.length} communication rounds` : "No round data"}
          color="green"
        />
        <AnalyticsKpi
          icon={<LockKeyhole size={20} />}
          label="Final Privacy Budget"
          value={latestPrivacy ? latestPrivacy.epsilon.toFixed(2) : "—"}
          detail={latestPrivacy ? `δ = ${latestPrivacy.delta}` : "No privacy records"}
          color="orange"
        />
      </section>

      <section className="analytics-chart-grid">
        <div className="panel analytics-chart-panel">
          <div className="panel-header">
            <div>
              <h3>Model Performance Comparison</h3>
              <p>Accuracy, precision, recall and F1 score</p>
            </div>
            <TrendingUp size={20} />
          </div>
          <div className="analytics-chart">
            {summaryQuery.isLoading ? (
              <p>Loading comparison...</p>
            ) : comparisonData.length === 0 ? (
              <p>No evaluation results available.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263044" vertical={false} />
                  <XAxis dataKey="model" stroke="#78849a" tickLine={false} axisLine={false} fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="#78849a" tickLine={false} axisLine={false} fontSize={11} />
                  <Tooltip
                    contentStyle={{ background: "#171f30", border: "1px solid #303b50", borderRadius: 10 }}
                    formatter={(value) => [`${Number(value).toFixed(2)}%`]}
                  />
                  <Legend />
                  <Bar dataKey="accuracy" name="Accuracy" fill="#8b7cf6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="precision" name="Precision" fill="#35b9a3" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="recall" name="Recall" fill="#e6a653" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="f1" name="F1 Score" fill="#5e9eea" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="panel analytics-chart-panel">
          <div className="panel-header">
            <div>
              <h3>DP-FedAvg Convergence</h3>
              <p>Test accuracy and F1 across communication rounds</p>
            </div>
            <span className="live-tag">{rounds.length} ROUNDS</span>
          </div>
          <div className="analytics-chart">
            {dpMetricsQuery.isLoading ? (
              <p>Loading federated round metrics...</p>
            ) : convergenceData.length === 0 ? (
              <p>No federated round metrics available.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={convergenceData}>
                  <defs>
                    <linearGradient id="analyticsAccuracy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8b7cf6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#8b7cf6" stopOpacity={0.01} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263044" vertical={false} />
                  <XAxis dataKey="round" stroke="#78849a" tickLine={false} axisLine={false} fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="#78849a" tickLine={false} axisLine={false} fontSize={11} />
                  <Tooltip
                    contentStyle={{ background: "#171f30", border: "1px solid #303b50", borderRadius: 10 }}
                    formatter={(value) => [`${Number(value).toFixed(2)}%`]}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="accuracy"
                    name="Accuracy"
                    stroke="#9a8cff"
                    fill="url(#analyticsAccuracy)"
                    strokeWidth={2.5}
                  />
                  <Area
                    type="monotone"
                    dataKey="f1"
                    name="F1 Score"
                    stroke="#35b9a3"
                    fill="transparent"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </section>

      <section className="panel analytics-table-panel">
        <div className="panel-header">
          <div>
            <h3>Evaluation Metrics</h3>
            <p>Persisted test-set results for each evaluated experiment</p>
          </div>
          <span className="panel-tag">ACTUAL RESULTS</span>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>MODEL</th>
                <th>ACCURACY</th>
                <th>PRECISION</th>
                <th>RECALL</th>
                <th>F1 SCORE</th>
                <th>ROC-AUC</th>
              </tr>
            </thead>
            <tbody>
              {comparisonData.map((item) => (
                <tr key={item.model}>
                  <td><strong>{item.model}</strong></td>
                  <td className="accuracy-cell">{item.accuracy.toFixed(2)}%</td>
                  <td>{item.precision.toFixed(2)}%</td>
                  <td>{item.recall.toFixed(2)}%</td>
                  <td>{item.f1.toFixed(2)}%</td>
                  <td>{(item.rocAuc / 100).toFixed(4)}</td>
                </tr>
              ))}
              {!summaryQuery.isLoading && comparisonData.length === 0 && (
                <tr><td colSpan={6}>No evaluation data available.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="analytics-bottom-grid">
        <div className="panel analytics-insight-panel">
          <div className="panel-header">
            <div>
              <h3>Privacy–Utility Observation</h3>
              <p>DP-FedAvg experiment result</p>
            </div>
            <LockKeyhole size={20} />
          </div>
          <div className="privacy-utility-values">
            <div>
              <span>Final test accuracy</span>
              <strong>{latestRound ? percent(latestRound.test_accuracy) : "—"}</strong>
            </div>
            <div>
              <span>Final epsilon</span>
              <strong>{latestPrivacy?.epsilon.toFixed(4) ?? "—"}</strong>
            </div>
            <div>
              <span>Delta</span>
              <strong>{latestPrivacy?.delta ?? "—"}</strong>
            </div>
            <div>
              <span>Noise multiplier</span>
              <strong>{latestPrivacy?.noise_multiplier ?? "—"}</strong>
            </div>
          </div>
          <div className="analytics-note">
            These values describe one recorded DP-FedAvg run. They do not
            establish a general privacy–utility curve or a comparison across
            multiple privacy budgets.
          </div>
        </div>

        <div className="panel analytics-insight-panel">
          <div className="panel-header">
            <div>
              <h3>Evaluation Context</h3>
              <p>Research benchmark information</p>
            </div>
            <Activity size={20} />
          </div>
          <div className="analytics-context-list">
            <div><span>Dataset</span><strong>Wisconsin Diagnostic Breast Cancer</strong></div>
            <div><span>Evaluation</span><strong>Held-out test split</strong></div>
            <div><span>Federated clients</span><strong>{dpExperiment?.client_count ?? "—"} simulated clients</strong></div>
            <div><span>Partition strategy</span><strong>{dpExperiment?.partition_strategy.toUpperCase() ?? "—"}</strong></div>
          </div>
          <div className="analytics-note">
            Research prototype using a public benchmark dataset. Results are
            experimental and are not clinical performance claims.
          </div>
        </div>
      </section>
    </div>
  );
}

function AnalyticsKpi({
  icon,
  label,
  value,
  detail,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  detail: string;
  color: string;
}) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <div className={`metric-icon ${color}`}>{icon}</div>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-footer"><span>{detail}</span></div>
    </div>
  );
}

export default ModelAnalyticsPage;
