import numpy as np


def partition_iid(
    labels: np.ndarray,
    num_clients: int,
    random_seed: int = 42,
) -> list[np.ndarray]:
    """Split sample indices randomly into approximately equal IID partitions."""
    if num_clients < 2:
        raise ValueError("num_clients must be at least 2")

    if len(labels) < num_clients:
        raise ValueError("There must be at least one sample per client")

    rng = np.random.default_rng(random_seed)
    indices = rng.permutation(len(labels))

    return [
        partition.astype(np.int64)
        for partition in np.array_split(indices, num_clients)
    ]


def partition_dirichlet_non_iid(
    labels: np.ndarray,
    num_clients: int,
    alpha: float = 0.5,
    random_seed: int = 42,
    min_samples_per_client: int = 10,
    max_attempts: int = 1_000,
) -> list[np.ndarray]:
    """
    Partition sample indices using a Dirichlet label distribution.

    Smaller alpha values generally produce stronger label imbalance.
    """
    if num_clients < 2:
        raise ValueError("num_clients must be at least 2")

    if alpha <= 0:
        raise ValueError("alpha must be greater than 0")

    if min_samples_per_client < 1:
        raise ValueError("min_samples_per_client must be positive")

    if len(labels) < num_clients * min_samples_per_client:
        raise ValueError("Not enough samples to satisfy the minimum client size")

    rng = np.random.default_rng(random_seed)
    class_indices = [
        np.flatnonzero(labels == class_label)
        for class_label in np.unique(labels)
    ]

    for indices in class_indices:
        rng.shuffle(indices)

    for _ in range(max_attempts):
        client_indices: list[list[int]] = [
            [] for _ in range(num_clients)
        ]

        for indices in class_indices:
            proportions = rng.dirichlet(
                np.full(num_clients, alpha, dtype=np.float64)
            )
            counts = rng.multinomial(len(indices), proportions)

            start = 0
            for client_id, count in enumerate(counts):
                end = start + count
                client_indices[client_id].extend(
                    indices[start:end].tolist()
                )
                start = end

        if all(
            len(indices) >= min_samples_per_client
            for indices in client_indices
        ):
            result = []
            for indices in client_indices:
                rng.shuffle(indices)
                result.append(np.asarray(indices, dtype=np.int64))
            return result

    raise RuntimeError(
        "Could not create valid partitions. Try increasing alpha "
        "or reducing min_samples_per_client."
    )
