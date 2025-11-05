import sqlite3

DB = "kissat.db"

# https://docs.python.org/3/library/sqlite3.html

def init():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            image_url TEXT NOT NULL,
            tag TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    con.commit()
    con.close()


def save_cat(user_id, username, image_url, tag=None):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    cur.execute(
        "INSERT INTO cats (user_id, username, image_url, tag) VALUES (?, ?, ?, ?)",
        (user_id, username, image_url, tag)
    )
    
    con.commit()
    con.close()



def get_all_cats(limit):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    cur.execute(
        "SELECT id, user_id, username, image_url, tag, timestamp FROM cats ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    
    results = cur.fetchall()
    con.close()

    cats = []

    for row in results:
        cat = {
            "id": row[0],
            "user_id": row[1],
            "username": row[2],
            "image_url": row[3],
            "tag": row[4],
            "timestamp": row[5]
        }
        cats.append(cat)

    return cats

"""
tulevaisuudessa tilastoihin... 

def get_user_cats(user_id, limit):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    cur.execute(
        "SELECT id, image_url, tag, timestamp FROM cats WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", # uusin ensin
        (user_id, limit)
    )
    
    results = cur.fetchall()
    con.close()
    
    return [
        {
            "id": row[0],
            "image_url": row[1],
            "tag": row[2],
            "timestamp": row[3]
        }
        for row in results
    ]

def get_user_count(user_id):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM cats WHERE user_id = ?", (user_id,))
    count = cur.fetchone()[0]
    
    con.close()
    return count
"""