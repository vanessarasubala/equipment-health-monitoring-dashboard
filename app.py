import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Equipment Health Monitoring Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.markdown("""
<style>
.metric-card {
    background-color: #f8f9fa;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #e6e6e6;
}
.main-title {
    font-size: 34px;
    font-weight: 700;
}
.subtitle {
    color: #666;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    conn = sqlite3.connect("equipment_health.db")
    df = pd.read_sql_query("SELECT * FROM sensor_readings", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    return df


df = load_data()

st.markdown('<div class="main-title">Equipment Health Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Interactive dashboard for monitoring equipment sensor trends, abnormal readings, and quality risk signals.</div>',
    unsafe_allow_html=True
)

st.divider()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

equipment_options = sorted(df["equipment_id"].unique())
selected_equipment = st.sidebar.multiselect(
    "Select Equipment",
    equipment_options,
    default=equipment_options
)

sensor_options = ["temperature", "vibration", "pressure", "current"]
selected_sensor = st.sidebar.selectbox(
    "Select Sensor Trend",
    sensor_options
)

risk_options = ["Normal", "Warning", "High Risk"]
selected_risk = st.sidebar.multiselect(
    "Select Risk Level",
    risk_options,
    default=risk_options
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[df["date"].min(), df["date"].max()]
)

filtered_df = df[
    (df["equipment_id"].isin(selected_equipment)) &
    (df["risk_level"].isin(selected_risk))
]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["date"] >= start_date) &
        (filtered_df["date"] <= end_date)
    ]

# KPI calculations
total_readings = len(filtered_df)
warning_count = len(filtered_df[filtered_df["risk_level"] == "Warning"])
high_risk_count = len(filtered_df[filtered_df["risk_level"] == "High Risk"])
abnormal_count = warning_count + high_risk_count

risk_rate = (abnormal_count / total_readings * 100) if total_readings > 0 else 0

avg_temp = filtered_df["temperature"].mean() if total_readings > 0 else 0
avg_vibration = filtered_df["vibration"].mean() if total_readings > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Readings", f"{total_readings:,}")
col2.metric("Abnormal Readings", f"{abnormal_count:,}")
col3.metric("Risk Rate", f"{risk_rate:.2f}%")
col4.metric("Avg Temperature", f"{avg_temp:.2f} °C")
col5.metric("Avg Vibration", f"{avg_vibration:.3f}")

st.divider()

# Sensor trend chart
st.subheader("Sensor Trend Analysis")

trend_fig = px.line(
    filtered_df,
    x="timestamp",
    y=selected_sensor,
    color="equipment_id",
    title=f"{selected_sensor.title()} Trend Over Time",
    markers=False
)

trend_fig.update_layout(
    xaxis_title="Timestamp",
    yaxis_title=selected_sensor.title(),
    legend_title="Equipment ID"
)

st.plotly_chart(trend_fig, use_container_width=True)

# Equipment comparison and risk monitoring
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Equipment Risk Comparison")

    risk_summary = filtered_df.groupby(["equipment_id", "risk_level"]).size().reset_index(name="count")

    risk_fig = px.bar(
        risk_summary,
        x="equipment_id",
        y="count",
        color="risk_level",
        title="Risk Level Distribution by Equipment",
        barmode="stack"
    )

    risk_fig.update_layout(
        xaxis_title="Equipment ID",
        yaxis_title="Number of Readings",
        legend_title="Risk Level"
    )

    st.plotly_chart(risk_fig, use_container_width=True)

with right_col:
    st.subheader("Sensor Distribution by Equipment")

    box_fig = px.box(
        filtered_df,
        x="equipment_id",
        y=selected_sensor,
        color="equipment_id",
        title=f"{selected_sensor.title()} Distribution by Equipment"
    )

    box_fig.update_layout(
        xaxis_title="Equipment ID",
        yaxis_title=selected_sensor.title(),
        showlegend=False
    )

    st.plotly_chart(box_fig, use_container_width=True)

st.divider()

# Abnormal readings table
st.subheader("Abnormal Readings / Potential Process Risk Signals")

abnormal_df = filtered_df[filtered_df["risk_level"] != "Normal"].copy()

if len(abnormal_df) > 0:
    abnormal_df = abnormal_df.sort_values("timestamp", ascending=False)

    st.dataframe(
        abnormal_df[
            [
                "timestamp",
                "equipment_id",
                "equipment_type",
                "temperature",
                "vibration",
                "pressure",
                "current",
                "risk_level"
            ]
        ],
        use_container_width=True
    )
else:
    st.success("No abnormal readings found for the selected filters.")

st.divider()

# Equipment health summary
st.subheader("Equipment Health Summary")

summary_df = filtered_df.groupby(["equipment_id", "equipment_type"]).agg(
    total_readings=("risk_level", "count"),
    warning_readings=("risk_level", lambda x: (x == "Warning").sum()),
    high_risk_readings=("risk_level", lambda x: (x == "High Risk").sum()),
    avg_temperature=("temperature", "mean"),
    avg_vibration=("vibration", "mean"),
    avg_pressure=("pressure", "mean"),
    avg_current=("current", "mean"),
).reset_index()

summary_df["risk_rate"] = (
    (summary_df["warning_readings"] + summary_df["high_risk_readings"])
    / summary_df["total_readings"] * 100
).round(2)

st.dataframe(summary_df, use_container_width=True)