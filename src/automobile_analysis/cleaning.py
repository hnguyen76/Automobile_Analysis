"""Reproducible cleaning pipeline for the automobile listing dataset.

The source has no VIN or stable listing identifier, so this module takes a
conservative approach: exact duplicates may be removed, but plausible repeated
listings are retained. Missing values are handled transparently with explicit
audit flags instead of dropping incomplete rows.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SOURCE_COLUMNS: tuple[str, ...] = (
    "make",
    "model",
    "year",
    "fuel_type",
    "transmission",
    "engine_size",
    "mileage",
    "horsepower",
    "torque",
    "owners",
    "accident_history",
    "service_history",
    "color",
    "body_type",
    "drivetrain",
    "fuel_efficiency",
    "location",
    "selling_price",
)

TEXT_COLUMNS: tuple[str, ...] = (
    "make",
    "model",
    "fuel_type",
    "transmission",
    "service_history",
    "color",
    "body_type",
    "drivetrain",
    "location",
)

NUMERIC_COLUMNS: tuple[str, ...] = (
    "year",
    "engine_size",
    "mileage",
    "horsepower",
    "torque",
    "owners",
    "accident_history",
    "fuel_efficiency",
    "selling_price",
)

CRITICAL_COLUMNS: tuple[str, ...] = (
    "make",
    "model",
    "year",
    "fuel_type",
    "mileage",
    "owners",
    "body_type",
    "drivetrain",
    "selling_price",
)

NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "year": (1886, 2100),
    "engine_size": (0, 20),
    "mileage": (0, 2_000_000),
    "horsepower": (1, 5_000),
    "torque": (1, 10_000),
    "owners": (1, 20),
    "fuel_efficiency": (1, 500),
    "selling_price": (1, 10_000_000),
}

UNKNOWN_CATEGORY_COLUMNS: tuple[str, ...] = (
    "transmission",
    "service_history",
    "color",
    "location",
)


@dataclass(frozen=True)
class CleaningResult:
    """Container returned by :func:`clean_automobile_data`."""

    data: pd.DataFrame
    report: dict[str, Any]


def _snake_case(value: object) -> str:
    """Convert a source header to a predictable snake_case name."""

    name = re.sub(r"[^0-9A-Za-z]+", "_", str(value).strip())
    return re.sub(r"_+", "_", name).strip("_").lower()


def _normalise_headers(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers and fail early if the source schema is incomplete."""

    cleaned = frame.copy()
    cleaned.columns = [_snake_case(column) for column in cleaned.columns]

    if cleaned.columns.duplicated().any():
        duplicates = cleaned.columns[cleaned.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate columns after normalization: {duplicates}")

    missing = sorted(set(SOURCE_COLUMNS) - set(cleaned.columns))
    if missing:
        raise ValueError(f"Missing required source columns: {', '.join(missing)}")
    return cleaned.loc[:, list(SOURCE_COLUMNS)]


def _normalise_text(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim text and standardize category presentation without inventing values."""

    cleaned = frame.copy()
    for column in TEXT_COLUMNS:
        values = cleaned[column].astype("string").str.strip()
        cleaned[column] = values.mask(values.eq(""), pd.NA)

    # Known category fields use stable presentation for filters and exports.
    for column in (
        "fuel_type",
        "transmission",
        "service_history",
        "color",
        "body_type",
    ):
        cleaned[column] = cleaned[column].str.title()
    cleaned["body_type"] = cleaned["body_type"].replace({"Suv": "SUV"})

    make_title = cleaned["make"].str.title()
    cleaned["make"] = make_title.replace(
        {
            "Bmw": "BMW",
            "Mercedes-Benz": "Mercedes-Benz",
        }
    )
    cleaned["drivetrain"] = cleaned["drivetrain"].str.upper()
    cleaned["location"] = cleaned["location"].str.upper()
    return cleaned


def _coerce_and_validate_numeric(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Coerce numeric values and replace out-of-range specifications with nulls."""

    cleaned = frame.copy()
    invalid_counts: dict[str, int] = {}

    for column in NUMERIC_COLUMNS:
        original_non_null = cleaned[column].notna()
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
        conversion_failures = original_non_null & cleaned[column].isna()

        range_failures = pd.Series(False, index=cleaned.index, dtype=bool)
        if column in NUMERIC_RANGES:
            lower, upper = NUMERIC_RANGES[column]
            range_failures = cleaned[column].notna() & ~cleaned[column].between(
                lower,
                upper,
                inclusive="both",
            )
            cleaned.loc[range_failures, column] = np.nan

        if column == "accident_history":
            invalid_accident = cleaned[column].notna() & ~cleaned[column].isin([0, 1])
            cleaned.loc[invalid_accident, column] = np.nan
            range_failures |= invalid_accident

        invalid_counts[column] = int((conversion_failures | range_failures).sum())

    missing_critical = [column for column in CRITICAL_COLUMNS if cleaned[column].isna().any()]
    if missing_critical:
        raise ValueError(
            "Critical analysis fields contain missing or invalid values after validation: "
            + ", ".join(missing_critical)
        )

    return cleaned, invalid_counts


def _fill_group_medians(
    frame: pd.DataFrame,
    column: str,
    group_levels: tuple[tuple[str, ...], ...],
    final_group: str | None = None,
) -> pd.Series:
    """Fill a numeric series using progressively broader peer-group medians."""

    filled = frame[column].copy()
    for keys in group_levels:
        medians = (
            frame.assign(**{column: filled})
            .groupby(
                list(keys),
                dropna=False,
                observed=True,
            )[column]
            .transform("median")
        )
        filled = filled.fillna(medians)

    if final_group is not None:
        medians = (
            frame.assign(**{column: filled})
            .groupby(
                final_group,
                dropna=False,
                observed=True,
            )[column]
            .transform("median")
        )
        filled = filled.fillna(medians)

    return filled.fillna(filled.median())


def _impute_numeric_specifications(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Impute specifications within comparable groups and preserve audit flags."""

    cleaned = frame.copy()
    imputation_counts: dict[str, int] = {}

    # Engine displacement is structurally zero for Electric records in this
    # dataset. ICE records use progressively broader engine peer groups.
    engine_missing = cleaned["engine_size"].isna()
    electric = cleaned["fuel_type"].eq("Electric")
    cleaned.loc[engine_missing & electric, "engine_size"] = 0.0
    cleaned["engine_size"] = _fill_group_medians(
        cleaned,
        "engine_size",
        (
            ("make", "model", "fuel_type"),
            ("make", "fuel_type"),
            ("fuel_type", "body_type"),
        ),
        final_group="fuel_type",
    )
    cleaned["engine_size_was_imputed"] = engine_missing
    imputation_counts["engine_size"] = int(engine_missing.sum())

    # Performance specifications are filled using vehicle peers before brand
    # and broad body/fuel fallbacks.
    for column in ("horsepower", "torque"):
        missing = cleaned[column].isna()
        cleaned[column] = _fill_group_medians(
            cleaned,
            column,
            (
                ("make", "model", "fuel_type"),
                ("make", "fuel_type"),
                ("fuel_type", "body_type"),
            ),
            final_group="fuel_type",
        ).round(1)
        cleaned[f"{column}_was_imputed"] = missing
        imputation_counts[column] = int(missing.sum())

    # MPG and MPGe are different scales, so fuel efficiency never falls back
    # across fuel type until same-unit group options have been exhausted.
    efficiency_missing = cleaned["fuel_efficiency"].isna()
    cleaned["efficiency_unit"] = np.where(
        cleaned["fuel_type"].eq("Electric"),
        "MPGe",
        "MPG",
    )
    cleaned["fuel_efficiency"] = _fill_group_medians(
        cleaned,
        "fuel_efficiency",
        (
            ("fuel_type", "make", "model"),
            ("fuel_type", "body_type"),
            ("fuel_type",),
        ),
        final_group="efficiency_unit",
    ).round(1)
    cleaned["fuel_efficiency_was_imputed"] = efficiency_missing
    imputation_counts["fuel_efficiency"] = int(efficiency_missing.sum())

    return cleaned, imputation_counts


def _accident_labels(values: pd.Series) -> pd.Series:
    """Convert 0/1 accident history into an explicit three-state label."""

    labels = pd.Series("Unknown", index=values.index, dtype="string")
    labels.loc[values.eq(0)] = "No Accident"
    labels.loc[values.eq(1)] = "Accident Reported"
    return labels


def _quality_flag_text(frame: pd.DataFrame) -> pd.Series:
    """Build a readable semicolon-separated reason list for flagged rows."""

    reasons = pd.Series("", index=frame.index, dtype="string")
    flag_labels = (
        ("is_price_floor", "Price floor"),
        ("is_mileage_floor_review", "Mileage floor review"),
        ("is_high_mileage", "High mileage"),
        ("is_ev_manual", "EV/manual anomaly"),
    )
    for column, label in flag_labels:
        reasons = reasons.mask(
            frame[column] & reasons.eq(""),
            label,
        )
        reasons = reasons.mask(
            frame[column] & reasons.ne("") & ~reasons.str.contains(label, regex=False),
            reasons + "; " + label,
        )
    return reasons.mask(reasons.eq(""), "No flags")


def _engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add documented, analysis-ready fields without using transaction dates."""

    cleaned = frame.copy()
    reference_year = int(cleaned["year"].max())
    cleaned["vehicle_age"] = (reference_year - cleaned["year"]).clip(lower=0).astype(int)
    cleaned["age_band"] = pd.cut(
        cleaned["vehicle_age"],
        bins=[-0.001, 3, 6, 11, 16, np.inf],
        labels=["0-2 years", "3-5 years", "6-10 years", "11-15 years", "16+ years"],
        right=False,
    ).astype("string")
    cleaned["price_band"] = pd.cut(
        cleaned["selling_price"],
        bins=[-np.inf, 5_000, 10_000, 20_000, 30_000, 50_000, np.inf],
        labels=["<$5K", "$5K-$10K", "$10K-$20K", "$20K-$30K", "$30K-$50K", "$50K+"],
        right=False,
    ).astype("string")
    cleaned["mileage_band"] = pd.cut(
        cleaned["mileage"],
        bins=[-np.inf, 25_000, 50_000, 100_000, 150_000, 200_000, np.inf],
        labels=["<25K", "25K-50K", "50K-100K", "100K-150K", "150K-200K", "200K+"],
        right=False,
    ).astype("string")
    cleaned["mileage_per_year"] = (cleaned["mileage"] / (cleaned["vehicle_age"] + 1)).round(0)

    cleaned["is_price_floor"] = cleaned["selling_price"].eq(500)
    cleaned["is_mileage_floor"] = cleaned["mileage"].eq(100)
    cleaned["is_mileage_floor_review"] = cleaned["is_mileage_floor"] & cleaned["vehicle_age"].gt(2)
    cleaned["is_high_mileage"] = cleaned["mileage"].gt(300_000)
    cleaned["is_ev_manual"] = cleaned["fuel_type"].eq("Electric") & cleaned["transmission"].eq(
        "Manual"
    )
    cleaned["needs_quality_review"] = cleaned[
        [
            "is_price_floor",
            "is_mileage_floor_review",
            "is_high_mileage",
            "is_ev_manual",
        ]
    ].any(axis=1)
    cleaned["quality_flags"] = _quality_flag_text(cleaned)
    return cleaned


def _to_builtin(value: Any) -> Any:
    """Convert NumPy/pandas scalars into JSON-serializable Python values."""

    if isinstance(value, dict):
        return {str(key): _to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_builtin(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def clean_automobile_data(raw: pd.DataFrame) -> CleaningResult:
    """Clean a raw automobile DataFrame and return its quality audit.

    The numbered sections intentionally mirror the documented portfolio
    workflow so a reviewer can audit each transformation independently.
    """

    if raw.empty:
        raise ValueError("The source dataset contains no rows.")

    # STEP 1 — Validate and normalize the source schema.
    frame = _normalise_headers(raw)
    source_row_count = len(frame)

    # STEP 2 — Standardize text while preserving true missing values.
    frame = _normalise_text(frame)

    # STEP 3 — Remove only exact duplicates. Similar-looking listings cannot be
    # deduplicated safely because the source has no VIN or listing ID.
    duplicate_mask = frame.duplicated(keep="first")
    duplicates_removed = int(duplicate_mask.sum())
    frame = frame.loc[~duplicate_mask].reset_index(drop=True)

    # STEP 4 — Record source missingness before any imputation or Unknown fill.
    source_missing_flags: dict[str, pd.Series] = {}
    for column in SOURCE_COLUMNS:
        source_missing_flags[column] = frame[column].isna()
        frame[f"{column}_was_missing"] = source_missing_flags[column]
    source_missing_by_column = {
        column: int(flag.sum()) for column, flag in source_missing_flags.items()
    }
    source_missing_cells = int(sum(source_missing_by_column.values()))

    # STEP 5 — Coerce numeric fields and validate defensible physical ranges.
    frame, invalid_numeric_counts = _coerce_and_validate_numeric(frame)
    for column, count in invalid_numeric_counts.items():
        if count:
            frame.loc[frame[column].isna(), f"{column}_was_missing"] = True

    # STEP 6 — Keep missing business categories visible instead of mode-filling
    # them, which would artificially change portfolio shares and rates.
    frame["accident_history"] = _accident_labels(frame["accident_history"])
    for column in UNKNOWN_CATEGORY_COLUMNS:
        frame[column] = frame[column].fillna("Unknown")
    for column in ("year", "mileage", "owners", "selling_price"):
        frame[column] = frame[column].astype("int64")

    # STEP 7 — Impute only numeric vehicle specifications, using peer medians,
    # and add explicit flags so downstream consumers can exclude imputed values.
    frame, imputation_counts = _impute_numeric_specifications(frame)

    # STEP 8 — Add business features and source-system quality flags.
    source_missing_columns = [f"{column}_was_missing" for column in SOURCE_COLUMNS]
    frame["source_missing_count"] = frame[source_missing_columns].sum(axis=1).astype(int)
    frame["row_completeness_pct"] = (
        100 * (1 - frame["source_missing_count"] / len(SOURCE_COLUMNS))
    ).round(2)
    frame["is_fully_complete_source"] = frame["source_missing_count"].eq(0)
    frame = _engineer_features(frame)

    # STEP 9 — Assign a deterministic row identifier. It is a surrogate key,
    # not a VIN and not evidence that two similar rows are the same vehicle.
    frame.insert(
        0,
        "vehicle_id",
        [f"AUTO-{number:06d}" for number in range(1, len(frame) + 1)],
    )

    # STEP 10 — Run final validation and build an audit report.
    unresolved_numeric = [
        column
        for column in ("engine_size", "horsepower", "torque", "fuel_efficiency")
        if frame[column].isna().any()
    ]
    if unresolved_numeric:
        raise ValueError(
            "Numeric imputation left unresolved values in: " + ", ".join(unresolved_numeric)
        )
    if frame["vehicle_id"].duplicated().any():
        raise ValueError("Generated vehicle_id values are not unique.")

    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_rows": source_row_count,
        "output_rows": len(frame),
        "source_columns": len(SOURCE_COLUMNS),
        "output_columns": len(frame.columns),
        "exact_duplicates_removed": duplicates_removed,
        "source_missing_cells": source_missing_cells,
        "source_missing_pct": round(
            100 * source_missing_cells / (len(frame) * len(SOURCE_COLUMNS)),
            2,
        ),
        "source_cell_completeness_pct": round(
            100 * (1 - source_missing_cells / (len(frame) * len(SOURCE_COLUMNS))),
            2,
        ),
        "fully_complete_source_rows": int(frame["is_fully_complete_source"].sum()),
        "fully_complete_source_rows_pct": round(
            100 * frame["is_fully_complete_source"].mean(),
            2,
        ),
        "source_missing_by_column": source_missing_by_column,
        "invalid_numeric_by_column": invalid_numeric_counts,
        "imputed_by_column": imputation_counts,
        "unknown_category_counts": {
            column: int(frame[column].eq("Unknown").sum())
            for column in (*UNKNOWN_CATEGORY_COLUMNS, "accident_history")
        },
        "quality_flags": {
            "price_floor_500": int(frame["is_price_floor"].sum()),
            "mileage_floor_100": int(frame["is_mileage_floor"].sum()),
            "mileage_floor_review": int(frame["is_mileage_floor_review"].sum()),
            "high_mileage_over_300k": int(frame["is_high_mileage"].sum()),
            "electric_manual_anomaly": int(frame["is_ev_manual"].sum()),
            "rows_needing_review": int(frame["needs_quality_review"].sum()),
        },
        "reference_model_year": int(frame["year"].max()),
        "validation": {
            "vehicle_id_unique": bool(frame["vehicle_id"].is_unique),
            "critical_fields_complete": bool(frame[list(CRITICAL_COLUMNS)].notna().all().all()),
            "numeric_imputation_complete": not unresolved_numeric,
            "all_electric_engine_sizes_zero": bool(
                frame.loc[frame["fuel_type"].eq("Electric"), "engine_size"].eq(0).all()
            ),
        },
    }

    # Keep business fields first and audit fields grouped after them.
    derived_columns = [
        "efficiency_unit",
        "vehicle_age",
        "age_band",
        "price_band",
        "mileage_band",
        "mileage_per_year",
        "source_missing_count",
        "row_completeness_pct",
        "is_fully_complete_source",
        "is_price_floor",
        "is_mileage_floor",
        "is_mileage_floor_review",
        "is_high_mileage",
        "is_ev_manual",
        "needs_quality_review",
        "quality_flags",
    ]
    missing_flags = [f"{column}_was_missing" for column in SOURCE_COLUMNS]
    imputation_flags = [
        "engine_size_was_imputed",
        "horsepower_was_imputed",
        "torque_was_imputed",
        "fuel_efficiency_was_imputed",
    ]
    ordered = [
        "vehicle_id",
        *SOURCE_COLUMNS,
        *derived_columns,
        *missing_flags,
        *imputation_flags,
    ]
    frame = frame.loc[:, list(dict.fromkeys(ordered))]
    return CleaningResult(data=frame, report=_to_builtin(report))


def run_cleaning_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    report_path: str | Path,
) -> CleaningResult:
    """Read, clean, validate, and export the automobile dataset."""

    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Raw dataset not found: {source.resolve()}")

    raw = pd.read_csv(source)
    result = clean_automobile_data(raw)

    destination = Path(output_path)
    quality_report = Path(report_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    quality_report.parent.mkdir(parents=True, exist_ok=True)

    result.data.to_csv(destination, index=False)
    quality_report.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result
