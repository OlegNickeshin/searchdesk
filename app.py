from flask import Flask, redirect, render_template, request, session
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import get_db, login_required, parse_boosts

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ALLOWED_SORTS = {
    "title": "title",
    "brand": "brand",
    "price": "price_cents",
    "created": "created_at",
    "category": "category",
    "gender": "gender",
    "size": "size_eu",
    "color": "color",
    "status": "in_stock",
}

@app.route("/")
@login_required
def index():
    return redirect("/products")

@app.route("/faq")
@login_required
def faq():
    return render_template("faq.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return render_template("login.html", error="Enter username")
        if not password:
            return render_template("login.html", error="Enter password")

        db = get_db()
        try:
            rows = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
        finally:
            db.close()

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("login.html", error="Invalid username and/or password")

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not name:
            return render_template("register.html", error="Enter username")
        if not password:
            return render_template("register.html", error="Enter password")
        if not confirmation:
            return render_template("register.html", error="Please confirm password")
        if confirmation != password:
            return render_template("register.html", error="Passwords must match")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                (name, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="This username already exists")
        finally:
            db.close()

        return render_template("register.html", message="You are registered!")

    return render_template("register.html")


@app.route("/products", methods=["GET"])
@login_required
def products():
    sort = request.args.get("sort", "created")
    order = request.args.get("order", "desc")

    if sort not in ALLOWED_SORTS:
        sort = "created"
    if order not in ("asc", "desc"):
        order = "desc"

    db = get_db()
    try:
        rows = db.execute(
            f"SELECT * FROM products ORDER BY {ALLOWED_SORTS[sort]} {order.upper()}"
        ).fetchall()
    finally:
        db.close()

    return render_template("products.html", rows=rows, order=order)


@app.route("/products/<int:id>/delete", methods=["POST"])
@login_required
def product_delete(id):
    db = get_db()
    try:
        db.execute("DELETE FROM products WHERE id = ?", (id,))
        db.commit()
    finally:
        db.close()
    return redirect("/products")


@app.route("/products/new", methods=["POST"])
@login_required
def products_new():
    title = (request.form.get("title") or "").strip()
    brand = request.form.get("brand")
    category = request.form.get("category")
    gender = request.form.get("gender")

    try:
        size_eu = int(request.form.get("size_eu"))
    except (TypeError, ValueError):
        size_eu = None

    color = (request.form.get("color") or "").strip() or None

    try:
        price = float(request.form.get("price"))
        price_cents = int(round(price * 100))
    except (TypeError, ValueError):
        price_cents = None

    in_stock = 1 if request.form.get("in_stock") == "1" else 0

    if not title:
        db = get_db()
        try:
            rows = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
        finally:
            db.close()

        return render_template(
            "products.html",
            rows=rows,
            error="Title is required",
            show_add_modal=True,
        )

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO products
            (title, brand, category, gender, size_eu, color, price_cents, in_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, brand, category, gender, size_eu, color, price_cents, in_stock),
        )
        db.commit()
    finally:
        db.close()

    return redirect("/products")


@app.route("/rules")
@login_required
def rules_list():
    db = get_db()
    try:
        rules = db.execute(
            """
            SELECT id, name, query_text, match_type, brand_boost, gender_boost, category_boost, in_stock_first, created_at
            FROM rules
            WHERE active = 1
            ORDER BY created_at DESC
            """
        ).fetchall()
    finally:
        db.close()
    return render_template("rules.html", rules=rules)


@app.route("/rules/new", methods=["POST"])
@login_required
def rules_new():
    name = (request.form.get("name") or "").strip()
    query_text = (request.form.get("query_text") or "").strip()

    match_type = (request.form.get("match_type") or "exact").strip()
    if match_type not in ("exact", "contains"):
        match_type = "exact"

    brand_boost = (request.form.get("brand_boost") or "").strip()
    gender_boost = (request.form.get("gender_boost") or "").strip()
    category_boost = (request.form.get("category_boost") or "").strip()
    in_stock_first = 1 if request.form.get("in_stock_first") == "1" else 0

    if not name or not query_text:
        return redirect("/rules")

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO rules (name, query_text, match_type, brand_boost, gender_boost, category_boost, in_stock_first)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, query_text, match_type, brand_boost, gender_boost, category_boost, in_stock_first),
        )
        db.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        db.close()

    return redirect("/rules")


@app.route("/rules/<int:rule_id>/delete", methods=["POST"])
@login_required
def rules_delete(rule_id):
    db = get_db()
    try:
        db.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        db.commit()
    finally:
        db.close()
    return redirect("/rules")


