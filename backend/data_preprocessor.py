"""
Data Preprocessor Module
Normalizes column names, handles data types, and cleans data
"""

import pandas as pd
import numpy as np
from typing import Dict
import re


class DataPreprocessor:
    """Preprocess and normalize data for graph construction"""
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Convert column names to snake_case and standardize"""
        df = df.copy()
        
        def to_snake_case(name: str) -> str:
            # Convert camelCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
            return s2.lower()
        
        df.columns = [to_snake_case(col) for col in df.columns]
        return df
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean data: handle nulls, empty strings, and data types"""
        df = df.copy()
        
        # Replace empty strings with None
        df = df.replace('', None)
        df = df.replace(r'^\s*$', None, regex=True)
        
        # Convert date columns
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        for col in date_columns:
            if col in df.columns and df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        # Convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    converted = pd.to_numeric(df[col], errors='coerce')
                    if converted.notna().sum() > len(df) * 0.5:  # If >50% are numeric
                        df[col] = converted
                except:
                    pass
        
        return df
    
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, primary_keys: list) -> pd.DataFrame:
        """Remove duplicate records based on primary keys"""
        if not primary_keys or not all(pk in df.columns for pk in primary_keys):
            return df
        
        before_count = len(df)
        df = df.drop_duplicates(subset=primary_keys, keep='first')
        after_count = len(df)
        
        if before_count > after_count:
            print(f"  Removed {before_count - after_count} duplicate records")
        
        return df
    
    @staticmethod
    def handle_nested_json(df: pd.DataFrame) -> pd.DataFrame:
        """Flatten nested JSON structures"""
        df = df.copy()
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains dict/list
                sample = df[col].dropna().head(1)
                if not sample.empty:
                    val = sample.iloc[0]
                    if isinstance(val, (dict, list)):
                        # Convert to JSON string for now
                        df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        
        return df
    
    def preprocess_all(self, entities: Dict[str, pd.DataFrame], 
                       primary_keys: Dict[str, list]) -> Dict[str, pd.DataFrame]:
        """Preprocess all entities"""
        processed = {}
        
        for name, df in entities.items():
            print(f"\nPreprocessing {name}...")
            df = self.normalize_column_names(df)
            df = self.handle_nested_json(df)
            df = self.clean_dataframe(df)
            
            # Remove duplicates if primary keys are defined
            if name in primary_keys:
                df = self.remove_duplicates(df, primary_keys[name])
            
            processed[name] = df
            print(f"  Final shape: {df.shape}")
        
        return processed
