"""
Loads your 6 F1 CSV files directly into f1.db using Python built-in sqlite3.
NO Flask, NO SQLAlchemy needed.

Put CSVs in:  data/
Run:          python load_from_csv.py
"""
import sqlite3
import csv
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(os.path.dirname(__file__), "f1.db")

# ── Helpers ────────────────────────────────────────────────────────────────


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [WARN] Not found: {path}")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_str(val):
    if val is None:
        return None
    v = str(val).strip()
    return None if v in ("", "\\N", "None", "NULL", "nan") else v


def safe_int(val):
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def safe_float(val):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None


def safe_date(val):
    if not val:
        return None
    v = str(val).strip()
    if v in ("", "\\N", "None", "NULL", "nan"):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def col(row, *keys):
    """Try multiple possible column names, return first match."""
    for k in keys:
        v = safe_str(row.get(k))
        if v:
            return v
    return None


# ── Create Tables ──────────────────────────────────────────────────────────
def create_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS f1_drivers (
        driver_id   TEXT PRIMARY KEY,
        given_name  TEXT,
        family_name TEXT,
        dob         TEXT,
        nationality TEXT,
        number      INTEGER,
        code        TEXT,
        url         TEXT
    );

    CREATE TABLE IF NOT EXISTS f1_circuits (
        circuit_id   TEXT PRIMARY KEY,
        circuit_name TEXT,
        locality     TEXT,
        country      TEXT,
        lat          REAL,
        lng          REAL,
        url          TEXT
    );

    CREATE TABLE IF NOT EXISTS f1_constructors (
        constructor_id TEXT PRIMARY KEY,
        name           TEXT,
        nationality    TEXT,
        url            TEXT
    );

    CREATE TABLE IF NOT EXISTS f1_races (
        season     INTEGER,
        round      INTEGER,
        race_name  TEXT,
        circuit_id TEXT,
        date       TEXT,
        time       TEXT,
        url        TEXT,
        PRIMARY KEY (season, round),
        FOREIGN KEY (circuit_id) REFERENCES f1_circuits(circuit_id)
    );

    CREATE TABLE IF NOT EXISTS f1_driver_standings (
        season      INTEGER,
        position    INTEGER,
        points      INTEGER,
        wins        INTEGER,
        driver_id   TEXT,
        constructor TEXT,
        PRIMARY KEY (season, driver_id),
        FOREIGN KEY (driver_id) REFERENCES f1_drivers(driver_id)
    );

    CREATE TABLE IF NOT EXISTS f1_constructor_standings (
        season         INTEGER,
        position       INTEGER,
        points         INTEGER,
        wins           INTEGER,
        constructor_id TEXT,
        constructor    TEXT,
        PRIMARY KEY (season, constructor_id),
        FOREIGN KEY (constructor_id) REFERENCES f1_constructors(constructor_id)
    );
    """)
    conn.commit()
    print("  ✓ Tables ready\n")


# ── Loaders ────────────────────────────────────────────────────────────────
def load_drivers(conn):
    print("Loading f1_drivers.csv ...")
    rows = read_csv("f1_drivers.csv")
    added = 0
    for r in rows:
        did = col(r, "driver_id", "driverId", "driverRef")
        if not did:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_drivers
                (driver_id, given_name, family_name, dob, nationality, number, code, url)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                did,
                col(r, "given_name",  "givenName",  "forename"),
                col(r, "family_name", "familyName", "surname"),
                safe_date(col(r, "dob", "dateOfBirth")),
                col(r, "nationality"),
                safe_int(col(r, "number", "permanentNumber")),
                col(r, "code"),
                col(r, "url"),
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] driver {did}: {e}")
    conn.commit()
    print(f"  ✓ {added} drivers loaded\n")


def load_circuits(conn):
    print("Loading f1_circuits.csv ...")
    rows = read_csv("f1_circuits.csv")
    added = 0
    for r in rows:
        cid = col(r, "circuit_id", "circuitId", "circuitRef")
        if not cid:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_circuits
                (circuit_id, circuit_name, locality, country, lat, lng, url)
                VALUES (?,?,?,?,?,?,?)
            """, (
                cid,
                col(r, "circuit_name", "circuitName", "name"),
                col(r, "locality", "location"),
                col(r, "country"),
                safe_float(col(r, "lat")),
                safe_float(col(r, "lng", "long")),
                col(r, "url"),
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] circuit {cid}: {e}")
    conn.commit()
    print(f"  ✓ {added} circuits loaded\n")


