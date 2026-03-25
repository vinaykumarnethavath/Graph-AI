"""
Data Loader Module
Loads JSONL files from the SAP Order-to-Cash dataset
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


class DataLoader:
    """Load and consolidate JSONL files from the dataset"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.entities = {}
        
    def load_entity(self, entity_folder: str) -> pd.DataFrame:
        """Load all JSONL files from an entity folder into a single DataFrame"""
        entity_path = self.base_path / entity_folder
        
        if not entity_path.exists():
            print(f"Warning: {entity_folder} does not exist")
            return pd.DataFrame()
        
        all_records = []
        jsonl_files = list(entity_path.glob("*.jsonl"))
        
        if not jsonl_files:
            print(f"Warning: No JSONL files found in {entity_folder}")
            return pd.DataFrame()
        
        for file_path in jsonl_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            all_records.append(record)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        df = pd.DataFrame(all_records)
        print(f"Loaded {entity_folder}: {len(df)} records, {len(df.columns)} columns")
        return df
    
    def load_all_entities(self) -> Dict[str, pd.DataFrame]:
        """Load all entities from the dataset"""
        entity_folders = [
            'sales_order_headers',
            'sales_order_items',
            'sales_order_schedule_lines',
            'outbound_delivery_headers',
            'outbound_delivery_items',
            'billing_document_headers',
            'billing_document_items',
            'billing_document_cancellations',
            'journal_entry_items_accounts_receivable',
            'payments_accounts_receivable',
            'business_partners',
            'business_partner_addresses',
            'customer_company_assignments',
            'customer_sales_area_assignments',
            'products',
            'product_descriptions',
            'product_plants',
            'product_storage_locations',
            'plants'
        ]
        
        for entity in entity_folders:
            df = self.load_entity(entity)
            if not df.empty:
                self.entities[entity] = df
        
        return self.entities
    
    def get_entity_summary(self) -> pd.DataFrame:
        """Get summary statistics for all loaded entities"""
        summary = []
        for name, df in self.entities.items():
            summary.append({
                'entity': name,
                'records': len(df),
                'columns': len(df.columns),
                'memory_mb': df.memory_usage(deep=True).sum() / 1024**2
            })
        return pd.DataFrame(summary)
