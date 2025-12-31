from functools import wraps
from flask import Flask, redirect, render_template, request, session
import sqlite3

def get_db():
    db = sqlite3.connect("data.db")
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def parse_boosts(text):
    boosts = {}
    if not text:
        return boosts

    parts = [p.strip() for p in text.split(",") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        key = key.strip()
        try:
            boosts[key] = int(val.strip())
        except ValueError:
            continue

    return boosts