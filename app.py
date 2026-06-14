import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

st.set_page_config(page_title="KalingaStone Master Logger", layout="wide")
st.title("🏭 KalingaStone Master Batch Logger")
st.markdown("Record raw batch data to build the plant's historical database.")

# --- 1. General Info ---
with st.expander("1. General Batch Information", expanded=True):
    col1, col2, col3 = st.columns(3)
    batch_id = col1.text_input("Batch ID (Manual)")
    line = col2.selectbox("Line", ["", "A2", "A5 Line 1", "A5 Line 2", "C1"])
    shift = col3.radio("Shift", ["Day", "Night"], horizontal=True)
    
    col4, col5, col6 = st.columns(3)
    design = col4.text_input("Design Name (Manual)")
    supplier = col5.text_input("Resin Supplier (Manual)")
    operator_name = col6.text_input("Operator Name")

# --- 2. Material Weights ---
with st.expander("2. Initial Material Weights (kg)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    resin_initial = c1.number_input("Initial Resin (kg)", value=0.0)
    powder = c2.number_input("Powder 400 (kg)", value=0.0)
    pigment = c3.number_input("Pigment (kg)", value=0.0)
    
    st.markdown("**Grit Additions**")
    g1, g2, g3, g4 = st.columns(4)
    grit_01_04 = g1.number_input("Grit 0.1-0.4 (kg)", value=0.0)
    grit_03_07 = g2.number_input("Grit 0.3-0.7 (kg)", value=0.0)
    grit_06_12 = g3.number_input("Grit 0.6-1.2 (kg)", value=0.0)
    grit_12_25 = g4.number_input("Grit 1.2-2.5 (kg)", value=0.0)
    
    g5, g6, g7, g8 = st.columns(4)
    grit_25_4 = g5.number_input("Grit 2.5-4 (kg)", value=0.0)
    grit_4_6 = g6.number_input("Grit 4-6 (kg)", value=0.0)
    grit_6_8 = g7.number_input("Grit 6-8 (kg)", value=0.0)
    
    st.markdown("**Mirror Additions**")
    m1, m2 = st.columns(2)
    mirror_03_125 = m1.number_input("Mirror 0.3-1.25 (kg)", value=0.0)
    mirror_125_25 = m2.number_input("Mirror 1.25-2.5 (kg)", value=0.0)

# --- 3. Process & Sensor Data ---
with st.expander("3. Process Parameters & Sensor Data", expanded=False):
    s1, s2, s3 = st.columns(3)
    ambient_temp = s1.number_input("Ambient Temp (°C)", value=0.0)
    mixer_temp = s2.number_input("Mixer Temp (°C)", value=0.0)
    viscosity = s3.number_input("True Viscosity (cP)", value=0.0)
    
    # Time Calculation Logic
    s4, s5, s6 = st.columns(3)
    mixing_start = s4.time_input("Mixing Start Time")
    mixing_end = s5.time_input("Mixing End Time")
    
    # Auto-calculate the difference in seconds
    dummy_date = date.today()
    dt_start = datetime.combine(dummy_date, mixing_start)
    dt_end = datetime.combine(dummy_date, mixing_end)
    
    if dt_end < dt_start:
        dt_end += timedelta(days=1)
        
    calculated_mix_sec = int((dt_end - dt_start).total_seconds())
    
    s6.info(f"**Auto-Calculated Mixing Time:** {calculated_mix_sec} sec")
    
    s7, s8, s9 = st.columns(3)
    final_mix_sec = s7.number_input("Final Mix Setting (Veegoo sec)", value=0)
    torque_stab = s8.number_input("Torque Stabilization (sec)", value=0)
    transit_time = s9.number_input("Transit Time (sec)", value=0)

# --- 4. Slab Specs ---
with st.expander("4. Downstream Slab Specifications", expanded=False):
    d1, d2, d3, d4 = st.columns(4)
    slab_size = d1.selectbox("Size Category", ["", "Regular", "Jumbo", "Super Jumbo", "Ultra Super Jumbo"])
    slab_len = d2.number_input("Length (mm)", value=0)
    slab_wid = d3.number_input("Width (mm)", value=0)
    slab_thk = d4.number_input("Thickness (mm)", value=0.0)
    
    d5, d6, d7 = st.columns(3)
    dist_weight = d5.number_input("Distributor Laying Wt (kg)", value=0.0)
    cnc_vein = d6.selectbox("CNC Vein?", ["No", "Yes"])
    sys_warning = d7.text_input("System Warning (If any)")

# --- 5. Operator Adjustments ---
with st.expander("5. Operator Adjustments & Observations", expanded=True):
    st.info("🎯 **Target Wetness is 100.** | Under 100 = Too Dry | Over 100 = Too Wet")
    o1, o2, o3 = st.columns(3)
    wetness_before = o1.slider("Wetness BEFORE Adjusting", 0, 200, 100)
    resin_adjustment = o2.number_input("Resin Adjustment (kg) [- to remove, + to add]", value=0.0, step=0.5)
    wetness_after = o3.slider("Wetness AFTER Adjusting", 0, 200, 100)
    
    remarks = st.text_area("Remarks / Batch Notes")

st.write("---")

# --- Auto-Calculations & Save ---
file_name = "KalingaStone_Raw_Master_Data.csv"

if batch_id:
    # Math Logic
    fine_grit = grit_01_04 + grit_03_07 + grit_06_12
    coarse_grit = grit_12_25 + grit_25_4 + grit_4_6 + grit_6_8
    total_grit = fine_grit + coarse_grit
    total_mirror = mirror_03_125 + mirror_125_25
    final_resin = resin_initial + resin_adjustment
    
    total_batch_weight = final_resin + powder + pigment + total_grit + total_mirror
    
    # Percentages
    resin_perc = (final_resin / total_batch_weight) * 100 if total_batch_weight > 0 else 0
    mirror_perc = (total_mirror / total_batch_weight) * 100 if total_batch_weight > 0 else 0
    fine_grit_perc = (fine_grit / total_batch_weight) * 100 if total_batch_weight > 0 else 0
    coarse_grit_perc = (coarse_grit / total_batch_weight) * 100 if total_batch_weight > 0 else 0
    
    wetness_diff = wetness_after - wetness_before
    
    # Density Logic
    volume_m3 = (slab_len * slab_wid * slab_thk) / 1e9
    density_gcc = (dist_weight / (volume_m3 * 1000)) if volume_m3 > 0 else 0
    density_status = "Normal"
    if density_gcc > 2.45: density_status = "High"
    elif 0 < density_gcc < 2.35: density_status = "Low"

    st.subheader("Auto-Calculated Production Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # Display the adjustment dynamically (+ or -)
    adj_label = f"+{resin_adjustment}" if resin_adjustment >= 0 else f"{resin_adjustment}"
    m1.metric("Final Resin (kg)", f"{final_resin:.1f}", f"{adj_label} kg manual")
    
    m2.metric("Total Batch Wt (kg)", f"{total_batch_weight:.1f}")
    m3.metric("Resin %", f"{resin_perc:.2f}%")
    m4.metric("Calculated Mix Time", f"{calculated_mix_sec} sec")
    m5.metric("Density Status", density_status)

    st.write("---")
    
    # --- Save Button ---
    if st.button("💾 SAVE BATCH DATA", type="primary", use_container_width=True):
        if not operator_name or not design:
            st.error("Please fill out Operator Name and Design.")
        else:
            new_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Batch_ID": batch_id, "Shift": shift, "Line": line, "Design": design, 
                "Resin_Supplier": supplier, "Operator_Name": operator_name,
                "Initial_Resin_kg": resin_initial, "Resin_Adjustment_kg": resin_adjustment, "Final_Resin_kg": final_resin,
                "Powder_400_kg": powder, "Pigment_kg": pigment,
                "Grit_0.1_0.4_kg": grit_01_04, "Grit_0.3_0.7_kg": grit_03_07, "Grit_0.6_1.2_kg": grit_06_12,
                "Grit_1.2_2.5_kg": grit_12_25, "Grit_2.5_4_kg": grit_25_4, "Grit_4_6_kg": grit_4_6, "Grit_6_8_kg": grit_6_8,
                "Mirror_0.3_1.25_kg": mirror_03_125, "Mirror_1.25_2.5_kg": mirror_125_25,
                "Ambient_Temp_C": ambient_temp, "Mixer_Temp_C": mixer_temp, "True_Viscosity_cP": viscosity,
                "Mixing_Start": str(mixing_start), "Mixing_End": str(mixing_end), 
                "Actual_Mix_sec": calculated_mix_sec, "Final_Mix_sec": final_mix_sec, "Torque_Stab_sec": torque_stab,
                "Wetness_Before": wetness_before, "Wetness_After": wetness_after, "Wetness_Change": wetness_diff,
                "Mixture_Density_gcc": round(density_gcc, 3), "Density_Status": density_status,
                "Slab_Size": slab_size, "Slab_Length_mm": slab_len, "Slab_Width_mm": slab_wid, "Slab_Thickness_mm": slab_thk,
                "Distributor_Weight_kg": dist_weight, "CNC_Vein": cnc_vein, "Transit_Time_sec": transit_time,
                "Total_Grit_kg": total_grit, "Total_Mirror_kg": total_mirror, "Total_Batch_Weight_kg": total_batch_weight,
                "Resin_Percentage": round(resin_perc, 2), "Mirror_Percentage": round(mirror_perc, 2),
                "Fine_Grit_Percentage": round(fine_grit_perc, 2), "Coarse_Grit_Percentage": round(coarse_grit_perc, 2),
                "System_Warning": sys_warning, "Remarks": remarks
            }
            
            df = pd.DataFrame([new_data])
            
            if os.path.isfile(file_name):
                df.to_csv(file_name, mode='a', header=False, index=False)
            else:
                df.to_csv(file_name, index=False)
                
            st.success(f"✅ Batch {batch_id} logged successfully!")

# --- Data Download Section ---
st.write("---")
st.markdown("### Data Management")
if os.path.isfile(file_name):
    with open(file_name, "rb") as file:
        st.download_button(
            label="📥 Download Master Excel/CSV File",
            data=file,
            file_name=file_name,
            mime="text/csv",
            help="Click here to download all logged batches to your computer."
        )
else:
    st.info("No data logged yet. The download button will appear after your first save.")
