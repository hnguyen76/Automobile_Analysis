"""Interactive Power BI-inspired dashboard for the automobile dataset."""

from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.automobile_analysis.analytics import (
    AGE_BAND_ORDER,
    apply_filters,
    business_insights,
    calculate_kpis,
    data_quality_summary,
    format_compact_number,
    format_currency,
    prepare_dashboard_data,
)

st.set_page_config(
    page_title="Automobile Intelligence | Hieu Nguyen",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded",
)


DATA_PATH = Path(__file__).resolve().parent / "data" / "processed" / "automobile_cleaned.csv"
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}

COLORS = {
    "navy": "#0B1F3A",
    "blue": "#118DFF",
    "blue_dark": "#0A66C2",
    "teal": "#01B8AA",
    "amber": "#F2C80F",
    "coral": "#FD625E",
    "purple": "#8B5CF6",
    "slate": "#64748B",
    "ink": "#182230",
    "muted": "#65758B",
    "border": "#DDE4ED",
    "surface": "#FFFFFF",
    "background": "#F4F6F9",
    "grid": "#E8EDF3",
}

FUEL_COLORS = {
    "Petrol": COLORS["blue"],
    "Diesel": COLORS["amber"],
    "Hybrid": COLORS["teal"],
    "Electric": COLORS["purple"],
    "Unknown": "#A3ACB9",
}
ACCIDENT_COLORS = {
    "No": COLORS["teal"],
    "Yes": COLORS["coral"],
    "Unknown": "#A3ACB9",
}
AGE_COLORS = {
    "0–2 years": COLORS["blue"],
    "3–5 years": COLORS["teal"],
    "6–10 years": COLORS["amber"],
    "11–15 years": "#F59E0B",
    "16+ years": COLORS["coral"],
}


