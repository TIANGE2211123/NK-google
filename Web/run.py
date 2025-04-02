# # import sys
# # import os

# from flask import Flask, request, jsonify

# app = Flask(__name__)
# SESSIONS = {}

# @app.route("/api/login", methods=["POST"])
# def login():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
#     if username == "admin" and password == "password123":
#         SESSIONS[username] = True
#         return jsonify({"status": "success"}), 200
#     return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# @app.route("/")
# def index():
#     if "admin" in SESSIONS and SESSIONS["admin"]:
#         return "欢迎回来，admin！"
#     else:
#         return "请先登录。"
    

# from Web import create_app
# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True, host="127.0.0.1", port=5000)

# import os
# import json
# from Web import create_app
# from flask import request, jsonify

# app = create_app()

# SESSION_FILE = "user_session.json"

# # 检查用户会话
# def get_current_user():
#     if os.path.exists(SESSION_FILE):
#         with open(SESSION_FILE, "r") as f:
#             session_data = json.load(f)
#             return session_data.get("username")
#     return None

# @app.route("/api/user", methods=["GET"])
# def current_user():
#     username = get_current_user()
#     if username:
#         return jsonify({"status": "success", "username": username}), 200
#     return jsonify({"status": "unauthenticated"}), 401

# @app.route("/")
# def index():
#     username = get_current_user()
#     if username:
#         return f"欢迎回来，{username}！这是您的个性化内容。"
#     else:
#         return "请先登录。"


from Web import create_app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
