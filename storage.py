"""SQLite 持久化与健康报告历史、每周自动汇总。

每个用户各自持有一份本地数据库（数据不出本机，符合隐私预期）。
报告历史均带 ISO 时间戳；应用启动时自动按自然周（周一为起点）聚合
历史报告生成汇总表格，并满足「每隔一星期」的自动触发条件（≥7 天）。
"""

import csv
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from calc import ActivityLevel, Gender, HealthResult

# 数据库 schema 版本：每次变更表结构时 +1，并在 _apply_migrations 中补迁移逻辑，
# 保证老用户升级软件后本地数据库能平滑演进、不会损坏。
SCHEMA_VERSION = 1

_AUTO_KEY = "last_weekly_auto_run"


def _user_data_dir(app_name: str = "健康管理") -> str:
    """返回跨平台的标准用户数据目录。

    Windows -> %APPDATA%\\健康管理；macOS -> ~/Library/Application Support/健康管理；
    Linux   -> $XDG_DATA_HOME 或 ~/.local/share/健康管理。
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, app_name)


# 数据库位置优先级：环境变量 HEALTH_DB_PATH > 标准用户数据目录下的 health.db。
# 这样高级用户可把库指向 U 盘或指定文件夹，便于携带/共享（仍属本机/个人文件）。
DB_PATH = os.environ.get("HEALTH_DB_PATH") or os.path.join(
    _user_data_dir(), "health.db"
)


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """按 user_version 增量迁移数据库结构。

    当前 SCHEMA_VERSION=1，结构已在建表语句中通过 IF NOT EXISTS 保证；
    日后升级时在此处追加 `if current < 2: ALTER TABLE ...` 等步骤，并置版本号。
    """
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current < SCHEMA_VERSION:
        # 未来迁移写在这里，例如：
        # if current < 2:
        #     conn.execute("ALTER TABLE reports ADD COLUMN xxx ...")
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()


def init_db() -> None:
    """初始化数据库表结构并执行迁移。"""
    conn = _connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT    NOT NULL,
                name          TEXT,
                gender        TEXT    NOT NULL,
                age           REAL    NOT NULL,
                height        REAL    NOT NULL,
                weight        REAL    NOT NULL,
                activity      TEXT    NOT NULL,
                bmi           REAL    NOT NULL,
                bmi_label     TEXT    NOT NULL,
                bmr           REAL    NOT NULL,
                tdee          REAL    NOT NULL,
                body_fat      REAL    NOT NULL,
                body_fat_label TEXT   NOT NULL,
                healthy_low   REAL    NOT NULL,
                healthy_high  REAL    NOT NULL,
                advice        TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weekly_summary (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start    TEXT    NOT NULL UNIQUE,
                week_end      TEXT    NOT NULL,
                report_count  INTEGER NOT NULL,
                avg_bmi       REAL,
                avg_weight    REAL,
                avg_bmr       REAL,
                avg_tdee      REAL,
                generated_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        _apply_migrations(conn)
        conn.commit()
    finally:
        conn.close()


def _week_bounds(d: date) -> tuple:
    """返回某日期所在自然周（周一~周日）的起止日期。"""
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)
    return start, end


def save_report(
    result: HealthResult,
    *,
    name: Optional[str],
    gender: Gender,
    age: float,
    height: float,
    weight: float,
    activity: ActivityLevel,
    ts: Optional[datetime] = None,
    advice: str = "",
) -> int:
    """保存一份健康报告，返回新记录 id。"""
    ts = ts or datetime.now()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO reports (
                ts, name, gender, age, height, weight, activity,
                bmi, bmi_label, bmr, tdee, body_fat, body_fat_label,
                healthy_low, healthy_high, advice
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                ts.isoformat(timespec="seconds"),
                name,
                gender.value,
                age,
                height,
                weight,
                activity.value,
                round(result.bmi, 2),
                result.bmi_label,
                round(result.bmr, 1),
                round(result.tdee, 1),
                round(result.body_fat, 1),
                result.body_fat_label,
                round(result.healthy_weight_low, 1),
                round(result.healthy_weight_high, 1),
                advice,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def list_reports(limit: Optional[int] = None) -> List[dict]:
    """按时间倒序列出报告历史。"""
    conn = _connect()
    try:
        sql = "SELECT * FROM reports ORDER BY ts DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_report(report_id: int) -> Optional[dict]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _aggregate_weekly() -> List[dict]:
    """按 ISO 周聚合所有报告。"""
    reports = list_reports()
    weeks: Dict[str, List[dict]] = {}
    for r in reports:
        d = datetime.fromisoformat(r["ts"]).date()
        start, end = _week_bounds(d)
        key = start.isoformat()
        weeks.setdefault(key, []).append(r)

    summaries = []
    for start_iso, items in sorted(weeks.items()):
        start = date.fromisoformat(start_iso)
        end = start + timedelta(days=6)
        bmis = [x["bmi"] for x in items]
        weights = [x["weight"] for x in items]
        bmrs = [x["bmr"] for x in items]
        tdees = [x["tdee"] for x in items]
        summaries.append(
            {
                "week_start": start.isoformat(),
                "week_end": end.isoformat(),
                "report_count": len(items),
                "avg_bmi": round(sum(bmis) / len(bmis), 2),
                "avg_weight": round(sum(weights) / len(weights), 1),
                "avg_bmr": round(sum(bmrs) / len(bmrs), 1),
                "avg_tdee": round(sum(tdees) / len(tdees), 1),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return summaries


def ensure_weekly_summaries(force: bool = False) -> List[dict]:
    """自动生成 / 更新每周汇总。

    - 满足「每隔一星期」：距上次自动运行 ≥7 天或首次运行时自动执行；
    - 汇总按周幂等 upsert，始终反映最新历史数据；
    - force=True 时跳过时间间隔限制（用于手动按钮 / 测试）。
    返回当前所有周汇总列表。
    """
    conn = _connect()
    try:
        last = conn.execute(
            "SELECT value FROM meta WHERE key = ?", (_AUTO_KEY,)
        ).fetchone()
        now = datetime.now()
        if not force and last:
            last_dt = datetime.fromisoformat(last["value"])
            if (now - last_dt) < timedelta(days=7):
                # 未到自动周期，直接返回已有汇总
                return get_weekly_summaries()

        summaries = _aggregate_weekly()
        for s in summaries:
            conn.execute(
                """
                INSERT INTO weekly_summary (
                    week_start, week_end, report_count, avg_bmi, avg_weight,
                    avg_bmr, avg_tdee, generated_at
                ) VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(week_start) DO UPDATE SET
                    week_end     = excluded.week_end,
                    report_count = excluded.report_count,
                    avg_bmi      = excluded.avg_bmi,
                    avg_weight   = excluded.avg_weight,
                    avg_bmr      = excluded.avg_bmr,
                    avg_tdee     = excluded.avg_tdee,
                    generated_at = excluded.generated_at
                """,
                (
                    s["week_start"],
                    s["week_end"],
                    s["report_count"],
                    s["avg_bmi"],
                    s["avg_weight"],
                    s["avg_bmr"],
                    s["avg_tdee"],
                    s["generated_at"],
                ),
            )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_AUTO_KEY, now.isoformat(timespec="seconds")),
        )
        conn.commit()
        return get_weekly_summaries()
    finally:
        conn.close()


def get_weekly_summaries() -> List[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM weekly_summary ORDER BY week_start DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def export_reports_csv(path: str) -> None:
    rows = list_reports()
    if not rows:
        return
    cols = [
        "id", "ts", "name", "gender", "age", "height", "weight", "activity",
        "bmi", "bmi_label", "bmr", "tdee", "body_fat", "body_fat_label",
        "healthy_low", "healthy_high",
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_weekly_csv(path: str) -> None:
    rows = get_weekly_summaries()
    if not rows:
        return
    cols = [
        "id", "week_start", "week_end", "report_count",
        "avg_bmi", "avg_weight", "avg_bmr", "avg_tdee", "generated_at",
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
