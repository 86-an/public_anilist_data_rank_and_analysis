import sqlite3
from pathlib import Path
import numpy as np


def create_enhanced_staff_basic_table(cursor):
    """拡張されたスタッフ基本統計テーブルを作成（アニメ+マンガ）"""
    cursor.execute('''DROP TABLE IF EXISTS staff_basic_enhanced''')
    cursor.execute('''
        CREATE TABLE staff_basic_enhanced (
            staff_id INTEGER PRIMARY KEY,
            staff_name TEXT,
            favorites INTEGER,
            total_count INTEGER,
            first_year INTEGER,
            year_count INTEGER,
            count_per_year REAL,
            -- anime_favorites統計
            anime_favorites_total REAL,
            anime_favorites_max REAL,
            anime_favorites_min REAL,
            anime_favorites_avg REAL,
            anime_favorites_median REAL,
            anime_favorites_q1 REAL,
            anime_favorites_q3 REAL,
            -- anime_meanScore統計
            anime_meanscore_total REAL,
            anime_meanscore_max REAL,
            anime_meanscore_min REAL,
            anime_meanscore_avg REAL,
            anime_meanscore_median REAL,
            anime_meanscore_q1 REAL,
            anime_meanscore_q3 REAL,
            -- manga_favorites統計
            manga_favorites_total REAL,
            manga_favorites_max REAL,
            manga_favorites_min REAL,
            manga_favorites_avg REAL,
            manga_favorites_median REAL,
            manga_favorites_q1 REAL,
            manga_favorites_q3 REAL,
            -- manga_meanScore統計
            manga_meanscore_total REAL,
            manga_meanscore_max REAL,
            manga_meanscore_min REAL,
            manga_meanscore_avg REAL,
            manga_meanscore_median REAL,
            manga_meanscore_q1 REAL,
            manga_meanscore_q3 REAL
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


def extract_enhanced_staff_basic_data(anime_cursor, manga_cursor):
    """拡張されたスタッフ基本データを抽出（アニメ+マンガ）"""
    print("拡張スタッフ基本データを計算中（アニメ+マンガ）...")
    
    # アニメスタッフの基本情報を取得
    anime_cursor.execute('''
        SELECT DISTINCT staff_id, staff_name, favorites
        FROM staff
        ORDER BY staff_id
    ''')
    
    anime_staff_list = {row[0]: (row[1], row[2]) for row in anime_cursor.fetchall()}
    
    # マンガスタッフの基本情報を取得（マンガDBが存在する場合）
    manga_staff_list = {}
    if manga_cursor:
        try:
            manga_cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='staff'
            ''')
            if manga_cursor.fetchone():
                manga_cursor.execute('''
                    SELECT DISTINCT staff_id, staff_name, favorites
                    FROM staff
                    ORDER BY staff_id
                ''')
                manga_staff_list = {row[0]: (row[1], row[2]) for row in manga_cursor.fetchall()}
        except:
            print("   マンガスタッフテーブルが見つかりません。アニメのみで処理します。")
    
    # 全スタッフリストを作成
    all_staff_ids = set(anime_staff_list.keys()) | set(manga_staff_list.keys())
    enhanced_data = []
    processed = 0
    
    for staff_id in sorted(all_staff_ids):
        processed += 1
        if processed % 1000 == 0:
            print(f"   進行状況: {processed}/{len(all_staff_ids)} ({processed/len(all_staff_ids)*100:.1f}%)")
        
        # スタッフ情報を取得（アニメを優先、なければマンガ）
        if staff_id in anime_staff_list:
            staff_name, favorites = anime_staff_list[staff_id]
        elif staff_id in manga_staff_list:
            staff_name, favorites = manga_staff_list[staff_id]
        else:
            continue
        
        # アニメ基本統計の計算
        anime_cursor.execute('''
            SELECT 
                COUNT(DISTINCT s.anilist_id) as total_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.seasonYear IS NOT NULL
        ''', (staff_id,))
        
        anime_basic_result = anime_cursor.fetchone()
        anime_count = anime_basic_result[0] if anime_basic_result else 0
        anime_first_year = anime_basic_result[1] if anime_basic_result else None
        anime_year_count = anime_basic_result[2] if anime_basic_result else 0
        
        # マンガ基本統計の計算
        manga_count = 0
        manga_first_year = None
        manga_year_count = 0
        
        if manga_cursor and staff_id in manga_staff_list:
            try:
                manga_cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT s.anilist_id) as total_count,
                        MIN(m.seasonYear) as first_year,
                        COUNT(DISTINCT m.seasonYear) as year_count
                    FROM staff s
                    JOIN manga m ON s.anilist_id = m.anilist_id
                    WHERE s.staff_id = ? AND m.seasonYear IS NOT NULL
                ''', (staff_id,))
                
                manga_basic_result = manga_cursor.fetchone()
                if manga_basic_result:
                    manga_count = manga_basic_result[0] if manga_basic_result[0] else 0
                    manga_first_year = manga_basic_result[1] if manga_basic_result[1] else None
                    manga_year_count = manga_basic_result[2] if manga_basic_result[2] else 0
            except:
                pass  # マンガテーブルが存在しない場合はスキップ
        
        # 統合統計の計算
        total_count = anime_count + manga_count
        if total_count == 0:
            continue
        
        # 最初の年と年数を統合
        years = [y for y in [anime_first_year, manga_first_year] if y is not None]
        first_year = min(years) if years else None
        year_count = anime_year_count + manga_year_count
        # 重複を除く場合の年数計算（簡易版）
        if anime_year_count > 0 and manga_year_count > 0:
            year_count = max(anime_year_count, manga_year_count)
        
        count_per_year = total_count / year_count if year_count > 0 else 0
        
        # anime_favorites統計
        anime_cursor.execute('''
            SELECT a.favorites
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.favorites IS NOT NULL
        ''', (staff_id,))
        
        anime_favorites_values = [row[0] for row in anime_cursor.fetchall()]
        anime_fav_total, anime_fav_max, anime_fav_min, anime_fav_avg, anime_fav_median, anime_fav_q1, anime_fav_q3 = calculate_percentiles(anime_favorites_values)
        
        # anime_meanScore統計
        anime_cursor.execute('''
            SELECT a.meanScore
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.meanScore IS NOT NULL
        ''', (staff_id,))
        
        anime_score_values = [row[0] for row in anime_cursor.fetchall()]
        anime_score_total, anime_score_max, anime_score_min, anime_score_avg, anime_score_median, anime_score_q1, anime_score_q3 = calculate_percentiles(anime_score_values)
        
        # manga_favorites統計
        manga_fav_total = manga_fav_max = manga_fav_min = manga_fav_avg = manga_fav_median = manga_fav_q1 = manga_fav_q3 = None
        if manga_cursor and staff_id in manga_staff_list:
            try:
                manga_cursor.execute('''
                    SELECT m.favorites
                    FROM staff s
                    JOIN manga m ON s.anilist_id = m.anilist_id
                    WHERE s.staff_id = ? AND m.favorites IS NOT NULL
                ''', (staff_id,))
                
                manga_favorites_values = [row[0] for row in manga_cursor.fetchall()]
                manga_fav_total, manga_fav_max, manga_fav_min, manga_fav_avg, manga_fav_median, manga_fav_q1, manga_fav_q3 = calculate_percentiles(manga_favorites_values)
            except:
                pass
        
        # manga_meanScore統計
        manga_score_total = manga_score_max = manga_score_min = manga_score_avg = manga_score_median = manga_score_q1 = manga_score_q3 = None
        if manga_cursor and staff_id in manga_staff_list:
            try:
                manga_cursor.execute('''
                    SELECT m.meanScore
                    FROM staff s
                    JOIN manga m ON s.anilist_id = m.anilist_id
                    WHERE s.staff_id = ? AND m.meanScore IS NOT NULL
                ''', (staff_id,))
                
                manga_score_values = [row[0] for row in manga_cursor.fetchall()]
                manga_score_total, manga_score_max, manga_score_min, manga_score_avg, manga_score_median, manga_score_q1, manga_score_q3 = calculate_percentiles(manga_score_values)
            except:
                pass
        
        enhanced_data.append({
            'staff_id': staff_id,
            'staff_name': staff_name,
            'favorites': favorites,
            'total_count': total_count,
            'first_year': first_year,
            'year_count': year_count,
            'count_per_year': count_per_year,
            'anime_favorites_total': anime_fav_total,
            'anime_favorites_max': anime_fav_max,
            'anime_favorites_min': anime_fav_min,
            'anime_favorites_avg': anime_fav_avg,
            'anime_favorites_median': anime_fav_median,
            'anime_favorites_q1': anime_fav_q1,
            'anime_favorites_q3': anime_fav_q3,
            'anime_meanscore_total': anime_score_total,
            'anime_meanscore_max': anime_score_max,
            'anime_meanscore_min': anime_score_min,
            'anime_meanscore_avg': anime_score_avg,
            'anime_meanscore_median': anime_score_median,
            'anime_meanscore_q1': anime_score_q1,
            'anime_meanscore_q3': anime_score_q3,
            'manga_favorites_total': manga_fav_total,
            'manga_favorites_max': manga_fav_max,
            'manga_favorites_min': manga_fav_min,
            'manga_favorites_avg': manga_fav_avg,
            'manga_favorites_median': manga_fav_median,
            'manga_favorites_q1': manga_fav_q1,
            'manga_favorites_q3': manga_fav_q3,
            'manga_meanscore_total': manga_score_total,
            'manga_meanscore_max': manga_score_max,
            'manga_meanscore_min': manga_score_min,
            'manga_meanscore_avg': manga_score_avg,
            'manga_meanscore_median': manga_score_median,
            'manga_meanscore_q1': manga_score_q1,
            'manga_meanscore_q3': manga_score_q3
        })
    
    print(f"   処理完了: {len(enhanced_data)}人のスタッフ")
    return enhanced_data


def insert_enhanced_staff_basic_data(cursor, enhanced_data):
    """拡張されたスタッフ基本データを挿入"""
    cursor.executemany('''
        INSERT INTO staff_basic_enhanced (
            staff_id, staff_name, favorites, total_count, first_year, year_count, count_per_year,
            anime_favorites_total, anime_favorites_max, anime_favorites_min, anime_favorites_avg, anime_favorites_median, anime_favorites_q1, anime_favorites_q3,
            anime_meanscore_total, anime_meanscore_max, anime_meanscore_min, anime_meanscore_avg, anime_meanscore_median, anime_meanscore_q1, anime_meanscore_q3,
            manga_favorites_total, manga_favorites_max, manga_favorites_min, manga_favorites_avg, manga_favorites_median, manga_favorites_q1, manga_favorites_q3,
            manga_meanscore_total, manga_meanscore_max, manga_meanscore_min, manga_meanscore_avg, manga_meanscore_median, manga_meanscore_q1, manga_meanscore_q3
        ) VALUES (
            :staff_id, :staff_name, :favorites, :total_count, :first_year, :year_count, :count_per_year,
            :anime_favorites_total, :anime_favorites_max, :anime_favorites_min, :anime_favorites_avg, :anime_favorites_median, :anime_favorites_q1, :anime_favorites_q3,
            :anime_meanscore_total, :anime_meanscore_max, :anime_meanscore_min, :anime_meanscore_avg, :anime_meanscore_median, :anime_meanscore_q1, :anime_meanscore_q3,
            :manga_favorites_total, :manga_favorites_max, :manga_favorites_min, :manga_favorites_avg, :manga_favorites_median, :manga_favorites_q1, :manga_favorites_q3,
            :manga_meanscore_total, :manga_meanscore_max, :manga_meanscore_min, :manga_meanscore_avg, :manga_meanscore_median, :manga_meanscore_q1, :manga_meanscore_q3
        )
    ''', enhanced_data)


def analyze_staff_role_table(anime_cursor, manga_cursor):
    """スタッフロールテーブルの分析（アニメ+マンガ）"""
    print("スタッフロールテーブル分析中（アニメ+マンガ）...")
    
    # アニメのスタッフロール分析
    print("\n【アニメスタッフロール】")
    anime_cursor.execute("SELECT COUNT(*) FROM staff_role")
    anime_total_records = anime_cursor.fetchone()[0]
    
    anime_cursor.execute("SELECT COUNT(DISTINCT staff_id) FROM staff_role")
    anime_unique_staff = anime_cursor.fetchone()[0]
    
    anime_cursor.execute("SELECT COUNT(DISTINCT role) FROM staff_role")
    anime_unique_roles = anime_cursor.fetchone()[0]
    
    print(f"  総レコード数: {anime_total_records}件")
    print(f"  ユニークなスタッフ数: {anime_unique_staff}人")
    print(f"  ユニークなロール数: {anime_unique_roles}種類")
    
    anime_cursor.execute('''
        SELECT role, COUNT(*) as count, COUNT(DISTINCT staff_id) as unique_staff
        FROM staff_role
        GROUP BY role
        ORDER BY count DESC
    ''')
    
    print(f"  ロール別統計:")
    for row in anime_cursor.fetchall():
        role, count, unique_staff = row
        print(f"    {role}: {count}件 ({unique_staff}人)")
    
    # マンガのスタッフロール分析
    manga_total_records = 0
    manga_unique_staff = 0
    manga_unique_roles = 0
    
    if manga_cursor:
        try:
            manga_cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='staff_role'
            ''')
            if manga_cursor.fetchone():
                print("\n【マンガスタッフロール】")
                
                manga_cursor.execute("SELECT COUNT(*) FROM staff_role")
                manga_total_records = manga_cursor.fetchone()[0]
                
                manga_cursor.execute("SELECT COUNT(DISTINCT staff_id) FROM staff_role")
                manga_unique_staff = manga_cursor.fetchone()[0]
                
                manga_cursor.execute("SELECT COUNT(DISTINCT role) FROM staff_role")
                manga_unique_roles = manga_cursor.fetchone()[0]
                
                print(f"  総レコード数: {manga_total_records}件")
                print(f"  ユニークなスタッフ数: {manga_unique_staff}人")
                print(f"  ユニークなロール数: {manga_unique_roles}種類")
                
                manga_cursor.execute('''
                    SELECT role, COUNT(*) as count, COUNT(DISTINCT staff_id) as unique_staff
                    FROM staff_role
                    GROUP BY role
                    ORDER BY count DESC
                ''')
                
                print(f"  ロール別統計:")
                for row in manga_cursor.fetchall():
                    role, count, unique_staff = row
                    print(f"    {role}: {count}件 ({unique_staff}人)")
            else:
                print("\n【マンガスタッフロール】 テーブルが存在しません")
        except:
            print("\n【マンガスタッフロール】 データベースに接続できません")
    
    return (anime_total_records + manga_total_records, 
            anime_unique_staff + manga_unique_staff, 
            max(anime_unique_roles, manga_unique_roles))


