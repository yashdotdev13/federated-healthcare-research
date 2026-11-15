import numpy as np
import pytest
import torch

from app.ml.clients.hospital_client import HospitalClient
from app.ml.federation.coordinator import FederatedCoordinator
from app.ml.models.diagnostic_model import DiagnosticMLP


def create_clients():
    rng = np.random.default_rng(42)

    clients = []

    for index in range(3):
        features = rng.normal(
            size=(40, 30)
        ).astype(np.float32)

        labels = rng.integers(
            0, 2, size=40
        ).astype(np.int64)

        clients.append(
            HospitalClient(
                client_id=f"hospital-{index + 1}",
                x_train=features,
                y_train=labels,
            )
        )

    return clients


def test_coordinator_requires_clients():
    model = DiagnosticMLP()

    with pytest.raises(ValueError):
        FederatedCoordinator(model, [])


def test_coordinator_rejects_invalid_round():
    model = DiagnosticMLP()
    coordinator = FederatedCoordinator(
        model,
        create_clients(),
    )

    with pytest.raises(ValueError):
        coordinator.run_round(round_number=0)


def test_coordinator_executes_federated_round():
    torch.manual_seed(42)

    model = DiagnosticMLP()
    clients = create_clients()

    coordinator = FederatedCoordinator(
        global_model=model,
        clients=clients,
    )

    initial_state = {
        name: tensor.clone()
        for name, tensor in model.state_dict().items()
    }

    result = coordinator.run_round(
        round_number=1,
        local_epochs=2,
        batch_size=16,
        learning_rate=0.01,
        random_seed=42,
    )

    assert result.round_number == 1
    assert result.client_count == 3
    assert result.total_samples == 120

    assert 0 <= result.average_training_accuracy <= 1
    assert result.average_training_loss >= 0

    assert any(
        not torch.equal(initial_state[name], updated_tensor)
        for name, updated_tensor in model.state_dict().items()
    )


def test_coordinator_executes_multiple_rounds():
    torch.manual_seed(42)

    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    first_result = coordinator.run_round(
        round_number=1,
        local_epochs=2,
    )

    second_result = coordinator.run_round(
        round_number=2,
        local_epochs=2,
    )

    assert first_result.round_number == 1
    assert second_result.round_number == 2

    assert first_result.total_samples == 120
    assert second_result.total_samples == 120

def test_coordinator_executes_private_federated_round():
    torch.manual_seed(42)

    model = DiagnosticMLP()
    coordinator = FederatedCoordinator(
        global_model=model,
        clients=create_clients(),
    )

    initial_state = {
        name: tensor.clone()
        for name, tensor in model.state_dict().items()
    }

    result = coordinator.run_round(
        round_number=1,
        local_epochs=2,
        batch_size=16,
        learning_rate=0.01,
        random_seed=42,
        differential_privacy=True,
        max_update_norm=1.0,
        noise_multiplier=1.0,
        public_sample_counts=[40, 40, 40],
    )

    assert result.round_number == 1
    assert result.client_count == 3
    assert result.total_samples == 120
    assert result.noise_std == pytest.approx(2.0 / 3.0)
    assert result.max_client_update_norm is None
    assert result.max_client_update_norm is None
    assert result.clipped_client_count is None

    assert any(
        not torch.equal(initial_state[name], updated_tensor)
        for name, updated_tensor in model.state_dict().items()
    )


def test_private_round_rejects_zero_noise_multiplier():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    with pytest.raises(ValueError):
        coordinator.run_round(
            round_number=1,
            differential_privacy=True,
            noise_multiplier=0.0,
        )


def test_non_private_round_preserves_existing_behavior():
    torch.manual_seed(42)

    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    result = coordinator.run_round(
        round_number=1,
        local_epochs=2,
    )

    assert result.noise_std is None
    assert result.clipped_client_count == 0
    assert result.max_client_update_norm is None

def test_private_round_does_not_expose_raw_training_metrics():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    result = coordinator.run_round(
        round_number=1,
        differential_privacy=True,
        public_sample_counts=[40, 40, 40],
    )

    assert result.average_training_loss is None
    assert result.average_training_accuracy is None
    assert result.clipped_client_count is None
    assert result.max_client_update_norm is None


def test_private_round_requires_public_sample_counts():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    with pytest.raises(ValueError, match="Public sample counts are required"):
        coordinator.run_round(
            round_number=1,
            differential_privacy=True,
        )


def test_private_round_rejects_mismatched_public_sample_counts():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    with pytest.raises(ValueError, match="public sample count"):
        coordinator.run_round(
            round_number=1,
            differential_privacy=True,
            public_sample_counts=[40, 40, 50],
        )

def test_private_round_does_not_expose_raw_training_metrics():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    result = coordinator.run_round(
        round_number=1,
        differential_privacy=True,
        public_sample_counts=[40, 40, 40],
    )

    assert result.average_training_loss is None
    assert result.average_training_accuracy is None
    assert result.clipped_client_count is None
    assert result.max_client_update_norm is None


def test_private_round_requires_public_sample_counts():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    with pytest.raises(ValueError, match="Public sample counts are required"):
        coordinator.run_round(
            round_number=1,
            differential_privacy=True,
        )


def test_private_round_rejects_mismatched_public_sample_counts():
    coordinator = FederatedCoordinator(
        global_model=DiagnosticMLP(),
        clients=create_clients(),
    )

    with pytest.raises(ValueError, match="public sample count"):
        coordinator.run_round(
            round_number=1,
            differential_privacy=True,
            public_sample_counts=[40, 40, 50],
        )


