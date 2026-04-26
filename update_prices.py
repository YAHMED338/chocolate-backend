import sqlite3
import os
import shutil
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from tkinter import ttk

# -------------------- CLEAN PATHS (IMPORTANT FIX) --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "products.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# -------------------- DB --------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
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


def fetch_products(search="", category="All"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if category and category != "All":
        query += " AND category=?"
        params.append(category)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_product(name, price, image, category):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO products VALUES (NULL,?,?,?,?)",
                (name, price, image, category))
    conn.commit()
    conn.close()


def update_product(pid, name, price, image, category):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE products SET name=?, price=?, image=?, category=? WHERE id=?",
                (name, price, image, category, pid))
    conn.commit()
    conn.close()


def delete_product(pid):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# -------------------- BACKUP (OPTIONAL FIXED) --------------------

def backup_db():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    ts = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(DB_PATH, os.path.join(BACKUP_DIR, f"backup_{ts}.db"))


# -------------------- APP --------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Pro Manager")
        self.root.geometry("1100x650")

        self.style = tb.Style(theme="darkly")
        init_db()

        self.selected_id = None
        self.img = None

        main = tb.Frame(root, padding=10)
        main.pack(fill=BOTH, expand=True)

        left = tb.Frame(main)
        left.pack(side=LEFT, fill=Y, padx=10)

        right = tb.Frame(main)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=10)

        # search
        self.search = tb.Entry(left)
        self.search.pack(fill=X, pady=5)
        self.search.bind("<KeyRelease>", lambda e: self.load())

        self.category = tb.Combobox(left, values=["All"])
        self.category.set("All")
        self.category.pack(fill=X, pady=5)
        self.category.bind("<<ComboboxSelected>>", lambda e: self.load())

        # table
        self.tree = ttk.Treeview(left, columns=("id","name","price","category","image"), show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("price", text="Price")
        self.tree.heading("category", text="Category")

        self.tree.column("id", width=40)
        self.tree.column("name", width=130)
        self.tree.column("price", width=70)
        self.tree.column("category", width=100)
        self.tree.column("image", width=0, stretch=False)

        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select)

        # form
        form = tb.Labelframe(right, text="Product Details", padding=15)
        form.pack(fill=BOTH, expand=True)

        self.name = tb.Entry(form)
        self.price = tb.Entry(form)
        self.image = tb.Entry(form)
        self.category_in = tb.Entry(form)

        tb.Label(form, text="Name").grid(row=0, column=0, sticky=W)
        tb.Label(form, text="Price").grid(row=1, column=0, sticky=W)
        tb.Label(form, text="Image").grid(row=2, column=0, sticky=W)
        tb.Label(form, text="Category").grid(row=3, column=0, sticky=W)

        self.name.grid(row=0, column=1, sticky="ew")
        self.price.grid(row=1, column=1, sticky="ew")
        self.image.grid(row=2, column=1, sticky="ew")
        self.category_in.grid(row=3, column=1, sticky="ew")

        form.columnconfigure(1, weight=1)

        tb.Button(form, text="Browse", command=self.browse).grid(row=2, column=2)

        self.preview = tb.Label(form, text="Image Preview")
        self.preview.grid(row=4, column=0, columnspan=3, pady=10)

        btns = tb.Frame(form)
        btns.grid(row=5, column=0, columnspan=3, pady=10)

        tb.Button(btns, text="Add", bootstyle=SUCCESS, command=self.add).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Update", bootstyle=WARNING, command=self.update).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Delete", bootstyle=DANGER, command=self.delete).pack(side=LEFT, padx=6)
        tb.Button(btns, text="Clear", bootstyle=SECONDARY, command=self.clear).pack(side=LEFT, padx=6)

        self.load()

    # ---------------- LOAD ----------------

    def load(self):
        self.tree.delete(*self.tree.get_children())
        data = fetch_products(self.search.get(), self.category.get())

        cats = list(set([d[4] for d in data if d[4]]))
        self.category["values"] = ["All"] + cats

        for p in data:
            self.tree.insert("", tk.END, iid=p[0], values=(p[0], p[1], p[2], p[4], p[3]))

    # ---------------- SELECT ----------------

    def select(self, e):
        sel = self.tree.focus()
        if not sel:
            return

        vals = self.tree.item(sel)["values"]

        self.selected_id = vals[0]

        self.clear_fields_only()

        self.name.insert(0, vals[1])
        self.price.insert(0, vals[2])
        self.category_in.insert(0, vals[3])
        self.image.insert(0, vals[4])

        self.show_image(vals[4])

    # ---------------- IMAGE ----------------

    def browse(self):
        f = filedialog.askopenfilename()
        if f:
            self.image.delete(0, tk.END)
            self.image.insert(0, f)
            self.show_image(f)

    def show_image(self, path):
        try:
            img = Image.open(path)
            img = img.resize((180,180))
            self.img = ImageTk.PhotoImage(img)
            self.preview.config(image=self.img, text="")
        except:
            self.preview.config(image="", text="No Image")

    # ---------------- CRUD ----------------

    def add(self):
        insert_product(self.name.get(), float(self.price.get()), self.image.get(), self.category_in.get())
        backup_db()
        self.load()

    def update(self):
        if not self.selected_id:
            messagebox.showerror("Error", "Select a product first")
            return

        update_product(self.selected_id,
                       self.name.get(),
                       float(self.price.get()),
                       self.image.get(),
                       self.category_in.get())

        backup_db()
        self.load()

    def delete(self):
        if not self.selected_id:
            return

        delete_product(self.selected_id)
        backup_db()
        self.load()
        self.clear()

    # ---------------- CLEAR ----------------

    def clear_fields_only(self):
        self.name.delete(0, tk.END)
        self.price.delete(0, tk.END)
        self.image.delete(0, tk.END)
        self.category_in.delete(0, tk.END)
        self.preview.config(image="", text="Image Preview")

    def clear(self):
        self.selected_id = None
        self.clear_fields_only()


# ---------------- RUN ----------------

if __name__ == "__main__":
    print("DB USED:", os.path.abspath(DB_PATH))
    root = tb.Window(themename="darkly")
    App(root)
    root.mainloop()