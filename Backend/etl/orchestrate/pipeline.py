from load.to_parquet import save_to_parquet
from load.to_duckdb import save as save_to_duckdb
from transform.normalize_and_join import normalize_and_join
from extract.from_mongo import fetch_collection
from extract.from_postgres import fetch_table
import sys
import os
# Ensure etl/ is in path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def run_pipeline():
    print("[ETL] Extracting from PostgreSQL...")
    tasks = fetch_table("tasks")
    habits = fetch_table("habits")

    print("[ETL] Extracting from MongoDB...")
    ai_logs = fetch_collection("model_usage")

    print("[ETL] Transforming and joining data...")
    combined = normalize_and_join(tasks, habits, ai_logs)

    print("[ETL] Loading to DuckDB...")
    save_to_duckdb(combined)

    print("[ETL] Loading to Parquet...")
    save_to_parquet(combined)

    print("[ETL] Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
