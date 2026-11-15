import math
import secrets
from collections.abc import Mapping

import torch


_SECURE_RANDOM = secrets.SystemRandom()


def calculate_gaussian_noise_std(
    max_update_norm: float,
    max_client_weight: float,
    noise_multiplier: float,
) -> float:
    """
    Calculate Gaussian noise standard deviation for replace-one-client
    adjacency with fixed, public aggregation weights.

    Sensitivity bound:
        sensitivity = 2 * max_update_norm * max_client_weight

    Noise standard deviation:
        noise_std = noise_multiplier * sensitivity
    """

    values = (
        max_update_norm,
        max_client_weight,
        noise_multiplier,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Privacy parameters must be finite")

    if max_update_norm <= 0:
        raise ValueError("Maximum update norm must be positive")

    if not 0 < max_client_weight <= 1:
        raise ValueError("Maximum client weight must be in (0, 1]")

    if noise_multiplier < 0:
        raise ValueError("Noise multiplier cannot be negative")

    sensitivity = 2.0 * max_update_norm * max_client_weight

    return noise_multiplier * sensitivity


def add_gaussian_noise(
    aggregated_update: Mapping[str, torch.Tensor],
    noise_std: float,
) -> dict[str, torch.Tensor]:
    """
    Add independent Gaussian noise to every element of an aggregated update.

    Noise is generated using Python's OS-backed SystemRandom source.

    This function does not calculate privacy guarantees. Those depend on
    sensitivity, adjacency, sampling, and cumulative privacy accounting.
    """

    if not math.isfinite(noise_std) or noise_std < 0:
        raise ValueError("Noise standard deviation must be finite and non-negative")

    if not aggregated_update:
        raise ValueError("Aggregated update cannot be empty")

    noisy_update = {}

    for name, tensor in aggregated_update.items():
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"Update '{name}' must be a PyTorch tensor")

        if not tensor.is_floating_point():
            raise TypeError(
                f"Update '{name}' must have a floating-point dtype"
            )

        if not torch.isfinite(tensor).all().item():
            raise ValueError(f"Update '{name}' contains non-finite values")

        if noise_std == 0:
            noisy_update[name] = tensor.detach().clone()
            continue

        noise_values = [
            _SECURE_RANDOM.gauss(0.0, noise_std)
            for _ in range(tensor.numel())
        ]

        noise = torch.tensor(
            noise_values,
            dtype=tensor.dtype,
            device=tensor.device,
        ).reshape(tensor.shape)

        noisy_update[name] = tensor.detach() + noise

    return noisy_update
