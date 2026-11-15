from collections.abc import Mapping, Sequence

import torch


class FedAvgAggregator:
    """
    Implements sample-weighted Federated Averaging (FedAvg).
    """

    @staticmethod
    def aggregate(
        client_states: Sequence[Mapping[str, torch.Tensor]],
        sample_counts: Sequence[int],
    ) -> dict[str, torch.Tensor]:
        """
        Aggregate client model states using sample-weighted averaging.
        """

        if not client_states:
            raise ValueError("At least one client model is required")

        if len(client_states) != len(sample_counts):
            raise ValueError(
                "Client states and sample counts must have equal lengths"
            )

        if any(
            isinstance(count, bool)
            or not isinstance(count, int)
            or count <= 0
            for count in sample_counts
        ):
            raise ValueError(
                "Every client sample count must be a positive integer"
            )

        reference_state = client_states[0]

        if not reference_state:
            raise ValueError("Client model state cannot be empty")

        reference_keys = set(reference_state.keys())

        for client_index, state in enumerate(client_states):
            if set(state.keys()) != reference_keys:
                raise ValueError(
                    f"Client {client_index} has incompatible model parameters"
                )

            for key in reference_keys:
                reference_tensor = reference_state[key]
                client_tensor = state[key]

                if not isinstance(reference_tensor, torch.Tensor):
                    raise TypeError(
                        f"Reference parameter '{key}' must be a tensor"
                    )

                if not isinstance(client_tensor, torch.Tensor):
                    raise TypeError(
                        f"Parameter '{key}' must be a PyTorch tensor"
                    )

                if client_tensor.shape != reference_tensor.shape:
                    raise ValueError(
                        f"Shape mismatch for parameter '{key}' "
                        f"at client {client_index}"
                    )

                if client_tensor.dtype != reference_tensor.dtype:
                    raise ValueError(
                        f"Dtype mismatch for parameter '{key}' "
                        f"at client {client_index}"
                    )

                if client_tensor.device != reference_tensor.device:
                    raise ValueError(
                        f"Device mismatch for parameter '{key}' "
                        f"at client {client_index}"
                    )

        total_samples = sum(sample_counts)
        aggregated_state = {}

        for key, reference_tensor in reference_state.items():

            if reference_tensor.is_floating_point() or reference_tensor.is_complex():
                accumulator = torch.zeros_like(reference_tensor)

                for state, sample_count in zip(
                    client_states,
                    sample_counts,
                    strict=True,
                ):
                    weight = sample_count / total_samples

                    accumulator.add_(
                        state[key],
                        alpha=weight,
                    )

                aggregated_state[key] = accumulator

            else:
                # Integer buffers cannot be meaningfully averaged.
                # Require identical values across all clients.
                if not all(
                    torch.equal(state[key], reference_tensor)
                    for state in client_states[1:]
                ):
                    raise ValueError(
                        f"Non-floating parameter '{key}' differs "
                        "between clients and cannot be averaged"
                    )

                aggregated_state[key] = reference_tensor.clone()

        return aggregated_state
