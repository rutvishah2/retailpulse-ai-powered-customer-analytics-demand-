"""
Customer Segmentation Models
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
import logging
from typing import Tuple, Dict, Any
import joblib

logger = logging.getLogger(__name__)


class CustomerSegmentation:
    """Segment customers using clustering algorithms."""
    
    def __init__(self, method: str = 'kmeans', n_clusters: int = 6):
        """
        Initialize segmentation model.
        
        Args:
            method: Clustering method ('kmeans' or 'dbscan')
            n_clusters: Number of clusters
        """
        self.method = method
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.model = None
        self.labels = None
        self.feature_names = None
    
    def prepare_features(self, df: pd.DataFrame, 
                        feature_cols: list = None) -> np.ndarray:
        """
        Prepare and scale features for clustering.
        
        Args:
            df: Customer dataframe with RFM scores
            feature_cols: Columns to use (if None, uses RFM features)
            
        Returns:
            Scaled feature matrix
        """
        if feature_cols is None:
            feature_cols = ['Recency', 'Frequency', 'Monetary']
        
        # Select features
        X = df[feature_cols].copy()
        
        # Handle missing values
        X = X.fillna(X.median())
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        self.feature_names = feature_cols
        logger.info(f"Features prepared: {feature_cols}")
        
        return X_scaled
    
    def fit(self, X: np.ndarray) -> 'CustomerSegmentation':
        """
        Fit clustering model.
        
        Args:
            X: Feature matrix
            
        Returns:
            Self
        """
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            self.labels = self.model.fit_predict(X)
            
            # Calculate metrics
            silhouette = silhouette_score(X, self.labels)
            davies_bouldin = davies_bouldin_score(X, self.labels)
            inertia = self.model.inertia_
            
            logger.info(f"KMeans fitted with {self.n_clusters} clusters")
            logger.info(f"Silhouette Score: {silhouette:.4f}, Davies-Bouldin: {davies_bouldin:.4f}, Inertia: {inertia:.2f}")
            
            return self
        
        elif self.method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=5)
            self.labels = self.model.fit_predict(X)
            
            n_clusters = len(set(self.labels)) - (1 if -1 in self.labels else 0)
            logger.info(f"DBSCAN fitted with {n_clusters} clusters")
            
            return self
        
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict clusters.
        
        Args:
            X: Feature matrix
            
        Returns:
            Cluster labels
        """
        if self.model is None:
            raise ValueError("Model not fitted yet")
        
        if self.method == 'kmeans':
            return self.model.predict(X)
        else:
            return self.model.predict(X)
    
    def get_segment_profiles(self, df: pd.DataFrame, 
                             original_features: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Get segment profiles and characteristics.
        
        Args:
            df: Customer dataframe with cluster labels
            original_features: Original feature values before scaling
            
        Returns:
            Segment profile dataframe
        """
        profiles = []
        
        for segment in np.unique(self.labels):
            segment_mask = df['Segment'] == segment
            segment_data = df[segment_mask]
            
            profile = {
                'Segment': segment,
                'Customer_Count': len(segment_data),
                'Customer_Pct': f"{len(segment_data) / len(df) * 100:.1f}%",
                'Avg_Recency': segment_data['Recency'].mean(),
                'Avg_Frequency': segment_data['Frequency'].mean(),
                'Avg_Monetary': segment_data['Monetary'].mean(),
                'Total_Revenue': segment_data['Monetary'].sum()
            }
            profiles.append(profile)
        
        profile_df = pd.DataFrame(profiles)
        logger.info(f"Generated profiles for {len(profiles)} segments")
        
        return profile_df
    
    def save(self, path: str):
        """Save model and scaler."""
        joblib.dump((self.model, self.scaler), path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model and scaler."""
        self.model, self.scaler = joblib.load(path)
        logger.info(f"Model loaded from {path}")


def segment_customers(df: pd.DataFrame, n_clusters: int = 6) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Segment customers using RFM and KMeans.
    
    Args:
        df: Customer RFM dataframe
        n_clusters: Number of clusters
        
    Returns:
        Tuple of (customer segments, segment profiles)
    """
    logger.info("Starting customer segmentation")
    
    # Initialize segmentation
    segmentation = CustomerSegmentation(method='kmeans', n_clusters=n_clusters)
    
    # Prepare features
    X = segmentation.prepare_features(df)
    
    # Fit model
    segmentation.fit(X)
    
    # Add segment labels
    df['Segment'] = segmentation.labels
    
    # Get profiles
    profiles = segmentation.get_segment_profiles(df)
    
    return df, profiles
