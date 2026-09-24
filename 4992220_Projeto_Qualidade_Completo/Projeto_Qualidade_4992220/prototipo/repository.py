"""Persistência local SQLite. Não contém dados pessoais reais."""
import sqlite3
from domain import UNITS, PRODUCTS

class LocalConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

def connect(path):
    db = sqlite3.connect(str(path), timeout=30, isolation_level=None, factory=LocalConnection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize(path, stock=100):
    with connect(path) as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS stock(unit TEXT,sku TEXT,qty INTEGER CHECK(qty>=0),PRIMARY KEY(unit,sku));
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,owner TEXT,unit TEXT,idem TEXT,hash TEXT,status TEXT,total INTEGER,points INTEGER,payload TEXT,UNIQUE(owner,unit,idem));
        CREATE TABLE IF NOT EXISTS order_requests(order_id TEXT PRIMARY KEY REFERENCES orders(id),payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS points(owner TEXT PRIMARY KEY,balance INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,order_id TEXT,unit TEXT,status TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        for unit in UNITS:
            for sku in PRODUCTS:
                db.execute('INSERT OR IGNORE INTO stock VALUES(?,?,?)',(unit,sku,stock))
