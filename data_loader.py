# data_loader.py (Updated version)
import pandas as pd
import sqlite3
import numpy as np
from ml_model_real import RealMaternalRiskModel

def clean_dataset():
    """Clean the dataset to handle blood pressure format"""
    try:
        df = pd.read_csv(r"C:\Users\ACER\Desktop\MamaCarePro\data\maternal_data.csv")
        print(f"Original dataset shape: {df.shape}")
        
        # Clean blood pressure column
        if 'blood_pressure' in df.columns:
            # Convert '110/82' format to numeric (take first number)
            df['blood_pressure'] = df['blood_pressure'].apply(
                lambda x: float(str(x).split('/')[0]) if pd.notna(x) and '/' in str(x) else float(x) if pd.notna(x) else 120.0
            )
        
        # Ensure all numeric columns are properly typed
        numeric_cols = ['age', 'bmi', 'blood_pressure', 'gestational_age', 'hb_level', 'blood_glucose']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median())
        
        # Save cleaned dataset
        df.to_csv('maternal_health_data_cleaned.csv', index=False)
        print(f"✅ Cleaned dataset saved with {len(df)} records")
        return 'maternal_health_data_cleaned.csv'
    except Exception as e:
        print(f"❌ Error cleaning dataset: {e}")
        return 'maternal_health_data.csv'  # Use original if cleaning fails

