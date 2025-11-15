#!/usr/bin/env python3
"""
Oracle Metadata Explorer - terminal app.

Usage:
    python oracle_metadata_explorer.py

Connects using oracledb (thin mode by default). Prompts for credentials and an Oracle
DSN string (host:port/service_name or easy connect form).
"""

import oracledb
import getpass
import sys

def connect_prompt():
    print("Welcome to Oracle Metadata Explorer!")
    print("-----------------------------------")
    user = input("Enter username: ").strip()
    pwd = getpass.getpass("Enter password: ")
    dsn = input("Enter DSN (host:port/service or tns alias): ").strip()
    try:
        conn = oracledb.connect(user=user, password=pwd, dsn=dsn)
        print("Connected successfully.\n")
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def get_current_user(conn):
    cur = conn.cursor()
    cur.execute("SELECT USER FROM DUAL")
    r = cur.fetchone()
    return r[0] if r else None

def main_menu():
    print("Select the object type you want to view:")
    print("1. Tables")
    print("2. Views")
    print("3. Sequences")
    print("4. Users")
    print("5. Exit")
    choice = input("Enter option number: ").strip()
    return choice

def list_objects(conn, obj_type, owner=None):
    cur = conn.cursor()
    owner_clause = ""
    binds = {}
    if owner:
        owner_clause = " WHERE OWNER = :owner"
        binds['owner'] = owner.upper()

    if obj_type == "1":  # Tables
        # prioritize USER_TABLES for current user if owner is None
        if owner is None:
            cur.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        else:
            cur.execute("SELECT table_name FROM all_tables WHERE owner = :owner ORDER BY table_name", binds)
    elif obj_type == "2":  # Views
        if owner is None:
            cur.execute("SELECT view_name FROM user_views ORDER BY view_name")
        else:
            cur.execute("SELECT view_name FROM all_views WHERE owner = :owner ORDER BY view_name", binds)
    elif obj_type == "3":  # Sequences
        if owner is None:
            cur.execute("SELECT sequence_name FROM user_sequences ORDER BY sequence_name")
        else:
            cur.execute("SELECT sequence_name FROM all_sequences WHERE sequence_owner = :owner ORDER BY sequence_name", binds)
    elif obj_type == "4":  # Users
        # all_users available, no owner concept
        cur.execute("SELECT username FROM all_users ORDER BY username")
    else:
        return []

    rows = [r[0] for r in cur.fetchall()]
    return rows

def show_columns(conn, table_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT column_id, column_name, data_type, data_length, nullable
        FROM user_tab_columns
        WHERE table_name = :t
        ORDER BY column_id
    """, [table_name])
    cols = cur.fetchall()
    if not cols:
        # try ALL_TAB_COLUMNS for cross-schema
        cur.execute("""
            SELECT owner, column_id, column_name, data_type, data_length, nullable
            FROM all_tab_columns
            WHERE table_name = :t
            ORDER BY owner, column_id
        """, [table_name])
        cols = cur.fetchall()
        print("(From ALL_TAB_COLUMNS)")
        for r in cols:
            owner, cid, cname, dtype, dlen, nullable = r
            print(f"{owner}.{cname} ({dtype}{'('+str(dlen)+')' if dlen else ''}) NULLABLE={nullable}")
        return

    print(f"Columns of {table_name}:")
    for col in cols:
        cid, cname, dtype, dlen, nullable = col
        extra = f"({dlen})" if dlen else ""
        print(f"{cid:>2}. {cname} - {dtype}{extra}  NULLABLE={nullable}")

def show_constraints(conn, object_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT constraint_name, constraint_type, status, delete_rule
        FROM user_constraints
        WHERE table_name = :t
        ORDER BY constraint_name
    """, [object_name])
    rows = cur.fetchall()
    if not rows:
        # try ALL_CONSTRAINTS
        cur.execute("""
            SELECT owner, constraint_name, constraint_type, status
            FROM all_constraints
            WHERE table_name = :t
            ORDER BY owner, constraint_name
        """, [object_name])
        rows = cur.fetchall()
        for r in rows:
            owner, cname, ctype, status = r
            print(f"{owner}.{cname} [{ctype}] status={status}")
        return

    print(f"Constraints on {object_name}:")
    for c in rows:
        cname, ctype, status, delrule = c
        print(f"- {cname}  type={ctype}  status={status}  delete_rule={delrule}")

    # Show constraint columns
    cur.execute("""
        SELECT a.constraint_name, a.column_name, a.position
        FROM user_cons_columns a
        JOIN user_constraints b ON a.constraint_name = b.constraint_name
        WHERE b.table_name = :t
        ORDER BY a.constraint_name, a.position
    """, [object_name])
    cons_cols = cur.fetchall()
    if cons_cols:
        print("\nConstraint columns:")
        last = None
        for cname, colname, pos in cons_cols:
            if cname != last:
                print(f" {cname}: {colname}", end="")
            else:
                print(f", {colname}", end="")
            last = cname
        print()

