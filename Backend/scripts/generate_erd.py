from eralchemy2 import render_er
import os

# Database connection string
db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Output file path
output_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'database_erd.pdf')

# Create docs directory if it doesn't exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Generate the ERD
try:
    render_er(db_url, output_path)
    print(f"ERD successfully generated at: {output_path}")
except Exception as e:
    print(f"Error generating ERD: {str(e)}")
