"""Focused tests for the automobile cleaning rules."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.automobile_analysis.cleaning import (
    clean_automobile_data,
    run_cleaning_pipeline,
)


def sample_raw_data() -> pd.DataFrame:
    """Return a compact source frame with missing values and one duplicate."""

    rows = [
        {
            "Make": "Ford",
            "Model": "Mustang",
            "Year": 2024,
            "Fuel_Type": "Petrol",
            "Transmission": "Automatic",
            "Engine_Size": 3.0,
            "Mileage": 100,
            "Horsepower": 300,
            "Torque": 280,
            "Owners": 1,
            "Accident_History": 0,
            "Service_History": "Full Service",
            "Color": "Blue",
            "Body_Type": "Coupe",
            "Drivetrain": "RWD",
            "Fuel_Efficiency": 25,
            "Location": "NY",
            "Selling_Price": 35_000,
        },
        {
            "Make": "Ford",
            "Model": "Mustang",
            "Year": 2015,
            "Fuel_Type": "Electric",
            "Transmission": "Manual",
            "Engine_Size": None,
            "Mileage": 100,
            "Horsepower": None,
            "Torque": None,
            "Owners": 2,
            "Accident_History": None,
            "Service_History": None,
            "Color": None,
            "Body_Type": "Coupe",
            "Drivetrain": "RWD",
            "Fuel_Efficiency": None,
            "Location": None,
            "Selling_Price": 500,
        },
        {
            "Make": "Nissan",
            "Model": "Leaf",
            "Year": 2022,
            "Fuel_Type": "Electric",
            "Transmission": "Automatic",
            "Engine_Size": 0,
            "Mileage": 20_000,
            "Horsepower": 210,
            "Torque": 220,
            "Owners": 1,
            "Accident_History": 1,
            "Service_History": "Partial Service",
            "Color": "White",
            "Body_Type": "Hatchback",
            "Drivetrain": "FWD",
            "Fuel_Efficiency": 110,
            "Location": "CA",
            "Selling_Price": 24_000,
        },
        {
            "Make": "Toyota",
            "Model": "Camry",
            "Year": 2019,
            "Fuel_Type": "Petrol",
            "Transmission": None,
            "Engine_Size": None,
            "Mileage": 80_000,
            "Horsepower": None,
            "Torque": 180,
            "Owners": 2,
            "Accident_History": 0,
            "Service_History": "No Service",
            "Color": "Gray",
            "Body_Type": "Sedan",
            "Drivetrain": "FWD",
            "Fuel_Efficiency": 33,
            "Location": "TX",
            "Selling_Price": 15_000,
        },
    ]
    rows.append(rows[0].copy())
    return pd.DataFrame(rows)


def test_cleaning_retains_unique_rows_and_audit_flags() -> None:
    result = clean_automobile_data(sample_raw_data())
    cleaned = result.data

    assert len(cleaned) == 4
    assert result.report["exact_duplicates_removed"] == 1
    assert cleaned["vehicle_id"].is_unique
    assert cleaned["transmission"].eq("Unknown").sum() == 1
    assert cleaned["accident_history"].isin(["No Accident", "Accident Reported", "Unknown"]).all()
    assert cleaned.loc[cleaned["model"].eq("Mustang"), "is_price_floor"].sum() == 1


def test_numeric_imputation_and_ev_business_rules() -> None:
    cleaned = clean_automobile_data(sample_raw_data()).data
    electric_manual = cleaned.loc[
        cleaned["fuel_type"].eq("Electric") & cleaned["transmission"].eq("Manual")
    ].iloc[0]

    assert electric_manual["engine_size"] == pytest.approx(0)
    assert bool(electric_manual["engine_size_was_imputed"])
    assert bool(electric_manual["horsepower_was_imputed"])
    assert bool(electric_manual["is_ev_manual"])
    assert bool(electric_manual["is_mileage_floor_review"])
    assert electric_manual["efficiency_unit"] == "MPGe"
    assert cleaned[["engine_size", "horsepower", "torque", "fuel_efficiency"]].notna().all().all()


def test_completeness_is_based_on_unmodified_source() -> None:
    cleaned = clean_automobile_data(sample_raw_data()).data
    incomplete = cleaned.loc[
        cleaned["fuel_type"].eq("Electric") & cleaned["transmission"].eq("Manual")
    ].iloc[0]

    assert incomplete["source_missing_count"] == 8
    assert incomplete["row_completeness_pct"] == pytest.approx(55.56, abs=0.01)
    assert not bool(incomplete["is_fully_complete_source"])


def test_pipeline_writes_clean_csv_and_json_report(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.csv"
    output_path = tmp_path / "processed" / "cleaned.csv"
    report_path = tmp_path / "reports" / "quality.json"
    sample_raw_data().to_csv(raw_path, index=False)

    result = run_cleaning_pipeline(raw_path, output_path, report_path)
    exported = pd.read_csv(output_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(exported) == len(result.data)
    assert report["output_rows"] == 4
    assert report["validation"]["vehicle_id_unique"] is True


def test_missing_required_column_has_actionable_error() -> None:
    raw = sample_raw_data().drop(columns=["Selling_Price"])

    with pytest.raises(ValueError, match="selling_price"):
        clean_automobile_data(raw)
