import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'manga_data.db'

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # テーブル一覧を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("manga_data.dbのテーブル一覧:")
    print("-" * 50)
    for table in tables:
        print(f"  - {table[0]}")
    
    # staffテーブルがあるか確認
    if ('staff',) in tables:
        print("\n✅ staffテーブルが存在します")
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        print(f"   レコード数: {count:,}件")
        
        # サンプルデータを表示
        cursor.execute("SELECT * FROM staff LIMIT 5")
        print("\n   サンプルデータ:")
        for row in cursor.fetchall():
            print(f"     {row}")
        
        # スタッフの役割を確認
        cursor.execute("SELECT DISTINCT role FROM staff WHERE role IS NOT NULL")
        roles = cursor.fetchall()
        print(f"\n   役割の種類: {len(roles)}種類")
        for role in roles[:10]:
            print(f"     - {role[0]}")
    else:
        print("\n❌ staffテーブルは存在しません")
    
    conn.close()
else:
    print(f"❌ データベースが見つかりません: {db_path}")
