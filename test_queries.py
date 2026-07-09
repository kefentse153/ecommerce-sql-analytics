import sqlite3, re, sys

conn = sqlite3.connect(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\ecommerce.db")
cur = conn.cursor()

with open(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\queries\queries.sql") as f:
    sql = f.read()

# split into blocks on the divider lines, keep blocks that contain a query
divider = "-- ------------------------------------------------------------"
raw_blocks = [b for b in sql.split(divider) if b.strip()]
# merge each header-comment block with the SQL block that follows it
blocks = []
i = 0
while i < len(raw_blocks):
    if re.search(r"-- Q\d+\.", raw_blocks[i]):
        merged = raw_blocks[i] + (raw_blocks[i + 1] if i + 1 < len(raw_blocks) else "")
        blocks.append(merged)
        i += 2
    else:
        i += 1

for b in blocks:
    m = re.search(r"-- Q(\d+)\.", b)
    num = m.group(1)
    statement = b.strip()
    try:
        cur.execute(statement)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print(f"Q{num}: OK, {len(rows)} rows, cols={cols}")
        if rows:
            print("   sample:", rows[0])
    except Exception as e:
        print(f"Q{num}: FAILED -> {e}")
        sys.exit(1)

print("\nAll queries executed successfully.")