def show_indexes(conn, object_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT index_name, uniqueness, last_analyzed
        FROM user_indexes
        WHERE table_name = :t
        ORDER BY index_name
    """, [object_name])
    rows = cur.fetchall()
    if not rows:
        # try ALL_INDEXES
        cur.execute("""
            SELECT owner, index_name, uniqueness
            FROM all_indexes
            WHERE table_name = :t
            ORDER BY owner, index_name
        """, [object_name])
        rows = cur.fetchall()
        for r in rows:
            owner, iname, uniq = r
            print(f"{owner}.{iname} uniqueness={uniq}")
        return
    print(f"Indexes on {object_name}:")
    for iname, uniq, analyzed in rows:
        print(f"- {iname}  uniqueness={uniq}  last_analyzed={analyzed}")

    # show index columns
    cur.execute("""
        SELECT index_name, column_name, column_position
        FROM user_ind_columns
        WHERE table_name = :t
        ORDER BY index_name, column_position
    """, [object_name])
    cols = cur.fetchall()
    if cols:
        print("\nIndex columns:")
        last = None
        for iname, colname, pos in cols:
            if iname != last:
                print(f" {iname}: {colname}", end="")
            else:
                print(f", {colname}", end="")
            last = iname
        print()

def preview_rows(conn, table_name, n=5):
    cur = conn.cursor()
    # table_name came from the DB listing so it's safe; still we uppercase it
    sql = f"SELECT * FROM {table_name} WHERE ROWNUM <= :n"
    try:
        cur.execute(sql, [n])
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        if not rows:
            print("(no rows)")
            return
        # print header
        print(" | ".join(cols))
        print("-" * min(120, max(len(" | ".join(cols)), 40)))
        for r in rows:
            print(" | ".join(str(x) if x is not None else "NULL" for x in r))
    except Exception as e:
        print(f"Failed to preview rows: {e}")

def object_submenu(conn, obj_type, object_name):
    while True:
        print(f"\nYou selected: {object_name}")
        print(f"Choose what to view about {object_name}:")
        print("1. Columns")
        print("2. Constraints")
        print("3. Indexes")
        print("4. Preview rows (first 5)")
        print("5. Back to main menu")
        choice = input("Enter option number: ").strip()
        if choice == "1":
            show_columns(conn, object_name)
        elif choice == "2":
            show_constraints(conn, object_name)
        elif choice == "3":
            show_indexes(conn, object_name)
        elif choice == "4":
            preview_rows(conn, object_name, n=5)
        elif choice == "5":
            return
        else:
            print("Invalid option. Try again.")

def run_explorer(conn):
    current_user = get_current_user(conn)
    while True:
        choice = main_menu()
        if choice == "5":
            print("Goodbye.")
            return
        if choice not in {"1","2","3","4"}:
            print("Invalid selection, try again.\n")
            continue

        # ask whether to specify schema (owner) for tables/views/sequences
        owner = None
        if choice in {"1","2","3"}:
            ans = input(f"Explore objects in current schema '{current_user}'? (Y/n): ").strip().lower()
            if ans.startswith("n"):
                owner = input("Enter schema owner (username): ").strip().upper()

        objs = list_objects(conn, choice, owner=owner)
        if not objs:
            print("No objects found.")
            continue

        # show list
        print("\nAvailable objects:")
        for i, o in enumerate(objs, start=1):
            print(f"{i}. {o}")
        sel = input("Select a number (or 'b' to go back): ").strip()
        if sel.lower() == 'b':
            continue
        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(objs):
                raise IndexError()
            obj_name = objs[idx]
            # object_name may be "SCHEMA.NAME" in some calls, but usually just NAME
            object_submenu(conn, choice, obj_name)
        except Exception:
            print("Invalid selection. Returning to main menu.\n")
            continue

def main():
    conn = None
    tries = 0
    while not conn and tries < 3:
        conn = connect_prompt()
        tries += 1
        if not conn and tries < 3:
            print("Try again.\n")
    if not conn:
        print("Could not connect. Exiting.")
        sys.exit(1)

    try:
        run_explorer(conn)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()