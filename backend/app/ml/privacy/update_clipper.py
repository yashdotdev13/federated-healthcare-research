from dataclasses import dataclass
from collections.abc import Mapping

import torch


@dataclass(frozen=True)
class ClippedUpdate:
    state_dict: dict[str, torch.Tensor]
    original_norm: float
    clipped_norm: float
    clipping_factor: float
    was_clipped: bool


def clip_client_update(
    global_state: Mapping[str, torch.Tensor],
    client_state: Mapping[str, torch.Tensor],
    max_update_norm: float,
) -> ClippedUpdate:
    """
    Clip a complete client model update using its global L2 norm.

    The update is defined as:

        delta = client_state - global_state

    The clipped local state is reconstructed as:

        global_state + clipped_delta

    Non-floating-point buffers must remain unchanged.
    """

    if max_update_norm <= 0:
        raise ValueError("Maximum update norm must be positive")

    if not global_state:
        raise ValueError("Global model state cannot be empty")

    if set(global_state) != set(client_state):
        raise ValueError("Global and client model states must have matching keys")

    squared_norm = 0.0
    updates = {}

    for name, global_tensor in global_state.items():
        client_tensor = client_state[name]

        if not isinstance(global_tensor, torch.Tensor):
            raise TypeError(f"Global parameter '{name}' must be a tensor")

        if not isinstance(client_tensor, torch.Tensor):
            raise TypeError(f"Client parameter '{name}' must be a tensor")

        if global_tensor.shape != client_tensor.shape:
            raise ValueError(f"Shape mismatch for parameter '{name}'")

        if global_tensor.dtype != client_tensor.dtype:
            raise ValueError(f"Dtype mismatch for parameter '{name}'")

        if global_tensor.device != client_tensor.device:
            raise ValueError(f"Device mismatch for parameter '{name}'")

        if global_tensor.is_floating_point() or global_tensor.is_complex():
            update = client_tensor - global_tensor
            updates[name] = update
            squared_norm += torch.sum(torch.abs(update) ** 2).item()
        else:
            if not torch.equal(global_tensor, client_tensor):
                raise ValueError(
                    f"Non-floating parameter '{name}' changed during local training"
                )

    original_norm = squared_norm ** 0.5

    clipping_factor = min(
        1.0,
        max_update_norm / (original_norm + 1e-12),
    )

    clipped_state = {}

    for name, global_tensor in global_state.items():
        if name in updates:
            clipped_state[name] = (
                global_tensor + updates[name] * clipping_factor
            ).detach().clone()
        else:
            clipped_state[name] = global_tensor.detach().clone()

    clipped_norm = original_norm * clipping_factor

    return ClippedUpdate(
        state_dict=clipped_state,
        original_norm=original_norm,
        clipped_norm=clipped_norm,
        clipping_factor=clipping_factor,
        was_clipped=clipping_factor < 1.0,
    )
