import sqlite3
from pathlib import Path
import numpy as np


def create_voiceactor_basic_table(cursor):
    """声優基本統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voiceactor_basic (
            voiceactor_id INTEGER PRIMARY KEY,
            voiceactor_name TEXT,
            favorites INTEGER,
            voiceactor_count INTEGER,
            first_year INTEGER,
            year_count INTEGER,
            count_per_year REAL
        )
    ''')


def create_voiceactor_stats_table(cursor):
    """声優統計テーブルを作成"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voiceactor_stats (
            voiceactor_id INTEGER,
            stat_type TEXT,
            total REAL,
            max_value REAL,
            min_value REAL,
            avg_value REAL,
            median_value REAL,
            q1_value REAL,
            q3_value REAL,
            PRIMARY KEY (voiceactor_id, stat_type),
            FOREIGN KEY (voiceactor_id) REFERENCES voiceactor_basic(voiceactor_id)
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


def extract_voiceactor_basic_data(cursor):
    """声優基本データを抽出"""
    print("声優基本データを計算中...")
    
    # 声優ごとの基本情報を集計
    cursor.execute('''
        SELECT 
            v.voiceactor_id,
            v.voiceactor_name,
            v.favorites,
            COUNT(DISTINCT v.anilist_id) as voiceactor_count,
            MIN(a.seasonYear) as first_year,
            COUNT(DISTINCT a.seasonYear) as year_count
        FROM voiceactors v
        JOIN anime a ON v.anilist_id = a.anilist_id
        WHERE a.seasonYear IS NOT NULL
        GROUP BY v.voiceactor_id, v.voiceactor_name, v.favorites
        HAVING voiceactor_count > 0
        ORDER BY voiceactor_count DESC
    ''')
    
    basic_data = []
    for row in cursor.fetchall():
        voiceactor_id, voiceactor_name, favorites, count, first_year, year_count = row
        
        # count_per_year を計算
        count_per_year = count / year_count if year_count > 0 else 0
        
        basic_data.append({
            'voiceactor_id': voiceactor_id,
            'voiceactor_name': voiceactor_name,
            'favorites': favorites,
            'voiceactor_count': count,
            'first_year': first_year,
            'year_count': year_count,
            'count_per_year': count_per_year
        })
    
    print(f"   処理完了: {len(basic_data)}人の声優")
    return basic_data


