"""Pure analytics helpers for the Streamlit automobile dashboard.

The functions in this module deliberately keep business calculations separate
from the presentation layer.  They accept ordinary pandas ``DataFrame``
objects, which makes the metrics easy to audit and reuse outside Streamlit.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd

BASE_COLUMNS: tuple[str, ...] = (
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

REQUIRED_COLUMNS: tuple[str, ...] = (
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

CATEGORICAL_COLUMNS: tuple[str, ...] = (
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
    "fuel_efficiency",
    "selling_price",
)

AGE_BAND_ORDER: tuple[str, ...] = (
    "0–2 years",
    "3–5 years",
    "6–10 years",
    "11–15 years",
    "16+ years",
)

PRICE_BAND_ORDER: tuple[str, ...] = (
    "<$5K",
    "$5K–$10K",
    "$10K–$20K",
    "$20K–$30K",
    "$30K–$50K",
    "$50K+",
)

MILEAGE_BAND_ORDER: tuple[str, ...] = (
    "<25K",
    "25K–50K",
    "50K–100K",
    "100K–150K",
    "150K–200K",
    "200K+",
)

UNKNOWN_TOKENS = frozenset(
    {
        "",
        "nan",
        "none",
        "null",
        "na",
        "n/a",
        "unknown",
        "missing",
        "not available",
        "unspecified",
    }
)


def _normalise_column_name(value: Any) -> str:
    """Convert a source header to a predictable snake_case name."""

    name = re.sub(r"[^0-9A-Za-z]+", "_", str(value).strip())
    return re.sub(r"_+", "_", name).strip("_").lower()


def _is_unknown(series: pd.Series) -> pd.Series:
    """Return a boolean mask for null or explicit unknown values."""

    text = series.astype("string").str.strip().str.lower()
    return series.isna() | text.isin(UNKNOWN_TOKENS)


def _coerce_flag(series: pd.Series) -> pd.Series:
    """Coerce common flag encodings to booleans without raising."""

    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    numeric = pd.to_numeric(series, errors="coerce")
    truthy_text = (
        series.astype("string")
        .str.strip()
        .str.lower()
        .isin({"true", "yes", "y", "1", "missing", "imputed"})
    )
    return numeric.fillna(0).ne(0) | truthy_text


def _source_missing_mask(frame: pd.DataFrame, column: str) -> pd.Series:
    """Recover source missingness from values or common audit flag names."""

    if column in frame:
        missing = _is_unknown(frame[column])
    else:
        missing = pd.Series(True, index=frame.index, dtype=bool)

    flag_names = (
        f"{column}_was_missing",
        f"was_missing_{column}",
        f"{column}_was_imputed",
        f"{column}_missing",
        f"missing_{column}",
        f"{column}_imputed",
        f"is_{column}_missing",
    )
    for flag_name in flag_names:
        if flag_name in frame:
            missing = missing | _coerce_flag(frame[flag_name])
    return missing.astype(bool)


def _normalise_accident_label(series: pd.Series) -> pd.Series:
    """Map numeric or textual accident values to No / Yes / Unknown."""

    numeric = pd.to_numeric(series, errors="coerce")
    text = series.astype("string").str.strip().str.lower()

    labels = pd.Series("Unknown", index=series.index, dtype="string")
    labels.loc[numeric.eq(0) | text.isin({"no", "none", "false", "no accident"})] = "No"
    labels.loc[
        numeric.eq(1) | text.isin({"yes", "true", "accident", "accident reported", "reported"})
    ] = "Yes"
    labels.loc[_is_unknown(series)] = "Unknown"
    return labels


def prepare_dashboard_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate and enrich the cleaned dataset for dashboard consumption.

    The cleaning pipeline is expected to produce snake_case columns.  This
    function still normalises headers defensively so an actionable validation
    message can be shown instead of a cryptic chart error.
    """

    if raw.empty:
        raise ValueError("The cleaned dataset contains no rows.")

    frame = raw.copy()
    normalised_columns = [_normalise_column_name(column) for column in frame.columns]
    if len(set(normalised_columns)) != len(normalised_columns):
        raise ValueError(
            "Normalising the cleaned dataset headers creates duplicate column names. "
            "Review the cleaning pipeline output."
        )
    frame.columns = normalised_columns

    aliases = {
        "price": "selling_price",
        "sellingprice": "selling_price",
        "fuel": "fuel_type",
        "body_style": "body_type",
        "service": "service_history",
        "accident": "accident_history",
        "state": "location",
    }
    for source, target in aliases.items():
        if target not in frame and source in frame:
            frame = frame.rename(columns={source: target})

    missing_required = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing_required:
        missing_list = ", ".join(missing_required)
        raise ValueError(
            "The cleaned dataset is missing required dashboard columns: "
            f"{missing_list}. Re-run or review the cleaning pipeline."
        )

    # Preserve source-level missingness before converting null categories into
    # a visible "Unknown" bucket.
    for column in BASE_COLUMNS:
        frame[f"__missing_{column}"] = _source_missing_mask(frame, column)

    for column in NUMERIC_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    for column in CATEGORICAL_COLUMNS:
        if column not in frame:
            frame[column] = "Unknown"
        values = frame[column].astype("string").str.strip()
        frame[column] = values.mask(_is_unknown(values), "Unknown").astype(str)

    if "accident_history" not in frame:
        frame["accident_history"] = np.nan
    frame["accident_label"] = _normalise_accident_label(frame["accident_history"]).astype(str)

    if "service_history" not in frame:
        frame["service_history"] = "Unknown"
    if "transmission" not in frame:
        frame["transmission"] = "Unknown"
    if "location" not in frame:
        frame["location"] = "Unknown"

    finite_years = frame["year"].dropna()
    if finite_years.empty:
        raise ValueError("The cleaned dataset does not contain any valid model years.")
    reference_year = int(finite_years.max())
    frame["vehicle_age"] = (reference_year - frame["year"]).clip(lower=0)
    frame["age_band"] = pd.cut(
        frame["vehicle_age"],
        bins=[-0.001, 3, 6, 11, 16, np.inf],
        labels=AGE_BAND_ORDER,
        right=False,
        ordered=True,
    )

    frame["price_band"] = pd.cut(
        frame["selling_price"],
        bins=[-np.inf, 5_000, 10_000, 20_000, 30_000, 50_000, np.inf],
        labels=PRICE_BAND_ORDER,
        right=False,
        ordered=True,
    )
    frame["mileage_band"] = pd.cut(
        frame["mileage"],
        bins=[-np.inf, 25_000, 50_000, 100_000, 150_000, 200_000, np.inf],
        labels=MILEAGE_BAND_ORDER,
        right=False,
        ordered=True,
    )

    existing_price_flag = next(
        (
            name
            for name in ("is_price_floor", "price_floor_flag", "selling_price_floor_flag")
            if name in frame
        ),
        None,
    )
    if existing_price_flag:
        frame["is_price_floor"] = _coerce_flag(frame[existing_price_flag])
    else:
        frame["is_price_floor"] = frame["selling_price"].eq(500)

    existing_mileage_flag = next(
        (name for name in ("is_mileage_floor", "mileage_floor_flag") if name in frame),
        None,
    )
    if existing_mileage_flag:
        frame["is_mileage_floor"] = _coerce_flag(frame[existing_mileage_flag])
    else:
        frame["is_mileage_floor"] = frame["mileage"].eq(100)

    missing_columns = [f"__missing_{column}" for column in BASE_COLUMNS]
    frame["missing_field_count"] = frame[missing_columns].sum(axis=1).astype(int)
    frame["row_completeness_pct"] = (1 - frame["missing_field_count"] / len(BASE_COLUMNS)) * 100
    frame["model_year_reference"] = reference_year
    return frame


