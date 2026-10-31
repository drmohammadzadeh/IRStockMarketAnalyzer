"""Auth & Analysis Requests Database Manager for tjb24.ir Local Server.

Backed by SQLite for local zero-dependency execution in `serve.py`
and mirroring the MariaDB production schema in `database/schema.sql`.
"""

import hashlib
import os
import random
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize the SQLite tables matching database/schema.sql."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        mobile TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 0,
        last_login_at TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activation_token TEXT NOT NULL UNIQUE,
        activation_code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_used INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reset_token TEXT NOT NULL UNIQUE,
        reset_code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_used INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_analysis_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        applicant_name TEXT NOT NULL,
        applicant_mobile TEXT,
        applicant_email TEXT NOT NULL,
        stock_symbol TEXT NOT NULL,
        request_type TEXT NOT NULL,
        notes TEXT,
        ip_address TEXT NOT NULL DEFAULT '127.0.0.1',
        user_agent TEXT,
        referer TEXT,
        client_language TEXT,
        device_info TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        analyzed_at TEXT,
        result_url TEXT,
        admin_notes TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)

    # Seed demo requests if empty
    cur.execute("SELECT COUNT(*) FROM stock_analysis_requests")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO stock_analysis_requests 
        (user_id, applicant_name, applicant_mobile, applicant_email, stock_symbol, request_type, notes, status, analyzed_at, result_url, admin_notes)
        VALUES 
        (NULL, 'کاربر نمونه', '09121111111', 'demo@tjb24.ir', 'خودرو', 'تحلیل بنیادی و تکنیکال', 'بررسی نقاط حمایت کلیدی', 'completed', '1403/08/01', 'سهام/خودرو/گزارش_تحلیلی.html', 'تحلیل کامل نماد خودرو در سامانه منتشر شده است.'),
        (NULL, 'کاربر نمونه', '09121111111', 'demo@tjb24.ir', 'شپنا', 'تحلیل بنیادی و تکنیکال', 'بررسی نرخ کرک اسپرد', 'in_progress', NULL, NULL, 'در حال پایش صورت‌های مالی کدال و تابلوی نماد.'),
        (NULL, 'کاربر نمونه', '09121111111', 'demo@tjb24.ir', 'اهرم', 'تحلیل صندوق اهرمی', 'بررسی حباب حباب و پرتفوی', 'pending', NULL, NULL, 'در صف بررسی تیم تحلیل‌گران')
        """)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password with sha256 + salt for local mock environment."""
    salt = "tjb24_ir_salt_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


