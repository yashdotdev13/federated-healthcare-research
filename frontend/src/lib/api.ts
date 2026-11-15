import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

export interface Experiment {
  id: string
  name: string
  description: string | null
  algorithm: string
  dataset_name: string
  partition_strategy: string
  client_count: number
  num_rounds: number
  local_epochs: number
  learning_rate: number
  differential_privacy: boolean
  dp_noise_multiplier: number | null
  dp_max_grad_norm: number | null
  secure_aggregation: boolean
  status: string
  created_at: string
}

export interface ExperimentPerformance {
  experiment_id: string
  name: string
  algorithm: string
  test_accuracy: number
  precision: number
  recall: number
  f1_score: number
  roc_auc: number
}

export interface DashboardSummary {
  total_experiments: number
  completed_experiments: number
  participating_clients: number
  best_accuracy: number | null
  latest_epsilon: number | null
  latest_delta: number | null
  performance: ExperimentPerformance[]
}

export interface FederatedRound {
  round_number: number
  client_count: number
  total_samples: number
  training_loss: number | null
  training_accuracy: number | null
  test_accuracy: number
  precision: number
  recall: number
  f1_score: number
  sensitivity: number
  specificity: number
  roc_auc: number
  created_at: string
}

export interface PrivacyMetric {
  round_number: number
  epsilon: number
  delta: number
  noise_multiplier: number
  steps: number
  optimal_order: number | null
  max_update_norm: number
  max_client_weight: number
  sensitivity: number
  accounting_method: string
  adjacency: string
  created_at: string
}

export interface ExperimentMetrics {
  experiment: Experiment
  centralized: {
    sample_count: number
    training_loss: number
    training_accuracy: number
    test_accuracy: number
    precision: number
    recall: number
    f1_score: number
    sensitivity: number
    specificity: number
    roc_auc: number
    created_at: string
  } | null
  federated_rounds: FederatedRound[]
  privacy_accounting: PrivacyMetric[]
  client_training_metrics: {
    client_id: string
    partition_strategy: string
    sample_count: number
    training_loss: number
    training_accuracy: number
    epochs_completed: number
    created_at: string
  }[]
}

export const getDashboardSummary = async () => {
  const response = await api.get<DashboardSummary>('/experiments/summary')
  return response.data
}

export const getExperiments = async () => {
  const response = await api.get<Experiment[]>('/experiments')
  return response.data
}

export const getExperimentMetrics = async (id: string) => {
  const response = await api.get<ExperimentMetrics>(`/experiments/${id}/metrics`)
  return response.data
}

export const getHealth = async () => {
  const response = await api.get<{ status: string; service: string }>('/health')
  return response.data
}
