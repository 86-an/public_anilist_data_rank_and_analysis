import sqlite3

conn = sqlite3.connect('anime_data.db')
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tables:', tables)
print()

# 声優関連のテーブルを探す
for table in tables:
    if 'voice' in table.lower() or 'actor' in table.lower() or 'staff' in table.lower():
        print(f'{table}:')
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        for col in cols:
            print(f'  {col}')
        
        # データ件数も確認
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f'  Records: {count:,}')
        print()

conn.close()
