# init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('inventory.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            remark TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL, -- 'in' or 'out'
            item_id INTEGER,
            item_name TEXT,
            item_brand TEXT,
            item_model TEXT,
            quantity INTEGER,
            operation_date TEXT,
            delivery_company TEXT,
            tracking_number TEXT,
            install_location TEXT,
            remark TEXT,
            photo_path TEXT,
            operator TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # 可选：创建默认管理员
    # conn.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('admin', ?)", 
    #              (generate_password_hash('admin123'),))
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

if __name__ == '__main__':
    init_db()# init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('inventory.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            remark TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL, -- 'in' or 'out'
            item_id INTEGER,
            item_name TEXT,
            item_brand TEXT,
            item_model TEXT,
            quantity INTEGER,
            operation_date TEXT,
            delivery_company TEXT,
            tracking_number TEXT,
            install_location TEXT,
            remark TEXT,
            photo_path TEXT,
            operator TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # 可选：创建默认管理员
    # conn.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('admin', ?)", 
    #              (generate_password_hash('admin123'),))
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

if __name__ == '__main__':
    init_db()# init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('inventory.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            remark TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL, -- 'in' or 'out'
            item_id INTEGER,
            item_name TEXT,
            item_brand TEXT,
            item_model TEXT,
            quantity INTEGER,
            operation_date TEXT,
            delivery_company TEXT,
            tracking_number TEXT,
            install_location TEXT,
            remark TEXT,
            photo_path TEXT,
            operator TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # 可选：创建默认管理员
    # conn.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES ('admin', ?)", 
    #              (generate_password_hash('admin123'),))
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

if __name__ == '__main__':
    init_db()