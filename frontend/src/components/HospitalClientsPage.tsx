import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Database,
  Users,
  ChartNoAxesCombined,
  Building2,
  CheckCircle2,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
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

function percentage(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function HospitalClientsPage() {
  const experimentsQuery = useQuery({
    queryKey: ["experiments"],
    queryFn: getExperiments,
  });

  const experiments = experimentsQuery.data ?? [];

  const localExperiment = experiments.find(
    (item) => item.algorithm === "local_training",
  );

  const metricsQuery = useQuery({
    queryKey: ["experiment-metrics", localExperiment?.id],
    queryFn: () => getExperimentMetrics(localExperiment!.id),
    enabled: Boolean(localExperiment?.id),
  });

  const clients = metricsQuery.data?.client_training_metrics ?? [];

  const totalSamples = clients.reduce(
    (total, client) => total + client.sample_count,
    0,
  );

  const averageAccuracy = clients.length
    ? clients.reduce((total, client) => total + client.training_accuracy, 0) /
      clients.length
    : null;

  const chartData = clients.map((client) => ({
    hospital: client.client_id,
    accuracy: client.training_accuracy * 100,
  }));

  const isLoading = experimentsQuery.isLoading || metricsQuery.isLoading;
  const hasError = experimentsQuery.isError || metricsQuery.isError;

  return (
    <div className="hospital-page">
      <section className="hospital-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            FEDERATED CLIENT NETWORK
          </div>
          <h1>Hospital Clients</h1>
          <p>
            Monitor simulated healthcare institutions, local dataset
            partitions, and recorded client training performance.
          </p>
        </div>
        <span className="panel-tag">SIMULATED ENVIRONMENT</span>
      </section>

      {hasError && (
        <div className="panel hospital-message">
          Unable to retrieve client records.
          <button className="text-button" onClick={() => void metricsQuery.refetch()}>
            Retry
          </button>
        </div>
      )}

      <section className="hospital-kpi-grid">
        <HospitalKpi
          icon={<Building2 size={20} />}
          label="Recorded Clients"
          value={isLoading ? "..." : String(clients.length)}
          detail="Simulated institutions"
          color="purple"
        />
        <HospitalKpi
          icon={<Database size={20} />}
          label="Total Local Samples"
          value={isLoading ? "..." : totalSamples.toLocaleString()}
          detail="Across recorded client partitions"
          color="blue"
        />
        <HospitalKpi
          icon={<ChartNoAxesCombined size={20} />}
          label="Average Training Accuracy"
          value={averageAccuracy == null ? "—" : percentage(averageAccuracy)}
          detail="Initial local training experiment"
          color="green"
        />
        <HospitalKpi
          icon={<Activity size={20} />}
          label="Local Training Epochs"
          value={
            clients.length
              ? String(Math.min(...clients.map((client) => client.epochs_completed)))
              : "—"
          }
          detail="Recorded per client"
          color="orange"
        />
      </section>

      <section className="hospital-main-grid">
        <div className="panel hospital-network-panel">
          <div className="panel-header">
            <div>
              <h3>Simulated Hospital Network</h3>
              <p>Institutions represented in the local training experiment</p>
            </div>
            <span className="live-tag">{clients.length} CLIENTS</span>
          </div>

          {isLoading ? (
            <div className="hospital-empty">Loading client records...</div>
          ) : clients.length === 0 ? (
            <div className="hospital-empty">
              No client training records found for the local training experiment.
            </div>
          ) : (
            <div className="hospital-client-grid">
              {clients.map((client) => (
                <div className="hospital-client-card" key={client.client_id}>
                  <div className="hospital-client-top">
                    <div className="hospital-client-icon">
                      <Building2 size={22} />
                    </div>
                    <span className="recorded-indicator">
                      <CheckCircle2 size={14} />
                      Recorded
                    </span>
                  </div>

                  <h3>{client.client_id}</h3>
                  <p>Simulated healthcare institution</p>

                  <div className="hospital-client-stat">
                    <span>Local samples</span>
                    <strong>{client.sample_count}</strong>
                  </div>
                  <div className="hospital-client-stat">
                    <span>Training accuracy</span>
                    <strong>{percentage(client.training_accuracy)}</strong>
                  </div>
                  <div className="hospital-client-stat">
                    <span>Training loss</span>
                    <strong>{client.training_loss.toFixed(4)}</strong>
                  </div>
                  <div className="hospital-client-stat">
                    <span>Partition</span>
                    <strong>{client.partition_strategy.toUpperCase()}</strong>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="panel hospital-chart-panel">
          <div className="panel-header">
            <div>
              <h3>Client Training Accuracy</h3>
              <p>Initial local training results</p>
            </div>
            <ChartNoAxesCombined size={20} />
          </div>

          <div className="hospital-chart">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#263044" horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    stroke="#78849a"
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                  />
                  <YAxis
                    type="category"
                    dataKey="hospital"
                    stroke="#78849a"
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                    width={90}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#171f30",
                      border: "1px solid #303b50",
                      borderRadius: 10,
                    }}
                    formatter={(value) => [
                      `${Number(value).toFixed(2)}%`,
                      "Training accuracy",
                    ]}
                  />
                  <Bar
                    dataKey="accuracy"
                    name="Training accuracy"
                    fill="#8b7cf6"
                    radius={[0, 5, 5, 0]}
                    barSize={25}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="hospital-empty">No client accuracy data available.</div>
            )}
          </div>
        </div>
      </section>

      <section className="panel hospital-table-panel">
        <div className="panel-header">
          <div>
            <h3>Client Training Records</h3>
            <p>Actual metrics persisted by the local training experiment</p>
          </div>
          <span className="panel-tag">DATABASE RECORDS</span>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>CLIENT ID</th>
                <th>PARTITION</th>
                <th>SAMPLES</th>
                <th>TRAINING LOSS</th>
                <th>TRAINING ACCURACY</th>
                <th>EPOCHS</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client) => (
                <tr key={client.client_id}>
                  <td>
                    <div className="experiment-name">
                      <div className="experiment-symbol">
                        <Users size={15} />
                      </div>
                      <strong>{client.client_id}</strong>
                    </div>
                  </td>
                  <td>{client.partition_strategy.toUpperCase()}</td>
                  <td>{client.sample_count}</td>
                  <td>{client.training_loss.toFixed(4)}</td>
                  <td className="accuracy-cell">
                    {percentage(client.training_accuracy)}
                  </td>
                  <td>{client.epochs_completed}</td>
                </tr>
              ))}
              {!isLoading && clients.length === 0 && (
                <tr>
                  <td colSpan={6}>No client records available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="hospital-research-note">
        <Database size={18} />
        <div>
          <strong>Research data provenance</strong>
          <p>
            These records belong to the Initial Hospital Local Training
            experiment. Each simulated client has an IID partition of the
            public WDBC benchmark. Recorded clients do not represent live
            hospital connections.
          </p>
        </div>
      </div>
    </div>
  );
}

function HospitalKpi({
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
      <div className="metric-footer">
        <span>{detail}</span>
      </div>
    </div>
  );
}

export default HospitalClientsPage;
