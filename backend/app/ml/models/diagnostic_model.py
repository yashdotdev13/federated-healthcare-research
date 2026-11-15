from torch import nn


class DiagnosticMLP(nn.Module):
    """Small MLP for binary classification on tabular diagnostic features."""

    def __init__(
        self,
        input_dim: int = 30,
        num_classes: int = 2,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, num_classes),
        )

    def forward(self, features):
        return self.network(features)
