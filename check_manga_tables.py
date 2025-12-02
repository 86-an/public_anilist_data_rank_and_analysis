import sqlite3

db_path = r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in manga_data.db:")
for table in tables:
    print(f"  - {table[0]}")

# genresテーブルが存在する場合、構造を確認
if any('genres' in str(table).lower() for table in tables):
    print("\nGenres table structure:")
    cursor.execute("PRAGMA table_info(genres)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # サンプルデータを取得
    cursor.execute("SELECT * FROM genres LIMIT 5")
    samples = cursor.fetchall()
    print("\nSample data:")
    for sample in samples:
        print(f"  {sample}")

conn.close()
