from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
import os
import sqlite3
import time

app = Flask(__name__)
app.secret_key = "food_mall_secret"
DB_FILE = "food_mall.db"
OUTLET_PASSWORD = "outlet"
TAX_RATE = 0.05


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def is_admin():
    return session.get("is_admin") is True


def get_cart():
    return session.setdefault("cart", {})


def clear_cart():
    session.pop("cart", None)
    session.pop("cart_outlet_id", None)


def build_cart_details(cart, outlet_id):
    if not cart:
        return [], 0, 0, 0

    item_ids = [int(item_id) for item_id in cart.keys()]
    placeholders = ",".join(["?"] * len(item_ids))

    db = get_db()
    cur = db.cursor()
    cur.execute(
        f"""
        SELECT item_id, item_name, price
        FROM food_items
        WHERE outlet_id = ? AND item_id IN ({placeholders})
        """,
        [outlet_id] + item_ids
    )
    items = cur.fetchall()
    db.close()

    item_map = {item["item_id"]: item for item in items}
    cart_items = []
    subtotal = 0

    for item_id_str, qty in cart.items():
        item_id = int(item_id_str)
        item = item_map.get(item_id)
        if not item:
            continue
        line_total = item["price"] * qty
        subtotal += line_total
        cart_items.append({
            "item_id": item_id,
            "item_name": item["item_name"],
            "price": item["price"],
            "quantity": qty,
            "line_total": line_total
        })

    tax = int(round(subtotal * TAX_RATE))
    total = subtotal + tax
    return cart_items, subtotal, tax, total


# ---------------- WELCOME ----------------
@app.route("/")
def welcome():
    table_no = request.args.get("table", type=int) or session.get("table_no")
    if table_no is not None:
        session["table_no"] = table_no

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT outlet_id, outlet_name, category
        FROM outlets
        WHERE is_active = 1
        ORDER BY outlet_name
    """)
    outlets = cur.fetchall()
    db.close()

    return render_template("index.html", outlets=outlets, table_no=table_no)



# ---------------- QR GALLERY ----------------
@app.route("/qr")
def qr_gallery():
    qr_dir = os.path.join(app.static_folder, "qr")
    qr_files = []
    if os.path.isdir(qr_dir):
        for name in os.listdir(qr_dir):
            if name.lower().endswith(".png"):
                qr_files.append(name)
    qr_files.sort()

    qr_items = []
    for name in qr_files:
        label = name.replace(".png", "").replace("_", " ")
        qr_items.append({
            "label": label,
            "url": url_for("static", filename=f"qr/{name}")
        })

    return render_template("qr_gallery.html", qr_items=qr_items)
# ---------------- MENU ----------------
@app.route("/menu/<int:outlet_id>")
def menu(outlet_id):
    table_no = request.args.get("table", type=int) or session.get("table_no")
    if table_no is not None:
        session["table_no"] = table_no

    if session.get("cart_outlet_id") != outlet_id:
        clear_cart()
        session["cart_outlet_id"] = outlet_id

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT outlet_id, outlet_name, category
        FROM outlets
        WHERE outlet_id = ? AND is_active = 1
    """, (outlet_id,))
    outlet = cur.fetchone()

    if outlet is None:
        db.close()
        return redirect("/")

    cur.execute("""
        SELECT item_id, item_name, description, image_url, price
        FROM food_items
        WHERE outlet_id = ? AND is_available = 1
        ORDER BY item_name
    """, (outlet_id,))
    items = cur.fetchall()
    db.close()

    cart = get_cart()
    cart_items, subtotal, tax, total = build_cart_details(cart, outlet_id)

    return render_template(
        "menu.html",
        outlet=outlet,
        items=items,
        table_no=table_no,
        cart_items=cart_items,
        subtotal=subtotal,
        tax=tax,
        total=total
    )


# ---------------- CART ----------------
@app.route("/cart/add/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    outlet_id = session.get("cart_outlet_id")
    if outlet_id is None:
        return redirect("/")

    qty = request.form.get("quantity", "1")
    try:
        qty = int(qty)
    except ValueError:
        qty = 1

    if qty < 1:
        qty = 1

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT item_id FROM food_items WHERE item_id = ? AND outlet_id = ? AND is_available = 1",
        (item_id, outlet_id)
    )
    row = cur.fetchone()
    db.close()

    if row is None:
        return redirect(url_for("menu", outlet_id=outlet_id))

    cart = get_cart()
    cart[str(item_id)] = cart.get(str(item_id), 0) + qty
    session["cart"] = cart

    return redirect(url_for("menu", outlet_id=outlet_id, table=session.get("table_no")))