class AuthManager:
    """Manages user registration, activations, password resets, and user requests."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        init_db(self.db_path)
        # Active sessions: session_token -> user_dict
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def register(self, first_name: str, last_name: str, mobile: str, email: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
        first_name = (first_name or "").strip()
        last_name = (last_name or "").strip()
        mobile = (mobile or "").strip()
        email = (email or "").strip().lower()

        if not first_name or not last_name:
            return False, "لطفاً نام و نام خانوادگی خود را کامل وارد نمایید.", {}

        # 09xxxxxxxxx (11 digits)
        if not re.match(r"^09\d{9}$", mobile):
            return False, "شماره موبایل نامعتبر است. شماره موبایل باید با ۰۹ شروع شده و ۱۱ رقم باشد.", {}

        # Email
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return False, "لطفاً یک آدرس ایمیل معتبر وارد نمایید.", {}

        if len(password or "") < 6:
            return False, "رمز عبور باید حداقل ۶ کاراکتر باشد.", {}

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, mobile, email, is_active FROM users WHERE mobile = ? OR email = ?", (mobile, email))
        existing = cur.fetchone()

        if existing:
            user_id = existing["id"]
            if existing["is_active"] == 0:
                # Issue new activation code
                token = secrets.token_hex(32)
                code = f"{random.randint(100000, 999999):06d}"
                expires = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(
                    "INSERT INTO user_activations (user_id, activation_token, activation_code, expires_at) VALUES (?, ?, ?, ?)",
                    (user_id, token, code, expires)
                )
                conn.commit()
                conn.close()
                return True, "حساب شما قبلاً ثبت شده اما هنوز فعال نشده است. کد فعال‌سازی جدید صادر شد.", {
                    "need_activation": True,
                    "mobile": mobile,
                    "email": email,
                    "activation_token": token,
                    "activation_code": code
                }
            else:
                conn.close()
                return False, "کاربری با این شماره موبایل یا ایمیل قبلاً ثبت‌نام کرده و فعال است. لطفاً وارد شوید.", {}

        # Insert new user
        pwd_hash = hash_password(password)
        cur.execute(
            "INSERT INTO users (first_name, last_name, mobile, email, password_hash, is_active) VALUES (?, ?, ?, ?, ?, 0)",
            (first_name, last_name, mobile, email, pwd_hash)
        )
        user_id = cur.lastrowid

        # Generate activation token & code
        token = secrets.token_hex(32)
        code = f"{random.randint(100000, 999999):06d}"
        expires = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO user_activations (user_id, activation_token, activation_code, expires_at) VALUES (?, ?, ?, ?)",
            (user_id, token, code, expires)
        )
        conn.commit()
        conn.close()

        return True, "ثبت‌نام شما با موفقیت انجام شد. کد و لینک فعال‌سازی برای شما ارسال گردید.", {
            "user_id": user_id,
            "mobile": mobile,
            "email": email,
            "activation_token": token,
            "activation_code": code
        }

    def activate(self, token: Optional[str] = None, mobile: Optional[str] = None, code: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        rec = None
        if token:
            cur.execute("""
            SELECT ua.id, ua.user_id, ua.is_used, ua.expires_at, u.first_name, u.last_name, u.mobile, u.email
            FROM user_activations ua
            JOIN users u ON u.id = ua.user_id
            WHERE ua.activation_token = ?
            LIMIT 1
            """, (token.strip(),))
            rec = cur.fetchone()
        elif mobile and code:
            cur.execute("""
            SELECT ua.id, ua.user_id, ua.is_used, ua.expires_at, u.first_name, u.last_name, u.mobile, u.email
            FROM user_activations ua
            JOIN users u ON u.id = ua.user_id
            WHERE u.mobile = ? AND ua.activation_code = ?
            ORDER BY ua.id DESC
            LIMIT 1
            """, (mobile.strip(), code.strip()))
            rec = cur.fetchone()

        if not rec:
            conn.close()
            return False, "کد یا لینک فعال‌سازی یافت نشد یا معتبر نمی‌باشد.", {}

        if rec["is_used"] == 1:
            conn.close()
            return False, "این کد یا لینک فعال‌سازی قبلاً استفاده شده است. لطفاً وارد شوید.", {}

        # Check expiry
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if rec["expires_at"] < now_str:
            conn.close()
            return False, "مهلت استفاده از این کد یا لینک به پایان رسیده است.", {}

        user_id = rec["user_id"]
        # Mark used
        cur.execute("UPDATE user_activations SET is_used = 1 WHERE id = ?", (rec["id"],))
        cur.execute("UPDATE users SET is_active = 1, last_login_at = ? WHERE id = ?", (now_str, user_id))
        conn.commit()
        conn.close()

        user_data = {
            "id": user_id,
            "first_name": rec["first_name"],
            "last_name": rec["last_name"],
            "mobile": rec["mobile"],
            "email": rec["email"]
        }

        session_token = secrets.token_hex(24)
        self._sessions[session_token] = user_data

        return True, "حساب کاربری شما با موفقیت فعال شد و هم‌اکنون وارد سامانه شدید.", {
            "user": user_data,
            "token": session_token
        }

    def login(self, username: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            return False, "لطفاً نام کاربری (شماره موبایل) و رمز عبور را وارد فرمایید.", {}

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, first_name, last_name, mobile, email, password_hash, is_active FROM users WHERE mobile = ? OR email = ? LIMIT 1", (username, username))
        user = cur.fetchone()

        if not user or not verify_password(password, user["password_hash"]):
            conn.close()
            return False, "شماره موبایل یا رمز عبور اشتباه است.", {}

        if user["is_active"] == 0:
            conn.close()
            return False, "حساب کاربری شما هنوز فعال نشده است. لطفاً کد فعال‌سازی ارسال‌شده به ایمیلتان را وارد کنید.", {
                "need_activation": True,
                "mobile": user["mobile"],
                "email": user["email"]
            }

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_str, user["id"]))
        conn.commit()
        conn.close()

        user_data = {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "mobile": user["mobile"],
            "email": user["email"]
        }

        session_token = secrets.token_hex(24)
        self._sessions[session_token] = user_data

        return True, "با موفقیت وارد شدید. خوش آمدید!", {
            "user": user_data,
            "token": session_token
        }

    def get_user_by_session(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        return self._sessions.get(token)

    def logout(self, token: Optional[str]) -> bool:
        if token and token in self._sessions:
            del self._sessions[token]
        return True

    def forgot_password(self, identifier: str) -> Tuple[bool, str, Dict[str, Any]]:
        identifier = (identifier or "").strip()
        if not identifier:
            return False, "لطفاً شماره موبایل یا آدرس ایمیل خود را وارد نمایید.", {}

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, first_name, last_name, mobile, email FROM users WHERE mobile = ? OR email = ? LIMIT 1", (identifier, identifier))
        user = cur.fetchone()

        if not user:
            conn.close()
            return False, "حساب کاربری با این مشخصات یافت نشد.", {}

        token = secrets.token_hex(32)
        code = f"{random.randint(100000, 999999):06d}"
        expires = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            "INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at) VALUES (?, ?, ?, ?)",
            (user["id"], token, code, expires)
        )
        conn.commit()
        conn.close()

        return True, "کد و لینک بازیابی رمز عبور صادر شد.", {
            "mobile": user["mobile"],
            "email": user["email"],
            "reset_token": token,
            "reset_code": code
        }

    def reset_password(self, new_password: str, token: Optional[str] = None, mobile: Optional[str] = None, code: Optional[str] = None) -> Tuple[bool, str]:
        if len(new_password or "") < 6:
            return False, "رمز عبور جدید باید حداقل ۶ کاراکتر باشد."

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        rec = None
        if token:
            cur.execute("""
            SELECT pr.id, pr.user_id, pr.is_used, pr.expires_at
            FROM password_resets pr
            WHERE pr.reset_token = ?
            LIMIT 1
            """, (token.strip(),))
            rec = cur.fetchone()
        elif mobile and code:
            cur.execute("""
            SELECT pr.id, pr.user_id, pr.is_used, pr.expires_at
            FROM password_resets pr
            JOIN users u ON u.id = pr.user_id
            WHERE u.mobile = ? AND pr.reset_code = ?
            ORDER BY pr.id DESC
            LIMIT 1
            """, (mobile.strip(), code.strip()))
            rec = cur.fetchone()

        if not rec:
            conn.close()
            return False, "کد یا لینک بازیابی رمز یافت نشد یا معتبر نیست."

        if rec["is_used"] == 1:
            conn.close()
            return False, "این کد بازیابی قبلاً استفاده شده است."

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if rec["expires_at"] < now_str:
            conn.close()
            return False, "مهلت استفاده از این کد به پایان رسیده است."

        pwd_hash = hash_password(new_password)
        cur.execute("UPDATE users SET password_hash = ?, is_active = 1 WHERE id = ?", (pwd_hash, rec["user_id"]))
        cur.execute("UPDATE password_resets SET is_used = 1 WHERE id = ?", (rec["id"],))
        conn.commit()
        conn.close()

        return True, "رمز عبور شما با موفقیت تغییر یافت. اکنون می‌توانید با رمز عبور جدید وارد شوید."

    def get_requests(self, user_id: Optional[int] = None, mobile: Optional[str] = None, email: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        clauses = []
        params = []
        if user_id:
            clauses.append("user_id = ?")
            params.append(user_id)
        if mobile:
            clauses.append("applicant_mobile = ?")
            params.append(mobile)
        if email:
            clauses.append("applicant_email = ?")
            params.append(email)

        if not clauses:
            conn.close()
            return []

        query = f"SELECT * FROM stock_analysis_requests WHERE {' OR '.join(clauses)} ORDER BY id DESC"
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        status_map = {
            "pending": ("در صف بررسی", "badge-pending"),
            "in_progress": ("در حال تحلیل", "badge-progress"),
            "completed": ("تحلیل شده", "badge-completed"),
            "rejected": ("رد شده", "badge-rejected")
        }

        results = []
        for r in rows:
            st = r["status"] or "pending"
            label, badge = status_map.get(st, (st, "badge-pending"))
            results.append({
                "id": r["id"],
                "stock_symbol": r["stock_symbol"],
                "request_type": r["request_type"],
                "notes": r["notes"],
                "status": st,
                "status_label": label,
                "status_badge": badge,
                "created_at": r["created_at"],
                "analyzed_at": r["analyzed_at"],
                "result_url": r["result_url"],
                "admin_notes": r["admin_notes"]
            })

        conn.close()
        return results

    def add_request(self, symbol: str, name: str, email: str, mobile: Optional[str] = None, request_type: str = "تحلیل بنیادی و تکنیکال", notes: str = "", user_id: Optional[int] = None) -> Tuple[bool, str, int]:
        symbol = (symbol or "").strip()
        if not symbol:
            return False, "لطفاً نام یا نماد سهم درخواستی را مشخص فرمایید.", 0

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO stock_analysis_requests 
        (user_id, applicant_name, applicant_mobile, applicant_email, stock_symbol, request_type, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (user_id, name or "کاربر سامانه", mobile, email or "no-reply@tjb24.ir", symbol, request_type, notes))

        req_id = cur.lastrowid
        conn.commit()
        conn.close()

        return True, f"درخواست تحلیل نماد {symbol} با موفقیت ثبت شد.", req_id
