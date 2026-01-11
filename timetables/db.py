import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()
db_loc = os.environ['DB_PATH']

def init_db():
    cur = conn.cursor()
    
    pass

conn = sqlite3.connect(db_loc + 'timetables.db')
init_db()