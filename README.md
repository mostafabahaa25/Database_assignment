# Oracle Metadata Explorer (CLI Tool)

A lightweight, interactive command-line application for exploring **Oracle database metadata**.
It connects to an Oracle database and lets you browse **tables, views, sequences, users**, and detailed metadata such as columns, constraints, indexes, and sample rows.

This tool uses the official **`oracledb`** Python driver (thin mode by default).

---

## Features

* 🔑 Interactive login (username, password, DSN)
* 📦 Browse:

  * Tables
  * Views
  * Sequences
  * Users
* 🔍 Inspect metadata:

  * Columns (with data types, nullability, lengths)
  * Constraints (PK, FK, unique, check…)
  * Constraint column details
  * Indexes + index columns
  * Row preview (`SELECT *` with ROWNUM ≤ 5)
* 🗂 Supports both:

  * Current user schema (USER_* views)
  * Cross-schema exploration (ALL_* views)
* 🧭 Simple text-based menu system

---

## Requirements

* Python **3.8+**
* Oracle Database reachable via network
* Python package:

  ```bash
  pip install oracledb
  ```

---

## How to Run

1. Clone or download the project.
2. Run the script:

```bash
python oracle_metadata_explorer.py
```

3. The app will prompt you for:

```
Enter username:
Enter password:
Enter DSN (host:port/service or tns alias):
```

Example DSN formats:

* `localhost:8521/freepdb`
* `myserver:1521/orcl`
* `tns_alias`

---

## Usage Flow

Once connected:

1. Choose an object type:

   ```
   1. Tables
   2. Views
   3. Sequences
   4. Users
   5. Exit
   ```

2. For tables/views/sequences, choose:

   * Current schema
   * Or specify a different owner (schema name)

3. Select an object to explore.

4. Choose what to view:

   ```
   1. Columns
   2. Constraints
   3. Indexes
   4. Preview rows (first 5)
   5. Back
   ```

---

## Example Output

### Column Listing

```
Columns of EMPLOYEES:
 1. EMP_ID - NUMBER(10)  NULLABLE=N
 2. NAME - VARCHAR2(100)  NULLABLE=Y
 3. DEPT_ID - NUMBER(10)  NULLABLE=Y
```

### Constraint Listing

```
Constraints on EMPLOYEES:
- PK_EMP  type=P  status=ENABLED  delete_rule=None

Constraint columns:
 PK_EMP: EMP_ID
```

---

## Code Structure

* `connect_prompt()` — login screen + connection attempt
* `main_menu()` — main object selection
* `list_objects()` — fetch USER_* or ALL_* metadata
* `show_columns()`, `show_constraints()`, `show_indexes()` — metadata viewers
* `preview_rows()` — safe row preview
* `object_submenu()` — per-object navigation
* `run_explorer()` — main interactive loop
* `main()` — entry point

---

## Notes

* The tool retries connection up to **3 times**.
* Works with Oracle Database **Thin Mode** (no client installation needed).
* Safe queries: no dynamic SQL except controlled table name usage from DB metadata.

---

## License

This code is for educational purpose.