def main():
    anime_db_file = Path(__file__).parent / 'anime_data.db'
    manga_db_file = Path(__file__).parent / 'manga_data.db'
    
    print("="*70)
    print("拡張スタッフ基本統計テーブル作成・スタッフロール分析ツール（アニメ+マンガ）")
    print("="*70)
    
    if not anime_db_file.exists():
        print(f"エラー: アニメデータベースが見つかりません: {anime_db_file}")
        return
    
    print(f"\nアニメデータベースに接続中: {anime_db_file}")
    anime_conn = sqlite3.connect(anime_db_file)
    anime_cursor = anime_conn.cursor()
    
    # マンガデータベースへの接続
    manga_cursor = None
    if manga_db_file.exists():
        print(f"マンガデータベースに接続中: {manga_db_file}")
        manga_conn = sqlite3.connect(manga_db_file)
        manga_cursor = manga_conn.cursor()
    else:
        print(f"警告: マンガデータベースが見つかりません: {manga_db_file}")
        print("アニメデータのみで処理を続行します")
    
    # 拡張スタッフ基本テーブル作成
    print("\n=== 拡張スタッフ基本テーブル作成 ===")
    print("staff_basic_enhancedテーブル作成中...")
    create_enhanced_staff_basic_table(anime_cursor)
    
    # データ抽出・計算
    enhanced_data = extract_enhanced_staff_basic_data(anime_cursor, manga_cursor)
    
    # データ挿入
    print("\n=== データ挿入 ===")
    print("拡張スタッフ基本データを挿入中...")
    insert_enhanced_staff_basic_data(anime_cursor, enhanced_data)
    print(f"   挿入完了: {len(enhanced_data)}件")
    
    anime_conn.commit()
    
    # スタッフロールテーブル分析
    print("\n=== スタッフロールテーブル分析 ===")
    analyze_staff_role_table(anime_cursor, manga_cursor)
    
    # 確認用データ表示
    print("\n" + "="*70)
    print("【確認: 拡張スタッフ基本統計テーブル】")
    print("="*70)
    
    print("\n【staff_basic_enhancedテーブル】上位5件（作品数順）:")
    anime_cursor.execute('''
        SELECT staff_id, staff_name, total_count, first_year, year_count, count_per_year,
               anime_meanscore_avg, manga_meanscore_avg
        FROM staff_basic_enhanced 
        ORDER BY total_count DESC 
        LIMIT 5
    ''')
    
    print("staff_id | staff_name | 作品数 | 初出年 | 活動年 | 年平均 | anime_score | manga_score")
    print("-" * 85)
    for row in anime_cursor.fetchall():
        staff_id, name, count, first_year, year_count, count_per_year, anime_score_avg, manga_score_avg = row
        anime_score_avg = anime_score_avg or 0
        manga_score_avg = manga_score_avg or 0
        print(f"{staff_id:8d} | {name[:12]:12} | {count:6d} | {first_year:6d} | {year_count:6d} | {count_per_year:6.2f} | {anime_score_avg:11.1f} | {manga_score_avg:11.1f}")
    
    # 統計情報
    print("\n" + "="*70)
    print("【統計情報】")
    print("="*70)
    
    anime_cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced")
    print(f"拡張スタッフ基本テーブル総数: {anime_cursor.fetchone()[0]}人")
    
    anime_cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE anime_favorites_avg IS NOT NULL")
    anime_favorites_count = anime_cursor.fetchone()[0]
    print(f"anime_favorites統計有り: {anime_favorites_count}人")
    
    anime_cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE anime_meanscore_avg IS NOT NULL")
    anime_score_count = anime_cursor.fetchone()[0]
    print(f"anime_meanScore統計有り: {anime_score_count}人")
    
    anime_cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE manga_favorites_avg IS NOT NULL")
    manga_favorites_count = anime_cursor.fetchone()[0]
    print(f"manga_favorites統計有り: {manga_favorites_count}人")
    
    anime_cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE manga_meanscore_avg IS NOT NULL")
    manga_score_count = anime_cursor.fetchone()[0]
    print(f"manga_meanScore統計有り: {manga_score_count}人")
    
    # トップスタッフの詳細表示
    print("\n" + "="*70)
    print("【トップスタッフの詳細統計】")
    print("="*70)
    
    anime_cursor.execute('''
        SELECT staff_id, staff_name, total_count, first_year, year_count, count_per_year,
               anime_meanscore_avg, manga_meanscore_avg
        FROM staff_basic_enhanced
        ORDER BY total_count DESC
        LIMIT 3
    ''')
    
    for row in anime_cursor.fetchall():
        staff_id, name, count, first_year, year_count, count_per_year, anime_score_avg, manga_score_avg = row
        
        print(f"\n【{name} (ID: {staff_id})】")
        print(f"  総作品数: {count}作品 ({first_year}年〜, {year_count}年活動)")
        print(f"  年平均: {count_per_year:.2f}作品/年")
        
        if anime_score_avg is not None:
            print(f"  anime_meanScore平均: {anime_score_avg:.1f}")
        
        if manga_score_avg is not None:
            print(f"  manga_meanScore平均: {manga_score_avg:.1f}")
    
    anime_conn.close()
    if manga_cursor:
        manga_conn.close()
    
    print("\n" + "="*70)
    print("完了しました！")
    print("="*70)


if __name__ == "__main__":
    main()