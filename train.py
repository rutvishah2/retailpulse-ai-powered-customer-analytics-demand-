"""
RetailPulse - Main Training Pipeline
Production-ready ML model training and evaluation
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import setup_logger, load_config
from src.data.loader import DataLoader
from src.features.engineer import FeatureEngineer
from src.models.segmentation import segment_customers
from src.models.forecasting import EnsembleForecaster
from src.models.churn import ChurnPredictor
from src.models.inventory import InventoryOptimizer

# Setup logging
logger = setup_logger("RetailPulse-Pipeline")
logger.info("=" * 80)
logger.info("RetailPulse - AI-Powered Customer Analytics & Demand Forecasting")
logger.info("Version: 2.0 | Author: Zidio Development | Date: March 2026")
logger.info("=" * 80)


class RetailPulsePipeline:
    """End-to-end ML pipeline for RetailPulse."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize pipeline."""
        self.config = load_config(config_path)
        self.logger = setup_logger("Pipeline")
        
        # MLflow setup
        self.setup_mlflow()
    
    def setup_mlflow(self):
        """Configure MLflow tracking."""
        tracking_uri = self.config['mlflow']['tracking_uri']
        experiment_name = self.config['mlflow']['experiment_name']
        
        # Set tracking URI
        mlflow.set_tracking_uri(tracking_uri)
        
        # Create/set experiment
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
        except:
            experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
        
        mlflow.set_experiment(experiment_name)
        
        self.logger.info(f"MLflow configured: {tracking_uri}")
    
    def load_data(self) -> pd.DataFrame:
        """Load and validate data."""
        self.logger.info("Step 1: Loading data...")
        
        loader = DataLoader(self.config['data']['input_path'])
        df = loader.load()
        
        # Validate
        validation = loader.validate()
        self.logger.info(f"Data validation report: {validation['total_rows']} rows, "
                        f"{validation['duplicate_rows']} duplicates")
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features."""
        self.logger.info("Step 2: Feature engineering...")
        
        engineer = FeatureEngineer()
        df_features = engineer.create_features(df)
        
        self.logger.info(f"Features created. Shape: {df_features.shape}")
        
        return df_features
    
    def segment_customers_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run customer segmentation."""
        self.logger.info("Step 3: Customer segmentation...")
        
        # Get RFM
        from src.features.engineer import RFMCalculator
        rfm_calc = RFMCalculator()
        rfm = rfm_calc.calculate(df)
        
        # Segment
        segments, profiles = segment_customers(rfm, n_clusters=self.config['segmentation']['n_clusters'])
        
        self.logger.info(f"Segmentation complete:\n{profiles.to_string()}")
        
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_param("n_clusters", self.config['segmentation']['n_clusters'])
            mlflow.log_metrics({
                f"segment_{i}_size": row['Customer_Count'] 
                for i, row in profiles.iterrows()
            })
        
        return segments
    
    def forecast_demand_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run demand forecasting."""
        self.logger.info("Step 4: Demand forecasting...")
        
        # Prepare time series data
        forecaster = EnsembleForecaster()
        forecaster.fit(df, date_col='InvoiceDate', value_col='TotalPrice')
        
        # Generate forecast
        forecast = forecaster.forecast(periods=self.config['forecasting']['horizons'][1])
        
        self.logger.info(f"Forecast generated for {len(forecast)} periods")
        self.logger.info(f"\nForecast preview:\n{forecast.head().to_string()}")
        
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_param("forecasting_method", "ensemble")
            mlflow.log_metrics({
                "forecast_horizon": self.config['forecasting']['horizons'][1]
            })
        
        return forecast
    
    def predict_churn_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run churn prediction."""
        self.logger.info("Step 5: Churn prediction...")
        
        predictor = ChurnPredictor(
            max_depth=self.config['churn']['xgboost']['max_depth'],
            learning_rate=self.config['churn']['xgboost']['learning_rate'],
            n_estimators=self.config['churn']['xgboost']['n_estimators']
        )
        
        # Create labels
        churn_labels = predictor.create_churn_labels(
            df,
            lookback_days=self.config['churn']['lookback_days'],
            target_days=self.config['churn']['target_days']
        )
        
        # Create features
        churn_features = predictor.create_features(
            df,
            lookback_days=self.config['churn']['lookback_days']
        )
        
        # Prepare data
        X, y, feature_names = predictor.prepare_data(churn_features, churn_labels)
        
        # Split and train
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        predictor.fit(X_train, y_train)
        
        # Evaluate
        from sklearn.metrics import classification_report, roc_auc_score
        y_pred_proba = predictor.predict(X_test)
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        self.logger.info(f"Churn prediction AUC-ROC: {auc_score:.4f}")
        
        # Get predictions for all
        y_pred_all = predictor.predict(X)
        
        # Create output
        result = churn_features[['CustomerID']].copy()
        result['Churn_Probability'] = y_pred_all
        result['Is_At_Risk'] = y_pred_all > self.config['churn']['probability_threshold']
        
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_param("churn_model_type", "xgboost")
            mlflow.log_metrics({
                "auc_roc": auc_score,
                "at_risk_customers": result['Is_At_Risk'].sum()
            })
        
        return result
    
    def optimize_inventory_pipeline(self, df: pd.DataFrame, 
                                   churn_predictions: pd.DataFrame) -> pd.DataFrame:
        """Run inventory optimization."""
        self.logger.info("Step 6: Inventory optimization...")
        
        optimizer = InventoryOptimizer(
            safety_stock_factor=self.config['inventory']['safety_stock_factor'],
            lead_time_days=self.config['inventory']['lead_time_days'],
            service_level=self.config['inventory']['service_level']
        )
        
        # Create simple forecast dictionary (daily average by product)
        forecast_data = {}
        for product in df['StockCode'].unique():
            daily_avg = df[df['StockCode'] == product]['Quantity'].mean()
            forecast_data[product] = daily_avg
        
        # Get recommendations
        recommendations = optimizer.optimize_inventory(
            product_data=df,
            forecast_data=forecast_data,
            churn_data=churn_predictions
        )
        
        self.logger.info(f"Inventory optimization complete. {len(recommendations)} products reviewed")
        
        # Count by action
        action_counts = recommendations['Action'].value_counts()
        self.logger.info(f"Actions recommended:\n{action_counts.to_string()}")
        
        return recommendations
    
    def save_results(self, outputs: dict):
        """Save results to outputs directory."""
        self.logger.info("Saving results...")
        
        output_dir = Path(self.config['data']['output_path'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for name, data in outputs.items():
            filename = f"{name}_{timestamp}.csv"
            filepath = output_dir / filename
            
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False)
                self.logger.info(f"Saved {name} to {filepath}")
    
    def run(self):
        """Execute full pipeline."""
        try:
            # Load data
            df = self.load_data()
            
            # Feature engineering
            df_features = self.engineer_features(df)
            
            # Customer segmentation
            segments = self.segment_customers_pipeline(df_features)
            
            # Demand forecasting
            forecast = self.forecast_demand_pipeline(df_features)
            
            # Churn prediction
            churn_predictions = self.predict_churn_pipeline(df_features)
            
            # Inventory optimization
            inventory_recommendations = self.optimize_inventory_pipeline(
                df_features, churn_predictions
            )
            
            # Save results
            self.save_results({
                'customer_segments': segments,
                'demand_forecast': forecast,
                'churn_predictions': churn_predictions,
                'inventory_recommendations': inventory_recommendations
            })
            
            self.logger.info("=" * 80)
            self.logger.info("Pipeline execution completed successfully!")
            self.logger.info(f"Results saved to {self.config['data']['output_path']}")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
            raise


if __name__ == "__main__":
    # Run pipeline
    pipeline = RetailPulsePipeline()
    pipeline.run()
