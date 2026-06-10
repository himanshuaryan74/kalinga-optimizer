import streamlit as st
import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor

import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KalingaStone First Batch Optimizer",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 KalingaStone Safety-Constrained Batch Optimizer")
st.markdown(
    """
    Dynamic replacement of lab recipe.
    
    Objective:
    - Minimize Resin Consumption
    - Maintain Distributor Flowability
    - Prevent Vacuum Limit Exceeded
    - Preserve Vibration Consistency
    """
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    df = pd.read_csv("KalingaStone_Master_Data.csv")

    return df

df = load_data()

# ============================================================
# SAFE ENVELOPE
# ============================================================

healthy = df[df["System_Warning"].isna()].copy()

vac_low = healthy["Press_Vac_85_99_sec"].quantile(0.05)
vac_high = healthy["Press_Vac_85_99_sec"].quantile(0.95)

dist_low = healthy["Dist_Time_sec"].quantile(0.05)
dist_high = healthy["Dist_Time_sec"].quantile(0.95)

vib_low = healthy["Press_Vib_sec"].quantile(0.05)
vib_high = healthy["Press_Vib_sec"].quantile(0.95)

safe_envelope = {
    "vac_low": vac_low,
    "vac_high": vac_high,
    "dist_low": dist_low,
    "dist_high": dist_high,
    "vib_low": vib_low,
    "vib_high": vib_high,
}

# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "Design",
    "Resin_Supplier",
    "Ambient_Temp_C",
    "Resin_kg",
    "Powder_400_kg",
    "Pigment_kg",
    "True_Viscosity_cP"
]

cat_cols = [
    "Design",
    "Resin_Supplier"
]

num_cols = [
    "Ambient_Temp_C",
    "Resin_kg",
    "Powder_400_kg",
    "Pigment_kg",
    "True_Viscosity_cP"
]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", "passthrough", num_cols)
    ]
)

# ============================================================
# MODEL TRAINING
# ============================================================

def build_model(target):

    X = df[FEATURES]
    y = df[target]

    model = Pipeline([
        ("prep", preprocessor),
        ("rf", RandomForestRegressor(
            n_estimators=400,
            max_depth=12,
            random_state=42
        ))
    ])

    model.fit(X, y)

    return model

torque_model = build_model("Torque_Stab_sec")
vac_model = build_model("Press_Vac_85_99_sec")
vib_model = build_model("Press_Vib_sec")
dist_model = build_model("Dist_Time_sec")

# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def feature_importance():

    X = df[FEATURES]

    prep = preprocessor.fit(X)

    names = prep.get_feature_names_out()

    rf = RandomForestRegressor(
        n_estimators=400,
        random_state=42
    )

    X_enc = prep.transform(X)

    rf.fit(X_enc, df["Press_Vac_85_99_sec"])

    imp = pd.DataFrame({
        "Feature": names,
        "Importance": rf.feature_importances_
    })

    return imp.sort_values(
        "Importance",
        ascending=False
    )

imp_df = feature_importance()

# ============================================================
# SIDEBAR INPUTS
# ============================================================

st.sidebar.header("Lab Recipe Inputs")

ambient_temp = st.sidebar.slider(
    "Ambient Temperature (°C)",
    15,
    45,
    30
)

design = st.sidebar.selectbox(
    "Design",
    sorted(df["Design"].unique())
)

supplier = st.sidebar.selectbox(
    "Resin Supplier",
    sorted(df["Resin_Supplier"].unique())
)

lab_resin = st.sidebar.number_input(
    "Lab Resin (kg)",
    value=float(df["Resin_kg"].median())
)

lab_powder = st.sidebar.number_input(
    "Lab Powder (kg)",
    value=float(df["Powder_400_kg"].median())
)

viscosity = st.sidebar.number_input(
    "Expected Resin Viscosity (cP)",
    value=float(df["True_Viscosity_cP"].median())
)

pigment = st.sidebar.number_input(
    "Pigment (kg)",
    value=float(df["Pigment_kg"].median())
)

# ============================================================
# OPTIMIZATION ENGINE
# ============================================================

def optimize_recipe():

    best = None

    search_range = np.arange(
        lab_resin - 4,
        lab_resin + 1,
        0.25
    )

    for resin in search_range:

        sample = pd.DataFrame([{
            "Design": design,
            "Resin_Supplier": supplier,
            "Ambient_Temp_C": ambient_temp,
            "Resin_kg": resin,
            "Powder_400_kg": lab_powder,
            "Pigment_kg": pigment,
            "True_Viscosity_cP": viscosity
        }])

        pred_torque = torque_model.predict(sample)[0]
        pred_vac = vac_model.predict(sample)[0]
        pred_vib = vib_model.predict(sample)[0]
        pred_dist = dist_model.predict(sample)[0]

        safe = (
            safe_envelope["vac_low"]
            <= pred_vac
            <= safe_envelope["vac_high"]
        ) and (
            safe_envelope["dist_low"]
            <= pred_dist
            <= safe_envelope["dist_high"]
        ) and (
            safe_envelope["vib_low"]
            <= pred_vib
            <= safe_envelope["vib_high"]
        )

        if safe:

            best = {
                "resin": resin,
                "torque": pred_torque,
                "vac": pred_vac,
                "vib": pred_vib,
                "dist": pred_dist
            }

            break

    return best

result = optimize_recipe()

# ============================================================
# OUTPUT
# ============================================================

if result is None:

    st.error(
        "No safe operating point found. Increase resin or review process."
    )

else:

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Optimized Resin (kg)",
            round(result["resin"], 2),
            round(result["resin"] - lab_resin, 2)
        )

    with col2:

        st.metric(
            "Recommended Mix Time (sec)",
            round(result["torque"], 1)
        )

    st.divider()

    # ========================================================
    # GAUGE CHART
    # ========================================================

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=result["vac"],
        title={"text": "Predicted Vacuum Time (sec)"},
        gauge={
            "axis": {"range": [0, 140]},
            "steps": [
                {
                    "range": [0, safe_envelope["vac_low"]],
                    "color": "lightcoral"
                },
                {
                    "range": [
                        safe_envelope["vac_low"],
                        safe_envelope["vac_high"]
                    ],
                    "color": "lightgreen"
                },
                {
                    "range": [
                        safe_envelope["vac_high"],
                        140
                    ],
                    "color": "red"
                }
            ]
        }
    ))

    st.plotly_chart(
        gauge,
        use_container_width=True
    )

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    st.subheader("Drivers of Vacuum Stability")

    top_imp = imp_df.head(15)

    fig = px.bar(
        top_imp,
        x="Importance",
        y="Feature",
        orientation="h"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ========================================================
    # PREDICTIONS TABLE
    # ========================================================

    st.subheader("Predicted Downstream Performance")

    pred_df = pd.DataFrame({
        "Metric": [
            "Torque Stabilization",
            "Distributor Time",
            "Vacuum Time",
            "Press Vibration"
        ],
        "Prediction": [
            round(result["torque"], 2),
            round(result["dist"], 2),
            round(result["vac"], 2),
            round(result["vib"], 2)
        ]
    })

    st.dataframe(
        pred_df,
        use_container_width=True
    )

# ============================================================
# SAFE ENVELOPE VIEW
# ============================================================

with st.expander("Process Safe Envelope"):

    st.write(safe_envelope)
