from collections.abc import Sequence
from dataclasses import dataclass
import math

import torch

from app.ml.aggregation.fedavg import FedAvgAggregator
from app.ml.clients.hospital_client import HospitalClient
from app.ml.models.diagnostic_model import DiagnosticMLP
from app.ml.privacy.update_clipper import clip_client_update
from app.ml.privacy.gaussian_mechanism import (
    add_gaussian_noise,
    calculate_gaussian_noise_std,
)


@dataclass(frozen=True)
class FederatedRoundResult:
    round_number: int
    client_count: int
    total_samples: int
    average_training_loss: float | None
    average_training_accuracy: float | None
    clipped_client_count: int | None = None
    max_client_update_norm: float | None = None
    noise_std: float | None = None


class FederatedCoordinator:
    """
    Coordinates multi-round Federated Averaging across hospital clients.

    Supports optional client-level central differential privacy using
    clipped client updates and Gaussian noise on the aggregate update.

    In DP mode, aggregation weights must be explicitly supplied as
    public, fixed sample counts independent of private training data.
    """

    def __init__(
        self,
        global_model: DiagnosticMLP,
        clients: list[HospitalClient],
    ) -> None:
        if not clients:
            raise ValueError("At least one hospital client is required")

        self.global_model = global_model
        self.clients = clients
        self.aggregator = FedAvgAggregator()

    def run_round(
        self,
        round_number: int,
        local_epochs: int = 5,
        batch_size: int = 32,
        learning_rate: float = 0.01,
        random_seed: int = 42,
        differential_privacy: bool = False,
        max_update_norm: float = 1.0,
        noise_multiplier: float = 1.0,
        public_sample_counts: Sequence[int] | None = None,
    ) -> FederatedRoundResult:
        """Execute one complete federated communication round."""

        if isinstance(round_number, bool) or not isinstance(round_number, int):
            raise ValueError("Round number must be a positive integer")

        if round_number < 1:
            raise ValueError("Round number must be positive")

        if differential_privacy:
            if (
                not math.isfinite(max_update_norm)
                or max_update_norm <= 0
            ):
                raise ValueError(
                    "Maximum update norm must be positive and finite"
                )

            if (
                not math.isfinite(noise_multiplier)
                or noise_multiplier <= 0
            ):
                raise ValueError(
                    "Noise multiplier must be positive and finite when DP is enabled"
                )

            if public_sample_counts is None:
                raise ValueError(
                    "Public sample counts are required when DP is enabled"
                )

            if len(public_sample_counts) != len(self.clients):
                raise ValueError(
                    "Public sample counts must match the number of clients"
                )

            if any(
                isinstance(count, bool)
                or not isinstance(count, int)
                or count <= 0
                for count in public_sample_counts
            ):
                raise ValueError(
                    "Every public sample count must be a positive integer"
                )

            aggregation_counts = list(public_sample_counts)

        else:
            aggregation_counts = []

        global_state = {
            name: tensor.detach().clone()
            for name, tensor in self.global_model.state_dict().items()
        }

        client_states = []
        actual_sample_counts = []
        training_losses = []
        training_accuracies = []

        for index, client in enumerate(self.clients):
            result = client.train(
                initial_model=self.global_model,
                epochs=local_epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                random_seed=random_seed + round_number,
            )

            actual_sample_counts.append(result.sample_count)

            if differential_privacy:
                expected_count = aggregation_counts[index]

                if result.sample_count != expected_count:
                    raise ValueError(
                        f"Client {client.client_id} returned "
                        f"{result.sample_count} samples, but its configured "
                        f"public sample count is {expected_count}"
                    )

                clipped = clip_client_update(
                    global_state=global_state,
                    client_state=result.state_dict,
                    max_update_norm=max_update_norm,
                )

                client_states.append(clipped.state_dict)

            else:
                client_states.append(result.state_dict)
                training_losses.append(result.average_loss)
                training_accuracies.append(result.accuracy)

        if differential_privacy:
            total_samples = sum(aggregation_counts)

            max_client_weight = max(aggregation_counts) / total_samples

            noise_std = calculate_gaussian_noise_std(
                max_update_norm=max_update_norm,
                max_client_weight=max_client_weight,
                noise_multiplier=noise_multiplier,
            )

            aggregated_clipped_state = self.aggregator.aggregate(
                client_states=client_states,
                sample_counts=aggregation_counts,
            )

            aggregated_update = {}

            for name, global_tensor in global_state.items():
                if global_tensor.is_floating_point() or global_tensor.is_complex():
                    aggregated_update[name] = (
                        aggregated_clipped_state[name] - global_tensor
                    )

            noisy_update = add_gaussian_noise(
                aggregated_update=aggregated_update,
                noise_std=noise_std,
            )

            updated_state = {}

            for name, global_tensor in global_state.items():
                if name in noisy_update:
                    updated_state[name] = (
                        global_tensor + noisy_update[name]
                    )
                else:
                    updated_state[name] = global_tensor.clone()

            self.global_model.load_state_dict(updated_state)

            # Do not expose raw training metrics or clipping diagnostics
            # as outputs of the differentially private round.
            weighted_loss = None
            weighted_accuracy = None
            clipped_client_count = None
            max_client_update_norm = None

        else:
            total_samples = sum(actual_sample_counts)

            aggregated_state = self.aggregator.aggregate(
                client_states=client_states,
                sample_counts=actual_sample_counts,
            )

            self.global_model.load_state_dict(aggregated_state)

            weighted_loss = sum(
                loss * count
                for loss, count in zip(
                    training_losses,
                    actual_sample_counts,
                    strict=True,
                )
            ) / total_samples

            weighted_accuracy = sum(
                accuracy * count
                for accuracy, count in zip(
                    training_accuracies,
                    actual_sample_counts,
                    strict=True,
                )
            ) / total_samples

            clipped_client_count = 0
            max_client_update_norm = None
            noise_std = None

        return FederatedRoundResult(
            round_number=round_number,
            client_count=len(self.clients),
            total_samples=total_samples,
            average_training_loss=weighted_loss,
            average_training_accuracy=weighted_accuracy,
            clipped_client_count=clipped_client_count,
            max_client_update_norm=max_client_update_norm,
            noise_std=noise_std,
        )
