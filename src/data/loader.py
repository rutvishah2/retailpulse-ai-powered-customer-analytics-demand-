"""
Data loading and validation utilities
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles data loading, cleaning, and validation."""
    
    def __init__(self, data_path: str):
        """
        Initialize data loader.
        
        Args:
            data_path: Path to CSV file
        """
        self.data_path = Path(data_path)
        self.df = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load(self) -> pd.DataFrame:
        """
        Load data from CSV.
        
        Returns:
            Loaded dataframe
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        self.logger.info(f"Loading data from {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        
        # Convert date column
        if 'InvoiceDate' in self.df.columns:
            self.df['InvoiceDate'] = pd.to_datetime(self.df['InvoiceDate'])
        
        self.logger.info(f"Loaded {len(self.df)} records with {self.df.shape[1]} columns")
        
        return self.df
    
    def validate(self) -> dict:
        """
        Validate data quality.
        
        Returns:
            Validation report
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load() first.")
        
        report = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'missing_values': self.df.isnull().sum().to_dict(),
            'duplicate_rows': self.df.duplicated().sum(),
            'data_types': self.df.dtypes.to_dict(),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2
        }
        
        self.logger.info(f"Validation report: {report['total_rows']} rows, "
                        f"{report['duplicate_rows']} duplicates found")
        
        return report
    
    def get_summary(self) -> pd.DataFrame:
        """Get statistical summary."""
        if self.df is None:
            raise ValueError("Data not loaded.")
        
        return self.df.describe()
    
    def train_test_split(self, test_size: float = 0.2, 
                        train_size: Optional[float] = None,
                        random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and testing sets.
        
        Args:
            test_size: Proportion of test set
            train_size: Proportion of train set
            random_state: Random seed
            
        Returns:
            Tuple of (train_df, test_df)
        """
        from sklearn.model_selection import train_test_split as sklearn_train_test_split
        
        train_df, test_df = sklearn_train_test_split(
            self.df,
            test_size=test_size,
            train_size=train_size,
            random_state=random_state
        )
        
        self.logger.info(f"Split data: {len(train_df)} train, {len(test_df)} test")
        
        return train_df, test_df
    
    def temporal_split(self, train_ratio: float = 0.8,
                       date_column: str = 'InvoiceDate') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data temporally (for time-series).
        
        Args:
            train_ratio: Proportion for training
            date_column: Date column name
            
        Returns:
            Tuple of (train_df, test_df)
        """
        if date_column not in self.df.columns:
            raise ValueError(f"Date column '{date_column}' not found")
        
        # Sort by date
        df_sorted = self.df.sort_values(date_column)
        
        # Split point
        split_idx = int(len(df_sorted) * train_ratio)
        train_df = df_sorted.iloc[:split_idx]
        test_df = df_sorted.iloc[split_idx:]
        
        self.logger.info(f"Temporal split: {len(train_df)} train, {len(test_df)} test")
        
        return train_df, test_df


def get_data_info(df: pd.DataFrame) -> dict:
    """Get comprehensive data information."""
    return {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.to_dict(),
        'missing_pct': (df.isnull().sum() / len(df) * 100).to_dict(),
        'date_range': (df['InvoiceDate'].min(), df['InvoiceDate'].max()) 
                      if 'InvoiceDate' in df.columns else None,
        'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
        'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
    }
