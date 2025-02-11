"""Script to check database schema and relationships."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.schema import ForeignKeyConstraint

# Database connection
DATABASE_URL = "postgresql://ahmed:0502747598@localhost:5432/aiwa_dev"

def main():
    """Check database schema and relationships."""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("\nDatabase Schema Analysis:")
    print("=" * 80)
    
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        print("-" * 40)
        
        # Get columns
        columns = inspector.get_columns(table_name)
        print("\nColumns:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}")
        
        # Get foreign keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print("\nForeign Keys:")
            for fk in fks:
                print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print("\nIndexes:")
            for idx in indexes:
                unique = "UNIQUE " if idx['unique'] else ""
                print(f"  - {unique}Index on {idx['column_names']}")

if __name__ == "__main__":
    main()
