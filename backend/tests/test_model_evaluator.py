import numpy as np
import pytest
import torch

from app.ml.evaluation.evaluator import (
    calculate_roc_auc,
    evaluate_model,
)
from app.ml.models.diagnostic_model import DiagnosticMLP


def test_roc_auc_perfect_predictions():
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.2, 0.8, 0.9])

    assert calculate_roc_auc(labels, probabilities) == 1.0


def test_roc_auc_random_tie_case():
    labels = np.array([0, 1])
    probabilities = np.array([0.5, 0.5])

    assert calculate_roc_auc(labels, probabilities) == 0.5


def test_roc_auc_requires_both_classes():
    labels = np.array([0, 0])
    probabilities = np.array([0.1, 0.2])

    with pytest.raises(ValueError):
        calculate_roc_auc(labels, probabilities)


def test_evaluate_model_returns_all_metrics():
    torch.manual_seed(42)

    model = DiagnosticMLP()

    features = np.random.default_rng(42).normal(
        size=(20, 30)
    ).astype(np.float32)

    labels = np.array([0, 1] * 10)

    result = evaluate_model(model, features, labels)

    assert result.sample_count == 20
    assert 0 <= result.accuracy <= 1
    assert 0 <= result.precision <= 1
    assert 0 <= result.recall <= 1
    assert 0 <= result.f1_score <= 1
    assert 0 <= result.sensitivity <= 1
    assert 0 <= result.specificity <= 1
    assert 0 <= result.roc_auc <= 1


def test_evaluator_rejects_empty_dataset():
    model = DiagnosticMLP()

    with pytest.raises(ValueError):
        evaluate_model(
            model,
            np.empty((0, 30), dtype=np.float32),
            np.array([], dtype=np.int64),
        )


def test_evaluator_rejects_mismatched_lengths():
    model = DiagnosticMLP()

    with pytest.raises(ValueError):
        evaluate_model(
            model,
            np.zeros((5, 30), dtype=np.float32),
            np.array([0, 1]),
        )