@app.route("/rules/<int:rule_id>/pin", methods=["POST"])
@login_required
def rule_pin(rule_id):
    try:
        product_id = int(request.form.get("product_id"))
    except (TypeError, ValueError):
        return redirect(f"/rank?q={(request.form.get('q') or '').strip()}")

    try:
        position = int(request.form.get("position", 1))
    except (TypeError, ValueError):
        position = 1

    if position < 1:
        position = 1

    db = get_db()
    try:
        db.execute("DELETE FROM rule_pins WHERE rule_id = ? AND position = ?", (rule_id, position))
        db.execute("DELETE FROM rule_pins WHERE rule_id = ? AND product_id = ?", (rule_id, product_id))
        db.execute(
            "INSERT INTO rule_pins (rule_id, product_id, position) VALUES (?, ?, ?)",
            (rule_id, product_id, position),
        )
        db.commit()
    finally:
        db.close()

    q = (request.form.get("q") or "").strip()
    return redirect(f"/rank?q={q}" if q else "/rank")


@app.route("/rules/<int:rule_id>/unpin", methods=["POST"])
@login_required
def rule_unpin(rule_id):
    try:
        product_id = int(request.form.get("product_id"))
    except (TypeError, ValueError):
        return redirect("/rank")

    db = get_db()
    try:
        db.execute("DELETE FROM rule_pins WHERE rule_id = ? AND product_id = ?", (rule_id, product_id))
        db.commit()
    finally:
        db.close()

    q = (request.form.get("q") or "").strip()
    return redirect(f"/rank?q={q}" if q else "/rank")


@app.route("/rank")
@login_required
def rank():
    q = (request.args.get("q") or "").strip()
    if not q:
        return render_template("rank.html", q="", rule=None, results=[], pinned=[])

    db = get_db()
    try:
        rule = db.execute(
            """
            SELECT *
            FROM rules
            WHERE active = 1 AND match_type = 'exact' AND query_text = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (q,),
        ).fetchone()

        if not rule:
            rule = db.execute(
                """
                SELECT *
                FROM rules
                WHERE active = 1 AND match_type = 'contains'
                  AND ? LIKE '%' || query_text || '%'
                ORDER BY LENGTH(query_text) DESC, created_at DESC
                LIMIT 1
                """,
                (q,),
            ).fetchone()

        pinned_rows = []
        pinned_ids = set()

        if rule:
            pinned_rows = db.execute(
                """
                SELECT p.*, rp.position
                FROM rule_pins rp
                JOIN products p ON p.id = rp.product_id
                WHERE rp.rule_id = ?
                ORDER BY rp.position ASC
                """,
                (rule["id"],),
            ).fetchall()
            pinned_ids = {row["id"] for row in pinned_rows}

        like = f"%{q}%"
        params = [like, like, like]
        sql = """
            SELECT *
            FROM products
            WHERE (title LIKE ? OR brand LIKE ? OR category LIKE ?)
        """

        if pinned_ids:
            placeholders = ",".join(["?"] * len(pinned_ids))
            sql += f" AND id NOT IN ({placeholders})"
            params.extend(list(pinned_ids))

        products_rows = db.execute(sql, params).fetchall()

        boosts_brand = parse_boosts(rule["brand_boost"]) if rule else {}
        boosts_gender = parse_boosts(rule["gender_boost"]) if rule else {}
        boosts_cat = parse_boosts(rule["category_boost"]) if rule else {}
        in_stock_first = bool(rule and rule["in_stock_first"] == 1)

        results = []
        for p in products_rows:
            score = 0
            why = []

            if in_stock_first and p["in_stock"] == 1:
                score += 1000
                why.append("in_stock +1000")

            b = boosts_brand.get(p["brand"], 0)
            if b:
                score += b
                why.append(f"brand +{b}")

            g = boosts_gender.get(p["gender"], 0)
            if g:
                score += g
                why.append(f"gender +{g}")

            c = boosts_cat.get(p["category"], 0)
            if c:
                score += c
                why.append(f"category +{c}")

            results.append(
                {
                    **dict(p),
                    "score": score,
                    "why": ", ".join(why) if why else "base",
                }
            )

        results.sort(key=lambda x: (x["score"], x.get("created_at", "")), reverse=True)

        pinned = []
        for row in pinned_rows:
            pinned.append(
                {
                    **dict(row),
                    "score": 10_000_000 - int(row["position"]),
                    "why": f"PINNED #{row['position']}",
                    "position": row["position"],
                }
            )

        final_results = pinned + results

        return render_template(
            "rank.html",
            q=q,
            rule=rule,
            results=final_results,
            pinned=pinned,
        )
    finally:
        db.close()