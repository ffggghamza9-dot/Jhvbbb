# utils.py
from config import ADMIN_IDS
from database import get_balance

def is_admin(uid:int):
    return uid in ADMIN_IDS

def format_balance(uid:int):
    bal = get_balance(uid)
    return f"${bal:.2f}"
