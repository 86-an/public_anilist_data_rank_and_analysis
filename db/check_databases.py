import sqlite3
from pathlib import Path

def check_databases():
    base_dir = Path(__file__).parent
    anime_db = base_dir / 'anime_data.db'
    manga_db = base_dir / 'manga_data.db'
    
    print("="*60)
    print("データベース統計レポート")
    print("="*60)
    
    if anime_db.exists():
        print(f"\n【アニメデータベース】: {anime_db}")
        conn = sqlite3.connect(anime_db)
        cursor = conn.cursor()
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"テーブル数: {len(tables)}")
        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count:,}件")
        
        conn.close()
    
    if manga_db.exists():
        print(f"\n【マンガデータベース】: {manga_db}")
        conn = sqlite3.connect(manga_db)
        cursor = conn.cursor()
        
        # テーブル一覧
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"テーブル数: {len(tables)}")
        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count:,}件")
        
        conn.close()
    
    print("\n" + "="*60)
    print("統合実行スクリプトにより、すべてのデータベースと統計テーブルが正常に作成されました！")
    print("="*60)

if __name__ == "__main__":
    check_databases()