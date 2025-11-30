import sqlite3

conn = sqlite3.connect('manga_data.db')
cursor = conn.cursor()

# テーブル一覧
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# キャラクター数
cursor.execute('SELECT COUNT(*) FROM characters')
print('\nCharacters count:', cursor.fetchone()[0])

# サンプルデータ
cursor.execute('SELECT * FROM characters LIMIT 5')
print('\nSample characters:')
for row in cursor.fetchall():
    print(row)

# キャラクターとマンガのJOINテスト
cursor.execute('''
    SELECT c.chara_id, c.chara_name, c.favorites as char_favorites,
           m.title_native, m.favorites as manga_favorites
    FROM characters c
    JOIN manga m ON c.anilist_id = m.anilist_id
    ORDER BY c.favorites DESC
    LIMIT 5
''')
print('\nTop 5 characters with manga:')
for row in cursor.fetchall():
    print(row)

conn.close()
