from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from app.ml.models.diagnostic_model import DiagnosticMLP
from app.ml.training.local_trainer import (
    LocalTrainingResult,
    train_local_model,
)


@dataclass
class HospitalClient:

    client_id: str

    x_train: np.ndarray

    y_train: np.ndarray

    def train(
        self,
        initial_model: DiagnosticMLP,
        epochs: int = 5,
        batch_size: int = 32,
        learning_rate: float = 0.01,
        random_seed: int = 42,
    ) -> LocalTrainingResult:

        local_model = deepcopy(initial_model)

        result = train_local_model(
            model=local_model,
            features=self.x_train,
            labels=self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            random_seed=random_seed,
        )

        return result