def extract_voiceactor_stats_data(cursor):
    """声優統計データを抽出"""
    print("声優統計データを計算中...")
    
    stats_data = []
    
    # 声優IDの一覧を取得
    cursor.execute('''
        SELECT DISTINCT voiceactor_id 
        FROM voiceactors 
        ORDER BY voiceactor_id
    ''')
    
    voiceactor_ids = [row[0] for row in cursor.fetchall()]
    processed = 0
    
    for va_id in voiceactor_ids:
        processed += 1
        if processed % 1000 == 0:
            print(f"   進行状況: {processed}/{len(voiceactor_ids)} ({processed/len(voiceactor_ids)*100:.1f}%)")
        
        # anime_favorites統計
        cursor.execute('''
            SELECT a.favorites
            FROM voiceactors v
            JOIN anime a ON v.anilist_id = a.anilist_id
            WHERE v.voiceactor_id = ? AND a.favorites IS NOT NULL
        ''', (va_id,))
        
        favorites_values = [row[0] for row in cursor.fetchall()]
        if favorites_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(favorites_values)
            stats_data.append({
                'voiceactor_id': va_id,
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
            FROM voiceactors v
            JOIN anime a ON v.anilist_id = a.anilist_id
            WHERE v.voiceactor_id = ? AND a.meanScore IS NOT NULL
        ''', (va_id,))
        
        score_values = [row[0] for row in cursor.fetchall()]
        if score_values:
            total, max_val, min_val, avg_val, median_val, q1_val, q3_val = calculate_percentiles(score_values)
            stats_data.append({
                'voiceactor_id': va_id,
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


def insert_voiceactor_basic_data(cursor, basic_data):
    """声優基本データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO voiceactor_basic (
            voiceactor_id, voiceactor_name, favorites, voiceactor_count,
            first_year, year_count, count_per_year
        ) VALUES (
            :voiceactor_id, :voiceactor_name, :favorites, :voiceactor_count,
            :first_year, :year_count, :count_per_year
        )
    ''', basic_data)


def insert_voiceactor_stats_data(cursor, stats_data):
    """声優統計データを挿入"""
    cursor.executemany('''
        INSERT OR REPLACE INTO voiceactor_stats (
            voiceactor_id, stat_type, total, max_value, min_value,
            avg_value, median_value, q1_value, q3_value
        ) VALUES (
            :voiceactor_id, :stat_type, :total, :max_value, :min_value,
            :avg_value, :median_value, :q1_value, :q3_value
        )
    ''', stats_data)


def main():
    db_file = Path(__file__).parent / 'anime_data.db'
    
    print("="*70)
    print("声優基本統計・詳細統計テーブル作成ツール")
    print("="*70)
    
    if not db_file.exists():
        print(f"エラー: データベースが見つかりません: {db_file}")
        return
    
    print(f"\nデータベースに接続中: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # テーブル作成
    print("\n=== テーブル作成 ===")
    print("1. voiceactor_basicテーブル作成中...")
    create_voiceactor_basic_table(cursor)
    
    print("2. voiceactor_statsテーブル作成中...")
    create_voiceactor_stats_table(cursor)
    print("   テーブル作成完了")
    
    # データ抽出・計算
    print("\n=== データ抽出・計算 ===")
    basic_data = extract_voiceactor_basic_data(cursor)
    stats_data = extract_voiceactor_stats_data(cursor)
    
    # データ挿入
    print("\n=== データ挿入 ===")
    print("1. 声優基本データを挿入中...")
    insert_voiceactor_basic_data(cursor, basic_data)
    print(f"   挿入完了: {len(basic_data)}件")
    
    print("2. 声優統計データを挿入中...")
    insert_voiceactor_stats_data(cursor, stats_data)
    print(f"   挿入完了: {len(stats_data)}件")
    
    conn.commit()
    
    # 確認用データ表示
    print("\n" + "="*70)
    print("【確認: 声優基本統計テーブル】")
    print("="*70)
    
    print("\n【voiceactor_basicテーブル】上位5件（作品数順）:")
    cursor.execute('''
        SELECT * FROM voiceactor_basic 
        ORDER BY voiceactor_count DESC 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    print("\n【voiceactor_statsテーブル】サンプル（最初の5件）:")
    cursor.execute('''
        SELECT * FROM voiceactor_stats 
        ORDER BY voiceactor_id, stat_type 
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # 統計情報
    print("\n" + "="*70)
    print("【統計情報】")
    print("="*70)
    
    cursor.execute("SELECT COUNT(*) FROM voiceactor_basic")
    print(f"声優総数: {cursor.fetchone()[0]}人")
    
    cursor.execute("SELECT COUNT(*) FROM voiceactor_stats")
    print(f"統計レコード総数: {cursor.fetchone()[0]}件")
    
    cursor.execute("SELECT COUNT(*) FROM voiceactor_stats WHERE stat_type = 'anime_favorites'")
    print(f"anime_favorites統計: {cursor.fetchone()[0]}件")
    
    cursor.execute("SELECT COUNT(*) FROM voiceactor_stats WHERE stat_type = 'anime_meanScore'")
    print(f"anime_meanScore統計: {cursor.fetchone()[0]}件")
    
    # トップ声優の詳細表示
    print("\n" + "="*70)
    print("【トップ声優の詳細】")
    print("="*70)
    
    cursor.execute('''
        SELECT vb.voiceactor_id, vb.voiceactor_name, vb.voiceactor_count,
               vb.first_year, vb.year_count, vb.count_per_year
        FROM voiceactor_basic vb
        ORDER BY vb.voiceactor_count DESC
        LIMIT 3
    ''')
    
    for basic_row in cursor.fetchall():
        va_id, va_name, count, first_year, year_count, count_per_year = basic_row
        print(f"\n【{va_name} (ID: {va_id})】")
        print(f"  作品数: {count}作品")
        print(f"  初出年: {first_year}年")
        print(f"  活動年数: {year_count}年")
        print(f"  年平均: {count_per_year:.2f}作品/年")
        
        # この声優の統計情報
        cursor.execute('''
            SELECT stat_type, avg_value, median_value, max_value, min_value
            FROM voiceactor_stats
            WHERE voiceactor_id = ?
        ''', (va_id,))
        
        for stat_row in cursor.fetchall():
            stat_type, avg_val, median_val, max_val, min_val = stat_row
            print(f"  {stat_type}:")
            print(f"    平均: {avg_val:.2f}, 中央値: {median_val:.2f}")
            print(f"    最高: {max_val:.2f}, 最低: {min_val:.2f}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("完了しました！")
    print("="*70)


if __name__ == "__main__":
    main()