def load_real_data_to_db(csv_path='maternal_health_data.csv'):
    """Load real dataset into the database"""
    # First, clean the dataset
    clean_path = clean_dataset()
    
    try:
        # Load the real dataset
        df = pd.read_csv(clean_path)
        print(f"✅ Loaded {len(df)} records from {clean_path}")
        
        # Initialize the real model
        model = RealMaternalRiskModel().load_model()
        
        # Connect to database
        conn = sqlite3.connect('maternalcare.db')
        c = conn.cursor()
        
        # Insert each record into the mothers table with risk calculation
        inserted_count = 0
        for idx, row in df.iterrows():
            if inserted_count >= 1000:  # Limit to first 1000 records to avoid timeout
                break
                
            # Prepare data for risk calculation
            mother_data = {}
            for col in df.columns:
                if col in model.feature_names:
                    value = row[col]
                    # Handle blood pressure format
                    if col == 'blood_pressure' and isinstance(value, str) and '/' in str(value):
                        value = float(str(value).split('/')[0])
                    elif not pd.isna(value):
                        value = float(value)
                    else:
                        value = 0
                    mother_data[col] = value
            
            # Calculate risk
            risk_result = model.predict_risk(mother_data)
            
            # Insert into database
            try:
                c.execute("""
                    INSERT OR IGNORE INTO mothers (
                        name, age, phone, village, risk_score, risk_breakdown,
                        bmi, blood_pressure, gestational_age, previous_c_section,
                        previous_miscarriages, previous_preterm_birth, chronic_hypertension,
                        diabetes, gestational_diabetes, preeclampsia_history, multiple_pregnancy,
                        smoking, alcohol_use, family_history, hb_level, urine_protein, blood_glucose
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"Patient_{idx}",  # Name
                    row.get('age', 25),  # Age
                    f"+123456{idx:04d}",  # Phone (simulated)
                    "Unknown Village",  # Village
                    risk_result['risk_score'],  # Risk score
                    str(risk_result),  # Risk breakdown
                    row.get('bmi', 25.0),  # BMI
                    row.get('blood_pressure', 120),  # Blood pressure (now numeric)
                    row.get('gestational_age', 20),  # Gestational age
                    row.get('previous_c_section', 0),  # Previous C-section
                    row.get('previous_miscarriages', 0),  # Previous miscarriages
                    row.get('previous_preterm_birth', 0),  # Previous preterm birth
                    row.get('chronic_hypertension', 0),  # Chronic hypertension
                    row.get('diabetes', 0),  # Diabetes
                    row.get('gestational_diabetes', 0),  # Gestational diabetes
                    row.get('preeclampsia_history', 0),  # Preeclampsia history
                    row.get('multiple_pregnancy', 0),  # Multiple pregnancy
                    row.get('smoking', 0),  # Smoking
                    row.get('alcohol_use', 0),  # Alcohol use
                    row.get('family_history', 0),  # Family history
                    row.get('hb_level', 11.0),  # Hemoglobin level
                    row.get('urine_protein', 0),  # Urine protein
                    row.get('blood_glucose', 90)  # Blood glucose
                ))
                inserted_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting record {idx}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error for record {idx}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Loaded {inserted_count} records into database with risk scores")
        
    except FileNotFoundError:
        print(f"⚠️ File {clean_path} not found. Creating sample data instead.")
        create_larger_sample_data()
        load_real_data_to_db('maternal_health_data.csv')

def create_larger_sample_data():
    """Create a larger sample dataset with realistic medical data"""
    np.random.seed(42)
    n_samples = 2000  # Much larger dataset
    
    # Generate realistic medical data
    data = {
        'age': np.random.randint(18, 45, n_samples),
        'bmi': np.random.normal(25, 5, n_samples),
        'blood_pressure': np.random.randint(90, 180, n_samples),  # Numeric values
        'gestational_age': np.random.randint(1, 42, n_samples),
        'previous_c_section': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'previous_miscarriages': np.random.choice([0, 1, 2, 3], n_samples, p=[0.85, 0.1, 0.04, 0.01]),
        'previous_preterm_birth': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'chronic_hypertension': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'diabetes': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'gestational_diabetes': np.random.choice([0, 1], n_samples, p=[0.88, 0.12]),
        'preeclampsia_history': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'multiple_pregnancy': np.random.choice([0, 1], n_samples, p=[0.98, 0.02]),
        'smoking': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'alcohol_use': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'family_history': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'hb_level': np.random.normal(11, 2, n_samples),
        'urine_protein': np.random.choice([0, 1, 2, 3], n_samples, p=[0.7, 0.2, 0.08, 0.02]),
        'blood_glucose': np.random.normal(90, 20, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate risk levels based on medical logic
    risk_score = (
        (df['blood_pressure'] > 140) * 0.2 +
        (df['age'] > 35) * 0.1 +
        (df['age'] < 20) * 0.1 +
        (df['bmi'] > 30) * 0.1 +
        (df['bmi'] < 18.5) * 0.05 +
        (df['chronic_hypertension'] == 1) * 0.3 +
        (df['diabetes'] == 1) * 0.2 +
        (df['gestational_diabetes'] == 1) * 0.15 +
        (df['preeclampsia_history'] == 1) * 0.25 +
        (df['multiple_pregnancy'] == 1) * 0.2 +
        (df['smoking'] == 1) * 0.1 +
        (df['alcohol_use'] == 1) * 0.1 +
        (df['hb_level'] < 11) * 0.1 +
        (df['urine_protein'] > 0) * 0.2 +
        (df['blood_glucose'] > 140) * 0.15 +
        np.random.normal(0, 0.1, n_samples)  # Add noise
    )
    
    # Convert to risk levels
    df['risk_level'] = pd.cut(
        risk_score, 
        bins=[-np.inf, 0.3, 0.6, 0.8, np.inf], 
        labels=['Low', 'Medium', 'High', 'Critical'],
        include_lowest=True
    )
    
    # Ensure we have at least 2 samples per class
    for risk_level in ['Low', 'Medium', 'High', 'Critical']:
        count = (df['risk_level'] == risk_level).sum()
        if count < 2:
            # Add some samples to ensure minimum count
            missing_count = 2 - count
            new_samples = df.head(missing_count).copy()
            new_samples['risk_level'] = risk_level
            df = pd.concat([df, new_samples], ignore_index=True)
    
    df.to_csv('maternal_health_data.csv', index=False)
    print(f"✅ Created larger sample dataset with {len(df)} records: maternal_health_data.csv")
    print(f"Risk level distribution:\n{df['risk_level'].value_counts()}")

if __name__ == "__main__":
    # Create larger sample data if needed
    import os
    if not os.path.exists('maternal_health_data.csv'):
        create_larger_sample_data()
    
    # Initialize database with correct schema first
    from database import init_db
    init_db()
    
    # Load data into database
    load_real_data_to_db('maternal_health_data.csv')