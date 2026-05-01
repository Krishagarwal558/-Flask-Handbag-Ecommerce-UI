import os
from datetime import datetime
from functools import wraps
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "replace-this-secret-key")
app.config["ADMIN_EMAIL"] = os.getenv("ADMIN_EMAIL", "agarwalpk2301@gmail.com")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "Kaddumon123")


# Empty by default. Connect these to your database later.
CATEGORIES = []
PRODUCTS = []
USERS = []
ORDERS = []


def current_user():
    return session.get("user")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user and user.get("role") == "admin":
            return view(*args, **kwargs)
        if request.method == "GET":
            return redirect(url_for("login", next=request.path))
        return jsonify({"ok": False, "message": "Admin authorization required"}), 403

    return wrapped


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user():
            return view(*args, **kwargs)
        return redirect(url_for("login", next=request.path))

    return wrapped


def get_product(product_id):
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def cart_items():
    cart = session.setdefault("cart", {})
    items = []
    for product_id, quantity in cart.items():
        product = get_product(int(product_id))
        if product:
            item = product.copy()
            item["quantity"] = quantity
            item["line_total"] = quantity * product["price"]
            items.append(item)
    return items


def cart_total():
    return sum(item["line_total"] for item in cart_items())


def filtered_products():
    query = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "")
    max_price = int(request.args.get("price", 100000))
    sort = request.args.get("sort", "popular")

    products = [
        product
        for product in PRODUCTS
        if (not query or query in product["name"].lower())
        and (not category or product["category"] == category)
        and product["price"] <= max_price
    ]

    if sort == "price-low":
        products.sort(key=lambda product: product["price"])
    elif sort == "price-high":
        products.sort(key=lambda product: product["price"], reverse=True)
    else:
        products.sort(key=lambda product: product.get("popularity", 0), reverse=True)
    return products


@app.context_processor
def inject_globals():
    items = cart_items()
    return {
        "categories": CATEGORIES,
        "cart_count": sum(item["quantity"] for item in items),
        "cart_total": sum(item["line_total"] for item in items),
        "currency_symbol": "Rs.",
        "current_user": current_user(),
        "year": datetime.now().year,
    }


@app.route("/")
def home():
    featured = sorted(PRODUCTS, key=lambda product: product.get("rating", 0), reverse=True)[:4]
    trending = sorted(PRODUCTS, key=lambda product: product.get("popularity", 0), reverse=True)
    return render_template("home.html", featured=featured, trending=trending)


@app.route("/products")
def products():
    return render_template("shop.html", products=filtered_products(), selected=request.args)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return redirect(url_for("products"))
    related = [
        item
        for item in PRODUCTS
        if item.get("category") == product.get("category") and item["id"] != product["id"]
    ][:3]
    return render_template("product_detail.html", product=product, related=related)


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    payload = request.get_json(silent=True) or request.form
    product_id = str(payload.get("product_id"))
    quantity = int(payload.get("quantity", 1))
    if not product_id.isdigit() or not get_product(int(product_id)):
        return jsonify({"ok": False, "message": "Handbag not found"}), 404
    cart = session.setdefault("cart", {})
    cart[product_id] = cart.get(product_id, 0) + quantity
    session.modified = True
    return jsonify({"ok": True, "message": "Added to cart", "cart_count": sum(cart.values())})


@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        payload = request.get_json(silent=True) or request.form
        product_id = str(payload.get("product_id"))
        action = payload.get("action")
        cart_data = session.setdefault("cart", {})
        if action == "remove":
            cart_data.pop(product_id, None)
        elif action == "increase":
            cart_data[product_id] = cart_data.get(product_id, 0) + 1
        elif action == "decrease" and product_id in cart_data:
            cart_data[product_id] -= 1
            if cart_data[product_id] <= 0:
                cart_data.pop(product_id, None)
        session.modified = True
        return jsonify({"ok": True, "total": cart_total(), "cart_count": sum(cart_data.values())})
    return render_template("cart.html", items=cart_items(), total=cart_total())


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        session["last_order"] = f"BB-{uuid4().hex[:6].upper()}"
        session["cart"] = {}
        session.modified = True
        return jsonify({"ok": True, "redirect": url_for("order_success")})
    return render_template("checkout.html", items=cart_items(), total=cart_total())


@app.route("/order-success")
def order_success():
    return render_template("order_success.html", order_id=session.get("last_order", "Pending"))


@app.route("/orders")
def orders():
    return render_template("orders.html", orders=ORDERS)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin_email = (app.config["ADMIN_EMAIL"] or "").strip().lower()
        admin_password = app.config["ADMIN_PASSWORD"] or ""

        if admin_email and admin_password and email == admin_email and password == admin_password:
            session["user"] = {"name": "Administrator", "email": email, "role": "admin"}
            redirect_to = request.args.get("next") or url_for("admin_dashboard")
            return jsonify({"ok": True, "message": "Admin login successful", "redirect": redirect_to})

        return jsonify({"ok": False, "message": "Invalid credentials"}), 401
    return render_template("auth/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return jsonify({"ok": True, "message": "Registration endpoint ready for your user database"})
    return render_template("auth/register.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        return jsonify({"ok": True, "message": "Reset link endpoint ready"})
    return render_template("auth/forgot_password.html")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user(), orders=ORDERS)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {"sales": 0, "orders": len(ORDERS), "users": len(USERS), "conversion": "0%"}
    return render_template("admin/dashboard.html", stats=stats, orders=ORDERS, products=PRODUCTS, users=USERS)


@app.route("/add-product", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        return jsonify({"ok": True, "message": "Handbag create endpoint ready"})
    return render_template("admin/add_product.html")


@app.route("/admin/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = get_product(product_id)
    if not product:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        return jsonify({"ok": True, "message": "Handbag update endpoint ready"})
    return render_template("admin/edit_product.html", product=product)


@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    return jsonify({"ok": True, "message": f"Delete endpoint ready for handbag {product_id}"})


@app.route("/admin/order-status", methods=["POST"])
@admin_required
def update_order_status():
    return jsonify({"ok": True, "message": "Order status updated"})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
