import sqlite3
from pathlib import Path
import numpy as np


def create_enhanced_staff_basic_table(cursor):
    """拡張されたスタッフ基本統計テーブルを作成"""
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
            favorites_total REAL,
            favorites_max REAL,
            favorites_min REAL,
            favorites_avg REAL,
            favorites_median REAL,
            favorites_q1 REAL,
            favorites_q3 REAL,
            -- anime_meanScore統計
            meanscore_total REAL,
            meanscore_max REAL,
            meanscore_min REAL,
            meanscore_avg REAL,
            meanscore_median REAL,
            meanscore_q1 REAL,
            meanscore_q3 REAL
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


def extract_enhanced_staff_basic_data(cursor):
    """拡張されたスタッフ基本データを抽出"""
    print("拡張スタッフ基本データを計算中...")
    
    # スタッフの基本情報を取得
    cursor.execute('''
        SELECT DISTINCT staff_id, staff_name, favorites
        FROM staff
        ORDER BY staff_id
    ''')
    
    staff_list = cursor.fetchall()
    enhanced_data = []
    processed = 0
    
    for staff_id, staff_name, favorites in staff_list:
        processed += 1
        if processed % 1000 == 0:
            print(f"   進行状況: {processed}/{len(staff_list)} ({processed/len(staff_list)*100:.1f}%)")
        
        # 基本統計の計算
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT s.anilist_id) as total_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.seasonYear IS NOT NULL
        ''', (staff_id,))
        
        basic_result = cursor.fetchone()
        if not basic_result or basic_result[0] == 0:
            continue
            
        total_count, first_year, year_count = basic_result
        count_per_year = total_count / year_count if year_count > 0 else 0
        
        # anime_favorites統計
        cursor.execute('''
            SELECT a.favorites
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.favorites IS NOT NULL
        ''', (staff_id,))
        
        favorites_values = [row[0] for row in cursor.fetchall()]
        fav_total, fav_max, fav_min, fav_avg, fav_median, fav_q1, fav_q3 = calculate_percentiles(favorites_values)
        
        # anime_meanScore統計
        cursor.execute('''
            SELECT a.meanScore
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id = ? AND a.meanScore IS NOT NULL
        ''', (staff_id,))
        
        score_values = [row[0] for row in cursor.fetchall()]
        score_total, score_max, score_min, score_avg, score_median, score_q1, score_q3 = calculate_percentiles(score_values)
        
        enhanced_data.append({
            'staff_id': staff_id,
            'staff_name': staff_name,
            'favorites': favorites,
            'total_count': total_count,
            'first_year': first_year,
            'year_count': year_count,
            'count_per_year': count_per_year,
            'favorites_total': fav_total,
            'favorites_max': fav_max,
            'favorites_min': fav_min,
            'favorites_avg': fav_avg,
            'favorites_median': fav_median,
            'favorites_q1': fav_q1,
            'favorites_q3': fav_q3,
            'meanscore_total': score_total,
            'meanscore_max': score_max,
            'meanscore_min': score_min,
            'meanscore_avg': score_avg,
            'meanscore_median': score_median,
            'meanscore_q1': score_q1,
            'meanscore_q3': score_q3
        })
    
    print(f"   処理完了: {len(enhanced_data)}人のスタッフ")
    return enhanced_data


def insert_enhanced_staff_basic_data(cursor, enhanced_data):
    """拡張されたスタッフ基本データを挿入"""
    cursor.executemany('''
        INSERT INTO staff_basic_enhanced (
            staff_id, staff_name, favorites, total_count, first_year, year_count, count_per_year,
            favorites_total, favorites_max, favorites_min, favorites_avg, favorites_median, favorites_q1, favorites_q3,
            meanscore_total, meanscore_max, meanscore_min, meanscore_avg, meanscore_median, meanscore_q1, meanscore_q3
        ) VALUES (
            :staff_id, :staff_name, :favorites, :total_count, :first_year, :year_count, :count_per_year,
            :favorites_total, :favorites_max, :favorites_min, :favorites_avg, :favorites_median, :favorites_q1, :favorites_q3,
            :meanscore_total, :meanscore_max, :meanscore_min, :meanscore_avg, :meanscore_median, :meanscore_q1, :meanscore_q3
        )
    ''', enhanced_data)


def analyze_staff_role_table(cursor):
    """スタッフロールテーブルの分析"""
    print("スタッフロールテーブル分析中...")
    
    # テーブル構造の確認
    cursor.execute("PRAGMA table_info(staff_role)")
    columns = cursor.fetchall()
    print("テーブル構造:")
    for col in columns:
        print(f"  {col}")
    
    # データの統計
    cursor.execute("SELECT COUNT(*) FROM staff_role")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT staff_id) FROM staff_role")
    unique_staff = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT role) FROM staff_role")
    unique_roles = cursor.fetchone()[0]
    
    print(f"\n統計:")
    print(f"  総レコード数: {total_records}件")
    print(f"  ユニークなスタッフ数: {unique_staff}人")
    print(f"  ユニークなロール数: {unique_roles}種類")
    
    # ロール別の統計
    cursor.execute('''
        SELECT role, COUNT(*) as count, COUNT(DISTINCT staff_id) as unique_staff
        FROM staff_role
        GROUP BY role
        ORDER BY count DESC
    ''')
    
    print(f"\nロール別統計:")
    for row in cursor.fetchall():
        role, count, unique_staff = row
        print(f"  {role}: {count}件 ({unique_staff}人)")
    
    # サンプルデータ表示
    cursor.execute("SELECT * FROM staff_role LIMIT 10")
    print(f"\nサンプルデータ（最初の10件）:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    return total_records, unique_staff, unique_roles


def main():
    db_file = Path(__file__).parent / 'anime_data.db'
    
    print("="*70)
    print("拡張スタッフ基本統計テーブル作成・スタッフロール分析ツール")
    print("="*70)
    
    if not db_file.exists():
        print(f"エラー: データベースが見つかりません: {db_file}")
        return
    
    print(f"\nデータベースに接続中: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 拡張スタッフ基本テーブル作成
    print("\n=== 拡張スタッフ基本テーブル作成 ===")
    print("staff_basic_enhancedテーブル作成中...")
    create_enhanced_staff_basic_table(cursor)
    
    # データ抽出・計算
    enhanced_data = extract_enhanced_staff_basic_data(cursor)
    
    # データ挿入
    print("\n=== データ挿入 ===")
    print("拡張スタッフ基本データを挿入中...")
    insert_enhanced_staff_basic_data(cursor, enhanced_data)
    print(f"   挿入完了: {len(enhanced_data)}件")
    
    conn.commit()
    
    # スタッフロールテーブル分析
    print("\n=== スタッフロールテーブル分析 ===")
    analyze_staff_role_table(cursor)
    
    # 確認用データ表示
    print("\n" + "="*70)
    print("【確認: 拡張スタッフ基本統計テーブル】")
    print("="*70)
    
    print("\n【staff_basic_enhancedテーブル】上位5件（作品数順）:")
    cursor.execute('''
        SELECT staff_id, staff_name, total_count, first_year, year_count, count_per_year,
               favorites_avg, meanscore_avg
        FROM staff_basic_enhanced 
        ORDER BY total_count DESC 
        LIMIT 5
    ''')
    
    print("staff_id | staff_name | 作品数 | 初出年 | 活動年 | 年平均 | fav平均 | score平均")
    print("-" * 80)
    for row in cursor.fetchall():
        staff_id, name, count, first_year, year_count, count_per_year, fav_avg, score_avg = row
        fav_avg = fav_avg or 0
        score_avg = score_avg or 0
        print(f"{staff_id:8d} | {name[:12]:12} | {count:6d} | {first_year:6d} | {year_count:6d} | {count_per_year:6.2f} | {fav_avg:7.1f} | {score_avg:8.1f}")
    
    # 統計情報
    print("\n" + "="*70)
    print("【統計情報】")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced")
    print(f"拡張スタッフ基本テーブル総数: {cursor.fetchone()[0]}人")
    
    cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE favorites_avg IS NOT NULL")
    favorites_count = cursor.fetchone()[0]
    print(f"anime_favorites統計有り: {favorites_count}人")
    
    cursor.execute("SELECT COUNT(*) FROM staff_basic_enhanced WHERE meanscore_avg IS NOT NULL")
    score_count = cursor.fetchone()[0]
    print(f"anime_meanScore統計有り: {score_count}人")
    
    # トップスタッフの詳細表示
    print("\n" + "="*70)
    print("【トップスタッフの詳細統計】")
    print("="*70)
    
    cursor.execute('''
        SELECT staff_id, staff_name, total_count, first_year, year_count, count_per_year,
               favorites_total, favorites_avg, favorites_median, favorites_max, favorites_min,
               meanscore_total, meanscore_avg, meanscore_median, meanscore_max, meanscore_min
        FROM staff_basic_enhanced
        ORDER BY total_count DESC
        LIMIT 3
    ''')
    
    for row in cursor.fetchall():
        (staff_id, name, count, first_year, year_count, count_per_year,
         fav_total, fav_avg, fav_median, fav_max, fav_min,
         score_total, score_avg, score_median, score_max, score_min) = row
        
        print(f"\n【{name} (ID: {staff_id})】")
        print(f"  作品数: {count}作品 ({first_year}年〜, {year_count}年活動)")
        print(f"  年平均: {count_per_year:.2f}作品/年")
        
        if fav_avg is not None:
            print(f"  anime_favorites:")
            print(f"    合計: {fav_total:.0f}, 平均: {fav_avg:.1f}, 中央値: {fav_median:.1f}")
            print(f"    最高: {fav_max:.0f}, 最低: {fav_min:.0f}")
        
        if score_avg is not None:
            print(f"  anime_meanScore:")
            print(f"    合計: {score_total:.1f}, 平均: {score_avg:.1f}, 中央値: {score_median:.1f}")
            print(f"    最高: {score_max:.1f}, 最低: {score_min:.1f}")
        
        # このスタッフのロール
        cursor.execute("SELECT role FROM staff_role WHERE staff_id = ?", (staff_id,))
        roles = [row[0] for row in cursor.fetchall()]
        print(f"  担当ロール: {', '.join(roles)}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("完了しました！")
    print("="*70)


if __name__ == "__main__":
    main()