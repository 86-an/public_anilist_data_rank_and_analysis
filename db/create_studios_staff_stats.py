import sqlite3
from pathlib import Path
import numpy as np


def create_studios_basic_table(cursor):
    """スタジオ基本統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS studios_basic (
            studios_id INTEGER PRIMARY KEY,
            studios_name TEXT,
            studios_count INTEGER,
            first_year INTEGER,
            year_count INTEGER,
            count_per_year REAL
        )
    ''')


def create_studios_stats_table(cursor):
    """スタジオ統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS studios_stats (
            studios_id INTEGER,
            stat_type TEXT,
            total REAL,
            max_value REAL,
            min_value REAL,
            avg_value REAL,
            median_value REAL,
            q1_value REAL,
            q3_value REAL,
            PRIMARY KEY (studios_id, stat_type),
            FOREIGN KEY (studios_id) REFERENCES studios_basic(studios_id)
        )
    ''')


def create_staff_basic_table(cursor):
    """スタッフ基本統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_basic (
            staff_id INTEGER PRIMARY KEY,
            staff_name TEXT,
            favorites INTEGER,
            staff_count INTEGER,
            first_year INTEGER,
            year_count INTEGER,
            count_per_year REAL
        )
    ''')


def create_staff_stats_table(cursor):
    """スタッフ統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_stats (
            staff_id INTEGER,
            stat_type TEXT,
            total REAL,
            max_value REAL,
            min_value REAL,
            avg_value REAL,
            median_value REAL,
            q1_value REAL,
            q3_value REAL,
            PRIMARY KEY (staff_id, stat_type),
            FOREIGN KEY (staff_id) REFERENCES staff_basic(staff_id)
        )
    ''')


def create_staff_role_table(cursor):
    """スタッフロールテーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff_role (
            staff_id INTEGER,
            role TEXT,
            PRIMARY KEY (staff_id, role),
            FOREIGN KEY (staff_id) REFERENCES staff_basic(staff_id)
        )
    ''')


def calculate_percentiles(values):
    """パーセンタイル値を計算"""
    if not values:
        return None, None, None, None, None, None, None
    
    arr = np.array([v for v in values if v is not None])
    if len(arr) == 0:
        return None, None, None, None, None, None, None
    
    total = float(np.sum(arr))
    max_val = float(np.max(arr))
    min_val = float(np.min(arr))
    avg_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    q1_val = float(np.percentile(arr, 25))
    q3_val = float(np.percentile(arr, 75))
    
    return total, max_val, min_val, avg_val, median_val, q1_val, q3_val


def extract_studios_basic_data(cursor):
    """スタジオ基本データを抽出"""
    print("スタジオ基本データを計算中...")
    
    cursor.execute('''
        SELECT 
            s.studios_id,
            s.studios_name,
            COUNT(DISTINCT s.anilist_id) as studios_count,
            MIN(a.seasonYear) as first_year,
            COUNT(DISTINCT a.seasonYear) as year_count
        FROM studios s
        JOIN anime a ON s.anilist_id = a.anilist_id
        WHERE a.seasonYear IS NOT NULL
        GROUP BY s.studios_id, s.studios_name
        HAVING studios_count > 0
        ORDER BY studios_count DESC
    ''')
    
    basic_data = []
    for row in cursor.fetchall():
        studios_id, studios_name, count, first_year, year_count = row
        
        count_per_year = count / year_count if year_count > 0 else 0
        
        basic_data.append({
            'studios_id': studios_id,
            'studios_name': studios_name,
            'studios_count': count,
            'first_year': first_year,
            'year_count': year_count,
            'count_per_year': count_per_year
        })
    
    print(f"   処理完了: {len(basic_data)}スタジオ")
    return basic_data


def extract_studios_stats_data(cursor):
    """スタジオ統計データを抽出"""
    print("スタジオ統計データを計算中...")
    
    stats_data = []
    
    cursor.execute('''
        SELECT DISTINCT studios_id 
        FROM studios 
        ORDER BY studios_id
    ''')
    
    studios_ids = [row[0] for row in cursor.fetchall()]
    processed = 0
    
    for studio_id in studios_ids:
        processed += 1
        if processed % 500 == 0:
            print(f"   進行状況: {processed}/{len(studios_ids)} ({processed/len(studios_ids)*100:.1f}%)")
        
        # anime_favorites統計
        cursor.execute('''
            SELECT a.favorites
            FROM studios s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.studios_id = ? AND a.favorites IS NOT NULL
        ''', (studio_id,))
        
        favorites_values = [row[0] for row in cursor.fetchall()]
        if favorites_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(favorites_values)
            stats_data.append({
                'studios_id': studio_id,
                'stat_type': 'anime_favorites',
                'total': total,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'median_value': median_val,
                'q1_value': q1_val,
                'q3_value': q3_val
            })
        
        # anime_popularity統計
        cursor.execute('''
            SELECT a.popularity
            FROM studios s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.studios_id = ? AND a.popularity IS NOT NULL
        ''', (studio_id,))
        
        popularity_values = [row[0] for row in cursor.fetchall()]
        if popularity_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(popularity_values)
            stats_data.append({
                'studios_id': studio_id,
                'stat_type': 'anime_popularity',
                'total': total,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'median_value': median_val,
                'q1_value': q1_val,
                'q3_value': q3_val
            })
    
    print(f"   処理完了: {len(stats_data)}件の統計データ")
    return stats_data


def extract_staff_basic_data(cursor):
    """スタッフ基本データを抽出"""
    print("スタッフ基本データを計算中...")
    
    cursor.execute('''
        SELECT 
            s.staff_id,
            s.staff_name,
            s.favorites,
            COUNT(DISTINCT s.anilist_id) as staff_count,
            MIN(a.seasonYear) as first_year,
            COUNT(DISTINCT a.seasonYear) as year_count
        FROM staff s
        JOIN anime a ON s.anilist_id = a.anilist_id
        WHERE a.seasonYear IS NOT NULL
        GROUP BY s.staff_id, s.staff_name, s.favorites
        HAVING staff_count > 0
        ORDER BY staff_count DESC
    ''')
    
    basic_data = []
    for row in cursor.fetchall():
        staff_id, staff_name, favorites, count, first_year, year_count = row
        
        count_per_year = count / year_count if year_count > 0 else 0
        
        basic_data.append({
            'staff_id': staff_id,
            'staff_name': staff_name,
            'favorites': favorites,
            'staff_count': count,
            'first_year': first_year,
            'year_count': year_count,
            'count_per_year': count_per_year
        })
    
    print(f"   処理完了: {len(basic_data)}人のスタッフ")
    return basic_data


def extract_staff_stats_data(cursor):
    """スタッフ統計データを抽出"""
    print("スタッフ統計データを計算中...")
    
    stats_data = []
    
    cursor.execute('''
        SELECT DISTINCT staff_id 
        FROM staff 
        ORDER BY staff_id
    ''')
    
    staff_ids = [row[0] for row in cursor.fetchall()]
    processed = 0
    
    for staff_id in staff_ids:
        processed += 1
        if processed % 500 == 0:
            print(f"   進行状況: {processed}/{len(staff_ids)} ({processed/len(staff_ids)*100:.1f}%)")
        
        # anime_favorites統計
        cursor.execute('''
            SELECT a.favorites
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.favorites IS NOT NULL
        ''', (staff_id,))
        
        favorites_values = [row[0] for row in cursor.fetchall()]
        if favorites_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(favorites_values)
            stats_data.append({
                'staff_id': staff_id,
                'stat_type': 'anime_favorites',
                'total': total,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'median_value': median_val,
                'q1_value': q1_val,
                'q3_value': q3_val
            })
        
        # anime_meanScore統計
        cursor.execute('''
            SELECT a.meanScore
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.meanScore IS NOT NULL
        ''', (staff_id,))
        
        score_values = [row[0] for row in cursor.fetchall()]
        if score_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(score_values)
            stats_data.append({
                'staff_id': staff_id,
                'stat_type': 'anime_meanScore',
                'total': total,
                'max_value': max_val,
                'min_value': min_val,
                'avg_value': avg_val,
                'median_value': median_val,
                'q1_value': q1_val,
                'q3_value': q3_val
            })
    
    print(f"   処理完了: {len(stats_data)}件の統計データ")
    return stats_data


def extract_staff_role_data(cursor):
    """スタッフロールデータを抽出"""
    print("スタッフロールデータを抽出中...")
    
    cursor.execute('''
        SELECT DISTINCT staff_id, role
        FROM staff
        ORDER BY staff_id, role
    ''')
    
    role_data = []
    for row in cursor.fetchall():
        staff_id, role = row
        role_data.append({
            'staff_id': staff_id,
            'role': role
        })
    
    print(f"   処理完了: {len(role_data)}件のロールデータ")
    return role_data


def insert_studios_basic_data(cursor, basic_data):
    """スタジオ基本データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO studios_basic (
            studios_id, studios_name, studios_count, first_year,
            year_count, count_per_year
        ) VALUES (
            :studios_id, :studios_name, :studios_count, :first_year,
            :year_count, :count_per_year
        )
    ''', basic_data)


