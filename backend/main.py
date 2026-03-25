"""
Main Pipeline Script
Orchestrates the complete data preprocessing workflow
"""

import pandas as pd
from pathlib import Path
from backend.data_loader import DataLoader
from backend.data_preprocessor import DataPreprocessor
from backend.relationship_analyzer import RelationshipAnalyzer


def main():
    # Configuration
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BASE_PATH = PROJECT_ROOT / 'dataset' / 'sap-o2c-data'
    OUTPUT_PATH = PROJECT_ROOT / 'dataset' / 'processed_data'
    OUTPUT_PATH.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("SAP Order-to-Cash Dataset Preprocessing Pipeline")
    print("=" * 80)
    
    # Step 1: Load Data
    print("\n[Step 1] Loading data...")
    loader = DataLoader(BASE_PATH)
    entities = loader.load_all_entities()
    
    print("\n[Summary] Entity Overview:")
    summary_df = loader.get_entity_summary()
    print(summary_df.to_string(index=False))
    summary_df.to_csv(OUTPUT_PATH / 'entity_summary.csv', index=False)
    
    # Step 2: Preprocess Data
    print("\n" + "=" * 80)
    print("[Step 2] Preprocessing data...")
    preprocessor = DataPreprocessor()
    analyzer = RelationshipAnalyzer()
    
    processed_entities = preprocessor.preprocess_all(entities, analyzer.primary_keys)
    
    # Step 3: Analyze Relationships
    print("\n" + "=" * 80)
    print("[Step 3] Analyzing relationships...")
    
    print("\n[3.1] Validating Primary Keys:")
    pk_validation = analyzer.validate_primary_keys(processed_entities)
    for entity, result in pk_validation.items():
        if result['valid']:
            print(f"  ✓ {entity}: {result['total_records']} records, {result['unique_keys']} unique keys")
        else:
            print(f"  ✗ {entity}: Issues found - {result}")
    
    print("\n[3.2] Analyzing Foreign Key Relationships:")
    fk_analysis = analyzer.analyze_foreign_keys(processed_entities)
    fk_df = pd.DataFrame(fk_analysis)
    print(fk_df[['child_entity', 'parent_entity', 'child_keys', 'integrity_pct']].to_string(index=False))
    fk_df.to_csv(OUTPUT_PATH / 'foreign_key_analysis.csv', index=False)
    
    # Step 4: Generate Schema Documentation
    print("\n" + "=" * 80)
    print("[Step 4] Generating schema documentation...")
    schema_df = analyzer.get_schema_summary(processed_entities)
    schema_df.to_csv(OUTPUT_PATH / 'schema_summary.csv', index=False)
    print(f"  Schema summary saved with {len(schema_df)} columns across {len(processed_entities)} entities")
    
    # Step 5: Export Relationship Metadata
    print("\n[Step 5] Exporting relationship metadata...")
    analyzer.export_relationships_to_json(fk_analysis, OUTPUT_PATH / 'relationships.json')
    
    # Step 6: Save Processed Data
    print("\n" + "=" * 80)
    print("[Step 6] Saving processed data...")
    
    # Save as CSV
    csv_path = OUTPUT_PATH / 'csv'
    csv_path.mkdir(exist_ok=True)
    
    for entity_name, df in processed_entities.items():
        output_file = csv_path / f'{entity_name}.csv'
        df.to_csv(output_file, index=False)
        print(f"  Saved {entity_name}.csv ({len(df)} records)")
    
    # Save as Parquet (more efficient for large datasets)
    parquet_path = OUTPUT_PATH / 'parquet'
    parquet_path.mkdir(exist_ok=True)
    
    for entity_name, df in processed_entities.items():
        output_file = parquet_path / f'{entity_name}.parquet'
        df.to_parquet(output_file, index=False, engine='pyarrow')
    
    print(f"\n  ✓ Parquet files saved to {parquet_path}")
    
    # Step 7: Generate Summary Report
    print("\n" + "=" * 80)
    print("[Step 7] Final Summary Report")
    print("=" * 80)
    
    total_records = sum(len(df) for df in processed_entities.values())
    total_columns = sum(len(df.columns) for df in processed_entities.values())
    
    print(f"\n✓ Processing Complete!")
    print(f"  - Total Entities: {len(processed_entities)}")
    print(f"  - Total Records: {total_records:,}")
    print(f"  - Total Columns: {total_columns}")
    print(f"  - Relationships Identified: {len(fk_analysis)}")
    print(f"\nOutput Location: {OUTPUT_PATH.absolute()}")
    print("\nFiles Generated:")
    print("  1. entity_summary.csv - Overview of all entities")
    print("  2. schema_summary.csv - Detailed column-level schema")
    print("  3. foreign_key_analysis.csv - Relationship integrity analysis")
    print("  4. relationships.json - Graph-ready relationship metadata")
    print("  5. csv/ - Clean CSV files for each entity")
    print("  6. parquet/ - Optimized Parquet files for each entity")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
