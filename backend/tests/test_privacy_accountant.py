import math

import pytest

from app.ml.privacy.privacy_accountant import compute_rdp_epsilon


def test_computes_finite_epsilon_for_five_rounds():
    result = compute_rdp_epsilon(
        noise_multiplier=1.5,
        steps=5,
        delta=1e-5,
    )

    assert math.isfinite(result.epsilon)
    assert result.epsilon > 0
    assert result.delta == 1e-5
    assert result.noise_multiplier == 1.5
    assert result.steps == 5
    assert result.optimal_order is not None
    assert result.optimal_order > 1


def test_more_rounds_increase_privacy_cost():
    five_rounds = compute_rdp_epsilon(
        noise_multiplier=1.5,
        steps=5,
        delta=1e-5,
    )

    ten_rounds = compute_rdp_epsilon(
        noise_multiplier=1.5,
        steps=10,
        delta=1e-5,
    )

    assert ten_rounds.epsilon >= five_rounds.epsilon


def test_more_noise_reduces_privacy_cost():
    lower_noise = compute_rdp_epsilon(
        noise_multiplier=1.0,
        steps=5,
        delta=1e-5,
    )

    higher_noise = compute_rdp_epsilon(
        noise_multiplier=2.0,
        steps=5,
        delta=1e-5,
    )

    assert higher_noise.epsilon < lower_noise.epsilon


def test_zero_noise_has_infinite_epsilon():
    result = compute_rdp_epsilon(
        noise_multiplier=0.0,
        steps=5,
        delta=1e-5,
    )

    assert math.isinf(result.epsilon)
    assert result.optimal_order is None


@pytest.mark.parametrize(
    ("noise_multiplier", "steps", "delta", "orders"),
    [
        (-1.0, 5, 1e-5, (2.0, 4.0)),
        (float("inf"), 5, 1e-5, (2.0,)),
        (1.0, 0, 1e-5, (2.0,)),
        (1.0, True, 1e-5, (2.0,)),
        (1.0, 5, 0.0, (2.0,)),
        (1.0, 5, 1.0, (2.0,)),
        (1.0, 5, 1e-5, (1.0,)),
        (1.0, 5, 1e-5, ()),
    ],
)
def test_rejects_invalid_accounting_parameters(
    noise_multiplier,
    steps,
    delta,
    orders,
):
    with pytest.raises(ValueError):
        compute_rdp_epsilon(
            noise_multiplier=noise_multiplier,
            steps=steps,
            delta=delta,
            orders=orders,
        )


def test_larger_delta_does_not_increase_epsilon():
    strict_delta = compute_rdp_epsilon(
        noise_multiplier=1.5,
        steps=5,
        delta=1e-6,
    )

    relaxed_delta = compute_rdp_epsilon(
        noise_multiplier=1.5,
        steps=5,
        delta=1e-4,
    )

    assert relaxed_delta.epsilon <= strict_delta.epsilon
