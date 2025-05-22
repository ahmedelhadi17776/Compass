import pandas as pd
from typing import List


def normalize_and_join(tasks: pd.DataFrame, habits: pd.DataFrame, ai_logs: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and join tasks, habits, and AI logs into a unified event dataframe.
    - Standardizes column names
    - Unifies timestamps
    - Joins on user_id/session_id where possible
    - Adds a 'source' column to distinguish data origin
    """
    # Example normalization [just example]
    tasks = tasks.copy()
    habits = habits.copy()
    ai_logs = ai_logs.copy()

    tasks['source'] = 'task'
    habits['source'] = 'habit'
    ai_logs['source'] = 'ai_log'

    # Standardize timestamp columns
    if 'created_at' in tasks:
        tasks['timestamp'] = pd.to_datetime(tasks['created_at'])
    if 'created_at' in habits:
        habits['timestamp'] = pd.to_datetime(habits['created_at'])
    if 'timestamp' in ai_logs:
        ai_logs['timestamp'] = pd.to_datetime(ai_logs['timestamp'])

    # Select common columns (expand as needed)
    cols = ['user_id', 'timestamp', 'source']
    tasks = tasks[[c for c in cols if c in tasks.columns]]
    habits = habits[[c for c in cols if c in habits.columns]]
    ai_logs = ai_logs[[c for c in cols if c in ai_logs.columns]]

    combined = pd.concat([tasks, habits, ai_logs], ignore_index=True)
    combined = combined.sort_values('timestamp')
    return combined
