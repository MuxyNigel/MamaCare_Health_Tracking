# app.py (Fixed - Proper Connection Management)
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection, init_db
from ml_model_real import RealMaternalRiskModel
from sms_service import sms_service

# Initialize everything
init_db()  # This will create the database if it doesn't exist
risk_model = RealMaternalRiskModel().load_model()

def main():
    st.set_page_config(
        page_title="MamaCare Pro",
        page_icon="🤰",
        layout="wide"
    )
    
    st.title("🤰 MaternalCare Pro - AI-Powered Maternal Health System (Real Dataset)")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Register Mother", "Appointments", "VHW Dashboard", "VHW Follow-up", "Analytics", "System Admin"]
    )
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Register Mother":
        register_mother_page()
    elif page == "Appointments":
        appointments_page()
    elif page == "VHW Dashboard":
        vhw_dashboard_page()
    elif page == "VHW Follow-up":
        vhw_followup_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "System Admin":
        admin_page()

def dashboard_page():
    st.header("📊 Maternal Health Dashboard")
    
    conn = get_db_connection()
    
    # Get summary statistics
    total_mothers = pd.read_sql("SELECT COUNT(*) as count FROM mothers", conn).iloc[0]['count']
    total_appointments = pd.read_sql("SELECT COUNT(*) as count FROM appointments", conn).iloc[0]['count']
    missed_appointments = pd.read_sql("SELECT COUNT(*) as count FROM appointments WHERE status = 'Missed'", conn).iloc[0]['count']
    high_risk_mothers = pd.read_sql("SELECT COUNT(*) as count FROM mothers WHERE risk_score > 0.5", conn).iloc[0]['count']
    
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Mothers", total_mothers)
    col2.metric("Total Appointments", total_appointments)
    col3.metric("Missed Appointments", missed_appointments)
    col4.metric("High-Risk Mothers", high_risk_mothers)
    
    # Recent activities
    st.subheader("Recent Activities")
    conn = get_db_connection()
    recent_mothers = pd.read_sql("""
        SELECT name, age, risk_score, created_at 
        FROM mothers 
        ORDER BY created_at DESC 
        LIMIT 10
    """, conn)
    conn.close()
    
    st.dataframe(recent_mothers)

