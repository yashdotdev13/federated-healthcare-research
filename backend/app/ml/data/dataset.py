import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class FederatedDataset:
    x_train: np.ndarray
    x_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    feature_names: tuple[str, ...]
    class_names: tuple[str, ...]


def load_breast_cancer_dataset(
    test_size: float = 0.2,
    random_seed: int = 42,
) -> FederatedDataset:
    """Load and preprocess the UCI Wisconsin Diagnostic Breast Cancer dataset."""
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")

    dataset_path = Path(__file__).resolve().parents[3] / "data" / "raw" / "wdbc.data"

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"WDBC dataset not found at {dataset_path}. "
            "Download it into backend/data/raw/wdbc.data."
        )

    features = []
    labels = []

    with dataset_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) != 32:
                raise ValueError(
                    f"Expected 32 columns in WDBC record, found {len(row)}"
                )

            # UCI labels: M = malignant (1), B = benign (0).
            labels.append(1 if row[1] == "M" else 0)
            features.append([float(value) for value in row[2:]])

    x = np.asarray(features, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int64)

    rng = np.random.default_rng(random_seed)
    train_indices = []
    test_indices = []

    # Stratified split: preserve class proportions in train and test.
    for class_label in np.unique(y):
        class_indices = np.flatnonzero(y == class_label)
        rng.shuffle(class_indices)

        test_count = max(1, int(round(len(class_indices) * test_size)))
        test_indices.extend(class_indices[:test_count])
        train_indices.extend(class_indices[test_count:])

    train_indices = np.asarray(train_indices, dtype=np.int64)
    test_indices = np.asarray(test_indices, dtype=np.int64)

    rng.shuffle(train_indices)
    rng.shuffle(test_indices)

    x_train = x[train_indices]
    x_test = x[test_indices]
    y_train = y[train_indices]
    y_test = y[test_indices]

    # Fit standardization on training samples only.
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)
    std[std == 0] = 1.0

    x_train = ((x_train - mean) / std).astype(np.float32)
    x_test = ((x_test - mean) / std).astype(np.float32)

    feature_names = tuple(
        f"{measurement}_{statistic}"
        for measurement in (
            "radius", "texture", "perimeter", "area", "smoothness",
            "compactness", "concavity", "concave_points", "symmetry",
            "fractal_dimension",
        )
        for statistic in ("mean", "se", "worst")
    )

    return FederatedDataset(
        x_train=x_train,
        x_test=x_test,
        y_train=y_train,
        y_test=y_test,
        feature_names=feature_names,
        class_names=("benign", "malignant"),
    )
