"""
Feature engineering utilities
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class RFMCalculator:
    """Calculate RFM (Recency, Frequency, Monetary) scores."""
    
    def __init__(self, reference_date: datetime = None):
        """
        Initialize RFM calculator.
        
        Args:
            reference_date: Reference date for calculations (default: max date in data)
        """
        self.reference_date = reference_date
        self.rfm_scores = None
    
    def calculate(self, df: pd.DataFrame, 
                  customer_col: str = 'CustomerID',
                  date_col: str = 'InvoiceDate',
                  amount_col: str = 'TotalPrice') -> pd.DataFrame:
        """
        Calculate RFM scores for each customer.
        
        Args:
            df: Transaction dataframe
            customer_col: Customer ID column
            date_col: Date column
            amount_col: Transaction amount column
            
        Returns:
            RFM dataframe with scores
        """
        if self.reference_date is None:
            self.reference_date = df[date_col].max()
        
        logger.info(f"Calculating RFM scores (reference: {self.reference_date})")
        
        # Calculate recency, frequency, monetary for each customer
        rfm = df.groupby(customer_col).agg({
            date_col: lambda x: (self.reference_date - x.max()).days,  # Recency
            customer_col: 'count',  # Frequency
            amount_col: 'sum'  # Monetary
        }).reset_index()
        
        rfm.columns = [customer_col, 'Recency', 'Frequency', 'Monetary']
        
        # Create RFM segments using quantiles
        rfm['R_segment'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
        rfm['F_segment'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4], duplicates='drop')
        rfm['M_segment'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4], duplicates='drop')
        
        # Calculate RFM score
        rfm['RFM_Score'] = rfm['R_segment'].astype(int) * 100 + \
                           rfm['F_segment'].astype(int) * 10 + \
                           rfm['M_segment'].astype(int)
        
        self.rfm_scores = rfm
        logger.info(f"RFM calculation complete. Unique customers: {len(rfm)}")
        
        return rfm


class TemporalFeatures:
    """Create temporal features from dates."""
    
    @staticmethod
    def create(df: pd.DataFrame, date_col: str = 'InvoiceDate') -> pd.DataFrame:
        """
        Create temporal features.
        
        Args:
            df: Dataframe
            date_col: Date column name
            
        Returns:
            Dataframe with temporal features
        """
        df = df.copy()
        
        df[date_col] = pd.to_datetime(df[date_col])
        
        df['Year'] = df[date_col].dt.year
        df['Month'] = df[date_col].dt.month
        df['Week'] = df[date_col].dt.isocalendar().week
        df['DayOfWeek'] = df[date_col].dt.dayofweek
        df['Day'] = df[date_col].dt.day
        df['Hour'] = df[date_col].dt.hour
        df['Quarter'] = df[date_col].dt.quarter
        df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
        
        # Create time-based features
        df['DayOfYear'] = df[date_col].dt.dayofyear
        df['MonthStart'] = df[date_col].dt.is_month_start.astype(int)
        df['MonthEnd'] = df[date_col].dt.is_month_end.astype(int)
        
        logger.info("Temporal features created")
        
        return df


class RollingStatistics:
    """Create rolling statistical features."""
    
    @staticmethod
    def create(df: pd.DataFrame, 
               group_col: str,
               value_col: str,
               windows: List[int] = [7, 30, 90],
               date_col: str = 'InvoiceDate') -> pd.DataFrame:
        """
        Create rolling statistics.
        
        Args:
            df: Dataframe
            group_col: Column to group by
            value_col: Column to calculate statistics on
            windows: List of window sizes
            date_col: Date column
            
        Returns:
            Dataframe with rolling features
        """
        df = df.copy()
        df = df.sort_values(date_col)
        
        for window in windows:
            window_str = f'{window}d'
            
            # Rolling mean
            df[f'{value_col}_rolling_mean_{window}d'] = df.groupby(group_col)[value_col]\
                .rolling(f'{window}d', on=date_col, min_periods=1).mean()\
                .reset_index(level=0, drop=True)
            
            # Rolling std
            df[f'{value_col}_rolling_std_{window}d'] = df.groupby(group_col)[value_col]\
                .rolling(f'{window}d', on=date_col, min_periods=1).std()\
                .reset_index(level=0, drop=True)
            
            # Rolling sum
            df[f'{value_col}_rolling_sum_{window}d'] = df.groupby(group_col)[value_col]\
                .rolling(f'{window}d', on=date_col, min_periods=1).sum()\
                .reset_index(level=0, drop=True)
        
        logger.info(f"Rolling statistics created for windows: {windows}")
        
        return df


class FeatureEngineer:
    """Comprehensive feature engineering pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with engineered features
        """
        self.logger.info("Starting feature engineering pipeline")
        
        # Temporal features
        df = TemporalFeatures.create(df)
        
        # RFM scores
        rfm_calc = RFMCalculator()
        rfm = rfm_calc.calculate(df)
        df = df.merge(rfm[['CustomerID', 'RFM_Score']], on='CustomerID', how='left')
        
        # Rolling statistics
        df = RollingStatistics.create(df, 'CustomerID', 'TotalPrice')
        
        # Additional features
        df['Price_per_Item'] = df['TotalPrice'] / df['Quantity']
        df['High_Value_Item'] = (df['UnitPrice'] > df['UnitPrice'].quantile(0.75)).astype(int)
        
        self.logger.info(f"Feature engineering complete. Shape: {df.shape}")
        
        return df
