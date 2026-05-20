"""
Demand Forecasting Models (Prophet + LSTM)
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import logging
from typing import Tuple, Dict, Any
import joblib
from datetime import datetime

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """Prophet-based demand forecasting."""
    
    def __init__(self, seasonality_mode: str = 'multiplicative'):
        """
        Initialize Prophet forecaster.
        
        Args:
            seasonality_mode: 'additive' or 'multiplicative'
        """
        self.seasonality_mode = seasonality_mode
        self.model = None
        self.forecast = None
    
    def prepare_data(self, df: pd.DataFrame, 
                     date_col: str = 'InvoiceDate',
                     value_col: str = 'TotalPrice') -> pd.DataFrame:
        """
        Prepare data for Prophet.
        
        Args:
            df: Transaction dataframe
            date_col: Date column
            value_col: Value column to forecast
            
        Returns:
            Prophet-formatted dataframe
        """
        # Aggregate to daily level
        daily_data = df.groupby(pd.Grouper(key=date_col, freq='D'))[value_col].sum().reset_index()
        daily_data.columns = ['ds', 'y']
        
        # Handle zero values
        daily_data['y'] = daily_data['y'].replace(0, daily_data['y'][daily_data['y'] > 0].mean())
        
        logger.info(f"Prepared {len(daily_data)} daily records for forecasting")
        
        return daily_data
    
    def fit(self, df: pd.DataFrame) -> 'ProphetForecaster':
        """
        Fit Prophet model.
        
        Args:
            df: Prophet-formatted dataframe (ds, y columns)
            
        Returns:
            Self
        """
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode=self.seasonality_mode,
            interval_width=0.95
        )
        
        self.model.fit(df)
        logger.info("Prophet model fitted")
        
        return self
    
    def forecast(self, periods: int = 30) -> pd.DataFrame:
        """
        Generate forecast.
        
        Args:
            periods: Number of periods to forecast
            
        Returns:
            Forecast dataframe
        """
        if self.model is None:
            raise ValueError("Model not fitted")
        
        future = self.model.make_future_dataframe(periods=periods)
        self.forecast = self.model.predict(future)
        
        logger.info(f"Generated forecast for {periods} periods")
        
        return self.forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
    
    def save(self, path: str):
        """Save model."""
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")


class LSTMForecaster(nn.Module):
    """LSTM-based demand forecasting."""
    
    def __init__(self, input_size: int = 1, hidden_size: int = 64, 
                 num_layers: int = 2, output_size: int = 1, dropout: float = 0.2):
        """
        Initialize LSTM model.
        
        Args:
            input_size: Number of input features
            hidden_size: Hidden layer size
            num_layers: Number of LSTM layers
            output_size: Number of output features
            dropout: Dropout rate
        """
        super(LSTMForecaster, self).__init__()
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                            batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        """Forward pass."""
        lstm_out, _ = self.lstm(x)
        predictions = self.fc(lstm_out[:, -1, :])
        return predictions


class LSTMTrainer:
    """Train and manage LSTM models."""
    
    def __init__(self, sequence_length: int = 30, hidden_size: int = 64,
                 learning_rate: float = 0.001, epochs: int = 100, batch_size: int = 32):
        """
        Initialize trainer.
        
        Args:
            sequence_length: Sequence length for LSTM
            hidden_size: Hidden layer size
            learning_rate: Learning rate
            epochs: Number of training epochs
            batch_size: Batch size
        """
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.scaler = MinMaxScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM.
        
        Args:
            data: Time series data
            
        Returns:
            Tuple of (X, y) sequences
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def fit(self, data: np.ndarray) -> 'LSTMTrainer':
        """
        Train LSTM model.
        
        Args:
            data: Time series data
            
        Returns:
            Self
        """
        # Scale data
        data_scaled = self.scaler.fit_transform(data.reshape(-1, 1)).flatten()
        
        # Prepare sequences
        X, y = self.prepare_sequences(data_scaled)
        
        # Convert to tensors
        X_tensor = torch.FloatTensor(X).reshape(X.shape[0], X.shape[1], 1).to(self.device)
        y_tensor = torch.FloatTensor(y).reshape(-1, 1).to(self.device)
        
        # Create dataset
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Initialize model
        self.model = LSTMForecaster(hidden_size=self.hidden_size).to(self.device)
        
        # Training
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()
        
        for epoch in range(self.epochs):
            total_loss = 0
            for X_batch, y_batch in dataloader:
                optimizer.zero_grad()
                predictions = self.model(X_batch)
                loss = criterion(predictions, y_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch + 1}/{self.epochs}, Loss: {total_loss:.6f}")
        
        logger.info("LSTM training completed")
        
        return self
    
    def forecast(self, data: np.ndarray, periods: int = 30) -> np.ndarray:
        """
        Generate forecast.
        
        Args:
            data: Historical data
            periods: Number of periods to forecast
            
        Returns:
            Forecast values
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        self.model.eval()
        
        # Scale data
        data_scaled = self.scaler.transform(data.reshape(-1, 1)).flatten()
        
        # Use last sequence for prediction
        last_sequence = data_scaled[-self.sequence_length:]
        predictions = []
        
        with torch.no_grad():
            current_sequence = last_sequence.copy()
            
            for _ in range(periods):
                X_input = torch.FloatTensor(current_sequence).reshape(1, self.sequence_length, 1).to(self.device)
                pred = self.model(X_input).item()
                predictions.append(pred)
                
                # Update sequence
                current_sequence = np.append(current_sequence[1:], pred)
        
        # Inverse transform
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        logger.info(f"Generated LSTM forecast for {periods} periods")
        
        return predictions


class EnsembleForecaster:
    """Ensemble Prophet + LSTM forecaster."""
    
    def __init__(self):
        self.prophet = ProphetForecaster()
        self.lstm = LSTMTrainer()
    
    def fit(self, df: pd.DataFrame, date_col: str = 'InvoiceDate', 
            value_col: str = 'TotalPrice'):
        """Fit both models."""
        # Prepare data
        daily_data = self.prophet.prepare_data(df, date_col, value_col)
        
        # Fit Prophet
        self.prophet.fit(daily_data)
        
        # Fit LSTM
        values = daily_data['y'].values
        self.lstm.fit(values)
        
        logger.info("Ensemble forecaster fitted")
    
    def forecast(self, periods: int = 30) -> pd.DataFrame:
        """Generate ensemble forecast."""
        if self.prophet.model is None or self.lstm.model is None:
            raise ValueError("Models not fitted")
        
        # Get individual forecasts
        prophet_forecast = self.prophet.forecast(periods)
        lstm_forecast = self.lstm.forecast(periods)
        
        # Ensemble (average)
        prophet_values = prophet_forecast['yhat'].values
        lstm_values = lstm_forecast
        
        ensemble_values = (prophet_values + lstm_values) / 2
        
        # Create output
        result = pd.DataFrame({
            'forecast_date': pd.date_range(start=datetime.now(), periods=periods, freq='D'),
            'prophet_forecast': prophet_values,
            'lstm_forecast': lstm_values,
            'ensemble_forecast': ensemble_values
        })
        
        logger.info(f"Generated ensemble forecast for {periods} periods")
        
        return result