def load_constructors(conn):
    print("Loading f1_constructors.csv ...")
    rows = read_csv("f1_constructors.csv")
    added = 0
    for r in rows:
        cid = col(r, "constructor_id", "constructorId", "constructorRef")
        if not cid:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_constructors
                (constructor_id, name, nationality, url)
                VALUES (?,?,?,?)
            """, (
                cid,
                col(r, "name"),
                col(r, "nationality"),
                col(r, "url"),
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] constructor {cid}: {e}")
    conn.commit()
    print(f"  ✓ {added} constructors loaded\n")


def load_races(conn):
    print("Loading f1_races.csv ...")
    rows = read_csv("f1_races.csv")
    added = 0
    for r in rows:
        season = safe_int(col(r, "season", "year"))
        round_num = safe_int(col(r, "round"))
        cid = col(r, "circuit_id", "circuitId", "circuitRef")
        if not season or not round_num or not cid:
            continue
        # Check circuit exists
        exists = conn.execute(
            "SELECT 1 FROM f1_circuits WHERE circuit_id=?", (cid,)
        ).fetchone()
        if not exists:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_races
                (season, round, race_name, circuit_id, date, url)
                VALUES (?,?,?,?,?,?)
            """, (
                season,
                round_num,
                col(r, "race_name", "raceName", "name"),
                cid,
                safe_date(col(r, "date")),
                col(r, "url"),
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] race {season} R{round_num}: {e}")
    conn.commit()
    print(f"  ✓ {added} races loaded\n")


def load_driver_standings(conn):
    print("Loading f1_driver_standings.csv ...")
    rows = read_csv("f1_driver_standings.csv")
    added = 0
    for r in rows:
        season = safe_int(col(r, "season", "year"))
        did = col(r, "driver_id", "driverId", "driverRef")
        if not season or not did:
            continue
        # Check driver exists
        exists = conn.execute(
            "SELECT 1 FROM f1_drivers WHERE driver_id=?", (did,)
        ).fetchone()
        if not exists:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_driver_standings
                (season, position, points, wins, driver_id, constructor)
                VALUES (?,?,?,?,?,?)
            """, (
                season,
                safe_int(col(r, "position")),
                safe_int(col(r, "points")),
                safe_int(col(r, "wins")),
                did,
                col(r, "constructor", "constructorName", "constructor_name"),
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] driver standing {season}/{did}: {e}")
    conn.commit()
    print(f"  ✓ {added} driver standings loaded\n")


def load_constructor_standings(conn):
    print("Loading f1_constructor_standings.csv ...")
    rows = read_csv("f1_constructor_standings.csv")
    added = 0
    for r in rows:
        season = safe_int(col(r, "season", "year"))
        cid = col(r, "constructor_id", "constructorId", "constructorRef")
        if not season or not cid:
            continue
        exists = conn.execute(
            "SELECT 1 FROM f1_constructors WHERE constructor_id=?", (cid,)
        ).fetchone()
        if not exists:
            continue
        # Get constructor name
        name_row = conn.execute(
            "SELECT name FROM f1_constructors WHERE constructor_id=?", (cid,)
        ).fetchone()
        con_name = name_row[0] if name_row else col(r, "constructor", "name")
        try:
            conn.execute("""
                INSERT OR IGNORE INTO f1_constructor_standings
                (season, position, points, wins, constructor_id, constructor)
                VALUES (?,?,?,?,?,?)
            """, (
                season,
                safe_int(col(r, "position")),
                safe_int(col(r, "points")),
                safe_int(col(r, "wins")),
                cid,
                con_name,
            ))
            added += conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            print(f"  [ERR] constructor standing {season}/{cid}: {e}")
    conn.commit()
    print(f"  ✓ {added} constructor standings loaded\n")


# ── Main ───────────────────────────────────────────────────────────────────
def load_all():
    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: 'data/' folder not found.")
        print(f"Create it at: {DATA_DIR}")
        print("Put your 6 CSV files inside it.")
        return

    print(f"=== F1 CSV Loader ===")
    print(f"  DB:   {DB_PATH}")
    print(f"  Data: {DATA_DIR}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        create_tables(conn)
        load_drivers(conn)
        load_circuits(conn)
        load_constructors(conn)
        load_races(conn)
        load_driver_standings(conn)
        load_constructor_standings(conn)

        # ── Summary ───────────────────────────────────────
        print("=" * 40)
        tables = [
            "f1_drivers", "f1_circuits", "f1_constructors",
            "f1_races", "f1_driver_standings", "f1_constructor_standings"
        ]
        total = 0
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            total += count
            print(f"  {t:<35} {count:>5}")
        print(f"{'  TOTAL RECORDS':<35} {total:>5}")
        print("=" * 40)

        if total < 2000:
            print(
                f"\n  [WARN] Only {total} records — assignment needs 2000-7000!")
        else:
            print(f"\n  [OK] {total} records — meets assignment requirement ✓")

    finally:
        conn.close()


if __name__ == "__main__":
    load_all()
