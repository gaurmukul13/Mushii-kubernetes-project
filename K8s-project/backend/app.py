import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import redis
import time

app = Flask(__name__)
CORS(app)

# Redis setup
redis_host = os.environ.get("REDIS_HOST", "redis")
r = redis.Redis(host=redis_host, port=6379)

# Wait for Postgres to be ready
postgres_host = os.environ.get("POSTGRES_HOST", "postgres")
postgres_user = os.environ.get("POSTGRES_USER", "postgres")
postgres_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
postgres_db = os.environ.get("POSTGRES_DB", "postgres")

conn = None
for i in range(10):
    try:
        conn = psycopg2.connect(
            host=postgres_host,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password
        )
        print("✅ Connected to PostgreSQL!")
        break
    except psycopg2.OperationalError:
        print("⏳ Waiting for PostgreSQL to be ready...")
        time.sleep(3)

if conn is None:
    raise Exception("❌ Could not connect to PostgreSQL after several attempts.")

# Create users table if not exists
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT
)
""")
conn.commit()
cur.close()
conn.close()

# Function to get DB connection
def get_db_connection():
    return psycopg2.connect(
        host=postgres_host,
        database=postgres_db,
        user=postgres_user,
        password=postgres_password
    )

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
