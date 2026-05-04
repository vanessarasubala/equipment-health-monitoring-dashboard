import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

equipment_list = [
    ("EQ-001", "Etching Machine"),
    ("EQ-002", "Deposition Tool"),
    ("EQ-003", "Lithography Tool"),
    ("EQ-004", "Cleaning Tool"),
    ("EQ-005", "Inspection Tool"),
    ("EQ-006", "Wafer Handling System"),
]

start_date = datetime.now() - timedelta(days=30)
timestamps = pd.date_range(start=start_date, periods=30 * 24, freq="H")

records = []

for equipment_id, equipment_type in equipment_list:
    base_temp = np.random.uniform(55, 68)
    base_vibration = np.random.uniform(0.25, 0.45)
    base_pressure = np.random.uniform(28, 34)
    base_current = np.random.uniform(10, 14)

    for ts in timestamps:
        temperature = np.random.normal(base_temp, 4)
        vibration = np.random.normal(base_vibration, 0.08)
        pressure = np.random.normal(base_pressure, 2)
        current = np.random.normal(base_current, 1.2)

        # Inject abnormal readings randomly
        if np.random.rand() < 0.035:
            temperature += np.random.uniform(15, 25)

        if np.random.rand() < 0.03:
            vibration += np.random.uniform(0.5, 0.9)

        if np.random.rand() < 0.025:
            pressure += np.random.choice([-10, 10])

        if np.random.rand() < 0.025:
            current += np.random.uniform(6, 10)

        abnormal_temperature = temperature > 80
        abnormal_vibration = vibration > 0.85
        abnormal_pressure = pressure < 25 or pressure > 38
        abnormal_current = current > 18

        abnormal_count = sum([
            abnormal_temperature,
            abnormal_vibration,
            abnormal_pressure,
            abnormal_current
        ])

        if abnormal_count >= 2:
            risk_level = "High Risk"
        elif abnormal_count == 1:
            risk_level = "Warning"
        else:
            risk_level = "Normal"

        records.append({
            "timestamp": ts,
            "equipment_id": equipment_id,
            "equipment_type": equipment_type,
            "temperature": round(temperature, 2),
            "vibration": round(vibration, 3),
            "pressure": round(pressure, 2),
            "current": round(current, 2),
            "abnormal_temperature": abnormal_temperature,
            "abnormal_vibration": abnormal_vibration,
            "abnormal_pressure": abnormal_pressure,
            "abnormal_current": abnormal_current,
            "risk_level": risk_level
        })

df = pd.DataFrame(records)

conn = sqlite3.connect("equipment_health.db")
df.to_sql("sensor_readings", conn, if_exists="replace", index=False)
conn.close()

print("Database created successfully: equipment_health.db")
print(df.head())