def insert_studios_stats_data(cursor, stats_data):
    """スタジオ統計データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO studios_stats (
            studios_id, stat_type, total, max_value, min_value,
            avg_value, median_value, q1_value, q3_value
        ) VALUES (
            :studios_id, :stat_type, :total, :max_value, :min_value,
            :avg_value, :median_value, :q1_value, :q3_value
        )
    ''', stats_data)


def insert_staff_basic_data(cursor, basic_data):
    """スタッフ基本データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO staff_basic (
            staff_id, staff_name, favorites, staff_count,
            first_year, year_count, count_per_year
        ) VALUES (
            :staff_id, :staff_name, :favorites, :staff_count,
            :first_year, :year_count, :count_per_year
        )
    ''', basic_data)


def insert_staff_stats_data(cursor, stats_data):
    """スタッフ統計データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO staff_stats (
            staff_id, stat_type, total, max_value, min_value,
            avg_value, median_value, q1_value, q3_value
        ) VALUES (
            :staff_id, :stat_type, :total, :max_value, :min_value,
            :avg_value, :median_value, :q1_value, :q3_value
        )
    ''', stats_data)


def insert_staff_role_data(cursor, role_data):
    """スタッフロールデータを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO staff_role (
            staff_id, role
        ) VALUES (
            :staff_id, :role
        )
    ''', role_data)


def main():
    db_file = Path(__file__).parent / 'anime_data.db'
    
    print("="*70)
    print("スタジオ・スタッフ統計テーブル作成ツール")
    print("="*70)
    
    if not db_file.exists():
        print(f"エラー: データベースが見つかりません: {db_file}")
        return
    
    print(f"\nデータベースに接続中: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # テーブル作成
    print("\n=== テーブル作成 ===")
    print("1. studios_basicテーブル作成中...")
    create_studios_basic_table(cursor)
    
    print("2. studios_statsテーブル作成中...")
    create_studios_stats_table(cursor)
    
    print("3. staff_basicテーブル作成中...")
    create_staff_basic_table(cursor)
    
    print("4. staff_statsテーブル作成中...")
    create_staff_stats_table(cursor)
    
    print("5. staff_roleテーブル作成中...")
    create_staff_role_table(cursor)
    print("   テーブル作成完了")
    
    # データ抽出・計算
    print("\n=== データ抽出・計算 ===")
    studios_basic_data = extract_studios_basic_data(cursor)
    studios_stats_data = extract_studios_stats_data(cursor)
    staff_basic_data = extract_staff_basic_data(cursor)
    staff_stats_data = extract_staff_stats_data(cursor)
    staff_role_data = extract_staff_role_data(cursor)
    
    # データ挿入
    print("\n=== データ挿入 ===")
    print("1. スタジオ基本データを挿入中...")
    insert_studios_basic_data(cursor, studios_basic_data)
    print(f"   挿入完了: {len(studios_basic_data)}件")
    
    print("2. スタジオ統計データを挿入中...")
    insert_studios_stats_data(cursor, studios_stats_data)
    print(f"   挿入完了: {len(studios_stats_data)}件")
    
    print("3. スタッフ基本データを挿入中...")
    insert_staff_basic_data(cursor, staff_basic_data)
    print(f"   挿入完了: {len(staff_basic_data)}件")
    
    print("4. スタッフ統計データを挿入中...")
    insert_staff_stats_data(cursor, staff_stats_data)
    print(f"   挿入完了: {len(staff_stats_data)}件")
    
    print("5. スタッフロールデータを挿入中...")
    insert_staff_role_data(cursor, staff_role_data)
    print(f"   挿入完了: {len(staff_role_data)}件")
    
    conn.commit()
    
    # 確認用データ表示
    print("\n" + "="*70)
    print("【確認: 統計テーブル】")
    print("="*70)
    
    print("\n【studios_basicテーブル】上位5件（作品数順）:")
    cursor.execute('''
        SELECT * FROM studios_basic 
        ORDER BY studios_count DESC 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    print("\n【staff_basicテーブル】上位5件（作品数順）:")
    cursor.execute('''
        SELECT * FROM staff_basic 
        ORDER BY staff_count DESC 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    print("\n【staff_roleテーブル】サンプル（最初の5件）:")
    cursor.execute('''
        SELECT * FROM staff_role 
        ORDER BY staff_id, role 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # 統計情報
    print("\n" + "="*70)
    print("【統計情報】")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM studios_basic")
    print(f"スタジオ総数: {cursor.fetchone()[0]}スタジオ")
    
    cursor.execute("SELECT COUNT(*) FROM studios_stats")
    print(f"スタジオ統計レコード総数: {cursor.fetchone()[0]}件")
    
    cursor.execute("SELECT COUNT(*) FROM staff_basic")
    print(f"スタッフ総数: {cursor.fetchone()[0]}人")
    
    cursor.execute("SELECT COUNT(*) FROM staff_stats")
    print(f"スタッフ統計レコード総数: {cursor.fetchone()[0]}件")
    
    cursor.execute("SELECT COUNT(*) FROM staff_role")
    print(f"スタッフロール総数: {cursor.fetchone()[0]}件")
    
    cursor.execute("SELECT COUNT(DISTINCT role) FROM staff_role")
    print(f"ユニークなロール数: {cursor.fetchone()[0]}種類")
    
    # トップ企業の詳細表示
    print("\n" + "="*70)
    print("【トップスタジオの詳細】")
    print("="*70)
    
    cursor.execute('''
        SELECT studios_id, studios_name, studios_count, first_year, year_count, count_per_year
        FROM studios_basic
        ORDER BY studios_count DESC
        LIMIT 3
    ''')
    
    for basic_row in cursor.fetchall():
        studio_id, studio_name, count, first_year, year_count, count_per_year = basic_row
        print(f"\n【{studio_name} (ID: {studio_id})】")
        print(f"  作品数: {count}作品")
        print(f"  初出年: {first_year}年")
        print(f"  活動年数: {year_count}年")
        print(f"  年平均: {count_per_year:.2f}作品/年")
    
    conn.close()
    
    print("\n" + "="*70)
    print("完了しました！")
    print("="*70)


if __name__ == "__main__":
    main()