def apply_filters(
    frame: pd.DataFrame,
    selections: Mapping[str, Iterable[Any]] | None = None,
    year_range: tuple[int, int] | None = None,
    price_range: tuple[float, float] | None = None,
    *,
    exclude_price_floor: bool = False,
) -> pd.DataFrame:
    """Apply dashboard slicers and return a copy of the matching rows."""

    mask = pd.Series(True, index=frame.index, dtype=bool)
    if exclude_price_floor and "is_price_floor" in frame:
        mask &= ~frame["is_price_floor"].fillna(False)

    if year_range is not None:
        lower_year, upper_year = year_range
        mask &= frame["year"].between(lower_year, upper_year, inclusive="both")

    if price_range is not None:
        lower_price, upper_price = price_range
        mask &= frame["selling_price"].between(lower_price, upper_price, inclusive="both")

    for column, values in (selections or {}).items():
        selected = list(values)
        if selected and column in frame:
            mask &= frame[column].isin(selected)

    return frame.loc[mask].copy()


def calculate_kpis(frame: pd.DataFrame, reference: pd.DataFrame | None = None) -> dict[str, float]:
    """Calculate headline portfolio measures for the current filter context."""

    if frame.empty:
        return {
            "vehicle_count": 0.0,
            "listing_value": 0.0,
            "average_price": np.nan,
            "median_price": np.nan,
            "average_mileage": np.nan,
            "no_accident_rate": np.nan,
            "average_price_delta": np.nan,
            "selection_share": 0.0,
        }

    known_accidents = frame["accident_label"].isin({"No", "Yes"})
    known_count = int(known_accidents.sum())
    no_accident_rate = (
        frame.loc[known_accidents, "accident_label"].eq("No").mean() if known_count else np.nan
    )

    average_price = frame["selling_price"].mean()
    reference_frame = reference if reference is not None and not reference.empty else frame
    reference_average = reference_frame["selling_price"].mean()
    price_delta = (
        average_price / reference_average - 1
        if pd.notna(reference_average) and reference_average != 0
        else np.nan
    )

    return {
        "vehicle_count": float(len(frame)),
        "listing_value": float(frame["selling_price"].sum()),
        "average_price": float(average_price),
        "median_price": float(frame["selling_price"].median()),
        "average_mileage": float(frame["mileage"].mean()),
        "no_accident_rate": float(no_accident_rate),
        "average_price_delta": float(price_delta),
        "selection_share": float(len(frame) / len(reference_frame)),
    }


