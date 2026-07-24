"""Regression tests for dashboard data preparation and KPI calculations."""

from __future__ import annotations

import pandas as pd
import pytest

from src.automobile_analysis.analytics import (
    apply_filters,
    calculate_kpis,
    data_quality_summary,
    prepare_dashboard_data,
)


def dashboard_source() -> pd.DataFrame:
    """Return cleaned-shaped rows with numeric and textual accident states."""

    return pd.DataFrame(
        {
            "make": ["Toyota", "Ford", "Nissan"],
            "model": ["Camry", "F-150", "Leaf"],
            "year": [2024, 2020, 2022],
            "fuel_type": ["Petrol", "Diesel", "Electric"],
            "transmission": ["Automatic", "Automatic", "Unknown"],
            "engine_size": [2.0, 3.0, 0.0],
            "mileage": [10_000, 75_000, 20_000],
            "horsepower": [180, 300, 210],
            "torque": [170, 350, 220],
            "owners": [1, 2, 1],
            "accident_history": [
                "No Accident",
                "Accident Reported",
                "Unknown",
            ],
            "service_history": ["Full Service", "Partial Service", "Unknown"],
            "color": ["Blue", "Black", "White"],
            "body_type": ["Sedan", "Truck", "Hatchback"],
            "drivetrain": ["FWD", "4WD", "FWD"],
            "fuel_efficiency": [35, 25, 110],
            "location": ["NY", "TX", "Unknown"],
            "selling_price": [25_000, 500, 24_000],
            "accident_history_was_missing": [False, False, True],
            "transmission_was_missing": [False, False, True],
        }
    )


def test_textual_accident_labels_survive_dashboard_preparation() -> None:
    prepared = prepare_dashboard_data(dashboard_source())

    assert prepared["accident_label"].tolist() == ["No", "Yes", "Unknown"]
    assert calculate_kpis(prepared)["no_accident_rate"] == pytest.approx(0.5)


def test_quality_summary_uses_preserved_source_flags() -> None:
    prepared = prepare_dashboard_data(dashboard_source())
    metrics, missingness = data_quality_summary(prepared)

    accident_row = missingness.loc[missingness["field"].eq("Accident History")].iloc[0]
    assert accident_row["missing_count"] == 1
    assert metrics["complete_row_rate"] < 1
    assert metrics["price_floor_rate"] == pytest.approx(1 / 3)


def test_filtering_excludes_price_floor_without_mutating_source() -> None:
    prepared = prepare_dashboard_data(dashboard_source())
    filtered = apply_filters(prepared, exclude_price_floor=True)

    assert len(filtered) == 2
    assert not filtered["selling_price"].eq(500).any()
    assert len(prepared) == 3
