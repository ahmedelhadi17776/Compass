import os
from pymongo import MongoClient
import pandas as pd


def get_client():
    return MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        maxPoolSize=20,
        minPoolSize=5
    )


def fetch_collection(coll):
    client = get_client()
    db = client[os.getenv("MONGODB_DATABASE", "compass_ai")]
    return pd.DataFrame(list(db[coll].find()))
