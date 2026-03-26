# pages/vhw_dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def get_db_connection():
    return sqlite3.connect('maternalcare.db')

def vhw_dashboard():
    st.title("👩‍⚕️ VHW Dashboard")
    
    # VHW selection (for demo)
    vhw_name = st.selectbox("Select VHW", ["John Doe", "Jane Smith", "Maria Garcia"])
    
    conn = get_db_connection()
    
    # Get high-risk mothers assigned to VHW (or all high-risk mothers for demo)
    assigned_mothers = pd.read_sql("""
        SELECT 
            m.id,
            m.name, 
            m.phone, 
            m.village, 
            m.risk_score, 
            m.edd,
            m.created_at
        FROM mothers m
        WHERE m.risk_score > 0.4  -- High and medium risk
        ORDER BY m.risk_score DESC
    """, conn)
    
    st.subheader(f"High-Priority Mothers for {vhw_name}")
    
    if assigned_mothers.empty:
        st.info("No high-risk mothers assigned yet.")
    else:
        # Display mothers in a scrollable table with action buttons
        for idx, row in assigned_mothers.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{row['name']}**")
                    st.write(f"Village: {row['village']}")
                
                with col2:
                    st.write(f"Phone: {row['phone']}")
                    st.write(f"EDD: {row['edd']}")
                
                with col3:
                    risk_color = "red" if row['risk_score'] > 0.7 else "orange" if row['risk_score'] > 0.4 else "green"
                    st.metric("Risk", f"{row['risk_score']:.2f}")
                
                with col4:
                    if st.button(f"Follow-up", key=f"followup_{row['id']}"):
                        # Log follow-up action
                        st.success("✅ Follow-up logged!")
        
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
        st.dataframe(follow_up_tasks)
    
    conn.close()

if __name__ == "__main__":
    vhw_dashboard()