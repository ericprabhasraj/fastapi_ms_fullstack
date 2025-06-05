# core/admin.py

import os
from core.db import users_collection

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

async def create_default_admin():
    existing_admin = users_collection.find_one({"email": ADMIN_EMAIL, "role": "admin"})
    if existing_admin:
        print("Admin user already exists.")
    else:
        users_collection.insert_one({
            "name": "Admin",
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "role": "admin"
        })
        print("Admin user created.")
