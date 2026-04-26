from flask import Flask, request, jsonify
import os
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
DB_PATH = os.path.join(os.path.dirname(__file__), "products.db")

# ---------------- DB ----------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            image TEXT,
            category TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- API ----------------

@app.route("/products", methods=["GET"])
def get_products():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/add", methods=["POST"])
def add_product():
    data = request.json

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products VALUES (NULL,?,?,?,?)",
        (data["name"], data["price"], data["image"], data["category"])
    )
    conn.commit()
    conn.close()

    return {"status": "added"}


@app.route("/update", methods=["POST"])
def update_product():
    data = request.json

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET name=?, price=?, image=?, category=? WHERE id=?",
        (data["name"], data["price"], data["image"], data["category"], data["id"])
    )
    conn.commit()
    conn.close()

    return {"status": "updated"}


@app.route("/delete", methods=["POST"])
def delete_product():
    data = request.json

    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (data["id"],))
    conn.commit()
    conn.close()

    return {"status": "deleted"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)