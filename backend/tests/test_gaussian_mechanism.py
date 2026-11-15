import pytest
import torch

from app.ml.privacy.gaussian_mechanism import (
    add_gaussian_noise,
    calculate_gaussian_noise_std,
)


def test_calculates_noise_std_for_equal_client_weights():
    noise_std = calculate_gaussian_noise_std(
        max_update_norm=2.0,
        max_client_weight=1 / 3,
        noise_multiplier=1.5,
    )

    assert noise_std == pytest.approx(2.0)


def test_calculates_noise_std_for_unequal_client_weights():
    noise_std = calculate_gaussian_noise_std(
        max_update_norm=2.0,
        max_client_weight=0.5,
        noise_multiplier=1.0,
    )

    assert noise_std == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("max_update_norm", "max_client_weight", "noise_multiplier"),
    [
        (0.0, 1 / 3, 1.0),
        (1.0, 0.0, 1.0),
        (1.0, 1.1, 1.0),
        (1.0, 1 / 3, -1.0),
        (float("inf"), 1 / 3, 1.0),
    ],
)
def test_rejects_invalid_privacy_parameters(
    max_update_norm,
    max_client_weight,
    noise_multiplier,
):
    with pytest.raises(ValueError):
        calculate_gaussian_noise_std(
            max_update_norm,
            max_client_weight,
            noise_multiplier,
        )


def test_adds_noise_to_aggregated_update():
    update = {
        "weight": torch.zeros(1000, dtype=torch.float32),
    }

    noisy_update = add_gaussian_noise(
        aggregated_update=update,
        noise_std=1.0,
    )

    assert noisy_update["weight"].shape == update["weight"].shape
    assert torch.isfinite(noisy_update["weight"]).all()
    assert not torch.equal(noisy_update["weight"], update["weight"])


def test_zero_noise_preserves_update():
    update = {
        "weight": torch.tensor([1.0, 2.0]),
    }

    noisy_update = add_gaussian_noise(update, noise_std=0.0)

    assert torch.equal(noisy_update["weight"], update["weight"])
    assert noisy_update["weight"].data_ptr() != update["weight"].data_ptr()


def test_rejects_negative_noise_standard_deviation():
    update = {"weight": torch.tensor([1.0])}

    with pytest.raises(ValueError):
        add_gaussian_noise(update, noise_std=-1.0)


def test_rejects_empty_update():
    with pytest.raises(ValueError):
        add_gaussian_noise({}, noise_std=1.0)


def test_rejects_non_floating_update():
    update = {"counter": torch.tensor([1, 2], dtype=torch.int64)}

    with pytest.raises(TypeError):
        add_gaussian_noise(update, noise_std=1.0)


def test_rejects_non_finite_update():
    update = {"weight": torch.tensor([float("nan")])}

    with pytest.raises(ValueError):
        add_gaussian_noise(update, noise_std=1.0)
