"""Rules for which models are valid given dataset structure and variable selection."""
from __future__ import annotations

from app.schemas.modeling import ModelType


CROSS_SECTION_MODELS: tuple[ModelType, ...] = ("ols", "robust_ols")
PANEL_MODELS: tuple[ModelType, ...] = (
    "pooled_ols",
    "fixed_effects",
    "random_effects",
    "two_way_fixed_effects",
)

_UNAVAILABLE_REASONS: dict[ModelType, str] = {
    "pooled_ols": (
        "Pooled OLS requires both an entity column and a time column to be selected. "
        "This dataset does not appear to have a valid panel structure under the current configuration."
    ),
    "fixed_effects": (
        "Fixed Effects requires both an entity column and a time column to be selected. "
        "This dataset does not appear to have a valid panel structure under the current configuration."
    ),
    "random_effects": (
        "Random Effects requires both an entity column and a time column to be selected. "
        "This dataset does not appear to have a valid panel structure under the current configuration."
    ),
    "two_way_fixed_effects": (
        "Two-Way Fixed Effects requires both an entity column and a time column to be selected. "
        "This dataset does not appear to have a valid panel structure under the current configuration."
    ),
}


def get_compatible_models(
    *,
    has_entity_column: bool,
    has_time_column: bool,
    requested_models: list[ModelType],
) -> tuple[list[ModelType], dict[ModelType, str]]:
    """Return (compatible_list, {model_type: unavailability_reason}).

    Only models that are structurally compatible with the dataset are returned
    in the compatible list. The reasons dict records why incompatible models
    cannot be run.
    """
    is_panel = has_entity_column and has_time_column
    compatible: list[ModelType] = []
    reasons: dict[ModelType, str] = {}

    for m in requested_models:
        if m in PANEL_MODELS and not is_panel:
            reasons[m] = _UNAVAILABLE_REASONS.get(
                m,
                "This panel model requires a valid entity/time column configuration.",
            )
        else:
            compatible.append(m)

    return compatible, reasons
