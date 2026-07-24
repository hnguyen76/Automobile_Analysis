"""Regression checks for important dashboard visual-layer contracts."""

from __future__ import annotations

import json

from streamlit.testing.v1 import AppTest


def test_price_lines_render_above_inventory_columns() -> None:
    """Average and median price must remain readable over the vehicle bars."""

    app = AppTest.from_file("app.py", default_timeout=60).run()
    assert not app.exception

    year_profile = json.loads(app.get("plotly_chart")[0].proto.spec)
    traces = {trace["name"]: trace for trace in year_profile["data"]}
    vehicles = traces["Vehicles"]
    average = traces["Average price"]
    median = traces["Median price"]

    assert vehicles["opacity"] <= 0.5
    assert vehicles["zorder"] < average["zorder"] < median["zorder"]
    assert average["line"]["width"] >= 4
    assert median["line"]["width"] >= 3
