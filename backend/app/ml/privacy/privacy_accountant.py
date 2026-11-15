import math
from dataclasses import dataclass
from collections.abc import Sequence


DEFAULT_RDP_ORDERS = (
    1.25,
    1.5,
    2.0,
    3.0,
    4.0,
    5.0,
    8.0,
    10.0,
    16.0,
    20.0,
    32.0,
    64.0,
    128.0,
    256.0,
)


@dataclass(frozen=True)
class PrivacyAccountantResult:
    epsilon: float
    delta: float
    noise_multiplier: float
    steps: int
    optimal_order: float | None


def compute_rdp_epsilon(
    noise_multiplier: float,
    steps: int,
    delta: float,
    orders: Sequence[float] = DEFAULT_RDP_ORDERS,
) -> PrivacyAccountantResult:
    """
    Compute an (epsilon, delta) upper bound using RDP composition
    for repeated Gaussian mechanisms with full participation.

    Assumptions:
    - Every step releases one Gaussian-perturbed aggregate.
    - Every step uses the same noise multiplier.
    - The sensitivity bound is valid for the chosen adjacency.
    - There is no subsampling amplification.
    - The aggregation weights are fixed and public.

    This accountant does not support client subsampling.
    """

    if (
        not math.isfinite(noise_multiplier)
        or noise_multiplier < 0
    ):
        raise ValueError("Noise multiplier must be finite and non-negative")

    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("Steps must be a positive integer")

    if not math.isfinite(delta) or not 0 < delta < 1:
        raise ValueError("Delta must be finite and in the interval (0, 1)")

    if not orders:
        raise ValueError("At least one RDP order is required")

    validated_orders = []

    for order in orders:
        if not math.isfinite(order) or order <= 1:
            raise ValueError("Every RDP order must be finite and greater than 1")

        validated_orders.append(float(order))

    if noise_multiplier == 0:
        return PrivacyAccountantResult(
            epsilon=float("inf"),
            delta=delta,
            noise_multiplier=noise_multiplier,
            steps=steps,
            optimal_order=None,
        )

    log_inverse_delta = math.log(1.0 / delta)

    candidates = [
        (
            steps * order / (2.0 * noise_multiplier**2)
            + log_inverse_delta / (order - 1.0),
            order,
        )
        for order in validated_orders
    ]

    epsilon, optimal_order = min(candidates, key=lambda item: item[0])

    return PrivacyAccountantResult(
        epsilon=epsilon,
        delta=delta,
        noise_multiplier=noise_multiplier,
        steps=steps,
        optimal_order=optimal_order,
    )
