import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from urllib.parse import urlparse


load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
print("Connecting to host:", urlparse(DATABASE_URL).hostname)


def get_conn():
    # Fail after 10s instead of hanging forever if the database can't be reached.
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)