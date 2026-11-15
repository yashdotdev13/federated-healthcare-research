import pytest
import torch

from app.ml.privacy.update_clipper import clip_client_update


def test_clips_client_update_to_maximum_norm():
    global_state = {
        "weight": torch.tensor([0.0, 0.0]),
        "bias": torch.tensor([0.0]),
    }

    client_state = {
        "weight": torch.tensor([3.0, 4.0]),
        "bias": torch.tensor([0.0]),
    }

    result = clip_client_update(
        global_state,
        client_state,
        max_update_norm=2.0,
    )

    assert result.was_clipped
    assert result.original_norm == pytest.approx(5.0)
    assert result.clipped_norm == pytest.approx(2.0)
    assert result.clipping_factor == pytest.approx(0.4)

    assert torch.allclose(
        result.state_dict["weight"],
        torch.tensor([1.2, 1.6]),
    )


def test_does_not_modify_update_below_threshold():
    global_state = {
        "weight": torch.tensor([1.0, 2.0]),
    }

    client_state = {
        "weight": torch.tensor([2.0, 4.0]),
    }

    result = clip_client_update(
        global_state,
        client_state,
        max_update_norm=10.0,
    )

    assert not result.was_clipped
    assert result.clipping_factor == 1.0
    assert torch.equal(
        result.state_dict["weight"],
        client_state["weight"],
    )


def test_handles_zero_update():
    global_state = {
        "weight": torch.tensor([1.0, 2.0]),
    }

    result = clip_client_update(
        global_state,
        global_state,
        max_update_norm=1.0,
    )

    assert result.original_norm == 0.0
    assert result.clipped_norm == 0.0
    assert not result.was_clipped


def test_rejects_non_positive_maximum_norm():
    state = {"weight": torch.tensor([1.0])}

    with pytest.raises(ValueError):
        clip_client_update(state, state, max_update_norm=0.0)


def test_rejects_mismatched_state_keys():
    global_state = {"weight": torch.tensor([1.0])}
    client_state = {"bias": torch.tensor([1.0])}

    with pytest.raises(ValueError):
        clip_client_update(
            global_state,
            client_state,
            max_update_norm=1.0,
        )


def test_rejects_different_integer_buffers():
    global_state = {
        "weight": torch.tensor([1.0]),
        "counter": torch.tensor(1),
    }

    client_state = {
        "weight": torch.tensor([2.0]),
        "counter": torch.tensor(2),
    }

    with pytest.raises(ValueError):
        clip_client_update(
            global_state,
            client_state,
            max_update_norm=1.0,
        )
