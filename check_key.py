from sqlalchemy import inspect

import db

if not hasattr(db, "engine"):
    raise SystemExit("db.py purani (sqlite3 wali) hai. Chapter 19 Step 5 ki nayi db.py paste kar.")

url = db.engine.url
print("Database type:", url.get_backend_name())
if url.get_backend_name() == "sqlite":
    print("Ye local SQLite hai. DATABASE_URL .env se padhi nahi gayi.")
else:
    print("Host:", url.host, "| port:", url.port, "| database:", url.database)

db.init_db()
print("Tables:", inspect(db.engine).get_table_names())
