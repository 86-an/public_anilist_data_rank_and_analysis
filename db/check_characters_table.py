import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'anime_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# charactersテーブルの構造を確認
cursor.execute("PRAGMA table_info(characters)")
columns = cursor.fetchall()
print("charactersテーブルの構造:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# サンプルデータを取得
print("\nサンプルデータ（最初の3件）:")
cursor.execute("SELECT * FROM characters LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
