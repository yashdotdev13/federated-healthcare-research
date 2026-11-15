import { useQuery } from "@tanstack/react-query";
import {
  ShieldCheck,
  ShieldAlert,
  LockKeyhole,
  Fingerprint,
  Activity,
  Info,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getExperiments,
  getExperimentMetrics,
} from "../lib/api";
import "../App.css";

function formatNumber(value: number | null | undefined, digits = 4) {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

export default function PrivacySecurityPage() {
  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: getExperiments,
  });

  const dpExperiment = experimentsQuery.data?.find(
    (experiment) =>
      experiment.differential_privacy &&
      experiment.status === "completed",
  );

  const metricsQuery = useQuery({
    queryKey: ["experiment-metrics", dpExperiment?.id],
    queryFn: () => getExperimentMetrics(dpExperiment!.id),
    enabled: Boolean(dpExperiment?.id),
  });

  const privacyRecords = metricsQuery.data?.privacy_accounting ?? [];
  const latestPrivacy = privacyRecords[privacyRecords.length - 1];
  const experiment = metricsQuery.data?.experiment ?? dpExperiment;

  if (experimentsQuery.isLoading) {
    return (
      <div className="privacy-page">
        <div className="privacy-loading">Loading privacy and security data...</div>
      </div>
    );
  }

  if (experimentsQuery.isError) {
    return (
      <div className="privacy-page">
        <div className="privacy-empty">
          Unable to load experiments. Check that the backend is running.
        </div>
      </div>
    );
  }

  return (
    <div className="privacy-page">
      <div className="privacy-heading">
        <div>
          <div className="section-eyebrow">
            <span />
            PRIVACY GOVERNANCE
          </div>
          <h1>Privacy &amp; Security</h1>
          <p>
            Inspect differential privacy configuration, recorded privacy
            accounting, and the implementation status of security controls.
          </p>
        </div>
        <span className="privacy-environment-tag">
          <ShieldCheck size={14} />
          RESEARCH ENVIRONMENT
        </span>
      </div>

      {!dpExperiment ? (
        <div className="privacy-empty">
          <ShieldAlert size={28} />
          <h3>No completed DP experiment found</h3>
          <p>
            Run a differential privacy experiment to populate the privacy
            accounting dashboard.
          </p>
        </div>
      ) : metricsQuery.isLoading ? (
        <div className="privacy-loading">Loading privacy accounting records...</div>
      ) : metricsQuery.isError ? (
        <div className="privacy-empty">
          Unable to load the selected experiment's privacy metrics.
        </div>
      ) : (
        <>
          <div className="privacy-experiment-banner">
            <div>
              <span className="privacy-muted-label">ACTIVE DATA SOURCE</span>
              <h3>{experiment?.name ?? dpExperiment.name}</h3>
              <p>
                {experiment?.algorithm ?? dpExperiment.algorithm} ·{" "}
                {experiment?.client_count ?? dpExperiment.client_count} simulated
                clients · {privacyRecords.length} recorded rounds
              </p>
            </div>
            <span className="privacy-recorded-badge">
              <CheckCircle2 size={14} />
              EXPERIMENT COMPLETED
            </span>
          </div>

          <div className="privacy-kpi-grid">
            <div className="privacy-kpi-card">
              <div className="privacy-kpi-top">
                <span>Privacy Budget (ε)</span>
                <div className="privacy-icon purple">
                  <Fingerprint size={19} />
                </div>
              </div>
              <strong>{latestPrivacy ? formatNumber(latestPrivacy.epsilon, 2) : "—"}</strong>
              <small>Final recorded round</small>
            </div>

            <div className="privacy-kpi-card">
              <div className="privacy-kpi-top">
                <span>Delta (δ)</span>
                <div className="privacy-icon blue">
                  <ShieldCheck size={19} />
                </div>
              </div>
              <strong>
                {latestPrivacy ? latestPrivacy.delta.toExponential(0) : "—"}
              </strong>
              <small>Configured privacy parameter</small>
            </div>

            <div className="privacy-kpi-card">
              <div className="privacy-kpi-top">
                <span>Noise Multiplier</span>
                <div className="privacy-icon green">
                  <Activity size={19} />
                </div>
              </div>
              <strong>
                {latestPrivacy
                  ? formatNumber(latestPrivacy.noise_multiplier, 2)
                  : "—"}
              </strong>
              <small>Gaussian mechanism</small>
            </div>

            <div className="privacy-kpi-card">
              <div className="privacy-kpi-top">
                <span>Gradient Clip (C)</span>
                <div className="privacy-icon orange">
                  <LockKeyhole size={19} />
                </div>
              </div>
              <strong>
                {experiment?.dp_max_grad_norm != null
                  ? formatNumber(experiment.dp_max_grad_norm, 2)
                  : "—"}
              </strong>
              <small>Maximum update norm</small>
            </div>
          </div>

          <div className="privacy-content-grid">
            <section className="privacy-panel">
              <div className="privacy-panel-heading">
                <div>
                  <h3>Privacy Budget Progression</h3>
                  <p>Recorded epsilon across federated rounds</p>
                </div>
                <Fingerprint size={20} />
              </div>

              {privacyRecords.length > 0 ? (
                <div className="privacy-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={privacyRecords}
                      margin={{ top: 12, right: 16, left: 0, bottom: 4 }}
                    >
                      <CartesianGrid stroke="#26344a" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="round_number"
                        tick={{ fill: "#8ea2c2", fontSize: 12 }}
                        axisLine={{ stroke: "#34445d" }}
                        tickLine={false}
                        label={{
                          value: "Federated round",
                          position: "insideBottom",
                          offset: -2,
                          fill: "#8ea2c2",
                          fontSize: 11,
                        }}
                      />
                      <YAxis
                        tick={{ fill: "#8ea2c2", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#111c2e",
                          border: "1px solid #34445d",
                          borderRadius: 10,
                          color: "#e8ecf5",
                        }}
                        formatter={(value) => [
                          Number(value).toFixed(4),
                          "Epsilon",
                        ]}
                        labelFormatter={(label) => `Round ${label}`}
                      />
                      <Line
                        type="monotone"
                        dataKey="epsilon"
                        stroke="#9580ff"
                        strokeWidth={3}
                        dot={{ r: 4, fill: "#9580ff" }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="privacy-chart-empty">
                  No privacy accounting records are available.
                </div>
              )}
            </section>

            <section className="privacy-panel">
              <div className="privacy-panel-heading">
                <div>
                  <h3>Privacy Configuration</h3>
                  <p>Configuration recorded for this experiment</p>
                </div>
                <LockKeyhole size={20} />
              </div>

              <div className="privacy-config-list">
                <div>
                  <span>Algorithm</span>
                  <strong>{experiment?.algorithm ?? "—"}</strong>
                </div>
                <div>
                  <span>Noise multiplier</span>
                  <strong>{formatNumber(experiment?.dp_noise_multiplier, 2)}</strong>
                </div>
                <div>
                  <span>Maximum gradient norm</span>
                  <strong>{formatNumber(experiment?.dp_max_grad_norm, 2)}</strong>
                </div>
                <div>
                  <span>Accounting method</span>
                  <strong>{latestPrivacy?.accounting_method ?? "—"}</strong>
                </div>
                <div>
                  <span>Adjacency definition</span>
                  <strong>{latestPrivacy?.adjacency ?? "—"}</strong>
                </div>
                <div>
                  <span>Secure aggregation setting</span>
                  <strong>
                    {experiment?.secure_aggregation ? "Enabled" : "Disabled"}
                  </strong>
                </div>
              </div>
            </section>
          </div>

          <section className="privacy-panel privacy-table-panel">
            <div className="privacy-panel-heading">
              <div>
                <h3>Round-wise Privacy Accounting</h3>
                <p>Actual privacy metrics persisted by the experiment</p>
              </div>
              <span className="privacy-record-count">
                {privacyRecords.length} RECORDS
              </span>
            </div>

            <div className="privacy-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ROUND</th>
                    <th>EPSILON</th>
                    <th>DELTA</th>
                    <th>NOISE</th>
                    <th>SENSITIVITY</th>
                    <th>MAX UPDATE NORM</th>
                    <th>STEPS</th>
                  </tr>
                </thead>
                <tbody>
                  {privacyRecords.map((record) => (
                    <tr key={record.round_number}>
                      <td>Round {record.round_number}</td>
                      <td className="privacy-epsilon">
                        {formatNumber(record.epsilon)}
                      </td>
                      <td>{record.delta.toExponential(0)}</td>
                      <td>{formatNumber(record.noise_multiplier, 2)}</td>
                      <td>{formatNumber(record.sensitivity)}</td>
                      <td>{formatNumber(record.max_update_norm)}</td>
                      <td>{record.steps}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {privacyRecords.length === 0 && (
                <div className="privacy-chart-empty">
                  No round-wise privacy records found.
                </div>
              )}
            </div>
          </section>

          <section className="privacy-panel">
            <div className="privacy-panel-heading">
              <div>
                <h3>Security Controls</h3>
                <p>Implemented capabilities versus planned research extensions</p>
              </div>
              <ShieldCheck size={20} />
            </div>

            <div className="privacy-controls-grid">
              <div className="privacy-control-item implemented">
                <CheckCircle2 size={19} />
                <div>
                  <strong>Differential Privacy</strong>
                  <p>Gaussian noise mechanism and privacy accounting implemented.</p>
                </div>
                <span>IMPLEMENTED</span>
              </div>

              <div className="privacy-control-item implemented">
                <CheckCircle2 size={19} />
                <div>
                  <strong>Update Clipping</strong>
                  <p>Client updates are clipped using the configured norm bound.</p>
                </div>
                <span>IMPLEMENTED</span>
              </div>

              <div className="privacy-control-item planned">
                <XCircle size={19} />
                <div>
                  <strong>Secure Aggregation</strong>
                  <p>
                    Cryptographic aggregation protocol is not implemented in
                    this prototype.
                  </p>
                </div>
                <span>NOT IMPLEMENTED</span>
              </div>

              <div className="privacy-control-item planned">
                <XCircle size={19} />
                <div>
                  <strong>Robust Aggregation</strong>
                  <p>
                    Byzantine or malicious-client robust aggregation is not
                    implemented.
                  </p>
                </div>
                <span>NOT IMPLEMENTED</span>
              </div>
            </div>
          </section>

          <div className="privacy-research-note">
            <Info size={20} />
            <div>
              <strong>Research interpretation</strong>
              <p>
                The displayed epsilon and delta values describe the recorded
                DP-FedAvg experiment under its configured accounting
                assumptions. Differential privacy is applied centrally in
                this implementation; the coordinator receives individual
                client updates before noise is added. Secure aggregation is
                disabled and is not part of the current implementation.
                These results are from a research prototype using a public
                benchmark dataset, not a clinical system.
              </p>
            </div>
          </div>

          {latestPrivacy && (
            <div className="privacy-last-updated">
              Latest privacy record: {formatDate(latestPrivacy.created_at)}
            </div>
          )}
        </>
      )}
    </div>
  );
}


