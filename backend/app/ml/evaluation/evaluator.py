from dataclasses import dataclass

import numpy as np
import torch

from app.ml.models.diagnostic_model import DiagnosticMLP


@dataclass(frozen=True)
class EvaluationResult:
    sample_count: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    sensitivity: float
    specificity: float
    roc_auc: float


def calculate_roc_auc(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    """Calculate ROC-AUC using pairwise positive-negative comparisons."""

    positives = probabilities[labels == 1]
    negatives = probabilities[labels == 0]

    if len(positives) == 0 or len(negatives) == 0:
        raise ValueError("ROC-AUC requires both classes")

    comparisons = (
        positives[:, None] - negatives[None, :]
    )

    return float(
        (
            np.sum(comparisons > 0)
            + 0.5 * np.sum(comparisons == 0)
        )
        / (len(positives) * len(negatives))
    )


def evaluate_model(
    model: DiagnosticMLP,
    features: np.ndarray,
    labels: np.ndarray,
) -> EvaluationResult:
    """Evaluate a binary classification model on held-out data."""

    if len(features) == 0:
        raise ValueError("Evaluation dataset cannot be empty")

    if len(features) != len(labels):
        raise ValueError("Features and labels must have equal lengths")

    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Labels must contain only binary values 0 and 1")

    x_tensor = torch.as_tensor(features, dtype=torch.float32)

    model.eval()

    with torch.inference_mode():
        logits = model(x_tensor)
        probabilities = torch.softmax(logits, dim=1)[:, 1]
        predictions = logits.argmax(dim=1)

    y_true = labels.astype(np.int64)
    y_pred = predictions.cpu().numpy()
    y_prob = probabilities.cpu().numpy()

    true_positive = int(np.sum((y_true == 1) & (y_pred == 1)))
    true_negative = int(np.sum((y_true == 0) & (y_pred == 0)))
    false_positive = int(np.sum((y_true == 0) & (y_pred == 1)))
    false_negative = int(np.sum((y_true == 1) & (y_pred == 0)))

    accuracy = (true_positive + true_negative) / len(y_true)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative else 0.0
    )

    specificity = (
        true_negative / (true_negative + false_positive)
        if true_negative + false_positive else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    roc_auc = calculate_roc_auc(y_true, y_prob)

    return EvaluationResult(
        sample_count=len(y_true),
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        sensitivity=recall,
        specificity=specificity,
        roc_auc=roc_auc,
    )
