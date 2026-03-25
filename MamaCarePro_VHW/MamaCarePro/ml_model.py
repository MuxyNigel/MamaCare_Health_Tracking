# ml_model_real.py (Fixed version)
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.exceptions import DataConversionWarning
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DataConversionWarning)

class RealMaternalRiskModel:
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=50,  # Reduced for smaller datasets
            learning_rate=0.1,
            max_depth=4,      # Reduced for smaller datasets
            random_state=42
        )
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = [
            'age', 'bmi', 'blood_pressure', 'gestational_age', 
            'previous_c_section', 'previous_miscarriages', 'previous_preterm_birth',
            'chronic_hypertension', 'diabetes', 'gestational_diabetes',
            'preeclampsia_history', 'multiple_pregnancy', 'smoking',
            'alcohol_use', 'family_history', 'hb_level', 'urine_protein', 'blood_glucose'
        ]
        self.is_trained = False
        self.feature_importance = None
    
    def load_real_dataset(self, csv_path=r"C:\Users\ACER\Desktop\MamaCarePro\data\maternal_data.csv"):
        """Load your real dataset"""
        try:
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded dataset with {len(df)} records")
            print(f"Dataset columns: {list(df.columns)}")
            return df
        except FileNotFoundError:
            print("⚠️ CSV file not found, generating synthetic data with your schema...")
            return self.generate_larger_synthetic_data()
    
    def generate_larger_synthetic_data(self, n_samples=2000):
        """Generate larger synthetic data matching your real dataset schema"""
        np.random.seed(42)
        
        data = {
            'age': np.random.randint(18, 45, n_samples),
            'bmi': np.random.normal(25, 5, n_samples),
            'blood_pressure': np.random.randint(90, 180, n_samples),
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
            'risk_level': None  # Will be calculated based on medical logic
        }
        
        df = pd.DataFrame(data)
        
        # Calculate risk level based on medical logic
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
        
        # Ensure we have at least 2 samples per class for stratification
        for risk_level in ['Low', 'Medium', 'High', 'Critical']:
            count = (df['risk_level'] == risk_level).sum()
            if count < 2:
                # Add some samples to ensure minimum count
                missing_count = 2 - count
                new_samples = df.head(missing_count).copy()
                new_samples['risk_level'] = risk_level
                df = pd.concat([df, new_samples], ignore_index=True)
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess the dataset"""
        df = df.copy()
        
        # Handle missing values
        df = df.fillna(df.median(numeric_only=True))
        
        # Encode categorical variables
        categorical_cols = ['risk_level']
        for col in categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        # Select features for training
        feature_cols = [col for col in self.feature_names if col in df.columns]
        X = df[feature_cols]
        y = df['risk_level_encoded'] if 'risk_level_encoded' in df.columns else df['risk_level']
        
        # Ensure all features exist
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0  # Default value for missing features
        
        X = X[self.feature_names]  # Ensure correct order
        
        return X, y
    
    def train(self, csv_path=None):
        """Train the model with real dataset"""
        if csv_path:
            df = self.load_real_dataset(csv_path)
        else:
            df = self.load_real_dataset()  # Use synthetic for now
        
        X, y = self.preprocess_data(df)
        
        # Check if we have enough samples for stratified split
        unique_classes = len(np.unique(y))
        if len(df) < 10 or unique_classes < 2:
            print("⚠️ Not enough data for train-test split, using all data for training")
            X_train, X_test, y_train, y_test = X, X, y, y
        else:
            # Use stratified split if we have enough samples
            test_size = min(0.2, 0.3)  # Use smaller test size for smaller datasets
            if len(df) < 20:
                test_size = 0.5  # For very small datasets, use 50% for testing
            
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42, stratify=y
                )
            except ValueError:
                # If stratify fails, use without stratification
                print("⚠️ Stratified split failed, using regular split")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )
        
        # Scale the features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train the model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate the model
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)
        
        print("=== Model Performance ===")
        print(f"Training samples: {len(X_train)}")
        print(f"Testing samples: {len(X_test)}")
        print(f"Training Accuracy: {self.model.score(X_train_scaled, y_train):.3f}")
        print(f"Testing Accuracy: {self.model.score(X_test_scaled, y_test):.3f}")
        
        try:
            print(f"ROC AUC Score: {roc_auc_score(y_test, y_prob, multi_class='ovr'):.3f}")
        except:
            print("ROC AUC calculation failed (likely due to small dataset)")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Store feature importance
        self.feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        
        return self.model
    
    def predict_risk(self, mother_data):
        """Predict risk level for a single mother"""
        if not self.is_trained:
            self.train()
        
        # Prepare features (ensure all required features are present)
        features = []
        for feature in self.feature_names:
            value = mother_data.get(feature, 0)  # Default to 0 if not provided
            features.append(value)
        
        features_array = np.array([features]).reshape(1, -1)
        features_scaled = self.scaler.transform(features_array)
        
        # Get prediction and probabilities
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Convert prediction back to risk level
        risk_levels = ['Low', 'Medium', 'High', 'Critical']
        if isinstance(prediction, (int, np.integer)):
            risk_level = risk_levels[prediction] if prediction < len(risk_levels) else 'Medium'
        else:
            risk_level = str(prediction)
        
        # Calculate risk score (0-1 scale for consistency)
        risk_score = probabilities.max()
        
        return {
            'risk_level': risk_level,
            'risk_score': float(risk_score),
            'all_probabilities': dict(zip(risk_levels[:len(probabilities)], probabilities)),
            'feature_importance': self.feature_importance
        }
    
    def get_feature_importance_plot(self):
        """Generate feature importance plot"""
        if self.feature_importance is None:
            return None
        
        importance_df = pd.DataFrame([
            {'Feature': k, 'Importance': v} 
            for k, v in self.feature_importance.items()
        ]).sort_values('Importance', ascending=True)
        
        fig = px.bar(
            importance_df.tail(10), 
            x='Importance', 
            y='Feature', 
            orientation='h',
            title='Top 10 Risk Factors'
        )
        return fig
    
    def save_model(self, filepath='real_risk_model.pkl'):
        """Save the trained model"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'is_trained': self.is_trained,
            'label_encoders': self.label_encoders
        }, filepath)
    
    def load_model(self, filepath='real_risk_model.pkl'):
        """Load a trained model"""
        try:
            loaded_data = joblib.load(filepath)
            self.model = loaded_data['model']
            self.scaler = loaded_data['scaler']
            self.feature_names = loaded_data['feature_names']
            self.feature_importance = loaded_data['feature_importance']
            self.is_trained = loaded_data['is_trained']
            self.label_encoders = loaded_data.get('label_encoders', {})
            return self
        except FileNotFoundError:
            print("No saved model found, training new model...")
            return self.train()

# Initialize and train the real model
try:
    real_risk_model = RealMaternalRiskModel()
    real_risk_model.train()
    real_risk_model.save_model()
    print("✅ Real ML Model trained and saved!")
except Exception as e:
    print(f"❌ Error training model: {e}")
    # Create and save a basic model
    real_risk_model = RealMaternalRiskModel()
    real_risk_model.train()
    real_risk_model.save_model()
    print("✅ Basic ML Model trained and saved!")