st.markdown(
    f"""
    <style>
        :root {{
            --navy: {COLORS["navy"]};
            --blue: {COLORS["blue"]};
            --teal: {COLORS["teal"]};
            --amber: {COLORS["amber"]};
            --coral: {COLORS["coral"]};
            --ink: {COLORS["ink"]};
            --muted: {COLORS["muted"]};
            --border: {COLORS["border"]};
            --surface: {COLORS["surface"]};
            --background: {COLORS["background"]};
        }}

        html, body, [class*="css"] {{
            font-family: "Segoe UI", Inter, Arial, sans-serif;
            color: var(--ink);
        }}

        .stApp {{
            background:
                radial-gradient(circle at 85% -5%, rgba(17, 141, 255, 0.09), transparent 26rem),
                var(--background);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stAppViewContainer"] > .main .block-container {{
            max-width: 1580px;
            padding: 1.1rem 2rem 2.5rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #081A31 0%, #0B2342 58%, #102B4E 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            color: #F7FAFC;
        }}

        [data-testid="stSidebar"] .stCaptionContainer p {{
            color: #B9C7D8;
        }}

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div {{
            background: rgba(255,255,255,0.96);
            border-color: rgba(255,255,255,0.16);
            color: #14213D;
        }}

        .side-brand {{
            padding: 0.35rem 0 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.12);
            margin-bottom: 0.9rem;
        }}

        .side-brand__eyebrow {{
            color: #73BAFF;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        .side-brand__title {{
            color: #FFFFFF;
            font-size: 1.25rem;
            line-height: 1.22;
            font-weight: 700;
            margin-top: 0.35rem;
        }}

        .side-brand__copy {{
            color: #B9C7D8;
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 0.4rem;
        }}

        .hero {{
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 1.5rem;
            padding: 1.55rem 1.7rem;
            margin-bottom: 1rem;
            border-radius: 16px;
            color: #FFFFFF;
            background:
                linear-gradient(115deg, rgba(11,31,58,1) 0%, rgba(13,58,101,1) 58%, rgba(17,141,255,0.92) 135%);
            box-shadow: 0 12px 32px rgba(11,31,58,0.16);
        }}

        .hero::after {{
            content: "";
            position: absolute;
            width: 18rem;
            height: 18rem;
            border-radius: 50%;
            right: -6rem;
            top: -10rem;
            border: 2.5rem solid rgba(255,255,255,0.06);
        }}

        .hero__content, .hero__meta {{
            position: relative;
            z-index: 1;
        }}

        .hero__eyebrow {{
            display: inline-flex;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.11);
            color: #CFE8FF;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        .hero h1 {{
            margin: 0.5rem 0 0.25rem;
            color: #FFFFFF;
            font-size: clamp(1.7rem, 3vw, 2.45rem);
            line-height: 1.1;
            letter-spacing: -0.035em;
        }}

        .hero p {{
            max-width: 760px;
            margin: 0;
            color: #D8E7F5;
            font-size: 0.93rem;
            line-height: 1.5;
        }}

        .hero__meta {{
            min-width: 170px;
            text-align: right;
        }}

        .hero__meta-value {{
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1;
        }}

        .hero__meta-label {{
            margin-top: 0.35rem;
            color: #D8E7F5;
            font-size: 0.76rem;
        }}

        .context-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0 0 0.9rem;
        }}

        .context-chip {{
            padding: 0.28rem 0.58rem;
            border: 1px solid #D7E1EC;
            border-radius: 999px;
            background: rgba(255,255,255,0.88);
            color: #4A5A70;
            font-size: 0.74rem;
            box-shadow: 0 2px 7px rgba(15,23,42,0.04);
        }}

        .section-heading {{
            margin: 0.55rem 0 0.85rem;
        }}

        .section-heading h2 {{
            margin: 0;
            color: var(--navy);
            font-size: 1.32rem;
            letter-spacing: -0.015em;
        }}

        .section-heading p {{
            margin: 0.22rem 0 0;
            color: var(--muted);
            font-size: 0.84rem;
        }}

        .kpi-card {{
            box-sizing: border-box;
            height: 150px;
            padding: 1rem 1rem 0.9rem;
            border: 1px solid var(--border);
            border-top: 4px solid var(--accent);
            border-radius: 12px;
            background: rgba(255,255,255,0.96);
            box-shadow: 0 6px 18px rgba(15,23,42,0.06);
        }}

        .kpi-card__label {{
            min-height: 2.2em;
            color: #627086;
            font-size: 0.71rem;
            font-weight: 700;
            letter-spacing: 0.045em;
            line-height: 1.35;
            text-transform: uppercase;
        }}

        .kpi-card__value {{
            margin-top: 0.42rem;
            color: var(--navy);
            font-size: clamp(1.4rem, 2.1vw, 1.85rem);
            font-weight: 700;
            letter-spacing: -0.035em;
            line-height: 1;
            white-space: nowrap;
        }}

        .kpi-card__note {{
            margin-top: 0.52rem;
            color: #6C7A8D;
            font-size: 0.72rem;
            line-height: 1.35;
        }}

        .insight-card {{
            height: 100%;
            min-height: 148px;
            padding: 0.95rem 1rem;
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            border-radius: 10px;
            background: #FFFFFF;
            box-shadow: 0 4px 14px rgba(15,23,42,0.045);
        }}

        .insight-card__title {{
            color: var(--navy);
            font-size: 0.82rem;
            font-weight: 700;
        }}

        .insight-card__body {{
            margin-top: 0.42rem;
            color: #5E6D82;
            font-size: 0.78rem;
            line-height: 1.5;
        }}

        .callout {{
            padding: 0.9rem 1rem;
            border: 1px solid #CFE3F8;
            border-radius: 10px;
            background: #F1F8FF;
            color: #34506E;
            font-size: 0.8rem;
            line-height: 1.5;
        }}

        .callout strong {{
            color: var(--navy);
        }}

        [data-baseweb="tab-list"] {{
            gap: 0.35rem;
            padding: 0.28rem;
            border: 1px solid var(--border);
            border-radius: 11px;
            background: rgba(255,255,255,0.82);
        }}

        [data-baseweb="tab"] {{
            height: 2.8rem;
            padding: 0 1rem;
            border-radius: 8px;
            color: #536176;
            font-weight: 600;
        }}

        [aria-selected="true"][data-baseweb="tab"] {{
            color: #FFFFFF;
            background: var(--navy);
        }}

        [data-testid="stPlotlyChart"] {{
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #FFFFFF;
            box-shadow: 0 5px 16px rgba(15,23,42,0.045);
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            background: #FFFFFF;
        }}

        .dashboard-footer {{
            margin-top: 1.8rem;
            padding: 1rem 0 0.2rem;
            border-top: 1px solid var(--border);
            color: #718096;
            font-size: 0.78rem;
            text-align: center;
        }}

        @media (max-width: 900px) {{
            [data-testid="stAppViewContainer"] > .main .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            .hero {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .hero__meta {{
                text-align: left;
            }}
            .kpi-card {{
                height: auto;
                min-height: 138px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_cleaned_data(path: str, modified_ns: int) -> pd.DataFrame:
    """Load a cleaned CSV; modified_ns invalidates the Streamlit cache."""

    del modified_ns
    return pd.read_csv(path)


def style_figure(
    figure: go.Figure,
    *,
    height: int = 390,
    legend: bool = True,
    margin: dict[str, int] | None = None,
) -> go.Figure:
    """Apply a consistent, accessible Power BI-like Plotly theme."""

    figure.update_layout(
        height=height,
        margin=margin or {"l": 28, "r": 24, "t": 72, "b": 38},
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"family": "Segoe UI, Inter, Arial", "color": COLORS["ink"], "size": 12},
        title={
            "font": {"size": 17, "color": COLORS["navy"]},
            "x": 0.035,
            "xanchor": "left",
        },
        hoverlabel={
            "bgcolor": COLORS["navy"],
            "font": {"color": "#FFFFFF", "family": "Segoe UI, Inter, Arial"},
            "bordercolor": COLORS["navy"],
        },
        hovermode="closest",
        showlegend=legend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 11},
            "title": {"text": ""},
        },
    )
    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=COLORS["grid"],
        tickfont={"color": COLORS["muted"]},
        title_font={"color": COLORS["muted"], "size": 11},
    )
    figure.update_yaxes(
        gridcolor=COLORS["grid"],
        zeroline=False,
        linecolor=COLORS["grid"],
        tickfont={"color": COLORS["muted"]},
        title_font={"color": COLORS["muted"], "size": 11},
    )
    return figure


def plot(figure: go.Figure) -> None:
    st.plotly_chart(figure, width="stretch", config=PLOTLY_CONFIG)


def section_heading(title: str, subtitle: str) -> None:
    st.markdown(
        (f'<div class="section-heading"><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>'),
        unsafe_allow_html=True,
    )


def kpi_card(
    title: str,
    value: str,
    note: str,
    *,
    accent: str = COLORS["blue"],
) -> None:
    st.markdown(
        f"""
        <div class="kpi-card" style="--accent:{accent}">
            <div class="kpi-card__label">{escape(title)}</div>
            <div class="kpi-card__value">{escape(value)}</div>
            <div class="kpi-card__note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight(insight: dict[str, str]) -> None:
    accent = COLORS.get(insight.get("tone", "blue"), COLORS["blue"])
    st.markdown(
        f"""
        <div class="insight-card" style="--accent:{accent}">
            <div class="insight-card__title">{escape(insight["title"])}</div>
            <div class="insight-card__body">{escape(insight["body"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sorted_values(frame: pd.DataFrame, column: str) -> list[str]:
    return sorted(frame[column].dropna().astype(str).unique().tolist())


def reset_slicers() -> None:
    slicer_keys = (
        "year_filter",
        "make_filter",
        "model_filter",
        "fuel_filter",
        "body_filter",
        "drive_filter",
        "transmission_filter",
        "location_filter",
        "accident_filter",
        "service_filter",
        "price_filter",
        "exclude_floor",
    )
    for key in slicer_keys:
        st.session_state.pop(key, None)


if not DATA_PATH.exists():
    st.error("The cleaned dashboard dataset is missing.")
    st.markdown(
        f"""
        The dashboard expects:

        `{DATA_PATH.relative_to(Path(__file__).resolve().parent)}`

        Run the cleaning pipeline from the repository root, then refresh this page:
        """
    )
    st.code("python scripts/clean_data.py", language="bash")
    st.info(
        "If your cleaning command differs, ensure it writes "
        "`data/processed/automobile_cleaned.csv` with the documented cleaned columns."
    )
    st.stop()

try:
    raw_data = load_cleaned_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
    full_data = prepare_dashboard_data(raw_data)
except (OSError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
    st.error("The cleaned dataset could not be prepared for the dashboard.")
    st.code(str(exc))
    st.info(
        "Re-run the cleaning pipeline and confirm that the output CSV contains "
        "the required snake_case fields."
    )
    st.stop()


with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-brand__eyebrow">Portfolio intelligence</div>
            <div class="side-brand__title">Automobile Analysis</div>
            <div class="side-brand__copy">
                Use slicers to update every KPI and visual in the report.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Sensitivity")
    exclude_floor = st.toggle(
        "Exclude $500 price-floor records",
        value=False,
        key="exclude_floor",
        help=(
            "Removes records exactly at the observed $500 minimum so you can "
            "assess their effect on price statistics."
        ),
    )

    available_data = (
        full_data.loc[~full_data["is_price_floor"]].copy() if exclude_floor else full_data.copy()
    )
    if available_data.empty:
        st.error("No records remain after applying the sensitivity setting.")
        st.stop()

    st.markdown("#### Vehicle profile")
    year_min = int(available_data["year"].min())
    year_max = int(available_data["year"].max())
    year_range = st.slider(
        "Model year",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        key="year_filter",
    )

    make_selection = st.multiselect(
        "Make",
        options=sorted_values(available_data, "make"),
        placeholder="All makes",
        key="make_filter",
    )
    model_scope = (
        available_data.loc[available_data["make"].isin(make_selection)]
        if make_selection
        else available_data
    )
    model_options = sorted_values(model_scope, "model")
    current_models = st.session_state.get("model_filter", [])
    if any(model not in model_options for model in current_models):
        st.session_state["model_filter"] = [
            model for model in current_models if model in model_options
        ]
    model_selection = st.multiselect(
        "Model",
        options=model_options,
        placeholder="All models",
        key="model_filter",
    )

    fuel_selection = st.multiselect(
        "Fuel type",
        options=sorted_values(available_data, "fuel_type"),
        placeholder="All fuel types",
        key="fuel_filter",
    )
    body_selection = st.multiselect(
        "Body type",
        options=sorted_values(available_data, "body_type"),
        placeholder="All body types",
        key="body_filter",
    )
    drive_selection = st.multiselect(
        "Drivetrain",
        options=sorted_values(available_data, "drivetrain"),
        placeholder="All drivetrains",
        key="drive_filter",
    )

    with st.expander("More slicers", expanded=False):
        transmission_selection = st.multiselect(
            "Transmission",
            options=sorted_values(available_data, "transmission"),
            placeholder="All transmissions",
            key="transmission_filter",
        )
        location_selection = st.multiselect(
            "Location",
            options=sorted_values(available_data, "location"),
            placeholder="All locations",
            key="location_filter",
        )
        accident_selection = st.multiselect(
            "Accident reported",
            options=["No", "Yes", "Unknown"],
            placeholder="All statuses",
            key="accident_filter",
        )
        service_selection = st.multiselect(
            "Service history",
            options=sorted_values(available_data, "service_history"),
            placeholder="All histories",
            key="service_filter",
        )

    price_min = int(np.floor(available_data["selling_price"].min()))
    price_max = int(np.ceil(available_data["selling_price"].max()))
    price_range = st.slider(
        "Asking price",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max),
        step=max(100, int((price_max - price_min) / 200)),
        format="$%d",
        key="price_filter",
    )

    st.button(
        "Reset all slicers",
        on_click=reset_slicers,
        width="stretch",
        type="primary",
    )
    st.caption("Unknown values remain visible so missing information is not silently reclassified.")


selections = {
    "make": make_selection,
    "model": model_selection,
    "fuel_type": fuel_selection,
    "body_type": body_selection,
    "drivetrain": drive_selection,
    "transmission": transmission_selection,
    "location": location_selection,
    "accident_label": accident_selection,
    "service_history": service_selection,
}
filtered_data = apply_filters(
    full_data,
    selections,
    year_range,
    price_range,
    exclude_price_floor=exclude_floor,
)

if filtered_data.empty:
    st.warning(
        "No vehicles match the current slicers. Broaden the model-year, price, "
        "or category selections in the sidebar."
    )
    st.stop()

kpis = calculate_kpis(filtered_data, full_data)
reference_year = int(full_data["model_year_reference"].iloc[0])
scope_note = f"{len(filtered_data):,} of {len(full_data):,} records" + (
    " · $500 floor excluded" if exclude_floor else " · $500 floor included"
)

st.markdown(
    f"""
    <div class="hero">
        <div class="hero__content">
            <div class="hero__eyebrow">Executive decision dashboard</div>
            <h1>Automobile Portfolio Intelligence</h1>
            <p>
                A cross-sectional view of vehicle mix, asking-price position,
                model-year profile, and source-data quality. Model year describes
                the vehicle—not the transaction date.
            </p>
        </div>
        <div class="hero__meta">
            <div class="hero__meta-value">{len(filtered_data):,}</div>
            <div class="hero__meta-label">vehicles in current view</div>
        </div>
    </div>
    <div class="context-strip">
        <span class="context-chip">{escape(scope_note)}</span>
        <span class="context-chip">Model-year reference: {reference_year}</span>
        <span class="context-chip">Source: cleaned automobile dataset</span>
        <span class="context-chip">All metrics respond to sidebar slicers</span>
    </div>
    """,
    unsafe_allow_html=True,
)


tabs = st.tabs(
    [
        "Executive Overview",
        "Pricing & Depreciation",
        "Segment & Geography",
        "Data Quality",
    ]
)


with tabs[0]:
    section_heading(
        "Executive Overview",
        "Portfolio scale, price position, mix, and the most important filter-aware observations.",
    )

    kpi_columns = st.columns(6)
    with kpi_columns[0]:
        kpi_card(
            "Vehicles",
            f"{int(kpis['vehicle_count']):,}",
            f"{kpis['selection_share']:.1%} of full dataset",
            accent=COLORS["blue"],
        )
    with kpi_columns[1]:
        kpi_card(
            "Total listing value",
            format_currency(kpis["listing_value"]),
            "Sum of selected asking prices",
            accent=COLORS["navy"],
        )
    with kpi_columns[2]:
        delta = kpis["average_price_delta"]
        direction = "above" if delta >= 0 else "below"
        kpi_card(
            "Average price",
            format_currency(kpis["average_price"]),
            f"{abs(delta):.1%} {direction} portfolio average",
            accent=COLORS["teal"] if delta >= 0 else COLORS["coral"],
        )
    with kpi_columns[3]:
        kpi_card(
            "Median price",
            format_currency(kpis["median_price"]),
            "Robust midpoint of selected prices",
            accent=COLORS["purple"],
        )
    with kpi_columns[4]:
        kpi_card(
            "Average mileage",
            f"{format_compact_number(kpis['average_mileage'])} mi",
            "Mean odometer reading",
            accent=COLORS["amber"],
        )
    with kpi_columns[5]:
        rate = kpis["no_accident_rate"]
        kpi_card(
            "No-accident rate",
            f"{rate:.1%}" if pd.notna(rate) else "—",
            "Among records with known status",
            accent=COLORS["teal"],
        )

    first_row_left, first_row_right = st.columns([1.65, 1])

    year_summary = (
        filtered_data.groupby("year", observed=True)
        .agg(
            vehicles=("selling_price", "size"),
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
        )
        .reset_index()
        .sort_values("year")
    )
    year_figure = make_subplots(specs=[[{"secondary_y": True}]])
    year_figure.add_trace(
        go.Bar(
            x=year_summary["year"],
            y=year_summary["vehicles"],
            name="Vehicles",
            marker={
                "color": "#A9D3F2",
                "line": {"color": "#7CB6E2", "width": 0.7},
            },
            opacity=0.85,
            zorder=0,
            hovertemplate="Model year %{x}<br>Vehicles %{y:,.0f}<extra></extra>",
        ),
        secondary_y=True,
    )
    year_figure.add_trace(
        go.Scatter(
            x=year_summary["year"],
            y=year_summary["average_price"],
            name="Average price",
            mode="lines+markers",
            line={"color": COLORS["blue_dark"], "width": 4},
            marker={
                "size": 9,
                "color": COLORS["blue_dark"],
                "line": {"color": "#FFFFFF", "width": 2},
            },
            zorder=3,
            hovertemplate="Model year %{x}<br>Average $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )
    year_figure.add_trace(
        go.Scatter(
            x=year_summary["year"],
            y=year_summary["median_price"],
            name="Median price",
            mode="lines+markers",
            line={"color": "#008F84", "width": 3.5, "dash": "dash"},
            marker={
                "size": 8,
                "color": "#008F84",
                "symbol": "diamond",
                "line": {"color": "#FFFFFF", "width": 1.8},
            },
            zorder=4,
            hovertemplate="Model year %{x}<br>Median $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )
    year_figure.update_layout(
        title={
            "text": (
                "Price and inventory profile by model year"
                "<br><sup>Model year is not a transaction timeline</sup>"
            )
        },
        barmode="overlay",
        bargap=0.28,
    )
    year_figure.update_yaxes(
        title_text="Asking price",
        tickprefix="$",
        tickformat=",.0f",
        secondary_y=False,
    )
    year_figure.update_yaxes(
        title_text="Vehicles",
        showgrid=False,
        secondary_y=True,
    )
    year_figure.update_xaxes(dtick=1, title_text="Model year")
    style_figure(year_figure, height=430)
    with first_row_left:
        plot(year_figure)

    make_summary = (
        filtered_data.groupby("make", observed=True)
        .agg(
            vehicles=("selling_price", "size"),
            average_price=("selling_price", "mean"),
        )
        .reset_index()
        .sort_values("average_price", ascending=True)
    )
    make_figure = go.Figure(
        go.Bar(
            x=make_summary["average_price"],
            y=make_summary["make"],
            orientation="h",
            marker={
                "color": make_summary["average_price"],
                "colorscale": [[0, "#B9DDFC"], [1, COLORS["blue"]]],
                "showscale": False,
            },
            customdata=make_summary[["vehicles"]],
            text=make_summary["average_price"].map(lambda value: f"${value / 1000:.1f}K"),
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>Average price $%{x:,.0f}<br>Vehicles %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )
    make_figure.update_layout(
        title={
            "text": "Average asking price by make<br><sup>Vehicle count is available in the tooltip</sup>"
        }
    )
    make_figure.update_xaxes(title_text="Average asking price", tickprefix="$")
    make_figure.update_yaxes(title_text="")
    style_figure(
        make_figure,
        height=430,
        legend=False,
        margin={"l": 24, "r": 54, "t": 72, "b": 38},
    )
    with first_row_right:
        plot(make_figure)

    second_row_left, second_row_right = st.columns([0.78, 1.65])
    fuel_summary = (
        filtered_data.groupby("fuel_type", observed=True)
        .size()
        .rename("vehicles")
        .reset_index()
        .sort_values("vehicles", ascending=False)
    )
    fuel_figure = px.pie(
        fuel_summary,
        names="fuel_type",
        values="vehicles",
        hole=0.68,
        color="fuel_type",
        color_discrete_map=FUEL_COLORS,
        title="Inventory mix by fuel type",
    )
    fuel_figure.update_traces(
        textinfo="percent",
        textposition="inside",
        hovertemplate="%{label}<br>%{value:,.0f} vehicles<br>%{percent}<extra></extra>",
        marker={"line": {"color": "#FFFFFF", "width": 2}},
    )
    fuel_figure.add_annotation(
        text=f"<b>{len(filtered_data):,}</b><br><span style='font-size:11px'>vehicles</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"color": COLORS["navy"], "size": 17},
    )
    style_figure(fuel_figure, height=405)
    with second_row_left:
        plot(fuel_figure)

    scatter_data = filtered_data.dropna(subset=["mileage", "selling_price", "age_band"]).copy()
    scatter_figure = px.scatter(
        scatter_data,
        x="mileage",
        y="selling_price",
        color="age_band",
        category_orders={"age_band": list(AGE_BAND_ORDER)},
        color_discrete_map=AGE_COLORS,
        hover_data={
            "make": True,
            "model": True,
            "year": True,
            "mileage": ":,.0f",
            "selling_price": ":$,.0f",
            "age_band": False,
        },
        render_mode="webgl",
        opacity=0.62,
        title="Asking price vs mileage by vehicle-age band",
    )
    scatter_figure.update_traces(marker={"size": 7})
    scatter_figure.update_xaxes(title_text="Mileage (miles)", tickformat=",.0f")
    scatter_figure.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(scatter_figure, height=405)
    with second_row_right:
        plot(scatter_figure)

    section_heading(
        "Dynamic business insights",
        "Observations update with the current slicers and describe association—not causation.",
    )
    insights = business_insights(filtered_data, full_data)
    insight_columns = st.columns(min(len(insights), 5))
    for column, insight in zip(insight_columns, insights, strict=True):
        with column:
            render_insight(insight)


with tabs[1]:
    section_heading(
        "Pricing & Depreciation",
        "Price distribution and age/mileage relationships, with explicit sensitivity to the observed $500 floor.",
    )

    q25, q75 = filtered_data["selling_price"].quantile([0.25, 0.75])
    under_10k = filtered_data["selling_price"].lt(10_000).mean()
    floor_share = filtered_data["is_price_floor"].mean()
    latest_year = int(filtered_data["year"].max())
    latest_median = filtered_data.loc[
        filtered_data["year"].eq(latest_year), "selling_price"
    ].median()

    pricing_cards = st.columns(4)
    with pricing_cards[0]:
        kpi_card(
            "Middle 50% price range",
            f"{format_currency(q25)}–{format_currency(q75)}",
            "25th to 75th percentile",
            accent=COLORS["blue"],
        )
    with pricing_cards[1]:
        kpi_card(
            "Vehicles below $10K",
            f"{under_10k:.1%}",
            "Share of current selection",
            accent=COLORS["amber"],
        )
    with pricing_cards[2]:
        kpi_card(
            f"Median · {latest_year} models",
            format_currency(latest_median),
            "Latest selected model year",
            accent=COLORS["teal"],
        )
    with pricing_cards[3]:
        kpi_card(
            "Observed $500 floor",
            f"{floor_share:.1%}",
            "0% when sensitivity exclusion is on",
            accent=COLORS["coral"],
        )

    st.markdown(
        """
        <div class="callout">
            <strong>Interpretation guardrail:</strong> this dataset is a
            cross-sectional inventory snapshot. The charts compare vehicle model
            years and do not measure transaction-time sales growth or realized
            depreciation for the same vehicle.
        </div>
        """,
        unsafe_allow_html=True,
    )

    pricing_left, pricing_right = st.columns(2)
    price_histogram = px.histogram(
        filtered_data,
        x="selling_price",
        nbins=36,
        color_discrete_sequence=[COLORS["blue"]],
        title="Asking-price distribution",
        labels={"selling_price": "Asking price"},
    )
    price_histogram.update_traces(
        hovertemplate="Price bin %{x}<br>Vehicles %{y:,.0f}<extra></extra>"
    )
    price_histogram.add_vline(
        x=filtered_data["selling_price"].median(),
        line_color=COLORS["teal"],
        line_width=2,
        line_dash="dash",
        annotation_text="Median",
        annotation_position="top right",
    )
    price_histogram.update_xaxes(tickprefix="$", tickformat=",.0f")
    price_histogram.update_yaxes(title_text="Vehicles")
    style_figure(price_histogram, height=390, legend=False)
    with pricing_left:
        plot(price_histogram)

    age_box_data = filtered_data.dropna(subset=["age_band", "selling_price"])
    age_box = px.box(
        age_box_data,
        x="age_band",
        y="selling_price",
        color="age_band",
        category_orders={"age_band": list(AGE_BAND_ORDER)},
        color_discrete_map=AGE_COLORS,
        points=False,
        title="Price range by vehicle-age band",
    )
    age_box.update_xaxes(title_text="Age relative to latest model year")
    age_box.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(age_box, height=390, legend=False)
    with pricing_right:
        plot(age_box)

    relationship_left, relationship_right = st.columns([1.45, 1])
    mileage_scatter = px.scatter(
        scatter_data,
        x="mileage",
        y="selling_price",
        color="accident_label",
        color_discrete_map=ACCIDENT_COLORS,
        hover_data={
            "make": True,
            "model": True,
            "year": True,
            "mileage": ":,.0f",
            "selling_price": ":$,.0f",
            "accident_label": False,
        },
        render_mode="webgl",
        opacity=0.58,
        title="Price–mileage relationship by accident status",
    )
    mileage_scatter.update_traces(marker={"size": 7})
    mileage_scatter.update_xaxes(title_text="Mileage (miles)", tickformat=",.0f")
    mileage_scatter.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(mileage_scatter, height=430)
    with relationship_left:
        plot(mileage_scatter)

    owner_summary = (
        filtered_data.groupby("owners", observed=True)
        .agg(
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
            vehicles=("selling_price", "size"),
        )
        .reset_index()
        .sort_values("owners")
    )
    owner_figure = go.Figure()
    owner_figure.add_trace(
        go.Bar(
            x=owner_summary["owners"].astype(str),
            y=owner_summary["average_price"],
            name="Average",
            marker_color=COLORS["blue"],
            customdata=owner_summary[["vehicles"]],
            hovertemplate=(
                "%{x} owner(s)<br>Average $%{y:,.0f}"
                "<br>Vehicles %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )
    owner_figure.add_trace(
        go.Scatter(
            x=owner_summary["owners"].astype(str),
            y=owner_summary["median_price"],
            name="Median",
            mode="lines+markers",
            line={"color": COLORS["teal"], "width": 3},
            hovertemplate="%{x} owner(s)<br>Median $%{y:,.0f}<extra></extra>",
        )
    )
    owner_figure.update_layout(title="Price by number of owners")
    owner_figure.update_xaxes(title_text="Owners")
    owner_figure.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(owner_figure, height=430)
    with relationship_right:
        plot(owner_figure)

    heatmap_data = (
        filtered_data.dropna(subset=["age_band"])
        .pivot_table(
            index="make",
            columns="age_band",
            values="selling_price",
            aggfunc="median",
            observed=True,
        )
        .reindex(columns=list(AGE_BAND_ORDER))
    )
    heatmap_text = heatmap_data.astype(object).copy()
    for heatmap_column in heatmap_text.columns:
        heatmap_text[heatmap_column] = heatmap_data[heatmap_column].map(
            lambda value: f"${value / 1000:.1f}K" if pd.notna(value) else ""
        )
    heatmap = go.Figure(
        go.Heatmap(
            z=heatmap_data.to_numpy(),
            x=heatmap_data.columns.astype(str),
            y=heatmap_data.index.astype(str),
            text=heatmap_text.to_numpy(),
            texttemplate="%{text}",
            colorscale=[[0, "#E9F4FE"], [0.5, "#64B5F6"], [1, COLORS["blue_dark"]]],
            colorbar={"title": "Median<br>price", "tickprefix": "$"},
            hovertemplate="%{y}<br>%{x}<br>Median $%{z:,.0f}<extra></extra>",
        )
    )
    heatmap.update_layout(
        title={
            "text": "Median asking price: make × vehicle-age band"
            "<br><sup>Blank cells have no matching records in the selected context</sup>"
        }
    )
    heatmap.update_xaxes(title_text="Vehicle-age band", side="top")
    heatmap.update_yaxes(title_text="")
    style_figure(
        heatmap,
        height=440,
        legend=False,
        margin={"l": 35, "r": 36, "t": 92, "b": 34},
    )
    plot(heatmap)


with tabs[2]:
    section_heading(
        "Segment & Geography",
        "Brand/model concentration, powertrain mix, state coverage, and a drillable model scorecard.",
    )

    segment_left, segment_right = st.columns([1.25, 1])
    model_tree = (
        filtered_data.groupby(["make", "model"], observed=True)
        .agg(
            vehicles=("selling_price", "size"),
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
        )
        .reset_index()
    )
    treemap = px.treemap(
        model_tree,
        path=[px.Constant("All vehicles"), "make", "model"],
        values="vehicles",
        color="average_price",
        color_continuous_scale=["#DCEEFF", "#66B5F5", COLORS["blue_dark"]],
        custom_data=["median_price"],
        title="Inventory concentration by make and model",
    )
    treemap.update_traces(
        root_color="#EDF4FA",
        marker={"line": {"color": "#FFFFFF", "width": 1.5}},
        hovertemplate=(
            "<b>%{label}</b><br>Vehicles %{value:,.0f}"
            "<br>Average price $%{color:,.0f}"
            "<br>Median price $%{customdata[0]:,.0f}<extra></extra>"
        ),
    )
    treemap.update_layout(coloraxis_colorbar={"title": "Average<br>price", "tickprefix": "$"})
    style_figure(treemap, height=475, legend=False)
    with segment_left:
        plot(treemap)

    body_fuel = pd.crosstab(
        filtered_data["body_type"],
        filtered_data["fuel_type"],
        normalize="index",
    ).mul(100)
    body_fuel = body_fuel.loc[body_fuel.sum(axis=1).sort_values().index]
    body_fuel_figure = go.Figure()
    for fuel in body_fuel.columns:
        body_fuel_figure.add_trace(
            go.Bar(
                y=body_fuel.index,
                x=body_fuel[fuel],
                name=str(fuel),
                orientation="h",
                marker_color=FUEL_COLORS.get(str(fuel), "#A3ACB9"),
                hovertemplate=(
                    f"{escape(str(fuel))}<br>%{{y}}<br>Share %{{x:.1f}}%<extra></extra>"
                ),
            )
        )
    body_fuel_figure.update_layout(
        barmode="stack",
        title={
            "text": "Fuel-type mix within each body type"
            "<br><sup>Each bar totals 100% of its body-type inventory</sup>"
        },
    )
    body_fuel_figure.update_xaxes(title_text="Share of body-type inventory", ticksuffix="%")
    body_fuel_figure.update_yaxes(title_text="")
    style_figure(body_fuel_figure, height=475)
    with segment_right:
        plot(body_fuel_figure)

    geography_left, geography_right = st.columns([1.2, 1])
    known_states = filtered_data.loc[
        filtered_data["location"].astype(str).str.fullmatch(r"[A-Z]{2}", na=False)
    ]
    state_summary = (
        known_states.groupby("location", observed=True)
        .agg(
            vehicles=("selling_price", "size"),
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
        )
        .reset_index()
    )
    if not state_summary.empty:
        state_map = px.choropleth(
            state_summary,
            locations="location",
            locationmode="USA-states",
            scope="usa",
            color="average_price",
            color_continuous_scale=["#E6F3FE", "#76BDF5", COLORS["blue_dark"]],
            hover_name="location",
            hover_data={
                "vehicles": ":,.0f",
                "average_price": ":$,.0f",
                "median_price": ":$,.0f",
                "location": False,
            },
            title="Average asking price by known state",
        )
        state_map.update_layout(
            geo={
                "bgcolor": COLORS["surface"],
                "lakecolor": COLORS["background"],
                "landcolor": "#EAF0F6",
            },
            coloraxis_colorbar={"title": "Average<br>price", "tickprefix": "$"},
        )
        style_figure(state_map, height=430, legend=False)
        with geography_left:
            plot(state_map)
    else:
        with geography_left:
            st.info("No valid two-letter U.S. state codes remain in the current selection.")

    drive_mix = pd.crosstab(
        filtered_data["body_type"],
        filtered_data["drivetrain"],
        normalize="index",
    ).mul(100)
    drive_colors = {
        "FWD": COLORS["blue"],
        "AWD": COLORS["teal"],
        "RWD": COLORS["amber"],
        "4WD": COLORS["purple"],
        "Unknown": "#A3ACB9",
    }
    drive_figure = go.Figure()
    for drivetrain in drive_mix.columns:
        drive_figure.add_trace(
            go.Bar(
                x=drive_mix.index,
                y=drive_mix[drivetrain],
                name=str(drivetrain),
                marker_color=drive_colors.get(str(drivetrain), "#A3ACB9"),
                hovertemplate=(
                    f"{escape(str(drivetrain))}<br>%{{x}}<br>Share %{{y:.1f}}%<extra></extra>"
                ),
            )
        )
    drive_figure.update_layout(
        barmode="stack",
        title="Drivetrain mix within each body type",
    )
    drive_figure.update_xaxes(title_text="Body type")
    drive_figure.update_yaxes(title_text="Share", ticksuffix="%", range=[0, 100])
    style_figure(drive_figure, height=430)
    with geography_right:
        plot(drive_figure)

    section_heading(
        "Model scorecard",
        "Use the minimum-observation control to avoid over-interpreting very small segments.",
    )
    minimum_n = st.slider(
        "Minimum vehicles per model",
        min_value=1,
        max_value=max(1, int(model_tree["vehicles"].max())),
        value=min(20, max(1, int(model_tree["vehicles"].max()))),
        key="minimum_model_n",
    )

    def known_no_accident_rate(values: pd.Series) -> float:
        known = values.isin({"No", "Yes"})
        return values.loc[known].eq("No").mean() if known.any() else np.nan

    model_scorecard = (
        filtered_data.groupby(["make", "model"], observed=True)
        .agg(
            vehicles=("selling_price", "size"),
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
            average_mileage=("mileage", "mean"),
            median_model_year=("year", "median"),
            no_accident_rate=("accident_label", known_no_accident_rate),
            row_completeness=("row_completeness_pct", "mean"),
        )
        .reset_index()
        .loc[lambda frame: frame["vehicles"].ge(minimum_n)]
        .sort_values(["average_price", "vehicles"], ascending=[False, False])
    )
    model_scorecard["no_accident_rate"] = model_scorecard["no_accident_rate"] * 100
    display_scorecard = model_scorecard.rename(
        columns={
            "make": "Make",
            "model": "Model",
            "vehicles": "Vehicles",
            "average_price": "Average Price",
            "median_price": "Median Price",
            "average_mileage": "Average Mileage",
            "median_model_year": "Median Model Year",
            "no_accident_rate": "No-Accident Rate",
            "row_completeness": "Row Completeness",
        }
    )
    st.dataframe(
        display_scorecard,
        width="stretch",
        hide_index=True,
        height=420,
        column_config={
            "Vehicles": st.column_config.NumberColumn(format="%d"),
            "Average Price": st.column_config.NumberColumn(format="$%,.0f"),
            "Median Price": st.column_config.NumberColumn(format="$%,.0f"),
            "Average Mileage": st.column_config.NumberColumn(format="%,.0f mi"),
            "Median Model Year": st.column_config.NumberColumn(format="%d"),
            "No-Accident Rate": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=100
            ),
            "Row Completeness": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=100
            ),
        },
    )


with tabs[3]:
    section_heading(
        "Data Quality",
        "Completeness and boundary-value diagnostics for the current filter context.",
    )
    quality_kpis, missingness = data_quality_summary(filtered_data)

    quality_columns = st.columns(5)
    with quality_columns[0]:
        kpi_card(
            "Cell completeness",
            f"{quality_kpis['cell_completeness']:.1%}",
            "Across 18 source fields",
            accent=COLORS["teal"],
        )
    with quality_columns[1]:
        kpi_card(
            "Fully complete rows",
            f"{quality_kpis['complete_row_rate']:.1%}",
            "No source-field values missing",
            accent=COLORS["blue"],
        )
    with quality_columns[2]:
        kpi_card(
            "$500 price floor",
            f"{quality_kpis['price_floor_rate']:.1%}",
            "Boundary value; review, do not assume error",
            accent=COLORS["coral"],
        )
    with quality_columns[3]:
        kpi_card(
            "100-mile boundary",
            f"{quality_kpis['mileage_floor_rate']:.1%}",
            "Potential new-vehicle/default value",
            accent=COLORS["amber"],
        )
    with quality_columns[4]:
        kpi_card(
            "Duplicate rows",
            f"{int(quality_kpis['duplicate_rows']):,}",
            "Across canonical source fields",
            accent=COLORS["purple"],
        )

    quality_left, quality_right = st.columns([1.25, 1])
    missing_plot_data = missingness.loc[missingness["missing_count"].gt(0)].sort_values(
        "missing_pct", ascending=True
    )
    if not missing_plot_data.empty:
        missing_figure = go.Figure(
            go.Bar(
                x=missing_plot_data["missing_pct"] * 100,
                y=missing_plot_data["field"],
                orientation="h",
                marker_color=COLORS["blue"],
                text=missing_plot_data["missing_pct"].map(lambda value: f"{value:.1%}"),
                textposition="outside",
                customdata=missing_plot_data[["missing_count"]],
                hovertemplate=(
                    "%{y}<br>Missing %{customdata[0]:,.0f}<br>Rate %{x:.1f}%<extra></extra>"
                ),
            )
        )
        missing_figure.update_layout(
            title={
                "text": "Missingness by source field"
                "<br><sup>Audit flags are used when the cleaning pipeline preserves them</sup>"
            }
        )
        missing_axis_max = max(
            5.0,
            float(missing_plot_data["missing_pct"].max() * 100 * 1.22),
        )
        missing_figure.update_xaxes(
            title_text="Missing share",
            ticksuffix="%",
            range=[0, missing_axis_max],
        )
        missing_figure.update_yaxes(title_text="")
        style_figure(
            missing_figure,
            height=465,
            legend=False,
            margin={"l": 30, "r": 56, "t": 78, "b": 38},
        )
        with quality_left:
            plot(missing_figure)
    else:
        with quality_left:
            st.success("No source-level missing values are flagged in this selection.")

    row_missing = (
        filtered_data["missing_field_count"]
        .value_counts()
        .sort_index()
        .rename_axis("missing_fields")
        .reset_index(name="vehicles")
    )
    row_quality_figure = go.Figure(
        go.Bar(
            x=row_missing["missing_fields"].astype(str),
            y=row_missing["vehicles"],
            marker_color=[
                COLORS["teal"] if value == 0 else COLORS["blue"]
                for value in row_missing["missing_fields"]
            ],
            text=row_missing["vehicles"].map(lambda value: f"{value:,}"),
            textposition="outside",
            hovertemplate=("%{x} missing field(s)<br>Vehicles %{y:,.0f}<extra></extra>"),
        )
    )
    row_quality_figure.update_layout(
        title="Row completeness distribution",
    )
    row_quality_figure.update_xaxes(title_text="Missing source fields per row")
    row_quality_figure.update_yaxes(title_text="Vehicles")
    style_figure(
        row_quality_figure,
        height=465,
        legend=False,
        margin={"l": 35, "r": 30, "t": 72, "b": 46},
    )
    with quality_right:
        plot(row_quality_figure)

    association_left, association_right = st.columns(2)
    accident_price = (
        filtered_data.groupby("accident_label", observed=True)
        .agg(
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
            vehicles=("selling_price", "size"),
        )
        .reindex(["No", "Yes", "Unknown"])
        .dropna(how="all")
        .reset_index()
    )
    accident_figure = go.Figure()
    accident_figure.add_trace(
        go.Bar(
            x=accident_price["accident_label"],
            y=accident_price["average_price"],
            name="Average",
            marker_color=[
                ACCIDENT_COLORS.get(status, "#A3ACB9")
                for status in accident_price["accident_label"]
            ],
            customdata=accident_price[["vehicles"]],
            hovertemplate=(
                "%{x}<br>Average $%{y:,.0f}<br>Vehicles %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )
    accident_figure.add_trace(
        go.Scatter(
            x=accident_price["accident_label"],
            y=accident_price["median_price"],
            name="Median",
            mode="lines+markers",
            line={"color": COLORS["navy"], "width": 2},
            hovertemplate="%{x}<br>Median $%{y:,.0f}<extra></extra>",
        )
    )
    accident_figure.update_layout(
        title={
            "text": "Price by accident-history status"
            "<br><sup>Association only; vehicle age and mileage also differ</sup>"
        }
    )
    accident_figure.update_xaxes(title_text="Accident reported")
    accident_figure.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(accident_figure, height=400)
    with association_left:
        plot(accident_figure)

    service_price = (
        filtered_data.groupby("service_history", observed=True)
        .agg(
            average_price=("selling_price", "mean"),
            median_price=("selling_price", "median"),
            vehicles=("selling_price", "size"),
        )
        .reset_index()
        .sort_values("average_price", ascending=False)
    )
    service_figure = go.Figure()
    service_figure.add_trace(
        go.Bar(
            x=service_price["service_history"],
            y=service_price["average_price"],
            name="Average",
            marker_color=COLORS["blue"],
            customdata=service_price[["vehicles"]],
            hovertemplate=(
                "%{x}<br>Average $%{y:,.0f}<br>Vehicles %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )
    service_figure.add_trace(
        go.Scatter(
            x=service_price["service_history"],
            y=service_price["median_price"],
            name="Median",
            mode="lines+markers",
            line={"color": COLORS["teal"], "width": 3},
            hovertemplate="%{x}<br>Median $%{y:,.0f}<extra></extra>",
        )
    )
    service_figure.update_layout(
        title={
            "text": "Price by documented service history"
            "<br><sup>Unknown remains a separate, visible category</sup>"
        }
    )
    service_figure.update_xaxes(title_text="")
    service_figure.update_yaxes(title_text="Asking price", tickprefix="$", tickformat=",.0f")
    style_figure(service_figure, height=400)
    with association_right:
        plot(service_figure)

    section_heading(
        "Cleaning audit & review queue",
        "Imputation remains traceable, while unusual source values stay available for investigation.",
    )
    audit_left, audit_right = st.columns([0.9, 1.35])

    imputation_fields = {
        "Engine size": "engine_size_was_imputed",
        "Horsepower": "horsepower_was_imputed",
        "Torque": "torque_was_imputed",
        "Fuel efficiency": "fuel_efficiency_was_imputed",
    }
    imputation_summary = pd.DataFrame(
        [
            {
                "field": label,
                "vehicles": int(filtered_data[column].fillna(False).sum()),
                "share": float(filtered_data[column].fillna(False).mean()),
            }
            for label, column in imputation_fields.items()
            if column in filtered_data
        ]
    ).sort_values("vehicles", ascending=True)
    if not imputation_summary.empty:
        imputation_figure = go.Figure(
            go.Bar(
                x=imputation_summary["vehicles"],
                y=imputation_summary["field"],
                orientation="h",
                marker_color=COLORS["purple"],
                text=imputation_summary["share"].map(lambda value: f"{value:.1%}"),
                textposition="outside",
                customdata=imputation_summary[["share"]],
                hovertemplate=(
                    "%{y}<br>Imputed %{x:,.0f} vehicles"
                    "<br>Share %{customdata[0]:.1%}<extra></extra>"
                ),
            )
        )
        imputation_figure.update_layout(
            title={
                "text": "Numeric specifications imputed"
                "<br><sup>Peer-group medians; every value retains an audit flag</sup>"
            }
        )
        imputation_axis_max = max(
            1.0,
            float(imputation_summary["vehicles"].max() * 1.22),
        )
        imputation_figure.update_xaxes(
            title_text="Vehicles",
            range=[0, imputation_axis_max],
        )
        imputation_figure.update_yaxes(title_text="")
        style_figure(
            imputation_figure,
            height=385,
            legend=False,
            margin={"l": 30, "r": 58, "t": 80, "b": 38},
        )
        with audit_left:
            plot(imputation_figure)
    else:
        with audit_left:
            st.info("No imputation audit flags are available in this dataset.")

    review_flag_columns = {
        "$500 price floor": "is_price_floor",
        "100-mile review": "is_mileage_floor_review",
        "High mileage": "is_high_mileage",
        "EV/manual anomaly": "is_ev_manual",
    }
    review_summary = pd.DataFrame(
        [
            {
                "reason": label,
                "vehicles": int(filtered_data[column].fillna(False).sum()),
            }
            for label, column in review_flag_columns.items()
            if column in filtered_data
        ]
    ).sort_values("vehicles", ascending=True)
    review_figure = go.Figure(
        go.Bar(
            x=review_summary["vehicles"],
            y=review_summary["reason"],
            orientation="h",
            marker_color=[
                COLORS["coral"],
                COLORS["amber"],
                COLORS["blue"],
                COLORS["purple"],
            ][: len(review_summary)],
            text=review_summary["vehicles"].map(lambda value: f"{value:,}"),
            textposition="outside",
            hovertemplate="%{y}<br>Flagged vehicles %{x:,.0f}<extra></extra>",
        )
    )
    review_figure.update_layout(
        title={
            "text": "Source-quality review flags"
            "<br><sup>Flags may overlap; they are diagnostic, not deletion rules</sup>"
        }
    )
    review_figure.update_xaxes(title_text="Vehicles")
    review_figure.update_yaxes(title_text="")
    style_figure(
        review_figure,
        height=385,
        legend=False,
        margin={"l": 30, "r": 58, "t": 80, "b": 38},
    )
    with audit_right:
        plot(review_figure)

    review_mask = pd.Series(False, index=filtered_data.index, dtype=bool)
    for column in review_flag_columns.values():
        if column in filtered_data:
            review_mask |= filtered_data[column].fillna(False)
    review_columns = [
        column
        for column in (
            "vehicle_id",
            "make",
            "model",
            "year",
            "selling_price",
            "mileage",
            "quality_flags",
        )
        if column in filtered_data
    ]
    review_queue = (
        filtered_data.loc[review_mask, review_columns]
        .sort_values(
            ["selling_price", "mileage"],
            ascending=[True, False],
        )
        .head(250)
        .rename(
            columns={
                "vehicle_id": "Vehicle ID",
                "make": "Make",
                "model": "Model",
                "year": "Model Year",
                "selling_price": "Asking Price",
                "mileage": "Mileage",
                "quality_flags": "Review Reason",
            }
        )
    )
    with st.expander(
        f"Open quality-review queue · {int(review_mask.sum()):,} flagged vehicles",
        expanded=False,
    ):
        st.caption("The first 250 records are shown; use the slicers to narrow the queue.")
        st.dataframe(
            review_queue,
            width="stretch",
            hide_index=True,
            height=360,
            column_config={
                "Asking Price": st.column_config.NumberColumn(format="$%,.0f"),
                "Mileage": st.column_config.NumberColumn(format="%,.0f mi"),
                "Model Year": st.column_config.NumberColumn(format="%d"),
            },
        )

    section_heading(
        "Field-level audit table",
        "Counts and rates use source nulls or preserved cleaning audit flags.",
    )
    audit_table = missingness.rename(
        columns={
            "field": "Source Field",
            "missing_count": "Missing Values",
            "missing_pct": "Missing Rate",
        }
    )
    audit_table["Missing Rate"] = audit_table["Missing Rate"] * 100
    st.dataframe(
        audit_table,
        width="stretch",
        hide_index=True,
        height=390,
        column_config={
            "Missing Values": st.column_config.NumberColumn(format="%d"),
            "Missing Rate": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=100
            ),
        },
    )
    st.markdown(
        """
        <div class="callout">
            <strong>Quality policy:</strong> zero engine size is valid for electric
            vehicles and should not be treated as missing. Exact $500 prices and
            100-mile readings are retained as boundary flags until provenance
            confirms whether they are legitimate observations or capped/default
            values. Unknown categorical values remain visible in every analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="dashboard-footer">
        Created by Hieu Nguyen · Automobile Portfolio Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)