def register_mother_page():
    st.header("👩 Register New Mother (Real Dataset Fields)")
    
    with st.form("mother_form"):
        st.subheader("Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=15, max_value=50, value=25)
            gestational_age = st.number_input("Gestational Age (weeks)", min_value=1, max_value=42, value=20)
        
        with col2:
            bmi = st.number_input("BMI", min_value=15.0, max_value=50.0, value=25.0)
            phone = st.text_input("Phone Number")
            village = st.text_input("Village")
        
        st.subheader("Medical History")
        col1, col2 = st.columns(2)
        
        with col1:
            previous_c_section = st.selectbox("Previous C-Section", [0, 1], format_func=lambda x: "Yes" if x else "No")
            previous_miscarriages = st.selectbox("Previous Miscarriages", [0, 1, 2, 3])
            previous_preterm_birth = st.selectbox("Previous Preterm Birth", [0, 1], format_func=lambda x: "Yes" if x else "No")
            chronic_hypertension = st.selectbox("Chronic Hypertension", [0, 1], format_func=lambda x: "Yes" if x else "No")
        
        with col2:
            diabetes = st.selectbox("Diabetes", [0, 1], format_func=lambda x: "Yes" if x else "No")
            gestational_diabetes = st.selectbox("Gestational Diabetes", [0, 1], format_func=lambda x: "Yes" if x else "No")
            preeclampsia_history = st.selectbox("Preeclampsia History", [0, 1], format_func=lambda x: "Yes" if x else "No")
            multiple_pregnancy = st.selectbox("Multiple Pregnancy", [0, 1], format_func=lambda x: "Yes" if x else "No")
        
        st.subheader("Current Health Status")
        col1, col2 = st.columns(2)
        
        with col1:
            blood_pressure = st.number_input("Blood Pressure (mmHg)", min_value=80, max_value=200, value=120)
            hb_level = st.number_input("Hemoglobin Level", min_value=5.0, max_value=15.0, value=11.0)
        
        with col2:
            smoking = st.selectbox("Smoking", [0, 1], format_func=lambda x: "Yes" if x else "No")
            alcohol_use = st.selectbox("Alcohol Use", [0, 1], format_func=lambda x: "Yes" if x else "No")
            family_history = st.selectbox("Family History", [0, 1], format_func=lambda x: "Yes" if x else "No")
            urine_protein = st.selectbox("Urine Protein", [0, 1, 2, 3])
            blood_glucose = st.number_input("Blood Glucose", min_value=50, max_value=300, value=90)
        
        submitted = st.form_submit_button("Register & Calculate Risk")
        
        if submitted:
            if name and phone:
                # Prepare mother data for real model
                mother_data = {
                    'age': age,
                    'bmi': bmi,
                    'blood_pressure': blood_pressure,
                    'gestational_age': gestational_age,
                    'previous_c_section': previous_c_section,
                    'previous_miscarriages': previous_miscarriages,
                    'previous_preterm_birth': previous_preterm_birth,
                    'chronic_hypertension': chronic_hypertension,
                    'diabetes': diabetes,
                    'gestational_diabetes': gestational_diabetes,
                    'preeclampsia_history': preeclampsia_history,
                    'multiple_pregnancy': multiple_pregnancy,
                    'smoking': smoking,
                    'alcohol_use': alcohol_use,
                    'family_history': family_history,
                    'hb_level': hb_level,
                    'urine_protein': urine_protein,
                    'blood_glucose': blood_glucose
                }
                
                try:
                    risk_result = risk_model.predict_risk(mother_data)
                    
                    # Save to database with ALL required fields
                    conn = get_db_connection()
                    c = conn.cursor()
                    
                    c.execute("""
                        INSERT INTO mothers (
                            name, age, phone, village, risk_score, risk_breakdown,
                            bmi, blood_pressure, gestational_age, previous_c_section,
                            previous_miscarriages, previous_preterm_birth, chronic_hypertension,
                            diabetes, gestational_diabetes, preeclampsia_history, multiple_pregnancy,
                            smoking, alcohol_use, family_history, hb_level, urine_protein, blood_glucose
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        name,  # Name
                        age,  # Age
                        phone,  # Phone
                        village,  # Village
                        risk_result['risk_score'],  # Risk score
                        str(risk_result),  # Risk breakdown
                        bmi,  # BMI
                        blood_pressure,  # Blood pressure
                        gestational_age,  # Gestational age
                        previous_c_section,  # Previous C-section
                        previous_miscarriages,  # Previous miscarriages
                        previous_preterm_birth,  # Previous preterm birth
                        chronic_hypertension,  # Chronic hypertension
                        diabetes,  # Diabetes
                        gestational_diabetes,  # Gestational diabetes
                        preeclampsia_history,  # Preeclampsia history
                        multiple_pregnancy,  # Multiple pregnancy
                        smoking,  # Smoking
                        alcohol_use,  # Alcohol use
                        family_history,  # Family history
                        hb_level,  # Hemoglobin level
                        urine_protein,  # Urine protein
                        blood_glucose  # Blood glucose
                    ))
                    conn.commit()
                    conn.close()
                    
                    # Verify the insertion worked
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM mothers WHERE name = ?", (name,))
                    new_count = cursor.fetchone()[0]
                    conn.close()
                    
                    if new_count > 0:
                        st.success(f"✅ Registered! Risk Level: {risk_result['risk_level']} (Score: {risk_result['risk_score']:.2f})")
                        st.success(f"✅ Mother '{name}' successfully saved to database!")
                        
                        # Show detailed risk breakdown
                        st.subheader("Risk Breakdown")
                        for level, prob in risk_result['all_probabilities'].items():
                            st.progress(prob, text=f"{level}: {prob:.2%}")
                        
                        # Show feature importance
                        st.subheader("Key Risk Factors")
                        importance_df = pd.DataFrame([
                            {'Factor': k, 'Importance': v} 
                            for k, v in risk_result['feature_importance'].items()
                        ]).sort_values('Importance', ascending=False)
                        st.bar_chart(importance_df.set_index('Factor'))
                        
                        # Force a page refresh to update dashboard
                        st.rerun()
                        
                    else:
                        st.error("❌ Failed to save to database!")
                        
                except Exception as e:
                    st.error(f"❌ Error during registration: {str(e)}")
                    import traceback
                    st.error(f"Full error: {traceback.format_exc()}")
            else:
                st.error("Please fill in required fields")

def appointments_page():
    st.header("📅 Schedule Appointments")
    
    conn = get_db_connection()
    mothers = pd.read_sql("SELECT id, name, phone FROM mothers", conn)
    conn.close()
    
    if mothers.empty:
        st.warning("No mothers registered yet.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        mother_id = st.selectbox(
            "Select Mother",
            mothers['id'],
            format_func=lambda x: mothers[mothers['id']==x]['name'].iloc[0]
        )
    
    with col2:
        appt_type = st.selectbox("Appointment Type", ["Antenatal", "Postnatal"])
        appt_date = st.date_input("Appointment Date")
    
    if st.button("Schedule Appointment"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO appointments (mother_id, appointment_date, appointment_type)
            VALUES (?, ?, ?)
        """, (mother_id, appt_date, appt_type))
        conn.commit()
        conn.close()
        
        # Send SMS reminder
        mother_phone = mothers[mothers['id']==mother_id]['phone'].iloc[0]
        st.success(f"✅ Appointment scheduled! SMS reminder would be sent to {mother_phone}")

def vhw_dashboard_page():
    st.title("👩‍⚕️ VHW Dashboard")
    
    # VHW selection
    vhw_name = st.selectbox("Select VHW", ["John Doe", "Jane Smith", "Maria Garcia"])
    
    conn = get_db_connection()
    
    # Get high-risk mothers (using real risk levels)
    assigned_mothers = pd.read_sql("""
        SELECT 
            m.id,
            m.name, 
            m.phone, 
            m.village, 
            m.risk_score, 
            m.created_at,
            m.age,
            m.bmi,
            m.blood_pressure
        FROM mothers m
        WHERE m.risk_score > 0.5  -- High risk mothers
        ORDER BY m.risk_score DESC
        LIMIT 20
    """, conn)
    
    st.subheader(f"High-Priority Mothers for {vhw_name}")
    
    if assigned_mothers.empty:
        st.info("No high-risk mothers assigned yet.")
    else:
        # Display mothers with risk levels
        for idx, row in assigned_mothers.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{row['name']}**")
                    st.write(f"Village: {row['village']}")
                
                with col2:
                    st.write(f"Phone: {row['phone']}")
                    st.write(f"Age: {row['age']}, BMI: {row['bmi']}")
                
                with col3:
                    risk_level = "Critical" if row['risk_score'] > 0.8 else "High" if row['risk_score'] > 0.6 else "Medium"
                    st.metric("Risk", f"{row['risk_score']:.2f}")
                
                with col4:
                    if st.button(f"Follow-up", key=f"followup_{row['id']}"):
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO follow_ups (mother_id, vhw_id, status, notes)
                            VALUES (?, ?, 'Pending', 'VHW follow-up required')
                        """, (row['id'], 1))  # Using VHW ID 1 for demo
                        conn.commit()
                        st.success("✅ Follow-up scheduled!")
        
        # Export button
        st.download_button(
            "📥 Download High-Risk List",
            assigned_mothers.to_csv(index=False),
            "high_risk_mothers.csv",
            "text/csv"
        )
    
    # Follow-up tasks
    st.subheader("Pending Follow-ups")
    follow_up_tasks = pd.read_sql("""
        SELECT 
            m.name, 
            m.phone, 
            m.village, 
            f.status, 
            f.notes,
            f.assigned_date
        FROM follow_ups f
        JOIN mothers m ON f.mother_id = m.id
        WHERE f.status = 'Pending'
        ORDER BY f.assigned_date DESC
    """, conn)
    
    if follow_up_tasks.empty:
        st.info("No pending follow-ups.")
    else:
        for idx, row in follow_up_tasks.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{row['name']}** - {row['village']}")
                    st.write(f"Phone: {row['phone']}")
                
                with col2:
                    st.write(f"Status: {row['status']}")
                    st.write(f"Notes: {row['notes']}")
                
                with col3:
                    if st.button(f"Complete", key=f"complete_{idx}"):
                        c = conn.cursor()
                        c.execute("""
                            UPDATE follow_ups 
                            SET status = 'Completed', notes = notes || ' - Completed on ' || date('now')
                            WHERE mother_id = (SELECT id FROM mothers WHERE name = ?)
                        """, (row['name'],))
                        conn.commit()
                        st.success("✅ Follow-up completed!")
    
    conn.close()

def vhw_followup_page():
    st.header("📋 VHW Follow-up Dashboard")
    
    conn = get_db_connection()
    
    # Get missed appointments
    query = """
    SELECT 
        m.id as mother_id,
        m.name,
        m.phone,
        m.village,
        m.risk_score,
        a.appointment_date,
        a.appointment_type
    FROM appointments a
    JOIN mothers m ON a.mother_id = m.id
    WHERE a.status = 'Scheduled' AND a.appointment_date < date('now')
    ORDER BY m.risk_score DESC
    """
    
    missed_appointments = pd.read_sql(query, conn)
    conn.close()
    
    if missed_appointments.empty:
        st.success("✅ No missed appointments!")
    else:
        st.warning(f"🚨 {len(missed_appointments)} mothers missed appointments!")
        
        # Display with risk prioritization
        for idx, row in missed_appointments.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{row['name']}** - Risk: {row['risk_score']:.2f}")
                    st.write(f"Village: {row['village']} | Phone: {row['phone']}")
                    st.write(f"Missed: {row['appointment_type']} on {row['appointment_date']}")
                
                with col2:
                    risk_level = "Critical" if row['risk_score'] > 0.8 else "High" if row['risk_score'] > 0.6 else "Medium"
                    st.metric("Risk Level", risk_level)
                
                with col3:
                    if st.button(f"Assign to Me", key=f"assign_{row['mother_id']}"):
                        st.success("✅ Assigned!")
        
        # Export for VHWs
        st.download_button(
            "📥 Download Follow-up List",
            missed_appointments.to_csv(index=False),
            "vhf_followup.csv",
            "text/csv"
        )

def analytics_page():
    st.header("📈 Maternal Health Analytics")
    
    conn = get_db_connection()
    
    # Risk distribution
    risk_dist = pd.read_sql("""
        SELECT 
            CASE 
                WHEN risk_score >= 0.8 THEN 'Critical'
                WHEN risk_score >= 0.6 THEN 'High'
                WHEN risk_score >= 0.4 THEN 'Medium'
                ELSE 'Low'
            END as risk_level,
            COUNT(*) as count
        FROM mothers
        GROUP BY risk_level
    """, conn)
    
    if not risk_dist.empty:
        fig = px.pie(risk_dist, values='count', names='risk_level', title='Risk Distribution')
        st.plotly_chart(fig)
    
    # Attendance patterns
    attendance = pd.read_sql("""
        SELECT 
            appointment_type,
            status,
            COUNT(*) as count
        FROM appointments
        GROUP BY appointment_type, status
    """, conn)
    
    if not attendance.empty:
        fig = px.bar(attendance, x='appointment_type', y='count', color='status', title='Appointment Attendance')
        st.plotly_chart(fig)
    
    # Feature importance analysis
    st.subheader("Risk Factor Analysis")
    if risk_model.feature_importance:
        importance_df = pd.DataFrame([
            {'Feature': k, 'Importance': v} 
            for k, v in risk_model.feature_importance.items()
        ]).sort_values('Importance', ascending=True).tail(10)
        
        fig = px.bar(importance_df, x='Importance', y='Feature', orientation='h', title='Top Risk Factors')
        st.plotly_chart(fig)
    
    # Village-wise analysis
    village_analysis = pd.read_sql("""
        SELECT 
            village,
            COUNT(*) as total_mothers,
            AVG(risk_score) as avg_risk,
            SUM(CASE WHEN risk_score > 0.6 THEN 1 ELSE 0 END) as high_risk_count
        FROM mothers
        GROUP BY village
        ORDER BY avg_risk DESC
    """, conn)
    
    if not village_analysis.empty:
        st.subheader("Village-wise Risk Analysis")
        st.dataframe(village_analysis)
    
    conn.close()

def admin_page():
    st.header("⚙️ System Administration")
    
    # Data management
    st.subheader("Data Management")
    
    conn = get_db_connection()
    
    # Show database tables
    tables = ['mothers', 'appointments', 'vhws', 'follow_ups', 'notifications']
    
    for table in tables:
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
        st.write(f"**{table}**: {count} records")
    
    # Show recent mothers
    st.subheader("Recent Mothers")
    recent_mothers = pd.read_sql("""
        SELECT name, age, risk_score, created_at 
        FROM mothers 
        ORDER BY created_at DESC 
        LIMIT 10
    """, conn)
    st.dataframe(recent_mothers)
    
    # Manual refresh button
    if st.button("🔄 Refresh Dashboard Counts"):
        st.rerun()
    
    conn.close()

if __name__ == "__main__":
    main()