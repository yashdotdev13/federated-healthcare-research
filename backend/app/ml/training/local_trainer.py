from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from app.ml.models.diagnostic_model import DiagnosticMLP


@dataclass(frozen=True)
class LocalTrainingResult:
    state_dict: dict[str, torch.Tensor]
    average_loss: float
    accuracy: float
    sample_count: int
    epochs_completed: int


def train_local_model(
    model: DiagnosticMLP,
    features: np.ndarray,
    labels: np.ndarray,
    epochs: int = 5,
    batch_size: int = 32,
    learning_rate: float = 0.01,
    random_seed: int = 42,
) -> LocalTrainingResult:
    """Train a model locally using one hospital's private training partition."""
    if len(features) == 0 or len(labels) == 0:
        raise ValueError("Local training data cannot be empty")

    if len(features) != len(labels):
        raise ValueError("Features and labels must have equal lengths")

    if epochs < 1 or batch_size < 1 or learning_rate <= 0:
        raise ValueError("Invalid local training configuration")

    torch.manual_seed(random_seed)

    x_tensor = torch.as_tensor(features, dtype=torch.float32)
    y_tensor = torch.as_tensor(labels, dtype=torch.long)

    dataset = TensorDataset(x_tensor, y_tensor)
    generator = torch.Generator().manual_seed(random_seed)

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )

    model.train()
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=learning_rate,
    )
    criterion = nn.CrossEntropyLoss()

    total_loss = 0.0
    correct_predictions = 0
    total_samples = 0

    for _ in range(epochs):
        for batch_features, batch_labels in loader:
            optimizer.zero_grad()

            logits = model(batch_features)
            loss = criterion(logits, batch_labels)

            loss.backward()
            optimizer.step()

            batch_size_actual = len(batch_labels)
            total_loss += loss.item() * batch_size_actual

            predictions = logits.argmax(dim=1)
            correct_predictions += (
                predictions == batch_labels
            ).sum().item()
            total_samples += batch_size_actual

    state = {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }

    return LocalTrainingResult(
        state_dict=state,
        average_loss=total_loss / total_samples,
        accuracy=correct_predictions / total_samples,
        sample_count=len(dataset),
        epochs_completed=epochs,
    )
