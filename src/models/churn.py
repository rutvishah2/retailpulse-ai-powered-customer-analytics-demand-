"""
Churn Prediction Models
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import shap
import logging
from typing import Tuple, Dict, Any
import joblib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChurnPredictor:
    """Predict customer churn using XGBoost with SHAP explainability."""
    
    def __init__(self, max_depth: int = 6, learning_rate: float = 0.1,
                 n_estimators: int = 100, random_state: int = 42):
        """
        Initialize churn predictor.
        
        Args:
            max_depth: Tree depth
            learning_rate: Learning rate
            n_estimators: Number of estimators
            random_state: Random seed
        """
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        self.explainer = None
    
    def create_churn_labels(self, df: pd.DataFrame, 
                           lookback_days: int = 90,
                           target_days: int = 30,
                           date_col: str = 'InvoiceDate',
                           customer_col: str = 'CustomerID',
                           value_col: str = 'TotalPrice') -> pd.DataFrame:
        """
        Create churn labels for training.
        
        Args:
            df: Transaction dataframe
            lookback_days: Historical period for features
            target_days: Future period to check for churn
            date_col: Date column
            customer_col: Customer ID column
            value_col: Transaction value column
            
        Returns:
            Dataframe with churn labels
        """
        # Get observation period boundaries
        max_date = df[date_col].max()
        observation_start = max_date - timedelta(days=lookback_days)
        observation_end = max_date
        future_start = observation_end + timedelta(days=1)
        future_end = future_start + timedelta(days=target_days)
        
        # Filter historical period
        historical_df = df[(df[date_col] >= observation_start) & (df[date_col] <= observation_end)]
        
        # Filter future period
        future_df = df[(df[date_col] >= future_start) & (df[date_col] <= future_end)]
        
        # Get customers in historical period
        customers_historical = set(historical_df[customer_col].unique())
        
        # Get customers in future period
        customers_future = set(future_df[customer_col].unique())
        
        # Create churn labels (1 = churned, 0 = active)
        churn_labels = pd.DataFrame({
            customer_col: list(customers_historical),
            'Churn': [1 if cust not in customers_future else 0 for cust in customers_historical]
        })
        
        logger.info(f"Created churn labels: {churn_labels['Churn'].sum()} churned out of {len(churn_labels)}")
        
        return churn_labels
    
    def create_features(self, df: pd.DataFrame,
                       lookback_days: int = 90,
                       date_col: str = 'InvoiceDate',
                       customer_col: str = 'CustomerID',
                       value_col: str = 'TotalPrice') -> pd.DataFrame:
        """
        Create features for churn prediction.
        
        Args:
            df: Transaction dataframe
            lookback_days: Historical period
            date_col: Date column
            customer_col: Customer ID column
            value_col: Transaction value column
            
        Returns:
            Customer features dataframe
        """
        max_date = df[date_col].max()
        observation_start = max_date - timedelta(days=lookback_days)
        
        # Filter to observation period
        obs_df = df[(df[date_col] >= observation_start) & (df[date_col] <= max_date)]
        
        # Calculate features
        features = obs_df.groupby(customer_col).agg({
            value_col: ['sum', 'mean', 'std', 'count', 'min', 'max'],
            date_col: ['min', 'max'],
            'Quantity': ['sum', 'mean'],
            'UnitPrice': ['mean', 'std']
        }).reset_index()
        
        features.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                           for col in features.columns.values]
        features.rename(columns={customer_col: customer_col}, inplace=True)
        
        # Calculate recency
        features['Recency'] = (max_date - features[f'{date_col}_max']).dt.days
        
        # Fill missing values
        features = features.fillna(0)
        
        logger.info(f"Created features with shape {features.shape}")
        
        return features
    
    def prepare_data(self, features: pd.DataFrame, labels: pd.DataFrame,
                    drop_cols: list = None) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Prepare data for modeling.
        
        Args:
            features: Feature dataframe
            labels: Label dataframe
            drop_cols: Columns to drop
            
        Returns:
            Tuple of (X, y, feature_names)
        """
        # Merge features and labels
        data = features.merge(labels, on='CustomerID', how='inner')
        
        # Separate X and y
        X = data.drop(['CustomerID', 'Churn'] + (drop_cols or []), axis=1, errors='ignore')
        y = data['Churn'].values
        
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        logger.info(f"Data prepared: {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")
        
        return X_scaled, y, self.feature_names
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'ChurnPredictor':
        """
        Train XGBoost model.
        
        Args:
            X: Feature matrix
            y: Labels
            
        Returns:
            Self
        """
        self.model = xgb.XGBClassifier(
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        self.model.fit(X, y, verbose=False)
        
        # Create SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        logger.info("XGBoost model trained")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict churn probability."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        return self.model.predict_proba(X)[:, 1]
    
    def explain_prediction(self, X: np.ndarray, sample_idx: int = 0):
        """Get SHAP explanation for a prediction."""
        if self.explainer is None:
            raise ValueError("Explainer not initialized")
        
        shap_values = self.explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Get values for churn class
        
        return shap_values
    
    def save(self, path: str):
        """Save model and scaler."""
        joblib.dump((self.model, self.scaler, self.feature_names), path)
        logger.info(f"Model saved to {path}")
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance


def identify_at_risk_customers(churn_proba: np.ndarray, 
                               probability_threshold: float = 0.5) -> np.ndarray:
    """
    Identify at-risk customers.
    
    Args:
        churn_proba: Churn probabilities
        probability_threshold: Threshold for classification
        
    Returns:
        Boolean array of at-risk customers
    """
    return churn_proba > probability_threshold
