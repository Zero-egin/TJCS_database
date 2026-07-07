#!/usr/bin/env python3
"""测试密码验证"""
import psycopg2
from passlib.context import CryptContext

# 初始化密码上下文
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# 连接数据库
conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/noise_db')
cur = conn.cursor()

# 查询用户
cur.execute("SELECT username, password_hash FROM users WHERE username = 'admin'")
user = cur.fetchone()

if user:
    username, password_hash = user
    print(f"用户名: {username}")
    print(f"密码哈希: {password_hash}")
    
    # 测试密码验证
    test_password = 'admin123'
    try:
        is_valid = pwd_context.verify(test_password, password_hash)
        print(f"\n密码 '{test_password}' 验证结果: {is_valid}")
    except Exception as e:
        print(f"\n密码验证失败: {e}")
else:
    print("未找到用户")

conn.close()
