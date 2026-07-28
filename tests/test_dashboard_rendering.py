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

    assert vehicles["opacity"] == 0.85
    assert vehicles["zorder"] < average["zorder"] < median["zorder"]
    assert average["line"]["width"] >= 4
    assert median["line"]["width"] >= 3


def test_cockpit_tooltip_uses_readable_contrast() -> None:
    """Cockpit hover labels must not use light text on a light background."""

    app = AppTest.from_file("app.py", default_timeout=60).run()
    app.radio[0].set_value("Automotive Cockpit").run()
    assert not app.exception

    year_profile = json.loads(app.get("plotly_chart")[0].proto.spec)
    hoverlabel = year_profile["layout"]["hoverlabel"]
    legend = year_profile["layout"]["legend"]

    assert hoverlabel["bgcolor"] == "#050A0D"
    assert hoverlabel["font"]["color"] == "#EAF7FF"
    assert hoverlabel["bordercolor"] == "#00D9FF"
    assert legend["font"]["color"] == "#EAF7FF"
    assert legend["bgcolor"] == "rgba(5,10,13,0.88)"
    assert legend["borderwidth"] == 1
