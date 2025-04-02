# import streamlit as st
# import requests

# API_URL = "http://127.0.0.1:5000/api/login"

# def login(username, password):
#     response = requests.post(API_URL, json={"username": username, "password": password})
#     if response.status_code == 200:
#         st.success("登录成功！")
#     else:
#         st.error("用户名或密码错误！")

# st.title("🔑 登录")
# username = st.text_input("用户名")
# password = st.text_input("密码", type="password")
# if st.button("登录"):
#     login(username, password)

import streamlit as st
import json
import os

SESSION_FILE = "user_session.json"

# 用户信息存储（临时字典）
USER_DATA = {
    "admin": "password123"
}

# 初始化会话文件
if not os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "w") as f:
        json.dump({}, f)

# 更新会话
def update_session(username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"username": username}, f)

# 登录功能
def login(username, password):
    if username in USER_DATA and USER_DATA[username] == password:
        update_session(username)
        st.success(f"欢迎，{username}！")
    else:
        st.error("用户名或密码错误！")

# 清除会话
def logout():
    with open(SESSION_FILE, "w") as f:
        json.dump({}, f)
    st.info("您已退出登录。")

# Streamlit 页面
st.set_page_config(page_title="登录系统", page_icon="🔑", layout="centered")

if st.button("退出登录"):
    logout()

if st.button("查看当前会话"):
    with open(SESSION_FILE, "r") as f:
        session_data = json.load(f)
    st.json(session_data)

if not st.button("已登录"):
    st.title("🔑 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        login(username, password)
