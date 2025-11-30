import sqlite3
from pathlib import Path

def check_manga_staff_tables():
    """manga_data.dbのスタッフ関連テーブルを確認"""
    db_file = Path(__file__).parent / 'manga_data.db'
    
    print("="*70)
    print("manga_data.db スタッフテーブル確認")
    print("="*70)
    
    if not db_file.exists():
        print(f"❌ データベースが見つかりません: {db_file}")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # テーブル一覧
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\nmanga_data.dbのテーブル一覧:")
    for table in tables:
        print(f"  - {table}")
    
    # staffテーブルの確認
    print("\n" + "="*70)
    print("【staffテーブル】")
    print("="*70)
    
    if 'staff' in tables:
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        print(f"✅ staffテーブル: {count}件")
        
        cursor.execute("SELECT COUNT(DISTINCT staff_id) FROM staff")
        unique_staff = cursor.fetchone()[0]
        print(f"   ユニークなスタッフ数: {unique_staff}人")
        
        cursor.execute("SELECT COUNT(DISTINCT role) FROM staff")
        unique_roles = cursor.fetchone()[0]
        print(f"   ユニークなロール数: {unique_roles}種類")
        
        print("\n   サンプルデータ（5件）:")
        cursor.execute("SELECT * FROM staff LIMIT 5")
        for row in cursor.fetchall():
            print(f"     {row}")
    else:
        print("❌ staffテーブルが見つかりません")
    
    # staff_basic_enhancedテーブルの確認
    print("\n" + "="*70)
    print("【staff_basic_enhancedテーブル】")
    print("="*70)
    
    if 'staff_basic_enhanced' in tables:
        cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced")
        count = cursor.fetchone()[0]
        print(f"✅ staff_basic_enhancedテーブル: {count}件")
        
        print("\n   テーブル構造:")
        cursor.execute("PRAGMA table_info(staff_basic_enhanced)")
        for row in cursor.fetchall():
            print(f"     {row[1]} ({row[2]})")
        
        print("\n   上位3件（作品数順）:")
        cursor.execute('''
            SELECT staff_id, staff_name, total_count, favorites_avg, meanscore_avg
            FROM staff_basic_enhanced
            ORDER BY total_count DESC
            LIMIT 3
        ''')
        for row in cursor.fetchall():
            staff_id, name, count, fav_avg, score_avg = row
            print(f"     {staff_id} | {name} | 作品数:{count} | fav平均:{fav_avg:.1f} | score平均:{score_avg:.1f}")
    else:
        print("❌ staff_basic_enhancedテーブルが見つかりません")
    
    # staff_roleテーブルの確認
    print("\n" + "="*70)
    print("【staff_roleテーブル】")
    print("="*70)
    
    if 'staff_role' in tables:
        cursor.execute("SELECT COUNT(*) FROM staff_role")
        count = cursor.fetchone()[0]
        print(f"✅ staff_roleテーブル: {count}件")
        
        cursor.execute("SELECT COUNT(DISTINCT staff_id) FROM staff_role")
        unique_staff = cursor.fetchone()[0]
        print(f"   ユニークなスタッフ数: {unique_staff}人")
        
        cursor.execute("SELECT COUNT(DISTINCT role) FROM staff_role")
        unique_roles = cursor.fetchone()[0]
        print(f"   ユニークなロール数: {unique_roles}種類")
        
        print("\n   ロール一覧:")
        cursor.execute("SELECT role, COUNT(*) FROM staff_role GROUP BY role ORDER BY COUNT(*) DESC")
        for row in cursor.fetchall():
            print(f"     {row[0]}: {row[1]}件")
    else:
        print("❌ staff_roleテーブルが見つかりません")
    
    conn.close()
    
    print("\n" + "="*70)
    print("確認完了")
    print("="*70)

if __name__ == "__main__":
    check_manga_staff_tables()
