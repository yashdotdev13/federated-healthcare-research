import pytest
import torch

from app.ml.aggregation.fedavg import FedAvgAggregator


def test_equal_weight_fedavg():
    client_states = [
        {"weight": torch.tensor([1.0, 2.0])},
        {"weight": torch.tensor([3.0, 4.0])},
        {"weight": torch.tensor([5.0, 6.0])},
    ]

    result = FedAvgAggregator.aggregate(
        client_states,
        [10, 10, 10],
    )

    assert torch.allclose(
        result["weight"],
        torch.tensor([3.0, 4.0]),
    )


def test_weighted_fedavg():
    client_states = [
        {"weight": torch.tensor([1.0])},
        {"weight": torch.tensor([3.0])},
    ]

    result = FedAvgAggregator.aggregate(
        client_states,
        [25, 75],
    )

    assert torch.allclose(
        result["weight"],
        torch.tensor([2.5]),
    )


def test_rejects_empty_clients():
    with pytest.raises(ValueError):
        FedAvgAggregator.aggregate([], [])


def test_rejects_mismatched_client_counts():
    states = [{"weight": torch.tensor([1.0])}]

    with pytest.raises(ValueError):
        FedAvgAggregator.aggregate(states, [10, 20])


def test_rejects_zero_sample_count():
    states = [{"weight": torch.tensor([1.0])}]

    with pytest.raises(ValueError):
        FedAvgAggregator.aggregate(states, [0])


def test_rejects_incompatible_model_shapes():
    states = [
        {"weight": torch.tensor([1.0, 2.0])},
        {"weight": torch.tensor([1.0])},
    ]

    with pytest.raises(ValueError):
        FedAvgAggregator.aggregate(states, [10, 10])


def test_preserves_matching_integer_buffers():
    states = [
        {
            "weight": torch.tensor([1.0]),
            "counter": torch.tensor(5),
        },
        {
            "weight": torch.tensor([3.0]),
            "counter": torch.tensor(5),
        },
    ]

    result = FedAvgAggregator.aggregate(states, [10, 10])

    assert torch.equal(result["counter"], torch.tensor(5))
    assert torch.allclose(result["weight"], torch.tensor([2.0]))


def test_rejects_different_integer_buffers():
    states = [
        {"counter": torch.tensor(5)},
        {"counter": torch.tensor(6)},
    ]

    with pytest.raises(ValueError):
        FedAvgAggregator.aggregate(states, [10, 10])