@app.route("/cart")
def cart_view():
    outlet_id = session.get("cart_outlet_id")
    if outlet_id is None:
        return redirect("/")

    cart = get_cart()
    cart_items, subtotal, tax, total = build_cart_details(cart, outlet_id)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        tax=tax,
        total=total
    )


@app.route("/cart/update", methods=["POST"])
def update_cart():
    outlet_id = session.get("cart_outlet_id")
    if outlet_id is None:
        return redirect("/")

    cart = {}
    for key, value in request.form.items():
        if not key.startswith("qty_"):
            continue
        item_id = key.replace("qty_", "")
        try:
            qty = int(value)
        except ValueError:
            qty = 0
        if qty > 0:
            cart[item_id] = qty

    session["cart"] = cart
    return redirect(url_for("cart_view"))


# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    outlet_id = session.get("cart_outlet_id")
    table_no = session.get("table_no")

    if outlet_id is None or table_no is None:
        return redirect("/")

    cart = get_cart()
    cart_items, subtotal, tax, total = build_cart_details(cart, outlet_id)

    if request.method == "POST":
        if not cart_items:
            return redirect(url_for("menu", outlet_id=outlet_id))

        method = request.form.get("method", "UPI")

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO orders (table_no, outlet_id, status, subtotal, tax, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
            (table_no, outlet_id, "Pending", subtotal, tax, total)
        )
        order_id = cur.lastrowid

        for item in cart_items:
            cur.execute(
                """
                INSERT INTO order_items (order_id, item_id, item_name, price, quantity, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (order_id, item["item_id"], item["item_name"], item["price"], item["quantity"], item["line_total"])
            )

        transaction_ref = f"MOCK-{order_id}-{int(time.time())}"
        cur.execute(
            "INSERT INTO payments (order_id, amount, method, status, transaction_ref) VALUES (?, ?, ?, ?, ?)",
            (order_id, total, method, "Paid", transaction_ref)
        )

        db.commit()
        db.close()

        clear_cart()

        return redirect(url_for("status_page", order_id=order_id))

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        table_no=table_no
    )


# ---------------- STATUS PAGE ----------------
@app.route("/status/<int:order_id>")
def status_page(order_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order = cur.fetchone()
    if order is None:
        db.close()
        return "Order not found", 404

    cur.execute(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order_id,)
    )
    items = cur.fetchall()

    cur.execute("SELECT * FROM payments WHERE order_id = ? ORDER BY payment_id DESC", (order_id,))
    payment = cur.fetchone()

    db.close()
    return render_template("status.html", order=order, items=items, payment=payment)


# ---------------- OUTLET LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        outlet_id = request.form.get("outlet_id", "").strip()
        password = request.form.get("password", "").strip()

        if outlet_id.isdigit() and password == OUTLET_PASSWORD:
            session["outlet_id"] = int(outlet_id)
            return redirect(url_for("kitchen_outlet"))

        return "Invalid Login"

    return render_template("login.html")


# ---------------- KITCHEN ----------------
@app.route("/kitchen")
def kitchen_outlet():
    outlet_id = session.get("outlet_id")
    if outlet_id is None:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT
            orders.order_id,
            orders.table_no,
            orders.status,
            orders.total_amount,
            orders.created_at
        FROM orders
        WHERE orders.outlet_id = ?
        ORDER BY orders.order_id DESC
    """, (outlet_id,))
    orders = cur.fetchall()

    order_items_map = {}
    if orders:
        order_ids = [str(order["order_id"]) for order in orders]
        placeholders = ",".join(["?"] * len(order_ids))
        cur.execute(
            f"SELECT order_id, item_name, quantity FROM order_items WHERE order_id IN ({placeholders})",
            order_ids
        )
        for row in cur.fetchall():
            order_items_map.setdefault(row["order_id"], []).append(row)

    db.close()

    return render_template("kitchen.html", orders=orders, order_items_map=order_items_map, outlet_id=outlet_id)


