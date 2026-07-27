"""数据库连接与初始化（含迁移支持）"""

import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "channel_tool.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def init_db():
    from database.models import ALL_TABLES

    conn = get_connection()
    try:
        # 创建基础表
        for _, sql in ALL_TABLES:
            conn.execute(sql)
        conn.commit()

        # 迁移 channels 表新增字段
        ch_migrations = [
            ("title", "TEXT DEFAULT ''"),
            ("business_industry", "TEXT DEFAULT ''"),
            ("founding_years", "INTEGER DEFAULT 0"),
            ("registered_capital", "REAL DEFAULT 0"),
            ("channel_level", "TEXT DEFAULT 'NSP'"),
            ("brand_certification", "TEXT DEFAULT ''"),
            ("boss_background", "TEXT DEFAULT ''"),
        ]
        for col, col_def in ch_migrations:
            if not _column_exists(conn, "channels", col):
                conn.execute(f"ALTER TABLE channels ADD COLUMN {col} {col_def}")

        # 迁移 projects 表新增字段
        proj_migrations = [
            ("industry_category", "TEXT DEFAULT ''"),
            ("sub_industry", "TEXT DEFAULT ''"),
            ("relationship_channel", "TEXT DEFAULT ''"),
            ("integrator", "TEXT DEFAULT ''"),
            ("distributor", "TEXT DEFAULT ''"),
            ("reporting_conflict", "TEXT DEFAULT ''"),
            ("success_probability", "REAL DEFAULT 0"),
            ("opportunity_id", "TEXT DEFAULT ''"),
            ("expected_close_date", "TEXT DEFAULT ''"),
        ]
        for col, col_def in proj_migrations:
            if not _column_exists(conn, "projects", col):
                conn.execute(f"ALTER TABLE projects ADD COLUMN {col} {col_def}")

        # 迁移 channel_leads 新增字段
        lead_migrations = [
            ("next_contact_date", "TEXT DEFAULT ''"),
        ]
        for col, col_def in lead_migrations:
            if not _column_exists(conn, "channel_leads", col):
                conn.execute(f"ALTER TABLE channel_leads ADD COLUMN {col} {col_def}")

        # 迁移 deliveries 表新增字段
        del_migrations = [
            ("month", "INTEGER DEFAULT 0"),
            ("channel_amount", "REAL DEFAULT 0"),
            ("final_amount", "REAL DEFAULT 0"),
            ("project_id", "INTEGER DEFAULT 0"),
            ("notes", "TEXT DEFAULT ''"),
        ]
        for col, col_def in del_migrations:
            if not _column_exists(conn, "deliveries", col):
                conn.execute(f"ALTER TABLE deliveries ADD COLUMN {col} {col_def}")

        conn.commit()
    finally:
        conn.close()


def query(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_one(sql: str, params: tuple = ()) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
