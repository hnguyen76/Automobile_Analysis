"""Command-line entry point for the automobile data-cleaning pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from automobile_analysis.cleaning import run_cleaning_pipeline  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line interface with reproducible default paths."""

    parser = argparse.ArgumentParser(
        description=(
            "Clean the raw automobile CSV, engineer analysis features, and "
            "write a JSON data-quality report."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "automobile_dataset.csv",
        help="Path to the raw CSV dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "automobile_cleaned.csv",
        help="Path for the cleaned CSV.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "reports" / "data_quality_report.json",
        help="Path for the JSON data-quality report.",
    )
    return parser


def main() -> int:
    """Run the pipeline and print a concise verification summary."""

    args = build_parser().parse_args()
    result = run_cleaning_pipeline(args.input, args.output, args.report)
    report = result.report

    print("Automobile cleaning pipeline completed.")
    print(f"  Source rows:       {report['source_rows']:,}")
    print(f"  Output rows:       {report['output_rows']:,}")
    print(f"  Duplicates removed:{report['exact_duplicates_removed']:>6,}")
    print(f"  Cell completeness:{report['source_cell_completeness_pct']:>8.2f}%")
    print(f"  Cleaned dataset:   {args.output.resolve()}")
    print(f"  Quality report:    {args.report.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
