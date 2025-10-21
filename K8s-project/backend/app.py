import psycopg2
from flask import Flask, request, jsonify
import os
import redis

app = Flask(__name__)

# Redis setup
redis_host = os.environ.get("REDIS_HOST", "redis-service")
r = redis.Redis(host=redis_host, port=6379)

# Postgres setup
postgres_host = os.environ.get("POSTGRES_HOST", "postgres-service")
conn = psycopg2.connect(
    host=postgres_host,
    database="postgres",
    user=os.environ.get("POSTGRES_USER", "postgres"),
    password=os.environ.get("POSTGRES_PASSWORD", "password")
)
cur = conn.cursor()

# ✅ Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT
)
""")
conn.commit()

@app.route("/api/users", methods=["POST"])
def add_user():
    data = request.json
    username = data.get("username")
    if not username:
        return jsonify({"error": "Username required"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username) VALUES (%s)", (username,))
    conn.commit()
    cur.close()
    conn.close()
    r.set(f"user:{username}", username)
    return jsonify({"message": f"User {username} added"}), 201

@app.route("/api/users", methods=["GET"])
def list_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users")
    users = [{"id": u[0], "username": u[1]} for u in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