def data_quality_summary(
    frame: pd.DataFrame,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Return audit-friendly data-quality KPIs and field-level missingness."""

    if frame.empty:
        empty = pd.DataFrame(columns=["field", "missing_count", "missing_pct"])
        return {
            "cell_completeness": np.nan,
            "complete_row_rate": np.nan,
            "price_floor_rate": np.nan,
            "mileage_floor_rate": np.nan,
            "duplicate_rows": 0.0,
        }, empty

    field_rows: list[dict[str, float | str]] = []
    total_missing = 0
    for column in BASE_COLUMNS:
        flag_name = f"__missing_{column}"
        missing_count = (
            int(frame[flag_name].fillna(False).sum())
            if flag_name in frame
            else int(frame[column].isna().sum())
        )
        total_missing += missing_count
        field_rows.append(
            {
                "field": column.replace("_", " ").title(),
                "missing_count": missing_count,
                "missing_pct": missing_count / len(frame),
            }
        )

    field_table = pd.DataFrame(field_rows).sort_values(
        ["missing_pct", "field"], ascending=[False, True], ignore_index=True
    )
    canonical = [column for column in BASE_COLUMNS if column in frame]
    duplicate_rows = int(frame[canonical].duplicated().sum()) if canonical else 0

    metrics = {
        "cell_completeness": float(1 - total_missing / (len(frame) * len(BASE_COLUMNS))),
        "complete_row_rate": float(frame["missing_field_count"].eq(0).mean()),
        "price_floor_rate": float(frame["is_price_floor"].fillna(False).mean()),
        "mileage_floor_rate": float(frame["is_mileage_floor"].fillna(False).mean()),
        "duplicate_rows": float(duplicate_rows),
    }
    return metrics, field_table


def _safe_correlation(left: pd.Series, right: pd.Series) -> float:
    aligned = pd.concat([left, right], axis=1).dropna()
    if len(aligned) < 3 or aligned.iloc[:, 0].nunique() < 2:
        return np.nan
    if aligned.iloc[:, 1].nunique() < 2:
        return np.nan
    return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))


def business_insights(frame: pd.DataFrame, reference: pd.DataFrame) -> list[dict[str, str]]:
    """Generate concise, filter-aware observations without causal language."""

    if frame.empty:
        return []

    insights: list[dict[str, str]] = []
    kpis = calculate_kpis(frame, reference)
    selected_share = kpis["selection_share"]
    delta = kpis["average_price_delta"]

    if pd.notna(delta):
        direction = "above" if delta >= 0 else "below"
        insights.append(
            {
                "title": "Portfolio position",
                "body": (
                    f"The selection contains {len(frame):,} vehicles "
                    f"({selected_share:.1%} of the full dataset). Its average asking "
                    f"price is {abs(delta):.1%} {direction} the unfiltered portfolio."
                ),
                "tone": "blue",
            }
        )

    make_counts = frame["make"].value_counts()
    if not make_counts.empty:
        lead_make = str(make_counts.index[0])
        lead_count = int(make_counts.iloc[0])
        lead_share = lead_count / len(frame)
        insights.append(
            {
                "title": "Largest selected brand",
                "body": (
                    f"{lead_make} represents {lead_count:,} vehicles "
                    f"({lead_share:.1%} of the current selection)."
                ),
                "tone": "teal",
            }
        )

    candidates = {
        "model year": _safe_correlation(frame["year"], frame["selling_price"]),
        "mileage": _safe_correlation(frame["mileage"], frame["selling_price"]),
        "owner count": _safe_correlation(frame["owners"], frame["selling_price"]),
    }
    finite_candidates = {label: value for label, value in candidates.items() if pd.notna(value)}
    if finite_candidates:
        strongest_label, strongest_value = max(
            finite_candidates.items(), key=lambda item: abs(item[1])
        )
        relationship = "positive" if strongest_value >= 0 else "negative"
        insights.append(
            {
                "title": "Strongest simple price relationship",
                "body": (
                    f"{strongest_label.title()} has the strongest bivariate "
                    f"association with asking price in this selection "
                    f"(r={strongest_value:.2f}, {relationship}). Correlation is not "
                    "a causal effect."
                ),
                "tone": "amber",
            }
        )

    accident = (
        frame.loc[frame["accident_label"].isin({"No", "Yes"})]
        .groupby("accident_label", observed=True)["selling_price"]
        .agg(["size", "mean"])
    )
    if {"No", "Yes"}.issubset(accident.index) and accident.loc[:, "size"].min() >= 10:
        no_average = float(accident.loc["No", "mean"])
        yes_average = float(accident.loc["Yes", "mean"])
        if no_average:
            gap = yes_average / no_average - 1
            direction = "lower" if gap < 0 else "higher"
            insights.append(
                {
                    "title": "Accident-history association",
                    "body": (
                        "Vehicles with a reported accident have an average price "
                        f"{abs(gap):.1%} {direction} than vehicles with no reported "
                        "accident in the current selection. Age and mileage mix can "
                        "also explain part of this gap."
                    ),
                    "tone": "coral",
                }
            )

    floor_rate = float(frame["is_price_floor"].fillna(False).mean())
    if floor_rate > 0:
        insights.append(
            {
                "title": "Sensitivity reminder",
                "body": (
                    f"{floor_rate:.1%} of selected records sit exactly at the $500 "
                    "observed price floor. Use the sidebar sensitivity toggle to "
                    "test how those records affect price metrics."
                ),
                "tone": "slate",
            }
        )

    return insights[:5]


def format_currency(value: float, *, decimals: int = 1) -> str:
    """Format a dashboard currency value compactly."""

    if pd.isna(value):
        return "—"
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:.{decimals}f}B"
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:.{decimals}f}M"
    if absolute >= 1_000:
        return f"${value / 1_000:.{decimals}f}K"
    return f"${value:,.0f}"


def format_compact_number(value: float, *, decimals: int = 1) -> str:
    """Format a count or distance without implying currency."""

    if pd.isna(value):
        return "—"
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    return f"{value:,.0f}"