# ---------------- UPDATE STATUS ----------------
@app.route("/update/<int:order_id>", methods=["POST"])
def update(order_id):
    outlet_id = session.get("outlet_id")
    if outlet_id is None:
        return redirect("/login")

    new_status = request.form.get("status")
    allowed = {"Preparing", "Ready", "Completed"}
    if new_status not in allowed:
        return "Invalid status", 400

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT outlet_id FROM orders WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    if row is None:
        db.close()
        return "Order not found", 404

    if int(row["outlet_id"]) != int(outlet_id):
        db.close()
        return "Forbidden", 403

    cur.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?", (new_status, order_id))
    db.commit()
    db.close()

    return redirect("/kitchen")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM admin_users WHERE username = ?", (username,))
        admin = cur.fetchone()
        db.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        return "Invalid Login"

    return render_template("admin_login.html")


# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect("/admin/login")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if not is_admin():
        return redirect("/admin/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT outlet_id, outlet_name, category, is_active FROM outlets ORDER BY outlet_name")
    outlets = cur.fetchall()

    cur.execute("""
        SELECT
            food_items.item_id,
            food_items.item_name,
            food_items.price,
            food_items.image_url,
            food_items.is_available,
            outlets.outlet_name
        FROM food_items
        JOIN outlets ON food_items.outlet_id = outlets.outlet_id
        ORDER BY outlets.outlet_name, food_items.item_name
    """)
    items = cur.fetchall()

    cur.execute("""
        SELECT order_id, table_no, outlet_id, status, total_amount, created_at
        FROM orders
        ORDER BY order_id DESC
        LIMIT 20
    """)
    orders = cur.fetchall()

    cur.execute("""
        SELECT method, COUNT(*) AS count, SUM(amount) AS total
        FROM payments
        GROUP BY method
    """)
    payments_summary = cur.fetchall()

    db.close()

    return render_template(
        "outlet_dashboard.html",
        outlets=outlets,
        items=items,
        orders=orders,
        payments_summary=payments_summary
    )


# ---------------- ADMIN ADD OUTLET ----------------
@app.route("/admin/outlet/add", methods=["POST"])
def add_outlet():
    if not is_admin():
        return redirect("/admin/login")

    outlet_name = request.form.get("outlet_name", "").strip()
    category = request.form.get("category", "").strip()

    if outlet_name and category:
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO outlets (outlet_name, category) VALUES (?, ?)", (outlet_name, category))
        db.commit()
        db.close()

    return redirect("/admin")


# ---------------- ADMIN TOGGLE OUTLET ----------------
@app.route("/admin/outlet/toggle/<int:outlet_id>", methods=["POST"])
def toggle_outlet(outlet_id):
    if not is_admin():
        return redirect("/admin/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE outlets SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE outlet_id = ?", (outlet_id,))
    db.commit()
    db.close()

    return redirect("/admin")


# ---------------- ADMIN ADD ITEM ----------------
@app.route("/admin/item/add", methods=["POST"])
def add_item():
    if not is_admin():
        return redirect("/admin/login")

    item_name = request.form.get("item_name", "").strip()
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    price = request.form.get("price", "").strip()
    outlet_id = request.form.get("outlet_id", "").strip()

    if item_name and price.isdigit() and outlet_id.isdigit():
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO food_items (outlet_id, item_name, description, image_url, price) VALUES (?, ?, ?, ?, ?)",
            (int(outlet_id), item_name, description, image_url, int(price))
        )
        db.commit()
        db.close()

    return redirect("/admin")


# ---------------- ADMIN TOGGLE ITEM ----------------
@app.route("/admin/item/toggle/<int:item_id>", methods=["POST"])
def toggle_item(item_id):
    if not is_admin():
        return redirect("/admin/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE food_items SET is_available = CASE WHEN is_available = 1 THEN 0 ELSE 1 END WHERE item_id = ?", (item_id,))
    db.commit()
    db.close()

    return redirect("/admin")


# ---------------- ADMIN DELETE ITEM ----------------
@app.route("/admin/item/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if not is_admin():
        return redirect("/admin/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM order_items WHERE item_id = ?", (item_id,))
    usage = cur.fetchone()[0]

    if usage == 0:
        cur.execute("DELETE FROM food_items WHERE item_id = ?", (item_id,))
    else:
        cur.execute("UPDATE food_items SET is_available = 0 WHERE item_id = ?", (item_id,))

    db.commit()
    db.close()

    return redirect("/admin")


# ---------------- API STATUS ----------------
@app.route("/api/status/<int:order_id>")
def api_status(order_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT status FROM orders WHERE order_id=?", (order_id,))
    row = cur.fetchone()
    db.close()

    if row is None:
        return jsonify({"status": "Unknown"}), 404

    return jsonify({"status": row["status"]})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

