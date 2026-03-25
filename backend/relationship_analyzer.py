"""
Relationship Analyzer Module
Identifies primary keys, foreign keys, and relationships between entities
"""

import pandas as pd
from typing import Dict, List, Tuple
import json


class RelationshipAnalyzer:
    """Analyze and identify relationships between entities"""
    
    def __init__(self):
        # Define known primary keys for SAP O2C entities
        self.primary_keys = {
            'sales_order_headers': ['sales_order'],
            'sales_order_items': ['sales_order', 'sales_order_item'],
            'sales_order_schedule_lines': ['sales_order', 'sales_order_item', 'schedule_line'],
            'outbound_delivery_headers': ['delivery_document'],
            'outbound_delivery_items': ['delivery_document', 'delivery_document_item'],
            'billing_document_headers': ['billing_document'],
            'billing_document_items': ['billing_document', 'billing_document_item'],
            'billing_document_cancellations': ['cancelled_billing_document'],
            'journal_entry_items_accounts_receivable': ['company_code', 'fiscal_year', 'accounting_document', 'accounting_document_item'],
            'payments_accounts_receivable': ['company_code', 'fiscal_year', 'accounting_document'],
            'business_partners': ['business_partner'],
            'business_partner_addresses': ['business_partner', 'address_id'],
            'customer_company_assignments': ['customer', 'company_code'],
            'customer_sales_area_assignments': ['customer', 'sales_organization', 'distribution_channel', 'division'],
            'products': ['product'],
            'product_descriptions': ['product', 'language'],
            'product_plants': ['product', 'plant'],
            'product_storage_locations': ['product', 'plant', 'storage_location'],
            'plants': ['plant']
        }
        
        # Define known foreign key relationships
        self.relationships = [
            # Sales Order relationships
            ('sales_order_items', 'sales_order', 'sales_order_headers', 'sales_order'),
            ('sales_order_schedule_lines', 'sales_order', 'sales_order_headers', 'sales_order'),
            ('sales_order_schedule_lines', ['sales_order', 'sales_order_item'], 
             'sales_order_items', ['sales_order', 'sales_order_item']),
            ('sales_order_headers', 'sold_to_party', 'business_partners', 'business_partner'),
            ('sales_order_items', 'material', 'products', 'product'),
            ('sales_order_items', 'production_plant', 'plants', 'plant'),
            
            # Delivery relationships
            ('outbound_delivery_items', 'delivery_document', 'outbound_delivery_headers', 'delivery_document'),
            ('outbound_delivery_items', 'material', 'products', 'product'),
            
            # Billing relationships
            ('billing_document_items', 'billing_document', 'billing_document_headers', 'billing_document'),
            ('billing_document_items', 'material', 'products', 'product'),
            ('billing_document_cancellations', 'cancelled_billing_document', 
             'billing_document_headers', 'billing_document'),
            
            # Product relationships
            ('product_descriptions', 'product', 'products', 'product'),
            ('product_plants', 'product', 'products', 'product'),
            ('product_plants', 'plant', 'plants', 'plant'),
            ('product_storage_locations', 'product', 'products', 'product'),
            ('product_storage_locations', 'plant', 'plants', 'plant'),
            
            # Customer relationships
            ('customer_company_assignments', 'customer', 'business_partners', 'business_partner'),
            ('customer_sales_area_assignments', 'customer', 'business_partners', 'business_partner'),
        ]
    
    def validate_primary_keys(self, entities: Dict[str, pd.DataFrame]) -> Dict[str, dict]:
        """Validate primary keys and check for uniqueness"""
        validation_results = {}
        
        for entity_name, df in entities.items():
            if entity_name not in self.primary_keys:
                continue
            
            pks = self.primary_keys[entity_name]
            missing_cols = [pk for pk in pks if pk not in df.columns]
            
            if missing_cols:
                validation_results[entity_name] = {
                    'valid': False,
                    'missing_columns': missing_cols
                }
                continue
            
            # Check uniqueness
            duplicates = df.duplicated(subset=pks).sum()
            total_records = len(df)
            null_count = df[pks].isnull().any(axis=1).sum()
            
            validation_results[entity_name] = {
                'valid': duplicates == 0 and null_count == 0,
                'primary_keys': pks,
                'total_records': total_records,
                'duplicates': duplicates,
                'null_keys': null_count,
                'unique_keys': len(df.drop_duplicates(subset=pks))
            }
        
        return validation_results
    
    def analyze_foreign_keys(self, entities: Dict[str, pd.DataFrame]) -> List[dict]:
        """Analyze foreign key relationships and validate referential integrity"""
        fk_analysis = []
        
        for rel in self.relationships:
            if len(rel) == 4:
                child_entity, child_key, parent_entity, parent_key = rel
                child_keys = [child_key] if isinstance(child_key, str) else child_key
                parent_keys = [parent_key] if isinstance(parent_key, str) else parent_key
            else:
                continue
            
            if child_entity not in entities or parent_entity not in entities:
                continue
            
            child_df = entities[child_entity]
            parent_df = entities[parent_entity]
            
            # Check if columns exist
            if not all(ck in child_df.columns for ck in child_keys):
                continue
            if not all(pk in parent_df.columns for pk in parent_keys):
                continue
            
            # Analyze relationship
            child_values = child_df[child_keys].dropna()
            if len(child_keys) == 1:
                child_unique = set(child_values[child_keys[0]].unique())
                parent_unique = set(parent_df[parent_keys[0]].unique())
            else:
                child_unique = set(child_values.apply(tuple, axis=1).unique())
                parent_unique = set(parent_df[parent_keys].apply(tuple, axis=1).unique())
            
            orphaned = child_unique - parent_unique
            
            fk_analysis.append({
                'child_entity': child_entity,
                'child_keys': child_keys,
                'parent_entity': parent_entity,
                'parent_keys': parent_keys,
                'total_child_records': len(child_df),
                'unique_child_values': len(child_unique),
                'unique_parent_values': len(parent_unique),
                'orphaned_records': len(orphaned),
                'integrity_pct': 100 * (1 - len(orphaned) / len(child_unique)) if child_unique else 100
            })
        
        return fk_analysis
    
    def get_schema_summary(self, entities: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate schema summary with data types"""
        schema_info = []
        
        for entity_name, df in entities.items():
            pks = self.primary_keys.get(entity_name, [])
            
            for col in df.columns:
                schema_info.append({
                    'entity': entity_name,
                    'column': col,
                    'data_type': str(df[col].dtype),
                    'is_primary_key': col in pks,
                    'null_count': df[col].isnull().sum(),
                    'null_pct': 100 * df[col].isnull().sum() / len(df),
                    'unique_values': df[col].nunique(),
                    'sample_value': str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else None
                })
        
        return pd.DataFrame(schema_info)
    
    def export_relationships_to_json(self, fk_analysis: List[dict], output_path: str):
        """Export relationship metadata to JSON"""
        metadata = {
            'primary_keys': self.primary_keys,
            'foreign_key_relationships': fk_analysis
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"Relationship metadata saved to {output_path}")
