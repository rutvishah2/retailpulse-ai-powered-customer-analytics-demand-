"""
Inventory Optimization Logic
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """Optimize inventory based on demand forecasts and churn predictions."""
    
    def __init__(self, safety_stock_factor: float = 1.5,
                 lead_time_days: int = 3,
                 service_level: float = 0.95):
        """
        Initialize optimizer.
        
        Args:
            safety_stock_factor: Multiplier for safety stock
            lead_time_days: Lead time for orders
            service_level: Target service level
        """
        self.safety_stock_factor = safety_stock_factor
        self.lead_time_days = lead_time_days
        self.service_level = service_level
    
    def calculate_reorder_point(self, avg_daily_demand: float,
                               demand_std: float) -> float:
        """
        Calculate reorder point.
        
        Args:
            avg_daily_demand: Average daily demand
            demand_std: Standard deviation of demand
            
        Returns:
            Reorder point
        """
        # Z-score for service level
        z_score = stats.norm.ppf(self.service_level)
        
        # Safety stock
        safety_stock = z_score * demand_std * np.sqrt(self.lead_time_days)
        
        # Reorder point = (avg demand * lead time) + safety stock
        reorder_point = (avg_daily_demand * self.lead_time_days) + safety_stock
        
        return max(reorder_point, 0)
    
    def calculate_economic_order_quantity(self, annual_demand: float,
                                         ordering_cost: float,
                                         holding_cost: float) -> float:
        """
        Calculate Economic Order Quantity (EOQ).
        
        Args:
            annual_demand: Annual demand quantity
            ordering_cost: Cost per order
            holding_cost: Cost per unit per year
            
        Returns:
            EOQ quantity
        """
        if holding_cost <= 0:
            return annual_demand / 12  # Default to monthly order
        
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        
        return max(eoq, 1)
    
    def optimize_inventory(self, product_data: pd.DataFrame,
                          forecast_data: pd.DataFrame,
                          churn_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate inventory optimization recommendations.
        
        Args:
            product_data: Product sales data
            forecast_data: Demand forecast
            churn_data: Customer churn predictions
            
        Returns:
            Optimization recommendations
        """
        recommendations = []
        
        for product_id in product_data['StockCode'].unique():
            product_sales = product_data[product_data['StockCode'] == product_id]
            
            # Calculate metrics
            total_quantity_sold = product_sales['Quantity'].sum()
            avg_daily_demand = product_sales['Quantity'].mean()
            demand_std = product_sales['Quantity'].std() or avg_daily_demand * 0.1
            avg_price = product_sales['UnitPrice'].mean()
            
            # Get forecast
            product_forecast = forecast_data.get(product_id, avg_daily_demand)
            
            # Adjust for churn impact
            churn_rate = churn_data['Churn'].mean()
            adjusted_forecast = product_forecast * (1 - churn_rate)
            
            # Calculate inventory parameters
            reorder_point = self.calculate_reorder_point(avg_daily_demand, demand_std)
            eoq = self.calculate_economic_order_quantity(
                total_quantity_sold,
                ordering_cost=50,  # Fixed cost per order
                holding_cost=avg_price * 0.2  # 20% of product value
            )
            
            # Calculate recommended stock levels
            min_stock = reorder_point
            max_stock = reorder_point + eoq
            
            # Classify product
            product_class = self._classify_product(total_quantity_sold, avg_price)
            
            recommendation = {
                'StockCode': product_id,
                'Product_Class': product_class,
                'Current_Avg_Daily_Demand': avg_daily_demand,
                'Forecasted_Demand_30d': adjusted_forecast,
                'Reorder_Point': reorder_point,
                'Min_Stock_Level': min_stock,
                'Max_Stock_Level': max_stock,
                'Economic_Order_Quantity': eoq,
                'Safety_Stock': reorder_point - (avg_daily_demand * self.lead_time_days),
                'Action': self._recommend_action(min_stock, max_stock, total_quantity_sold)
            }
            
            recommendations.append(recommendation)
        
        result_df = pd.DataFrame(recommendations)
        logger.info(f"Generated inventory recommendations for {len(result_df)} products")
        
        return result_df
    
    def _classify_product(self, quantity_sold: float, price: float) -> str:
        """Classify product using ABC analysis."""
        revenue = quantity_sold * price
        
        if revenue > revenue * 0.7:
            return 'A'  # High-value
        elif revenue > revenue * 0.3:
            return 'B'  # Medium-value
        else:
            return 'C'  # Low-value
    
    def _recommend_action(self, min_stock: float, max_stock: float, 
                         current_quantity: float) -> str:
        """Recommend action based on stock levels."""
        if current_quantity < min_stock:
            return 'URGENT_REORDER'
        elif current_quantity < min_stock * 1.2:
            return 'REORDER_SOON'
        elif current_quantity > max_stock:
            return 'REDUCE_STOCK'
        else:
            return 'MAINTAIN'
    
    def calculate_cost_savings(self, current_inventory: float,
                              optimized_inventory: float,
                              holding_cost_per_unit: float) -> float:
        """
        Calculate potential cost savings.
        
        Args:
            current_inventory: Current inventory level
            optimized_inventory: Optimized inventory level
            holding_cost_per_unit: Cost per unit per period
            
        Returns:
            Projected savings
        """
        savings = (current_inventory - optimized_inventory) * holding_cost_per_unit
        
        return max(savings, 0)


class StockoutPrevention:
    """Prevent stockouts using demand forecasting and inventory optimization."""
    
    @staticmethod
    def calculate_stockout_risk(current_stock: float,
                               daily_demand: float,
                               lead_time_days: int) -> float:
        """
        Calculate risk of stockout.
        
        Args:
            current_stock: Current stock quantity
            daily_demand: Daily demand quantity
            lead_time_days: Lead time for replenishment
            
        Returns:
            Stockout risk (0-1)
        """
        days_of_stock = current_stock / max(daily_demand, 0.1)
        
        if days_of_stock >= lead_time_days:
            return 0.0
        else:
            return 1.0 - (days_of_stock / lead_time_days)
    
    @staticmethod
    def estimate_lost_sales(stockout_days: int,
                           daily_demand: float,
                           unit_price: float) -> float:
        """
        Estimate lost sales from stockout.
        
        Args:
            stockout_days: Duration of stockout
            daily_demand: Daily demand quantity
            unit_price: Unit price
            
        Returns:
            Estimated lost revenue
        """
        return stockout_days * daily_demand * unit_price
