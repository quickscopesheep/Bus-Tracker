import sqlite3
import xml.etree.cElementTree as ET

class DataSetParser:
    def __init__(self, stream, db : sqlite3.Cursor):
        self.db = db
        self.tree = ET.parse(stream)

        pass
    
    def parse(self):
        pass