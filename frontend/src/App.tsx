import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BrainCircuit,
  ChartNoAxesCombined,
  ChevronDown,
  CircleHelp,
  FlaskConical,
  LayoutDashboard,
  LockKeyhole,
  Microscope,
  Search,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import ExperimentsPage from "./components/ExperimentsPage";
import ModelAnalyticsPage from "./components/ModelAnalyticsPage";
import HospitalClientsPage from "./components/HospitalClientsPage";
import PrivacySecurityPage from "./components/PrivacySecurityPage";
import {
  getDashboardSummary,
  getExperiments,
  getExperimentMetrics,
  getHealth,
} from "./lib/api";

import "./App.css";

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Experiments", icon: FlaskConical },
  { label: "Model Analytics", icon: ChartNoAxesCombined },
  { label: "Hospital Clients", icon: Users },
  { label: "Privacy & Security", icon: ShieldCheck },
];

function formatPercent(value: number | null | undefined) {
  return value == null ? "—" : `${(value * 100).toFixed(2)}%`;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function App() {
  const [selectedPage, setSelectedPage] = useState("Overview");
  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: getExperiments,
  });

  const healthQuery = useQuery({
    queryKey: ["api-health"],
    queryFn: getHealth,
    refetchInterval: 30000,
  });

  const dpExperiment = experimentsQuery.data?.find(
    (experiment) =>
      experiment.differential_privacy &&
      experiment.algorithm === "fedavg",
  );

  const dpMetricsQuery = useQuery({
    queryKey: ["experiment-metrics", dpExperiment?.id],
    queryFn: () => getExperimentMetrics(dpExperiment!.id),
    enabled: Boolean(dpExperiment?.id),
  });

  const summary = summaryQuery.data;
  const experiments = experimentsQuery.data ?? [];
  const performanceData =
    summary?.performance.map((item) => ({
      model:
        item.algorithm === "centralized"
          ? "Centralized"
          : item.name.toLowerCase().includes("dp")
            ? "DP-FedAvg"
            : "FedAvg",
      accuracy: item.test_accuracy * 100,
      f1: item.f1_score * 100,
    })) ?? [];

  const trainingData =
    dpMetricsQuery.data?.federated_rounds.map((round) => ({
      round: `Round ${round.round_number}`,
      accuracy: round.test_accuracy * 100,
    })) ?? [];

  const privacyMetrics =
    dpMetricsQuery.data?.privacy_accounting ?? [];

  const latestPrivacy = privacyMetrics.at(-1);
  const finalRound = dpMetricsQuery.data?.federated_rounds.at(-1);

  const isDashboardLoading =
    summaryQuery.isLoading || experimentsQuery.isLoading;

  const hasDashboardError =
    summaryQuery.isError || experimentsQuery.isError;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <BrainCircuit size={25} />
          </div>
          <div>
            <h2>FedHealth</h2>
            <span>RESEARCH PLATFORM</span>
          </div>
        </div>

        <div className="workspace">
          <div className="workspace-icon">FH</div>
          <div className="workspace-info">
            <strong>Research Workspace</strong>
            <span>Healthcare AI Lab</span>
          </div>
          <ChevronDown size={15} />
        </div>

        <div className="nav-section">
          <span className="nav-heading">WORKSPACE</span>
          {navigation.map((item, index) => {
            const Icon = item.icon;

            return (
              <a
                href="#"
                key={item.label}
                className={`nav-link ${selectedPage === item.label ? "active" : ""}`}
                onClick={(event) => {
                  event.preventDefault();
                  if (item.label === "Overview" || item.label === "Experiments" || item.label === "Model Analytics" || item.label === "Hospital Clients" || item.label === "Privacy & Security") {
                    setSelectedPage(item.label);
                  } else {
                    alert(`${item.label} page is coming in the next milestone.`);
                  }
                }}
              >
                <Icon size={19} />
                <span>{item.label}</span>
                {index === 1 && (
                  <span className="nav-count">{experiments.length}</span>
                )}
              </a>
            );
          })}
        </div>

        <div className="nav-section tools-section">
          <span className="nav-heading">PREFERENCES</span>
          <a href="#" className="nav-link" onClick={(e) => e.preventDefault()}>
            <Settings size={19} />
            <span>Settings</span>
          </a>
          <a href="#" className="nav-link" onClick={(e) => e.preventDefault()}>
            <CircleHelp size={19} />
            <span>Documentation</span>
          </a>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span
              className="status-dot"
              style={{
                background: healthQuery.isSuccess ? "#35b9a3" : "#e5a34c",
              }}
            />
            <div>
              <strong>Research system</strong>
              <span>
                {healthQuery.isLoading
                  ? "Checking API..."
                  : healthQuery.isSuccess
                    ? "Backend operational"
                    : "Backend unavailable"}
              </span>
            </div>
          </div>
          <div className="user-profile">
            <div className="avatar">RA</div>
            <div className="user-info">
              <strong>Research Admin</strong>
              <span>Administrator</span>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-divider">/</span>
            <strong>{selectedPage}</strong>
          </div>

          <div className="topbar-actions">
            <div className="search-box">
              <Search size={17} />
              <input placeholder="Search experiments..." />
              <kbd>Ctrl K</kbd>
            </div>
            <button className="icon-button" aria-label="Notifications">
              <Bell size={19} />
              <span className="notification-dot" />
            </button>
            <div className="top-avatar">RA</div>
          </div>
        </header>

        <div className="dashboard-content">
          {selectedPage === "Experiments" ? <ExperimentsPage /> : selectedPage === "Model Analytics" ? <ModelAnalyticsPage /> : selectedPage === "Hospital Clients" ? <HospitalClientsPage /> : selectedPage === "Privacy & Security" ? <PrivacySecurityPage /> : (<>
          <section className="welcome-section">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" />
                RESEARCH OVERVIEW
              </div>
              <h1>Research Dashboard</h1>
              <p>
                Monitor federated learning experiments, model performance,
                and privacy metrics.
              </p>
            </div>

            <button
              className="primary-button"
              onClick={() =>
                alert("Experiment creation will be implemented in the next milestone.")
              }
            >
              <FlaskConical size={17} />
              New Experiment
            </button>
          </section>

          {hasDashboardError && (
            <div className="panel" style={{ padding: 18, marginBottom: 20 }}>
              Unable to load dashboard data. Check that the FastAPI server and
              PostgreSQL are running, then refresh the page.
              <button
                className="text-button"
                onClick={() => {
                  void summaryQuery.refetch();
                  void experimentsQuery.refetch();
                }}
              >
                Retry
              </button>
            </div>
          )}

          <section className="metrics-grid">
            <div className="metric-card">
              <div className="metric-top">
                <span>Total Experiments</span>
                <div className="metric-icon purple">
                  <FlaskConical size={19} />
                </div>
              </div>
              <div className="metric-value">
                {isDashboardLoading
                  ? "..."
                  : String(summary?.total_experiments ?? 0).padStart(2, "0")}
              </div>
              <div className="metric-footer">
                <span className="positive">
                  <ArrowUpRight size={15} />
                  {summary?.completed_experiments ?? 0} completed
                </span>
                <span>Research runs</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-top">
                <span>Best Model Accuracy</span>
                <div className="metric-icon blue">
                  <ChartNoAxesCombined size={19} />
                </div>
              </div>
              <div className="metric-value">
                {isDashboardLoading
                  ? "..."
                  : summary?.best_accuracy == null
                    ? "—"
                    : `${(summary.best_accuracy * 100).toFixed(2)}`}
                {summary?.best_accuracy != null && <span>%</span>}
              </div>
              <div className="metric-footer">
                <span className="positive">
                  <ArrowUpRight size={15} /> Best recorded
                </span>
                <span>Test accuracy</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-top">
                <span>Participating Hospitals</span>
                <div className="metric-icon green">
                  <Users size={19} />
                </div>
              </div>
              <div className="metric-value">
                {isDashboardLoading
                  ? "..."
                  : String(summary?.participating_clients ?? 0).padStart(2, "0")}
              </div>
              <div className="metric-footer">
                <span className="positive">
                  <Activity size={15} /> Simulated
                </span>
                <span>Configured federated clients</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-top">
                <span>Privacy Budget (ε)</span>
                <div className="metric-icon orange">
                  <LockKeyhole size={19} />
                </div>
              </div>
              <div className="metric-value">
                {summary?.latest_epsilon?.toFixed(2) ?? "—"}
              </div>
              <div className="metric-footer">
                <span className="neutral">
                  δ = {summary?.latest_delta ?? "—"}
                </span>
                <span>DP-FedAvg</span>
              </div>
            </div>
          </section>

          <section className="charts-grid">
            <div className="panel performance-panel">
              <div className="panel-header">
                <div>
                  <h3>Model Performance Comparison</h3>
                  <p>Test accuracy and F1 score across algorithms</p>
                </div>
                <span className="panel-tag">WDBC DATASET</span>
              </div>

              <div className="chart-legend">
                <span><i className="legend-dot accuracy-dot" /> Accuracy</span>
                <span><i className="legend-dot f1-dot" /> F1 Score</span>
              </div>

              <div className="chart-container">
                {summaryQuery.isLoading ? (
                  <p>Loading model performance...</p>
                ) : performanceData.length === 0 ? (
                  <p>No evaluation metrics available yet.</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={performanceData} barGap={8}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#263044" vertical={false} />
                      <XAxis dataKey="model" stroke="#78849a" tickLine={false} axisLine={false} fontSize={12} />
                      <YAxis domain={[0, 100]} stroke="#78849a" tickLine={false} axisLine={false} fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: "#171f30", border: "1px solid #303b50", borderRadius: 10 }}
                        formatter={(value) => [`${Number(value).toFixed(2)}%`]}
                      />
                      <Bar dataKey="accuracy" name="Accuracy" fill="#8b7cf6" radius={[5, 5, 0, 0]} />
                      <Bar dataKey="f1" name="F1 Score" fill="#35b9a3" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="panel training-panel">
              <div className="panel-header">
                <div>
                  <h3>DP-FedAvg Training Progress</h3>
                  <p>Test accuracy across communication rounds</p>
                </div>
                <span className="live-tag">
                  {trainingData.length} ROUNDS
                </span>
              </div>

              <div className="training-summary">
                <div>
                  <strong>
                    {finalRound
                      ? formatPercent(finalRound.test_accuracy)
                      : "—"}
                  </strong>
                  <span>Final accuracy</span>
                </div>
                <div className="summary-change">
                  <ArrowDownRight size={16} />
                  <span>Round-to-round variation</span>
                </div>
              </div>

              <div className="chart-container">
                {dpMetricsQuery.isLoading ? (
                  <p>Loading federated rounds...</p>
                ) : trainingData.length === 0 ? (
                  <p>No federated round metrics available.</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trainingData}>
                      <defs>
                        <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8b7cf6" stopOpacity={0.32} />
                          <stop offset="100%" stopColor="#8b7cf6" stopOpacity={0.01} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#263044" vertical={false} />
                      <XAxis dataKey="round" stroke="#78849a" tickLine={false} axisLine={false} fontSize={11} />
                      <YAxis domain={[0, 100]} stroke="#78849a" tickLine={false} axisLine={false} fontSize={12} />
                      <Tooltip
                        contentStyle={{ background: "#171f30", border: "1px solid #303b50", borderRadius: 10 }}
                        formatter={(value) => [`${Number(value).toFixed(2)}%`, "Accuracy"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="accuracy"
                        stroke="#9a8cff"
                        strokeWidth={2.5}
                        fill="url(#accuracyGradient)"
                        dot={{ fill: "#9a8cff", strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
              {dpMetricsQuery.isError && (
                <p>Unable to load DP-FedAvg round metrics.</p>
              )}
            </div>
          </section>

          <section className="bottom-grid">
            <div className="panel experiments-panel">
              <div className="panel-header">
                <div>
                  <h3>Recent Experiments</h3>
                  <p>Latest research runs from the database</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => void experimentsQuery.refetch()}
                >
                  Refresh
                </button>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>EXPERIMENT</th>
                      <th>ALGORITHM</th>
                      <th>ACCURACY</th>
                      <th>STATUS</th>
                      <th>DATE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {experiments.map((experiment) => {
                      const performance = summary?.performance.find(
                        (item) => item.experiment_id === experiment.id,
                      );

                      return (
                        <tr key={experiment.id}>
                          <td>
                            <div className="experiment-name">
                              <div className="experiment-symbol">
                                <Microscope size={16} />
                              </div>
                              <strong>{experiment.name}</strong>
                            </div>
                          </td>
                          <td>
                            <span className="algorithm-label">
                              {experiment.differential_privacy
                                ? "DP-FedAvg"
                                : experiment.algorithm === "centralized"
                                  ? "Centralized"
                                  : experiment.algorithm === "fedavg"
                                    ? "FedAvg"
                                    : experiment.algorithm}
                            </span>
                          </td>
                          <td className="accuracy-cell">
                            {formatPercent(performance?.test_accuracy)}
                          </td>
                          <td>
                            <span className="completed-status">
                              <i />
                              {experiment.status}
                            </span>
                          </td>
                          <td className="date-cell">
                            {formatDate(experiment.created_at)}
                          </td>
                        </tr>
                      );
                    })}
                    {!experimentsQuery.isLoading && experiments.length === 0 && (
                      <tr>
                        <td colSpan={5}>No experiments found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {experimentsQuery.isError && (
                <p>Unable to load experiment records.</p>
              )}
            </div>

            <div className="panel privacy-panel">
              <div className="panel-header">
                <div>
                  <h3>Privacy Configuration</h3>
                  <p>DP-FedAvg experiment settings</p>
                </div>
                <ShieldCheck size={21} className="privacy-shield" />
              </div>

              <div className="privacy-item">
                <span>Noise Multiplier</span>
                <strong>
                  {latestPrivacy?.noise_multiplier ?? "—"}
                </strong>
              </div>
              <div className="privacy-item">
                <span>Max Update Norm</span>
                <strong>
                  {latestPrivacy?.max_update_norm ?? "—"}
                </strong>
              </div>
              <div className="privacy-item">
                <span>Delta (δ)</span>
                <strong>{latestPrivacy?.delta ?? "—"}</strong>
              </div>
              <div className="privacy-item">
                <span>Adjacency</span>
                <strong>
                  {latestPrivacy?.adjacency ?? "—"}
                </strong>
              </div>

              <div className="privacy-note">
                <LockKeyhole size={17} />
                <span>
                  {dpExperiment
                    ? `Differential privacy enabled. Secure aggregation ${
                        dpExperiment.secure_aggregation ? "enabled" : "not enabled"
                      }.`
                    : "No completed DP-FedAvg privacy configuration found."}
                </span>
              </div>
            </div>
          </section>

          <footer className="dashboard-footer">
            <span>FedHealth Research Platform · Research Prototype</span>
            <span>
              <i
                className="status-dot"
                style={{
                  background: healthQuery.isSuccess ? "#35b9a3" : "#e5a34c",
                }}
              />
              {healthQuery.isSuccess
                ? "Connected to FastAPI"
                : healthQuery.isLoading
                  ? "Checking FastAPI..."
                  : "FastAPI unavailable"}
            </span>
          </footer>
          </>)}
        </div>
      </main>
    </div>
  );
}

export default App;





