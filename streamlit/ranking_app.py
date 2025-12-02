import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="AniList ランキング分析",
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 共通ユーティリティ関数 ====================

def get_db_path(db_name):
    """データベースパスを取得（絶対パス→相対パスの順で試行）"""
    # 絶対パス
    db_path = Path(rf'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\{db_name}')
    
    # 相対パス（バックアップ）
    if not db_path.exists():
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        db_path = project_root / 'db' / db_name
    
    return db_path

@st.cache_data
def load_data_from_db(db_name, query, success_message):
    """データベースからデータを読み込む汎用関数
    
    Args:
        db_name: データベースファイル名（例: 'anime_data.db'）
        query: SQL クエリ文字列
        success_message: 成功時のメッセージ
    
    Returns:
        pd.DataFrame または None
    """
    try:
        db_path = get_db_path(db_name)
        
        if not db_path.exists():
            st.error(f"❌ {db_name} が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        data = pd.read_sql_query(query, conn)
        conn.close()
        
        st.success(f"✅ {success_message}: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

def apply_numeric_conversion(display_data, numeric_columns):
    """指定された列を数値型に変換
    
    Args:
        display_data: データフレーム
        numeric_columns: 数値変換する列名のリスト
    
    Returns:
        変換後のデータフレーム
    """
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = pd.to_numeric(display_data[col], errors='coerce')
    return display_data

def calculate_basic_statistics(data, metric_col):
    """基礎統計を計算する汎用関数
    
    Args:
        data: データフレーム
        metric_col: 統計を計算する列名
    
    Returns:
        統計情報の辞書 または None
    """
    if metric_col not in data.columns:
        return None
    
    metric_data = data[metric_col].dropna()
    
    if len(metric_data) == 0:
        return None
    
    stats = {
        "合計": float(metric_data.sum()),
        "カウント": len(metric_data),
        "最大": float(metric_data.max()),
        "最小": float(metric_data.min()),
        "平均": float(metric_data.mean()),
        "中央値": float(metric_data.median()),
        "1/4分位": float(metric_data.quantile(0.25)),
        "3/4分位": float(metric_data.quantile(0.75))
    }
    
    if len(metric_data) > 1:
        stats["標準偏差"] = float(metric_data.std())
        stats["分散"] = float(metric_data.var())
    
    return stats

def create_filter_ui(data, key_prefix, db_type='anime', show_metric=False, custom_columns=None):
    """フィルターUIを生成する汎用関数
    
    Args:
        data: データフレーム
        key_prefix: Streamlitウィジェットのキープレフィックス
        db_type: 'anime' or 'manga'
        show_metric: 指標選択を表示するか
        custom_columns: カスタム列設定のリスト（例: [('column_name', 'ラベル名')]）
    
    Returns:
        filters: フィルター辞書
        selected_metric: 選択された指標（show_metric=Trueの場合のみ）
    """
    st.subheader("🔧 フィルター設定")
    
    filters = {}
    selected_metric = None
    
    # 基本フィルター（3列）
    if show_metric:
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_options = ["meanScore", "favorites", "popularity"]
            metric_labels = {
                "meanScore": "平均スコア",
                "favorites": "お気に入り数", 
                "popularity": "人気度"
            }
            selected_metric = st.selectbox(
                "指標",
                metric_options,
                format_func=lambda x: metric_labels.get(x, x),
                key=f"{key_prefix}_metric"
            )
        start_col = col2
    else:
        col1, col2, col3 = st.columns(3)
        start_col = col1
    
    # 年度選択
    with start_col:
        if 'seasonYear' in data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(data, 'seasonYear')]
            selected_year = st.selectbox("年度", years, key=f"{key_prefix}_year")
            if selected_year != "全て":
                try:
                    filters['seasonYear'] = float(selected_year)
                except ValueError:
                    pass
    
    # 季節選択
    next_col = col3 if show_metric else col2
    with next_col:
        if 'season' in data.columns:
            seasons = ["全て"] + get_unique_values(data, 'season')
            selected_season = st.selectbox("季節", seasons, key=f"{key_prefix}_season")
            if selected_season != "全て":
                filters['season'] = selected_season
    
    # フォーマット選択
    third_col = col3 if not show_metric else None
    if third_col:
        with third_col:
            if 'format' in data.columns:
                formats = ["全て"] + get_unique_values(data, 'format')
                selected_format = st.selectbox("フォーマット", formats, key=f"{key_prefix}_format")
                if selected_format != "全て":
                    filters['format'] = selected_format
    
    # 追加フィルター
    additional_filters = []
    if not third_col and 'format' in data.columns:
        additional_filters.append(('format', 'フォーマット'))
    if 'source' in data.columns:
        additional_filters.append(('source', '原作'))
    
    # ジャンルフィルターを追加
    db_name = 'anime_data.db' if db_type == 'anime' else 'manga_data.db'
    db_path = get_db_path(db_name)
    if db_path.exists():
        additional_filters.append(('genre', 'ジャンル'))
    
    # カスタム列を追加
    if custom_columns:
        # custom_columnsがタプルのリストでない場合は変換
        for col in custom_columns:
            if isinstance(col, tuple):
                additional_filters.append(col)
            else:
                # カラム名から日本語ラベルを推測
                label_map = {
                    'seasonYear': '年度',
                    'season': '季節',
                    'format': 'フォーマット',
                    'source': '原作',
                    'genre': 'ジャンル',
                    'genre_name': 'ジャンル'
                }
                label = label_map.get(col, col)
                additional_filters.append((col, label))
    
    # 追加フィルターの表示
    if additional_filters:
        num_cols = min(3, len(additional_filters))
        cols = st.columns(num_cols)
        
        for idx, (col_name, label) in enumerate(additional_filters):
            with cols[idx % num_cols]:
                if col_name == 'genre':
                    # ジャンル選択（データベースから取得）
                    available_genres = get_genres_data(db_path)
                    genres_options = ["全て"] + available_genres
                    selected_genre = st.selectbox(label, genres_options, key=f"{key_prefix}_genre")
                    if selected_genre != "全て":
                        filters['genre'] = selected_genre
                elif col_name in data.columns:
                    options = ["全て"] + get_unique_values(data, col_name)
                    selected = st.selectbox(label, options, key=f"{key_prefix}_{col_name}")
                    if selected != "全て":
                        filters[col_name] = selected
    
    if show_metric:
        return filters, selected_metric
    return filters

def apply_filters_to_data(data, filters, db_type='anime'):
    """フィルターをデータに適用する汎用関数
    
    Args:
        data: データフレーム
        filters: フィルター辞書
        db_type: 'anime' or 'manga'
    
    Returns:
        フィルター適用後のデータフレーム
    """
    db_name = 'anime_data.db' if db_type == 'anime' else 'manga_data.db'
    db_path = get_db_path(db_name)
    return filter_data(data, filters, db_path if db_path.exists() else None)

def show_ranking_template(data, config):
    """ランキング表示の汎用テンプレート
    
    Args:
        data: データフレーム
        config: 設定辞書 {
            'title': ヘッダータイトル,
            'key_prefix': フィルターキープレフィックス,
            'db_type': 'anime' or 'manga',
            'dedup_config': {'id_col': ID列, 'sort_col': ソート列, 'sort_by': ソート基準列} or None,
            'sort_by': ソート列名,
            'display_columns': 表示列リスト,
            'column_mapping': 列名マッピング辞書,
            'chart_config': {'x': X軸列, 'y': Y軸列, 'title': タイトル, 'labels': ラベル辞書, 'hover_data': ホバーデータリスト}
        }
    """
    st.header(config['title'])
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    filters = create_filter_ui(data, config['key_prefix'], db_type=config['db_type'])
    filtered_data = apply_filters_to_data(data, filters, config['db_type'])
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 重複削除処理
    if config.get('dedup_config'):
        dedup = config['dedup_config']
        if 'role_aggregate' in dedup and dedup['role_aggregate']:
            # スタッフの役割集約
            filtered_data['roles'] = filtered_data.groupby([dedup['id_col'], dedup['sort_col']])['role'].transform(
                lambda x: ', '.join(sorted(set(x.dropna())))
            )
            filtered_data = filtered_data.drop_duplicates(subset=[dedup['id_col'], dedup['sort_col']], keep='first')
        
        filtered_data = filtered_data.sort_values(
            [dedup['id_col'], dedup['sort_by']], 
            ascending=[True, False]
        ).groupby(dedup['id_col']).first().reset_index()
    
    # フィルター適用後のデータ件数
    filtered_count = len(filtered_data)
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # ソート
    sorted_data = filtered_data.sort_values(config['sort_by'], ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    available_columns = [col for col in config['display_columns'] if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # 数値型変換
    numeric_columns = [col for col in available_columns if col not in ['title_native', 'chara_name', 'voiceactor_name', 'staff_name', 'studios_name', 'roles', 'season', 'source', 'format', 'genre_name']]
    display_data = apply_numeric_conversion(display_data, numeric_columns)
    
    # カラム名変更
    display_data = display_data.rename(columns=config['column_mapping'])
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # トップ10チャート
    if len(sorted_data) >= 1 and config.get('chart_config'):
        st.subheader("📊 トップ10チャート")
        top10_data = sorted_data.head(10)
        
        if not top10_data.empty:
            chart = config['chart_config']
            fig = px.bar(
                top10_data,
                x=chart['x'],
                y=chart['y'],
                title=chart['title'],
                labels=chart['labels'],
                hover_data=chart.get('hover_data', [])
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=500)
            st.plotly_chart(fig, width='stretch')

# ==================== データロード関数（既存） ====================

@st.cache_data
def load_anime_data():
    """アニメデータの読み込み"""
    query = """
        SELECT 
            a.anilist_id, a.title_romaji, a.title_native, a.format, 
            a.season, a.seasonYear, a.favorites, a.meanScore, 
            a.popularity, a.source
        FROM anime a
        WHERE a.title_romaji IS NOT NULL
        ORDER BY a.meanScore DESC NULLS LAST
    """
    return load_data_from_db('anime_data.db', query, 'アニメデータ読み込み成功')

@st.cache_data
def get_genres_data(db_path):
    """データベースからジャンルデータを取得"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT genre_name FROM genres ORDER BY genre_name")
        genres = [row[0] for row in cursor.fetchall()]
        conn.close()
        return genres
    except Exception as e:
        st.error(f"❌ ジャンルデータ取得エラー: {e}")
        return []

@st.cache_data
def load_character_data():
    """キャラクターデータの読み込み"""
    query = """
        SELECT 
            c.chara_id, c.chara_name, c.favorites as char_favorites,
            a.anilist_id, a.title_romaji, a.title_native, 
            a.season, a.seasonYear, a.favorites as anime_favorites, 
            a.popularity as anime_popularity,
            a.meanScore, a.format, a.source
        FROM characters c
        JOIN anime a ON c.anilist_id = a.anilist_id
        WHERE c.chara_name IS NOT NULL
        ORDER BY c.favorites DESC NULLS LAST
    """
    return load_data_from_db('anime_data.db', query, 'キャラクターデータ読み込み成功')

@st.cache_data
def load_voiceactor_data():
    """声優データの読み込み"""
    query = """
        SELECT 
            v.voiceactor_id, v.voiceactor_name, v.favorites as va_favorites,
            a.anilist_id, a.title_romaji, a.title_native, 
            a.season, a.seasonYear, a.favorites as anime_favorites, 
            a.meanScore, a.format, a.source,
            vb.voiceactor_count, vb.count_per_year
        FROM voiceactors v
        JOIN anime a ON v.anilist_id = a.anilist_id
        LEFT JOIN voiceactor_basic vb ON v.voiceactor_id = vb.voiceactor_id
        WHERE v.voiceactor_name IS NOT NULL
        ORDER BY v.favorites DESC NULLS LAST
    """
    return load_data_from_db('anime_data.db', query, '声優データ読み込み成功')

@st.cache_data
def load_staff_data():
    """スタッフデータの読み込み"""
    query = """
        SELECT 
            s.staff_id, s.staff_name, s.role, s.favorites as staff_favorites,
            a.anilist_id, a.title_romaji, a.title_native, 
            a.season, a.seasonYear, a.favorites as anime_favorites, 
            a.meanScore, a.format, a.source,
            sb.staff_count, sb.count_per_year
        FROM staff s
        JOIN anime a ON s.anilist_id = a.anilist_id
        LEFT JOIN staff_basic sb ON s.staff_id = sb.staff_id
        WHERE s.staff_name IS NOT NULL
        ORDER BY s.favorites DESC NULLS LAST
    """
    return load_data_from_db('anime_data.db', query, 'スタッフデータ読み込み成功')

@st.cache_data
def load_studios_data():
    """スタジオデータの読み込み（統計データ付き）"""
    try:
        db_path = get_db_path('anime_data.db')
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                s.studios_id, s.studios_name,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites as anime_favorites, 
                a.meanScore, a.format, a.source,
                sb.studios_count, sb.count_per_year
            FROM studios s
            JOIN anime a ON s.anilist_id = a.anilist_id
            LEFT JOIN studios_basic sb ON s.studios_id = sb.studios_id
            WHERE s.studios_name IS NOT NULL
            ORDER BY sb.studios_count DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        
        # studios_statsテーブルから統計データを取得
        stats_query = """
            SELECT 
                studios_id,
                stat_type,
                total,
                avg_value
            FROM studios_stats
        """
        stats_data = pd.read_sql_query(stats_query, conn)
        conn.close()
        
        # 統計データをピボットして各studios_idに対して横展開
        if not stats_data.empty:
            stats_pivot = stats_data.pivot_table(
                index='studios_id',
                columns='stat_type',
                values=['total', 'avg_value'],
                aggfunc='first'
            )
            
            # カラム名をフラット化
            stats_pivot.columns = ['_'.join(col).strip() for col in stats_pivot.columns.values]
            stats_pivot = stats_pivot.reset_index()
            
            # メインデータと結合
            data = data.merge(stats_pivot, on='studios_id', how='left')
        
        st.success(f"✅ スタジオデータ読み込み成功: {len(data):,}件")
        return data
        
    except Exception as e:
        st.error(f"❌ エラー: {e}")
        return None

@st.cache_data
def load_source_data():
    """原作データの読み込み（CTE使用）"""
    query = """
        WITH source_stats AS (
            SELECT 
                source,
                COUNT(DISTINCT anilist_id) as source_count,
                MIN(seasonYear) as first_year,
                MAX(seasonYear) as last_year,
                MAX(seasonYear) - MIN(seasonYear) + 1 as year_range,
                CAST(COUNT(DISTINCT anilist_id) AS FLOAT) / 
                    NULLIF(MAX(seasonYear) - MIN(seasonYear) + 1, 0) as count_per_year,
                AVG(meanScore) as avg_mean_score,
                SUM(favorites) as total_favorites,
                AVG(favorites) as avg_favorites,
                SUM(popularity) as total_popularity,
                AVG(popularity) as avg_popularity
            FROM anime
            WHERE source IS NOT NULL AND seasonYear IS NOT NULL
            GROUP BY source
        )
        SELECT 
            a.anilist_id,
            a.title_romaji,
            a.title_native,
            a.source,
            a.season,
            a.seasonYear,
            a.favorites as anime_favorites,
            a.popularity as anime_popularity,
            a.meanScore,
            a.format,
            ss.source_count,
            ss.first_year,
            ss.year_range,
            ss.count_per_year,
            ss.avg_mean_score as source_avg_mean_score,
            ss.total_favorites as source_total_favorites,
            ss.avg_favorites as source_avg_favorites,
            ss.total_popularity as source_total_popularity,
            ss.avg_popularity as source_avg_popularity
        FROM anime a
        JOIN source_stats ss ON a.source = ss.source
        WHERE a.source IS NOT NULL
        ORDER BY ss.source_count DESC, a.favorites DESC
    """
    return load_data_from_db('anime_data.db', query, '原作データ読み込み成功')

@st.cache_data
def load_genre_data():
    """ジャンルデータの読み込み（CTE使用）"""
    query = """
        WITH genre_stats AS (
            SELECT 
                g.genre_name,
                COUNT(DISTINCT g.anilist_id) as genre_count,
                MIN(a.seasonYear) as first_year,
                MAX(a.seasonYear) as last_year,
                MAX(a.seasonYear) - MIN(a.seasonYear) + 1 as year_range,
                CAST(COUNT(DISTINCT g.anilist_id) AS FLOAT) / 
                    NULLIF(MAX(a.seasonYear) - MIN(a.seasonYear) + 1, 0) as count_per_year,
                AVG(a.meanScore) as avg_mean_score,
                SUM(a.favorites) as total_favorites,
                AVG(a.favorites) as avg_favorites,
                SUM(a.popularity) as total_popularity,
                AVG(a.popularity) as avg_popularity
            FROM genres g
            JOIN anime a ON g.anilist_id = a.anilist_id
            WHERE g.genre_name IS NOT NULL AND a.seasonYear IS NOT NULL
            GROUP BY g.genre_name
        )
        SELECT 
            a.anilist_id,
            a.title_romaji,
            a.title_native,
            g.genre_name,
            a.season,
            a.seasonYear,
            a.favorites as anime_favorites,
            a.popularity as anime_popularity,
            a.meanScore,
            a.format,
            gs.genre_count,
            gs.first_year,
            gs.year_range,
            gs.count_per_year,
            gs.avg_mean_score as genre_avg_mean_score,
            gs.total_favorites as genre_total_favorites,
            gs.avg_favorites as genre_avg_favorites,
            gs.total_popularity as genre_total_popularity,
            gs.avg_popularity as genre_avg_popularity
        FROM genres g
        JOIN anime a ON g.anilist_id = a.anilist_id
        JOIN genre_stats gs ON g.genre_name = gs.genre_name
        WHERE g.genre_name IS NOT NULL
        ORDER BY gs.genre_count DESC, a.favorites DESC
    """
    return load_data_from_db('anime_data.db', query, 'ジャンルデータ読み込み成功')

@st.cache_data
def load_manga_genre_data():
    """マンガジャンルデータの読み込み（CTE使用）"""
    query = """
        WITH genre_stats AS (
            SELECT 
                g.genre_name,
                COUNT(DISTINCT g.anilist_id) as genre_count,
                MIN(m.seasonYear) as first_year,
                MAX(m.seasonYear) as last_year,
                MAX(m.seasonYear) - MIN(m.seasonYear) + 1 as year_range,
                CAST(COUNT(DISTINCT g.anilist_id) AS FLOAT) / 
                    NULLIF(MAX(m.seasonYear) - MIN(m.seasonYear) + 1, 0) as count_per_year,
                AVG(m.meanScore) as avg_mean_score,
                SUM(m.favorites) as total_favorites,
                AVG(m.favorites) as avg_favorites,
                SUM(m.popularity) as total_popularity,
                AVG(m.popularity) as avg_popularity
            FROM genres g
            JOIN manga m ON g.anilist_id = m.anilist_id
            WHERE g.genre_name IS NOT NULL AND m.seasonYear IS NOT NULL
            GROUP BY g.genre_name
        )
        SELECT 
            m.anilist_id,
            m.title_romaji,
            m.title_native,
            g.genre_name,
            m.season,
            m.seasonYear,
            m.favorites as manga_favorites,
            m.popularity as manga_popularity,
            m.meanScore,
            m.format,
            m.source,
            gs.genre_count,
            gs.first_year,
            gs.year_range,
            gs.count_per_year,
            gs.avg_mean_score as genre_avg_mean_score,
            gs.total_favorites as genre_total_favorites,
            gs.avg_favorites as genre_avg_favorites,
            gs.total_popularity as genre_total_popularity,
            gs.avg_popularity as genre_avg_popularity
        FROM genres g
        JOIN manga m ON g.anilist_id = m.anilist_id
        JOIN genre_stats gs ON g.genre_name = gs.genre_name
        WHERE g.genre_name IS NOT NULL
        ORDER BY gs.genre_count DESC, m.favorites DESC
    """
    return load_data_from_db('manga_data.db', query, 'マンガジャンルデータ読み込み成功')

@st.cache_data
def load_manga_character_data():
    """マンガキャラクターデータの読み込み（テーブル存在確認付き）"""
    try:
        db_path = get_db_path('manga_data.db')
        
        if not db_path.exists():
            st.error(f"❌ manga_data.db が見つかりません")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        # テーブル存在確認
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='characters'")
        
        if not cursor.fetchone():
            conn.close()
            st.warning("⚠️ manga_data.dbにcharactersテーブルが存在しません。")
            return None
        
        query = """
            SELECT 
                c.chara_id, c.chara_name, c.favorites as char_favorites,
                m.anilist_id, m.title_romaji, m.title_native, 
                m.season, m.seasonYear, m.favorites as manga_favorites, 
                m.popularity as manga_popularity,
                m.meanScore, m.format, m.source
            FROM characters c
            JOIN manga m ON c.anilist_id = m.anilist_id
            WHERE c.chara_name IS NOT NULL
            ORDER BY c.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ マンガキャラクターデータ読み込み成功: {len(data):,}件")
        return data
        
    except Exception as e:
        st.error(f"❌ エラー: {e}")
        return None

@st.cache_data
def load_manga_staff_data():
    """マンガスタッフデータの読み込み（条件分岐付き）"""
    try:
        db_path = get_db_path('manga_data.db')
        
        if not db_path.exists():
            st.error(f"❌ manga_data.db が見つかりません")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # staffテーブル存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff'")
        if not cursor.fetchone():
            conn.close()
            st.warning("⚠️ manga_data.dbにstaffテーブルが存在しません。")
            return None
        
        # staff_basic_enhancedテーブルの存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff_basic_enhanced'")
        has_enhanced = cursor.fetchone() is not None
        
        if has_enhanced:
            query = """
                SELECT 
                    s.staff_id, s.staff_name, s.role,
                    m.anilist_id, m.title_romaji, m.title_native, 
                    m.season, m.seasonYear, m.favorites as manga_favorites, 
                    m.meanScore, m.format, m.source,
                    sbe.favorites as staff_favorites,
                    sbe.total_count as staff_count,
                    sbe.count_per_year
                FROM staff s
                JOIN manga m ON s.anilist_id = m.anilist_id
                LEFT JOIN staff_basic_enhanced sbe ON s.staff_id = sbe.staff_id
                WHERE s.staff_name IS NOT NULL
                ORDER BY sbe.favorites DESC NULLS LAST
            """
        else:
            query = """
                SELECT 
                    s.staff_id, s.staff_name, s.role, s.favorites as staff_favorites,
                    m.anilist_id, m.title_romaji, m.title_native, 
                    m.season, m.seasonYear, m.favorites as manga_favorites, 
                    m.meanScore, m.format, m.source
                FROM staff s
                JOIN manga m ON s.anilist_id = m.anilist_id
                WHERE s.staff_name IS NOT NULL
                ORDER BY s.favorites DESC NULLS LAST
            """
        
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ マンガスタッフデータ読み込み成功: {len(data):,}件")
        return data
        
    except Exception as e:
        st.error(f"❌ エラー: {e}")
        return None

@st.cache_data
def load_manga_data():
    """マンガデータの読み込み"""
    query = """
        SELECT 
            m.anilist_id, m.title_romaji, m.title_native, m.format,
            m.season, m.seasonYear, m.meanScore, m.favorites, m.popularity, m.source
        FROM manga m
        WHERE m.title_romaji IS NOT NULL
        ORDER BY m.meanScore DESC NULLS LAST
    """
    return load_data_from_db('manga_data.db', query, 'マンガデータ読み込み成功')

def get_unique_values(data, column):
    """指定されたカラムのユニークな値を取得"""
    if column in data.columns:
        unique_vals = data[column].dropna().unique()
        # 数値の場合は降順でソート、文字列の場合は昇順でソート
        if pd.api.types.is_numeric_dtype(unique_vals):
            return sorted(unique_vals, reverse=True)
        else:
            return sorted(unique_vals)
    return []

def filter_data(data, filters, db_path=None):
    """フィルター条件に基づいてデータを絞り込み"""
    filtered_data = data.copy()
    
    # ジャンルフィルターの処理
    if 'genre' in filters and filters['genre'] and filters['genre'] != "全て" and db_path:
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT anilist_id 
                FROM genres 
                WHERE genre_name = ?
            """, (filters['genre'],))
            genre_anime_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if genre_anime_ids:
                filtered_data = filtered_data[filtered_data['anilist_id'].isin(genre_anime_ids)]
            else:
                # 該当するジャンルのアニメがない場合は空のDataFrameを返す
                filtered_data = filtered_data.iloc[0:0]
        except Exception as e:
            st.error(f"ジャンルフィルター適用エラー: {e}")
    
    # その他のフィルターの処理
    for key, value in filters.items():
        if key != 'genre' and value and value != "全て" and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
    return filtered_data

def show_ranking_tab(data, genre):
    """ランキングタブの表示"""
    st.header(f"🏆 {genre} ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    db_type = 'anime' if genre == "アニメ" else 'manga'
    filters, selected_metric = create_filter_ui(data, f"ranking_{genre}", db_type, show_metric=True)
    
    # フィルター適用
    filtered_data = apply_filters_to_data(data, filters, db_type)
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件)")
    
    # データをソート
    sorted_data = filtered_data.sort_values(selected_metric, ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    if genre == "アニメ":
        display_columns = ['title_native', 'season', 'seasonYear', 'favorites', 'meanScore', 'popularity']
        available_columns = [col for col in display_columns if col in sorted_data.columns]
        display_data = sorted_data[available_columns].copy()
        
        # カラム名を日本語に変更
        column_mapping = {
            'title_native': 'タイトル（日本語）',
            'season': '季節',
            'seasonYear': '年度',
            'favorites': 'お気に入り数',
            'meanScore': '平均スコア',
            'popularity': '人気度'
        }
        
    else:  # マンガ
        display_columns = ['title_native', 'season', 'seasonYear', 'favorites', 'meanScore', 'popularity']
        available_columns = [col for col in display_columns if col in sorted_data.columns]
        display_data = sorted_data[available_columns].copy()
        
        # カラム名を日本語に変更
        column_mapping = {
            'title_native': 'タイトル（日本語）',
            'season': '季節',
            'seasonYear': '年度',
            'favorites': 'お気に入り数',
            'meanScore': '平均スコア',
            'popularity': '人気度'
        }
    
    # 数値フォーマット - 数値型を維持しながら表示フォーマットを適用
    # Streamlitのst.dataframeは数値型をそのまま扱うため、フォーマットは不要
    # 必要に応じてカラムの型を明示的に設定
    if 'favorites' in display_data.columns:
        display_data['favorites'] = pd.to_numeric(display_data['favorites'], errors='coerce')
    if 'popularity' in display_data.columns:
        display_data['popularity'] = pd.to_numeric(display_data['popularity'], errors='coerce')
    if 'meanScore' in display_data.columns:
        display_data['meanScore'] = pd.to_numeric(display_data['meanScore'], errors='coerce')
    if 'seasonYear' in display_data.columns:
        display_data['seasonYear'] = pd.to_numeric(display_data['seasonYear'], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10チャート")
        
        # メトリックラベル定義
        metric_labels = {
            "meanScore": "平均スコア",
            "favorites": "お気に入り数", 
            "popularity": "人気度"
        }
        
        top10_data = sorted_data.head(10)
        
        if not top10_data.empty:
            fig = px.bar(
                top10_data,
                x='title_romaji' if 'title_romaji' in top10_data.columns else 'title_native',
                y=selected_metric,
                title=f"トップ10 - {metric_labels.get(selected_metric, selected_metric)}",
                labels={
                    'title_romaji': 'タイトル',
                    'title_native': 'タイトル',
                    selected_metric: metric_labels.get(selected_metric, selected_metric)
                }
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=500)
            st.plotly_chart(fig, width='stretch')

def show_character_ranking_tab(data):
    """キャラクターランキングタブの表示"""
    config = {
        'title': '🎭 キャラクター ランキング',
        'key_prefix': 'char',
        'db_type': 'anime',
        'dedup_config': {'id_col': 'chara_id', 'sort_col': 'anime_favorites', 'sort_by': 'anime_favorites'},
        'sort_by': 'char_favorites',
        'display_columns': ['chara_name', 'title_native', 'seasonYear', 'season', 
                          'char_favorites', 'anime_favorites', 'anime_popularity', 'meanScore'],
        'column_mapping': {
            'chara_name': 'キャラクター名',
            'title_native': 'アニメタイトル',
            'seasonYear': '年度',
            'season': '季節',
            'char_favorites': 'キャラクターお気に入り数',
            'anime_favorites': 'アニメお気に入り数',
            'anime_popularity': 'アニメ人気度',
            'meanScore': 'アニメ平均スコア'
        },
        'chart_config': {
            'x': 'chara_name',
            'y': 'char_favorites',
            'title': 'トップ10 - キャラクターお気に入り数',
            'labels': {'chara_name': 'キャラクター名', 'char_favorites': 'お気に入り数'},
            'hover_data': ['title_native', 'seasonYear', 'season']
        }
    }
    show_ranking_template(data, config)

def show_manga_character_ranking_tab(data):
    """マンガキャラクターランキングタブの表示"""
    config = {
        'title': '📚 マンガキャラクター ランキング',
        'key_prefix': 'manga_char',
        'db_type': 'manga',
        'dedup_config': {'id_col': 'chara_id', 'sort_col': 'manga_favorites', 'sort_by': 'manga_favorites'},
        'sort_by': 'char_favorites',
        'display_columns': ['chara_name', 'title_native', 'seasonYear', 'season', 
                          'char_favorites', 'manga_favorites', 'manga_popularity', 'meanScore'],
        'column_mapping': {
            'chara_name': 'キャラクター名',
            'title_native': 'マンガタイトル',
            'seasonYear': '年度',
            'season': '季節',
            'char_favorites': 'キャラクターお気に入り数',
            'manga_favorites': 'マンガお気に入り数',
            'manga_popularity': 'マンガ人気度',
            'meanScore': 'マンガ平均スコア'
        },
        'chart_config': {
            'x': 'chara_name',
            'y': 'char_favorites',
            'title': 'トップ10 - キャラクターお気に入り数',
            'labels': {'chara_name': 'キャラクター名', 'char_favorites': 'お気に入り数'},
            'hover_data': ['title_native', 'seasonYear', 'season']
        }
    }
    show_ranking_template(data, config)

def show_voiceactor_ranking_tab(data):
    """声優ランキングタブの表示"""
    config = {
        'title': '🎤 声優 ランキング',
        'key_prefix': 'voiceactor',
        'db_type': 'anime',
        'dedup_config': {'id_col': 'voiceactor_id', 'sort_col': 'anime_favorites', 'sort_by': 'anime_favorites'},
        'sort_by': 'va_favorites',
        'display_columns': ['voiceactor_name', 'title_native', 'seasonYear', 'season', 
                          'voiceactor_count', 'count_per_year', 'va_favorites', 'anime_favorites', 'meanScore'],
        'column_mapping': {
            'voiceactor_name': '声優名',
            'title_native': 'アニメタイトル',
            'seasonYear': '年度',
            'season': '季節',
            'voiceactor_count': '声優カウント数',
            'count_per_year': '声優年平均カウント数',
            'va_favorites': '声優お気に入り数',
            'anime_favorites': 'アニメお気に入り数',
            'meanScore': 'アニメ平均スコア'
        },
        'chart_config': {
            'x': 'voiceactor_name',
            'y': 'va_favorites',
            'title': 'トップ10 - 声優お気に入り数',
            'labels': {'voiceactor_name': '声優名', 'va_favorites': 'お気に入り数'},
            'hover_data': ['title_native', 'seasonYear', 'season']
        }
    }
    show_ranking_template(data, config)

def show_staff_ranking_tab(data):
    """スタッフランキングタブの表示"""
    config = {
        'title': '🎬 スタッフ ランキング',
        'key_prefix': 'staff',
        'db_type': 'anime',
        'dedup_config': {'id_col': 'staff_id', 'sort_col': 'anilist_id', 'sort_by': 'anime_favorites', 'role_aggregate': True},
        'sort_by': 'staff_favorites',
        'display_columns': ['staff_name', 'roles', 'title_native', 'seasonYear', 'season', 
                          'staff_count', 'count_per_year', 'staff_favorites', 'anime_favorites', 'meanScore'],
        'column_mapping': {
            'staff_name': 'スタッフ名',
            'roles': '役割',
            'title_native': 'アニメタイトル',
            'seasonYear': '年度',
            'season': '季節',
            'staff_count': 'スタッフカウント数',
            'count_per_year': 'スタッフ年平均カウント数',
            'staff_favorites': 'スタッフお気に入り数',
            'anime_favorites': 'アニメお気に入り数',
            'meanScore': 'アニメ平均スコア'
        },
        'chart_config': {
            'x': 'staff_name',
            'y': 'staff_favorites',
            'title': 'トップ10 - スタッフお気に入り数',
            'labels': {'staff_name': 'スタッフ名', 'staff_favorites': 'お気に入り数'},
            'hover_data': ['title_native', 'seasonYear', 'season', 'roles']
        }
    }
    show_ranking_template(data, config)

def show_studios_ranking_tab(data):
    """スタジオランキングタブの表示"""
    st.header("🏢 スタジオ ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "studios_rank", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # スタジオIDが重複している場合、アニメのfavoritesが最も多いものだけを残す
    filtered_data = filtered_data.sort_values(['studios_id', 'anime_favorites'], ascending=[True, False]).groupby('studios_id').first().reset_index()
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # データをスタジオのカウント数でソート
    sorted_data = filtered_data.sort_values('studios_count', ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    display_columns = [
        'studios_name', 'title_native', 'seasonYear', 'season', 
        'studios_count', 'count_per_year', 'anime_favorites', 'meanScore'
    ]
    
    # stat_type別のカラムを追加
    stat_columns = [col for col in sorted_data.columns if col.startswith('total_') or col.startswith('avg_value_')]
    display_columns.extend(stat_columns)
    
    available_columns = [col for col in display_columns if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # カラム名を日本語に変更
    column_mapping = {
        'studios_name': 'スタジオ名',
        'title_native': 'アニメタイトル',
        'seasonYear': '年度',
        'season': '季節',
        'studios_count': 'スタジオカウント数',
        'count_per_year': 'スタジオ年度平均回数',
        'anime_favorites': 'アニメお気に入り数',
        'meanScore': 'アニメ平均スコア',
        'total_anime_favorites': 'anime_favorites合計',
        'avg_value_anime_favorites': 'anime_favorites平均',
        'total_anime_popularity': 'anime_popularity合計',
        'avg_value_anime_popularity': 'anime_popularity平均'
    }
    
    # 数値フォーマット - 数値型を維持
    numeric_columns = ['studios_count', 'count_per_year', 'anime_favorites', 'meanScore', 'seasonYear'] + stat_columns
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = pd.to_numeric(display_data[col], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10スタジオ")
        
        top_n = min(10, len(sorted_data))
        top_data = sorted_data.head(top_n)
        
        fig = px.bar(
            top_data,
            x='studios_count',
            y='studios_name',
            orientation='h',
            title=f"トップ{top_n}スタジオ（作品数順）",
            labels={
                'studios_count': 'スタジオカウント数',
                'studios_name': 'スタジオ名'
            },
            hover_data={
                'studios_name': True,
                'title_native': True,
                'studios_count': True,
                'count_per_year': ':.2f',
                'anime_favorites': True,
                'meanScore': ':.1f'
            }
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, width='stretch')

def show_source_ranking_tab(data):
    """原作ランキングタブの表示"""
    st.header("📚 原作 ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    # sourceランキングではsourceフィルターは不要（データ自体がsource別）
    filters = create_filter_ui(data, "source", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 原作タイプが重複している場合、アニメのfavoritesが最も多いものだけを残す
    filtered_data = filtered_data.sort_values(['source', 'anime_favorites'], ascending=[True, False]).groupby('source').first().reset_index()
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # データを原作のカウント数でソート
    sorted_data = filtered_data.sort_values('source_count', ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    display_columns = [
        'source', 'title_native', 'seasonYear', 'season', 
        'source_count', 'count_per_year', 'anime_favorites', 'anime_popularity', 'meanScore',
        'source_avg_mean_score', 'source_total_favorites', 'source_avg_favorites',
        'source_total_popularity', 'source_avg_popularity'
    ]
    
    available_columns = [col for col in display_columns if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # カラム名を日本語に変更
    column_mapping = {
        'source': '原作の種類',
        'title_native': 'アニメタイトル',
        'seasonYear': '年度',
        'season': '季節',
        'source_count': '原作カウント数',
        'count_per_year': '原作年度平均回数',
        'anime_favorites': 'アニメお気に入り数',
        'anime_popularity': 'アニメ人気度',
        'meanScore': 'アニメ平均スコア',
        'source_avg_mean_score': '原作別anime_meanScore平均',
        'source_total_favorites': '原作別anime_favorites合計',
        'source_avg_favorites': '原作別anime_favorites平均',
        'source_total_popularity': '原作別anime_popularity合計',
        'source_avg_popularity': '原作別anime_popularity平均'
    }
    
    # 数値フォーマット - 数値型を維持
    numeric_columns = ['source_count', 'count_per_year', 'anime_favorites', 'anime_popularity', 'meanScore', 
                      'source_avg_mean_score', 'source_total_favorites', 'source_avg_favorites',
                      'source_total_popularity', 'source_avg_popularity', 'seasonYear']
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = pd.to_numeric(display_data[col], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10原作")
        
        top_n = min(10, len(sorted_data))
        top_data = sorted_data.head(top_n)
        
        fig = px.bar(
            top_data,
            x='source_count',
            y='source',
            orientation='h',
            title=f"トップ{top_n}原作（作品数順）",
            labels={
                'source_count': '原作カウント数',
                'source': '原作の種類'
            },
            hover_data={
                'source': True,
                'title_native': True,
                'source_count': True,
                'count_per_year': ':.2f',
                'anime_favorites': True,
                'meanScore': ':.1f'
            }
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, width='stretch')

def show_genre_ranking_tab(data):
    """ジャンルランキングタブの表示"""
    st.header("🎭 ジャンル ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    # genreランキングではgenreフィルターは不要（データ自体がgenre別）
    filters = create_filter_ui(data, "genre", db_type='anime')
    
    # genreランキングの特殊フィルター適用（genre_nameを直接フィルター）
    filtered_data = data.copy()
    if 'genre' in filters and filters['genre']:
        filtered_data = filtered_data[filtered_data['genre_name'] == filters['genre']]
    
    # その他のフィルター処理
    for key, value in filters.items():
        if key != 'genre' and value and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # ジャンルが重複している場合、アニメのfavoritesが最も多いものだけを残す
    filtered_data = filtered_data.sort_values(['genre_name', 'anime_favorites'], ascending=[True, False]).groupby('genre_name').first().reset_index()
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # データをジャンルのカウント数でソート
    sorted_data = filtered_data.sort_values('genre_count', ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    display_columns = [
        'genre_name', 'title_native', 'seasonYear', 'season', 
        'genre_count', 'count_per_year', 'anime_favorites', 'anime_popularity', 'meanScore',
        'genre_avg_mean_score', 'genre_total_favorites', 'genre_avg_favorites',
        'genre_total_popularity', 'genre_avg_popularity'
    ]
    
    available_columns = [col for col in display_columns if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # カラム名を日本語に変更
    column_mapping = {
        'genre_name': 'ジャンルの種類',
        'title_native': 'アニメタイトル',
        'seasonYear': '年度',
        'season': '季節',
        'genre_count': 'ジャンルカウント数',
        'count_per_year': 'ジャンル年度平均回数',
        'anime_favorites': 'アニメお気に入り数',
        'anime_popularity': 'アニメ人気度',
        'meanScore': 'アニメ平均スコア',
        'genre_avg_mean_score': 'ジャンル別anime_meanScore平均',
        'genre_total_favorites': 'ジャンル別anime_favorites合計',
        'genre_avg_favorites': 'ジャンル別anime_favorites平均',
        'genre_total_popularity': 'ジャンル別anime_popularity合計',
        'genre_avg_popularity': 'ジャンル別anime_popularity平均'
    }
    
    # 数値フォーマット - 数値型を維持
    numeric_columns = ['genre_count', 'count_per_year', 'anime_favorites', 'anime_popularity', 'meanScore', 
                      'genre_avg_mean_score', 'genre_total_favorites', 'genre_avg_favorites', 
                      'genre_total_popularity', 'genre_avg_popularity', 'seasonYear']
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = pd.to_numeric(display_data[col], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # ジャンル名の英語→日本語対応表
    st.subheader("🔤 ジャンル名の対応表")
    genre_translation = {
        'Action': 'アクション',
        'Adventure': 'アドベンチャー',
        'Comedy': 'コメディ',
        'Drama': 'ドラマ',
        'Ecchi': 'エッチ',
        'Fantasy': 'ファンタジー',
        'Horror': 'ホラー',
        'Mahou Shoujo': '魔法少女',
        'Mecha': 'メカ',
        'Music': '音楽',
        'Mystery': 'ミステリー',
        'Psychological': 'サイコロジカル',
        'Romance': 'ロマンス',
        'Sci-Fi': 'SF',
        'Slice of Life': '日常',
        'Sports': 'スポーツ',
        'Supernatural': '超常現象',
        'Thriller': 'スリラー'
    }
    
    # 実際にデータに存在するジャンルのみ表示
    existing_genres = sorted_data['genre_name'].unique()
    translation_df = pd.DataFrame([
        {'英語': eng, '日本語': jpn} 
        for eng, jpn in genre_translation.items() 
        if eng in existing_genres
    ])
    
    if not translation_df.empty:
        st.dataframe(translation_df, hide_index=True, use_container_width=True)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10ジャンル")
        
        top_n = min(10, len(sorted_data))
        top_data = sorted_data.head(top_n)
        
        fig = px.bar(
            top_data,
            x='genre_count',
            y='genre_name',
            orientation='h',
            title=f"トップ{top_n}ジャンル（作品数順）",
            labels={
                'genre_count': 'ジャンルカウント数',
                'genre_name': 'ジャンルの種類'
            },
            hover_data={
                'genre_name': True,
                'title_native': True,
                'genre_count': True,
                'count_per_year': ':.2f',
                'anime_favorites': True,
                'meanScore': ':.1f'
            }
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, width='stretch')

def show_manga_staff_ranking_tab(data):
    """マンガスタッフランキングタブの表示"""
    st.header("📚 マンガスタッフ ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "manga_staff", db_type='manga')
    filtered_data = apply_filters_to_data(data, filters, 'manga')
    
    if filtered_data.empty:
        st.warning("フィルター条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # スタッフIDが重複している場合、マンガのfavoritesが最も多いものだけを残す
    # まず、staff_idとanilist_idの組み合わせでroleを集約
    filtered_data['roles'] = filtered_data.groupby(['staff_id', 'anilist_id'])['role'].transform(lambda x: ', '.join(sorted(set(x.dropna()))))
    
    # 重複を削除（staff_idとanilist_idの組み合わせで最初の行を保持）
    filtered_data = filtered_data.drop_duplicates(subset=['staff_id', 'anilist_id'], keep='first')
    
    # staff_idごとにマンガfavoritesが最大のものを選択
    filtered_data = filtered_data.sort_values(['staff_id', 'manga_favorites'], ascending=[True, False]).groupby('staff_id').first().reset_index()
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # データをスタッフのお気に入り数でソート
    sorted_data = filtered_data.sort_values('staff_favorites', ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    if 'staff_count' in sorted_data.columns and 'count_per_year' in sorted_data.columns:
        display_columns = ['staff_name', 'roles', 'title_native', 'seasonYear', 'season', 
                          'staff_count', 'count_per_year', 'staff_favorites', 'manga_favorites', 'meanScore']
    else:
        display_columns = ['staff_name', 'roles', 'title_native', 'seasonYear', 'season', 
                          'staff_favorites', 'manga_favorites', 'meanScore']
    
    available_columns = [col for col in display_columns if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # カラム名を日本語に変更
    column_mapping = {
        'staff_name': 'スタッフ名',
        'roles': '役割',
        'title_native': 'マンガタイトル',
        'seasonYear': '年度',
        'season': '季節',
        'staff_count': 'スタッフカウント数',
        'count_per_year': 'スタッフ年平均カウント数',
        'staff_favorites': 'スタッフお気に入り数',
        'manga_favorites': 'マンガお気に入り数',
        'meanScore': 'マンガ平均スコア'
    }
    
    # 数値フォーマット - 数値型を維持
    if 'staff_count' in display_data.columns:
        display_data['staff_count'] = pd.to_numeric(display_data['staff_count'], errors='coerce')
    if 'count_per_year' in display_data.columns:
        display_data['count_per_year'] = pd.to_numeric(display_data['count_per_year'], errors='coerce')
    if 'staff_favorites' in display_data.columns:
        display_data['staff_favorites'] = pd.to_numeric(display_data['staff_favorites'], errors='coerce')
    if 'manga_favorites' in display_data.columns:
        display_data['manga_favorites'] = pd.to_numeric(display_data['manga_favorites'], errors='coerce')
    if 'meanScore' in display_data.columns:
        display_data['meanScore'] = pd.to_numeric(display_data['meanScore'], errors='coerce')
    if 'seasonYear' in display_data.columns:
        display_data['seasonYear'] = pd.to_numeric(display_data['seasonYear'], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10スタッフ")
        
        top_n = min(10, len(sorted_data))
        top_data = sorted_data.head(top_n)
        
        fig = px.bar(
            top_data,
            x='staff_favorites',
            y='staff_name',
            orientation='h',
            title=f"トップ{top_n}スタッフ（お気に入り数順）",
            labels={
                'staff_favorites': 'スタッフお気に入り数',
                'staff_name': 'スタッフ名'
            },
            hover_data={
                'staff_name': True,
                'roles': True,
                'title_native': True,
                'staff_favorites': True,
                'manga_favorites': True,
                'meanScore': ':.1f'
            }
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, width='stretch')

def show_manga_genre_ranking_tab(data):
    """マンガジャンルランキングタブの表示"""
    st.header("📚 マンガジャンル ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "manga_genre", db_type='manga')
    
    # フィルター適用
    filtered_data = data.copy()
    
    # その他のフィルター処理
    for key, value in filters.items():
        if value and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
    if filtered_data.empty:
        st.warning("フィルター条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({filtered_count:,}件）")
    
    # ジャンルごとにマンガfavoritesが最大のものを選択
    filtered_data = filtered_data.sort_values(['genre_name', 'manga_favorites'], ascending=[True, False]).groupby('genre_name').first().reset_index()
    
    # データをジャンルカウント数でソート
    sorted_data = filtered_data.sort_values('genre_count', ascending=False).reset_index(drop=True)
    
    # 表示用データフレーム準備
    display_columns = ['genre_name', 'title_native', 'seasonYear', 'season', 
                      'genre_count', 'count_per_year', 'manga_favorites', 'manga_popularity', 'meanScore',
                      'genre_avg_mean_score', 'genre_total_favorites', 'genre_avg_favorites',
                      'genre_total_popularity', 'genre_avg_popularity']
    available_columns = [col for col in display_columns if col in sorted_data.columns]
    display_data = sorted_data[available_columns].copy()
    
    # カラム名を日本語に変更
    column_mapping = {
        'genre_name': 'ジャンル名',
        'title_native': 'マンガタイトル',
        'seasonYear': '年度',
        'season': '季節',
        'genre_count': 'ジャンルカウント数',
        'count_per_year': 'ジャンル年度平均回数',
        'manga_favorites': 'マンガお気に入り数',
        'manga_popularity': 'マンガ人気度',
        'meanScore': 'マンガ平均スコア',
        'genre_avg_mean_score': 'ジャンル別manga_meanScore平均',
        'genre_total_favorites': 'ジャンル別manga_favorite合計',
        'genre_avg_favorites': 'ジャンル別manga_favorite平均',
        'genre_total_popularity': 'ジャンル別manga_popularity合計',
        'genre_avg_popularity': 'ジャンル別manga_popularity平均'
    }
    
    # 数値フォーマット - 数値型を維持
    numeric_columns = ['genre_count', 'count_per_year', 'manga_favorites', 'manga_popularity', 'meanScore', 
                      'genre_avg_mean_score', 'genre_total_favorites', 'genre_avg_favorites',
                      'genre_total_popularity', 'genre_avg_popularity', 'seasonYear']
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = pd.to_numeric(display_data[col], errors='coerce')
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, width='stretch', height=400)
    
    # ジャンル名の英語→日本語対応表
    st.subheader("🔤 ジャンル名の対応表")
    genre_translation = {
        'Action': 'アクション',
        'Adventure': 'アドベンチャー',
        'Comedy': 'コメディ',
        'Drama': 'ドラマ',
        'Ecchi': 'エッチ',
        'Fantasy': 'ファンタジー',
        'Horror': 'ホラー',
        'Mahou Shoujo': '魔法少女',
        'Mecha': 'メカ',
        'Music': '音楽',
        'Mystery': 'ミステリー',
        'Psychological': 'サイコロジカル',
        'Romance': 'ロマンス',
        'Sci-Fi': 'SF',
        'Slice of Life': '日常',
        'Sports': 'スポーツ',
        'Supernatural': '超常現象',
        'Thriller': 'スリラー'
    }
    
    # 実際にデータに存在するジャンルのみ表示
    existing_genres = sorted_data['genre_name'].unique()
    translation_df = pd.DataFrame([
        {'英語': eng, '日本語': jpn} 
        for eng, jpn in genre_translation.items() 
        if eng in existing_genres
    ])
    
    if len(translation_df) > 0:
        st.dataframe(translation_df, hide_index=True, width='stretch')
    
    # トップ10のチャート表示
    if len(sorted_data) >= 1:
        st.subheader("📊 トップ10ジャンル")
        
        top_n = min(10, len(sorted_data))
        top_data = sorted_data.head(top_n)
        
        fig = px.bar(
            top_data,
            x='genre_count',
            y='genre_name',
            orientation='h',
            title=f"トップ{top_n}ジャンル（作品数順）",
            labels={
                'genre_count': 'ジャンル作品数',
                'genre_name': 'ジャンル名'
            },
            hover_data={
                'genre_name': True,
                'title_native': True,
                'genre_count': True,
                'count_per_year': ':.2f',
                'manga_favorites': True,
                'meanScore': ':.1f'
            }
        )
        
        fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, width='stretch')

def show_studios_statistics_tab(data):
    """スタジオ基礎統計タブの表示"""
    st.header("📊 スタジオ 基礎統計")
    st.markdown("**このタブでは選択された条件に基づくスタジオの基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "studios_stats", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # スタジオIDが重複している場合、アニメのfavoritesが最も多いものだけを残す
    filtered_data = filtered_data.sort_values(['studios_id', 'anime_favorites'], ascending=[True, False]).groupby('studios_id').first().reset_index()
    
    st.markdown("---")
    st.subheader(f"📈 統計データ（{len(filtered_data):,}スタジオ）")
    
    # 表1: studios_basicデータの統計
    st.markdown("### 📊 表1: スタジオ基本統計（studios_basic）")
    
    basic_stats_dict = {}
    
    # studios_count統計
    if 'studios_count' in filtered_data.columns:
        studios_count_data = filtered_data['studios_count'].dropna()
        if len(studios_count_data) > 0:
            basic_stats_dict['スタジオカウント数'] = {
                '合計': f"{studios_count_data.sum():,.0f}",
                '最大値': f"{studios_count_data.max():,.0f}",
                '最小値': f"{studios_count_data.min():,.0f}",
                '平均値': f"{studios_count_data.mean():,.2f}",
                '中央値': f"{studios_count_data.median():,.2f}",
                '第1四分位数': f"{studios_count_data.quantile(0.25):,.2f}",
                '第3四分位数': f"{studios_count_data.quantile(0.75):,.2f}"
            }
    
    # first_year統計
    if 'first_year' in filtered_data.columns:
        first_year_data = filtered_data['first_year'].dropna()
        if len(first_year_data) > 0:
            basic_stats_dict['初出年'] = {
                '合計': '-',
                '最大値': f"{int(first_year_data.max())}",
                '最小値': f"{int(first_year_data.min())}",
                '平均値': f"{first_year_data.mean():,.1f}",
                '中央値': f"{first_year_data.median():,.1f}",
                '第1四分位数': f"{first_year_data.quantile(0.25):,.1f}",
                '第3四分位数': f"{first_year_data.quantile(0.75):,.1f}"
            }
    
    # year_count統計
    if 'year_count' in filtered_data.columns:
        year_count_data = filtered_data['year_count'].dropna()
        if len(year_count_data) > 0:
            basic_stats_dict['活動年数'] = {
                '合計': f"{year_count_data.sum():,.0f}",
                '最大値': f"{year_count_data.max():,.0f}",
                '最小値': f"{year_count_data.min():,.0f}",
                '平均値': f"{year_count_data.mean():,.2f}",
                '中央値': f"{year_count_data.median():,.2f}",
                '第1四分位数': f"{year_count_data.quantile(0.25):,.2f}",
                '第3四分位数': f"{year_count_data.quantile(0.75):,.2f}"
            }
    
    # count_per_year統計
    if 'count_per_year' in filtered_data.columns:
        count_per_year_data = filtered_data['count_per_year'].dropna()
        if len(count_per_year_data) > 0:
            basic_stats_dict['年平均カウント数'] = {
                '合計': f"{count_per_year_data.sum():,.2f}",
                '最大値': f"{count_per_year_data.max():,.2f}",
                '最小値': f"{count_per_year_data.min():,.2f}",
                '平均値': f"{count_per_year_data.mean():,.4f}",
                '中央値': f"{count_per_year_data.median():,.4f}",
                '第1四分位数': f"{count_per_year_data.quantile(0.25):,.4f}",
                '第3四分位数': f"{count_per_year_data.quantile(0.75):,.4f}"
            }
    
    if basic_stats_dict:
        basic_stats_df = pd.DataFrame(basic_stats_dict)
        st.dataframe(basic_stats_df, width='stretch', height=300)
    else:
        st.info("基本統計データがありません。")
    
    # 表2: studios_statsデータの統計（stat_type別）
    st.markdown("### 📊 表2: スタジオ統計情報（studios_stats）")
    st.markdown("**注: この表は全スタジオの統計値（total_anime_favorites等）の分布を示しています**")
    
    # stat_type別のカラムを抽出
    stat_columns = {}
    for col in filtered_data.columns:
        if col.startswith('total_') or col.startswith('max_value_') or col.startswith('min_value_') or \
           col.startswith('avg_value_') or col.startswith('median_value_') or \
           col.startswith('q1_value_') or col.startswith('q3_value_'):
            stat_columns[col] = filtered_data[col]
    
    if stat_columns:
        stats_dict = {}
        
        # anime_favoritesの統計
        if 'total_anime_favorites' in stat_columns:
            fav_data = filtered_data['total_anime_favorites'].dropna()
            if len(fav_data) > 0:
                stats_dict['anime_favorites合計'] = {
                    '合計': f"{fav_data.sum():,.0f}",
                    '最大値': f"{fav_data.max():,.0f}",
                    '最小値': f"{fav_data.min():,.0f}",
                    '平均値': f"{fav_data.mean():,.2f}",
                    '中央値': f"{fav_data.median():,.2f}",
                    '第1四分位数': f"{fav_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{fav_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{fav_data.std():,.2f}",
                    '分散': f"{fav_data.var():,.2f}"
                }
        
        if 'avg_value_anime_favorites' in stat_columns:
            fav_avg_data = filtered_data['avg_value_anime_favorites'].dropna()
            if len(fav_avg_data) > 0:
                stats_dict['anime_favorites平均'] = {
                    '合計': f"{fav_avg_data.sum():,.2f}",
                    '最大値': f"{fav_avg_data.max():,.2f}",
                    '最小値': f"{fav_avg_data.min():,.2f}",
                    '平均値': f"{fav_avg_data.mean():,.2f}",
                    '中央値': f"{fav_avg_data.median():,.2f}",
                    '第1四分位数': f"{fav_avg_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{fav_avg_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{fav_avg_data.std():,.2f}",
                    '分散': f"{fav_avg_data.var():,.2f}"
                }
        
        # anime_meanScoreの統計
        if 'total_anime_meanScore' in stat_columns:
            score_data = filtered_data['total_anime_meanScore'].dropna()
            if len(score_data) > 0:
                stats_dict['anime_meanScore合計'] = {
                    '合計': f"{score_data.sum():,.2f}",
                    '最大値': f"{score_data.max():,.2f}",
                    '最小値': f"{score_data.min():,.2f}",
                    '平均値': f"{score_data.mean():,.2f}",
                    '中央値': f"{score_data.median():,.2f}",
                    '第1四分位数': f"{score_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{score_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{score_data.std():,.2f}",
                    '分散': f"{score_data.var():,.2f}"
                }
        
        if 'avg_value_anime_meanScore' in stat_columns:
            score_avg_data = filtered_data['avg_value_anime_meanScore'].dropna()
            if len(score_avg_data) > 0:
                stats_dict['anime_meanScore平均'] = {
                    '合計': f"{score_avg_data.sum():,.2f}",
                    '最大値': f"{score_avg_data.max():,.2f}",
                    '最小値': f"{score_avg_data.min():,.2f}",
                    '平均値': f"{score_avg_data.mean():,.2f}",
                    '中央値': f"{score_avg_data.median():,.2f}",
                    '第1四分位数': f"{score_avg_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{score_avg_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{score_avg_data.std():,.2f}",
                    '分散': f"{score_avg_data.var():,.2f}"
                }
        
        if stats_dict:
            stats_df = pd.DataFrame(stats_dict)
            st.dataframe(stats_df, width='stretch', height=400)
        else:
            st.info("統計情報データがありません。")
    else:
        st.info("統計情報データがありません。")
    
    # 表3: スタジオごとのanime_favorites統計の詳細分析
    st.markdown("---")
    st.markdown("### 📊 表3: スタジオごとのanime_favorites統計の詳細分析")
    st.markdown("**注: この表はスタジオごとに集計されたanime_favorites合計・平均の統計分析です**")
    
    if 'total_anime_favorites' in filtered_data.columns or 'avg_value_anime_favorites' in filtered_data.columns:
        table3_dict = {}
        
        # スタジオごとのanime_favorites合計の統計
        if 'total_anime_favorites' in filtered_data.columns:
            total_fav_data = filtered_data['total_anime_favorites'].dropna()
            if len(total_fav_data) > 0:
                table3_dict['スタジオごとのanime_favorites合計'] = {
                    '合計': f"{total_fav_data.sum():,.0f}",
                    '最大値': f"{total_fav_data.max():,.0f}",
                    '最小値': f"{total_fav_data.min():,.0f}",
                    '平均値': f"{total_fav_data.mean():,.2f}",
                    '中央値': f"{total_fav_data.median():,.2f}",
                    '第1四分位数': f"{total_fav_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{total_fav_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{total_fav_data.std():,.2f}",
                    '分散': f"{total_fav_data.var():,.2f}"
                }
        
        # スタジオごとのanime_favorites平均の統計
        if 'avg_value_anime_favorites' in filtered_data.columns:
            avg_fav_data = filtered_data['avg_value_anime_favorites'].dropna()
            if len(avg_fav_data) > 0:
                table3_dict['スタジオごとのanime_favorites平均'] = {
                    '合計': f"{avg_fav_data.sum():,.2f}",
                    '最大値': f"{avg_fav_data.max():,.2f}",
                    '最小値': f"{avg_fav_data.min():,.2f}",
                    '平均値': f"{avg_fav_data.mean():,.2f}",
                    '中央値': f"{avg_fav_data.median():,.2f}",
                    '第1四分位数': f"{avg_fav_data.quantile(0.25):,.2f}",
                    '第3四分位数': f"{avg_fav_data.quantile(0.75):,.2f}",
                    '標準偏差': f"{avg_fav_data.std():,.2f}",
                    '分散': f"{avg_fav_data.var():,.2f}"
                }
        
        if table3_dict:
            table3_df = pd.DataFrame(table3_dict)
            st.dataframe(table3_df, width='stretch', height=400)
        else:
            st.info("anime_favorites統計データがありません。")
    else:
        st.info("anime_favorites統計データがありません。")
    
    # ヒストグラム: スタジオカウント数の分布
    st.markdown("---")
    st.markdown("### 📊 ヒストグラム: スタジオカウント数の分布（対数スケール）")
    
    if 'studios_count' in filtered_data.columns:
        count_data = filtered_data['studios_count'].dropna()
        
        if len(count_data) > 0:
            # 対数変換（0の場合は1に置き換え）
            log_count_data = np.log10(count_data.replace(0, 1))
            
            fig = px.histogram(
                x=log_count_data,
                nbins=50,
                title="スタジオカウント数の分布（対数スケール）",
                labels={'x': 'log10(スタジオカウント数)', 'y': '頻度'}
            )
            
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_title="log10(スタジオカウント数)",
                yaxis_title="頻度"
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # 統計サマリー
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("データ数", f"{len(count_data):,}")
            with col2:
                st.metric("平均値", f"{count_data.mean():,.2f}")
            with col3:
                st.metric("中央値", f"{count_data.median():,.2f}")
            with col4:
                st.metric("標準偏差", f"{count_data.std():,.2f}")
        else:
            st.info("カウント数データがありません。")
    else:
        st.info("カウント数データがありません。")

def show_voiceactor_statistics_tab(data):
    """声優基礎統計タブの表示"""
    st.header("📊 声優 基礎統計")
    st.markdown("**このタブでは選択された条件に基づく声優の基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "va_stats", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 声優IDが重複している場合、アニメのfavoritesが最も多いものだけを残す
    filtered_data = filtered_data.sort_values(['voiceactor_id', 'anime_favorites'], ascending=[True, False]).groupby('voiceactor_id').first().reset_index()
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果 ({filtered_count:,}件）")
    
    # === 表1: キャラクターfavorites統計 ===
    st.subheader("📋 表1: 声優のお気に入り数統計")
    
    va_favorites_data = filtered_data['va_favorites'].dropna()
    
    if len(va_favorites_data) == 0:
        st.error("選択された条件では声優のお気に入り数のデータが存在しません。")
    else:
        try:
            va_stats = {
                "合計": float(va_favorites_data.sum()),
                "カウント": len(va_favorites_data),
                "最大": float(va_favorites_data.max()),
                "最小": float(va_favorites_data.min()),
                "平均": float(va_favorites_data.mean()),
                "中央値": float(va_favorites_data.median()),
                "1/4分位": float(va_favorites_data.quantile(0.25)),
                "3/4分位": float(va_favorites_data.quantile(0.75))
            }
            
            if len(va_favorites_data) > 1:
                va_stats["標準偏差"] = float(va_favorites_data.std())
                va_stats["分散"] = float(va_favorites_data.var())
            else:
                va_stats["標準偏差"] = "計算できません（データ数不足）"
                va_stats["分散"] = "計算できません（データ数不足）"
            
            va_stats_df = pd.DataFrame(
                [(key, value) for key, value in va_stats.items()],
                columns=["統計項目", "声優お気に入り数"]
            )
            st.dataframe(va_stats_df, width='stretch', height=400)
            
        except Exception as e:
            st.error(f"統計計算エラー: {e}")
    
    # === 表2: アニメfavorites統計 ===
    st.subheader("📋 表2: アニメお気に入り数統計")
    
    anime_favorites_data = filtered_data['anime_favorites'].dropna()
    
    if len(anime_favorites_data) == 0:
        st.error("選択された条件ではアニメのお気に入り数のデータが存在しません。")
    else:
        try:
            anime_fav_stats = {
                "合計": float(anime_favorites_data.sum()),
                "カウント": len(anime_favorites_data),
                "最大": float(anime_favorites_data.max()),
                "最小": float(anime_favorites_data.min()),
                "平均": float(anime_favorites_data.mean()),
                "中央値": float(anime_favorites_data.median()),
                "1/4分位": float(anime_favorites_data.quantile(0.25)),
                "3/4分位": float(anime_favorites_data.quantile(0.75))
            }
            
            if len(anime_favorites_data) > 1:
                anime_fav_stats["標準偏差"] = float(anime_favorites_data.std())
                anime_fav_stats["分散"] = float(anime_favorites_data.var())
            else:
                anime_fav_stats["標準偏差"] = "計算できません（データ数不足）"
                anime_fav_stats["分散"] = "計算できません（データ数不足）"
            
            anime_fav_stats_df = pd.DataFrame(
                [(key, value) for key, value in anime_fav_stats.items()],
                columns=["統計項目", "アニメお気に入り数"]
            )
            st.dataframe(anime_fav_stats_df, width='stretch', height=400)
            
        except Exception as e:
            st.error(f"統計計算エラー: {e}")
    
    # === ヒストグラム: 声優お気に入り数の分布 ===
    st.subheader("📊 データ分布（ヒストグラム）")
    if len(va_favorites_data) > 0:
        # 対数スケールに対応するため、データを対数変換
        log_data = np.log10(va_favorites_data[va_favorites_data > 0])  # 0より大きい値のみ対数変換
        
        fig_hist = px.histogram(
            x=log_data,
            nbins=30,
            title="声優お気に入り数の分布（対数スケール）",
            labels={
                'x': '声優お気に入り数 (log10)',
                'y': '頻度'
            }
        )
        
        # y軸を対数スケールに設定
        fig_hist.update_yaxes(type="log")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, width='stretch')

def show_staff_statistics_tab(data):
    """スタッフ基礎統計タブの表示"""
    st.header("📊 スタッフ 基礎統計")
    st.markdown("**このタブでは選択された条件に基づくスタッフの基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "staff_stats", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # スタッフIDが重複している場合、アニメのfavoritesが最も多いものだけを残す
    # まず、staff_idとanilist_idの組み合わせでroleを集約
    filtered_data['roles'] = filtered_data.groupby(['staff_id', 'anilist_id'])['role'].transform(lambda x: ', '.join(sorted(set(x.dropna()))))
    
    # 重複を削除（staff_idとanilist_idの組み合わせで最初の行を保持）
    filtered_data = filtered_data.drop_duplicates(subset=['staff_id', 'anilist_id'], keep='first')
    
    # staff_idごとにアニメfavoritesが最大のものを選択
    filtered_data = filtered_data.sort_values(['staff_id', 'anime_favorites'], ascending=[True, False]).groupby('staff_id').first().reset_index()
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果 ({filtered_count:,}件）")
    
    # === 表1: スタッフfavorites統計 ===
    st.subheader("📋 表1: スタッフのお気に入り数統計")
    
    staff_favorites_data = filtered_data['staff_favorites'].dropna()
    
    if len(staff_favorites_data) == 0:
        st.error("選択された条件ではスタッフのお気に入り数のデータが存在しません。")
    else:
        try:
            staff_stats = {
                "合計": float(staff_favorites_data.sum()),
                "カウント": len(staff_favorites_data),
                "最大": float(staff_favorites_data.max()),
                "最小": float(staff_favorites_data.min()),
                "平均": float(staff_favorites_data.mean()),
                "中央値": float(staff_favorites_data.median()),
                "1/4分位": float(staff_favorites_data.quantile(0.25)),
                "3/4分位": float(staff_favorites_data.quantile(0.75))
            }
            
            if len(staff_favorites_data) > 1:
                staff_stats["標準偏差"] = float(staff_favorites_data.std())
                staff_stats["分散"] = float(staff_favorites_data.var())
            else:
                staff_stats["標準偏差"] = "計算できません（データ数不足）"
                staff_stats["分散"] = "計算できません（データ数不足）"
            
            staff_stats_df = pd.DataFrame(
                [(key, value) for key, value in staff_stats.items()],
                columns=["統計項目", "スタッフお気に入り数"]
            )
            st.dataframe(staff_stats_df, width='stretch', height=400)
            
        except Exception as e:
            st.error(f"統計計算エラー: {e}")
    
    # === 表2: staff_basic テーブルからの統計 ===
    st.subheader("📋 表2: スタッフ基本統計（staff_basicテーブル）")
    
    try:
        db_path = get_db_path('anime_data.db')
        conn = sqlite3.connect(str(db_path))
        
        # フィルタリングされたstaff_idのリストを取得
        staff_ids = filtered_data['staff_id'].unique().tolist()
        
        if len(staff_ids) > 0:
            # staff_basicテーブルからデータを取得
            placeholders = ','.join(['?'] * len(staff_ids))
            query = f"""
                SELECT 
                    staff_id,
                    staff_name,
                    favorites,
                    staff_count,
                    first_year,
                    year_count,
                    count_per_year
                FROM staff_basic
                WHERE staff_id IN ({placeholders})
            """
            
            staff_basic_df = pd.read_sql_query(query, conn, params=staff_ids)
            
            if not staff_basic_df.empty:
                # 各カラムの統計を計算
                basic_stats = {
                    "スタッフ数": len(staff_basic_df),
                    "favorites合計": float(staff_basic_df['favorites'].sum()),
                    "favorites平均": float(staff_basic_df['favorites'].mean()),
                    "favorites中央値": float(staff_basic_df['favorites'].median()),
                    "staff_count合計": float(staff_basic_df['staff_count'].sum()),
                    "staff_count平均": float(staff_basic_df['staff_count'].mean()),
                    "最古の年度": int(staff_basic_df['first_year'].min()),
                    "最新の年度": int(staff_basic_df['first_year'].max()),
                    "年間平均作品数（平均）": float(staff_basic_df['count_per_year'].mean())
                }
                
                basic_stats_df = pd.DataFrame(
                    [(key, value) for key, value in basic_stats.items()],
                    columns=["統計項目", "値"]
                )
                st.dataframe(basic_stats_df, width='stretch', height=400)
            else:
                st.warning("staff_basicテーブルにデータが見つかりません。")
        else:
            st.warning("フィルタリング後のスタッフIDがありません。")
        
        conn.close()
        
    except Exception as e:
        st.error(f"staff_basicテーブル読み込みエラー: {e}")
    
    # === ヒストグラム: スタッフお気に入り数の分布 ===
    st.subheader("📊 データ分布（ヒストグラム）")
    if len(staff_favorites_data) > 0:
        # 対数スケールに対応するため、データを対数変換
        log_data = np.log10(staff_favorites_data[staff_favorites_data > 0])  # 0より大きい値のみ対数変換
        
        fig_hist = px.histogram(
            x=log_data,
            nbins=30,
            title="スタッフお気に入り数の分布（対数スケール）",
            labels={
                'x': 'スタッフお気に入り数 (log10)',
                'y': '頻度'
            }
        )
        
        # y軸を対数スケールに設定
        fig_hist.update_yaxes(type="log")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, width='stretch')

def show_character_statistics_tab(data):
    """キャラクター基礎統計タブの表示"""
    st.header("📊 キャラクター 基礎統計")
    st.markdown("**このタブでは選択された条件に基づくキャラクターの基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定（共通化）
    filters = create_filter_ui(data, "char_stats", db_type='anime')
    filtered_data = apply_filters_to_data(data, filters, 'anime')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # キャラクターIDが重複している場合、最も短いアニメタイトルのものだけを残す
    filtered_data['title_length'] = filtered_data['title_native'].str.len()
    filtered_data = filtered_data.sort_values(['chara_id', 'title_length']).groupby('chara_id').first().reset_index()
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果 ({filtered_count:,}件）")
    
    # キャラクターのお気に入り数データを取得
    metric_data = filtered_data['char_favorites'].dropna()
    
    if len(metric_data) == 0:
        st.error("選択された条件ではキャラクターのお気に入り数のデータが存在しません。")
        return
    
    # 基礎統計の計算
    try:
        stats = {
            "合計": float(metric_data.sum()),
            "カウント": len(metric_data),
            "最大": float(metric_data.max()),
            "最小": float(metric_data.min()),
            "平均": float(metric_data.mean()),
            "中央値": float(metric_data.median()),
            "1/4分位": float(metric_data.quantile(0.25)),
            "3/4分位": float(metric_data.quantile(0.75))
        }
        
        # 標準偏差と分散（計算できない場合の処理）
        if len(metric_data) > 1:
            stats["標準偏差"] = float(metric_data.std())
            stats["分散"] = float(metric_data.var())
        else:
            stats["標準偏差"] = "計算できません（データ数不足）"
            stats["分散"] = "計算できません（データ数不足）"
        
    except Exception as e:
        st.error(f"統計計算エラー: {e}")
        return
    
    # 統計表の表示
    st.subheader("📋 基礎統計表")
    stats_df = pd.DataFrame(
        [(key, value) for key, value in stats.items()],
        columns=["統計項目", "キャラクターお気に入り数"]
    )
    st.dataframe(stats_df, width='stretch', height=400)
    
    # 計算できなかった項目の表示
    non_numeric_stats = {k: v for k, v in stats.items() if not isinstance(v, (int, float))}
    if non_numeric_stats:
        st.subheader("⚠️ 計算できない項目")
        for item, reason in non_numeric_stats.items():
            st.warning(f"**{item}**: {reason}")
    
    # ヒストグラム表示
    st.subheader("📊 データ分布（ヒストグラム）")
    if len(metric_data) > 0:
        # 対数スケールに対応するため、データを対数変換
        log_data = np.log10(metric_data[metric_data > 0])  # 0より大きい値のみ対数変換
        
        fig_hist = px.histogram(
            x=log_data,
            nbins=30,
            title="キャラクターお気に入り数の分布（対数スケール）",
            labels={
                'x': 'キャラクターお気に入り数 (log10)',
                'y': '頻度'
            }
        )
        
        # y軸を対数スケールに設定
        fig_hist.update_yaxes(type="log")
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, width='stretch')

def show_statistics_tab(data, genre):
    """基礎統計タブの表示"""
    st.header(f"📊 {genre} 基礎統計")
    st.markdown("**このタブでは選択された条件に基づく基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 指標選択
        metric_options = ["meanScore", "favorites", "popularity"]
        metric_labels = {
            "meanScore": "平均スコア",
            "favorites": "お気に入り数", 
            "popularity": "人気度"
        }
        selected_metric = st.selectbox(
            "指標",
            metric_options,
            format_func=lambda x: metric_labels.get(x, x),
            key="stats_metric"
        )
    
    with col2:
        # 年度選択
        if genre == "アニメ" and 'seasonYear' in data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(data, 'seasonYear')]
            selected_year = st.selectbox("年度", years, key="stats_year")
        elif genre == "漫画" and 'startYear' in data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(data, 'startYear')]
            selected_year = st.selectbox("年度", years, key="stats_year")
        else:
            selected_year = "全て"
    
    with col3:
        # 季節選択（アニメのみ）
        if genre == "アニメ" and 'season' in data.columns:
            seasons = ["全て"] + get_unique_values(data, 'season')
            selected_season = st.selectbox("季節", seasons, key="stats_season")
        else:
            selected_season = "全て"
    
    # 追加フィルター
    col4, col5, col6 = st.columns(3)
    
    with col4:
        # 原作選択
        if 'source' in data.columns:
            sources = ["全て"] + get_unique_values(data, 'source')
            selected_source = st.selectbox("原作", sources, key="stats_source")
        else:
            selected_source = "全て"
    
    with col5:
        # フォーマット選択
        if 'format' in data.columns:
            formats = ["全て"] + get_unique_values(data, 'format')
            selected_format = st.selectbox("フォーマット", formats, key="stats_format")
        else:
            selected_format = "全て"
    
    with col6:
        # ジャンル選択（データベースから取得）
        if genre == "アニメ":
            # 絶対パスでデータベースの場所を指定
            db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
            
            if db_path.exists():
                available_genres = get_genres_data(db_path)
                genres_options = ["全て"] + available_genres
                selected_genre_filter = st.selectbox("ジャンル", genres_options, key="stats_genre")
            else:
                selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="stats_genre")
        else:
            # マンガの場合は今後実装予定
            selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="stats_genre")
    
    # フィルター適用
    filters = {}
    if genre == "アニメ":
        if selected_year != "全て":
            try:
                filters['seasonYear'] = float(selected_year)
            except ValueError:
                pass
        if selected_season != "全て":
            filters['season'] = selected_season
    elif genre == "漫画":
        if selected_year != "全て":
            try:
                filters['startYear'] = float(selected_year)
            except ValueError:
                pass
    
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_genre_filter != "全て":
        filters['genre'] = selected_genre_filter
    
    # データベースパスを絶対パスで指定
    if genre == "アニメ":
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
    else:
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
    
    filtered_data = filter_data(data, filters, db_path if db_path.exists() else None)
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果 ({filtered_count:,}件)")
    
    # 選択された指標のデータを取得
    metric_data = filtered_data[selected_metric].dropna()
    
    if len(metric_data) == 0:
        st.error(f"選択された条件では{metric_labels.get(selected_metric, selected_metric)}のデータが存在しません。")
        return
    
    # 基礎統計の計算
    try:
        stats = {
            "合計": float(metric_data.sum()),
            "カウント": len(metric_data),
            "最大": float(metric_data.max()),
            "最小": float(metric_data.min()),
            "平均": float(metric_data.mean()),
            "中央値": float(metric_data.median()),
            "1/4分位": float(metric_data.quantile(0.25)),
            "3/4分位": float(metric_data.quantile(0.75))
        }
        
        # 標準偏差と分散（計算できない場合の処理）
        if len(metric_data) > 1:
            stats["標準偏差"] = float(metric_data.std())
            stats["分散"] = float(metric_data.var())
        else:
            stats["標準偏差"] = "計算できません（データ数不足）"
            stats["分散"] = "計算できません（データ数不足）"
        
    except Exception as e:
        st.error(f"統計計算エラー: {e}")
        return
    
    # 統計表の表示
    st.subheader("📋 基礎統計表")
    stats_df = pd.DataFrame(
        [(key, value) for key, value in stats.items()],
        columns=["統計項目", metric_labels.get(selected_metric, selected_metric)]
    )
    st.dataframe(stats_df, width='stretch', height=400)
    
    # 計算できなかった項目の表示
    non_numeric_stats = {k: v for k, v in stats.items() if not isinstance(v, (int, float))}
    if non_numeric_stats:
        st.subheader("⚠️ 計算できない項目")
        for item, reason in non_numeric_stats.items():
            st.warning(f"**{item}**: {reason}")
    
    # ヒストグラム表示
    st.subheader("📊 データ分布（ヒストグラム）")
    if len(metric_data) > 0:
        fig_hist = px.histogram(
            x=metric_data,
            nbins=30,
            title=f"{metric_labels.get(selected_metric, selected_metric)} の分布",
            labels={
                'x': metric_labels.get(selected_metric, selected_metric),
                'y': '頻度'
            }
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, width='stretch')



def show_scatter_tab(data, genre):
    """相関分析タブの表示"""
    st.header(f"🔍 {genre} 相関分析")
    st.markdown("**このタブでは選択された2つの指標間の相関関係を分析します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # エピソード数カラムをクエリに追加する必要があるため、データベースから再取得
    try:
        if genre == "アニメ":
            db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
            conn = sqlite3.connect(str(db_path))
            query = """
                SELECT 
                    a.anilist_id, a.title_romaji, a.title_native, a.format, 
                    a.season, a.seasonYear, a.favorites, a.meanScore, 
                    a.popularity, a.source, a.episode
                FROM anime a
                WHERE a.title_romaji IS NOT NULL
            """
            extended_data = pd.read_sql_query(query, conn)
            conn.close()
        else:
            extended_data = data.copy()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        extended_data = data.copy()
    
    # 選択肢の定義
    categorical_options = {
        "format": "フォーマット",
        "season": "シーズン", 
        "seasonYear": "年度",
        "source": "ソース"
    }
    
    numerical_options = {
        "episode": "エピソード数",
        "favorites": "お気に入り",
        "meanScore": "平均スコア",
        "popularity": "人気度"
    }
    
    # ジャンルオプションをデータベースから取得
    if genre == "アニメ":
        try:
            available_genres = get_genres_data(db_path)
            if available_genres:
                categorical_options["genre"] = "ジャンル"
        except:
            pass
    
    # フィルター設定
    st.subheader("🔧 データフィルター設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 年度選択
        if genre == "アニメ" and 'seasonYear' in extended_data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(extended_data, 'seasonYear')]
            selected_year = st.selectbox("年度", years, key="corr_year")
        elif genre == "漫画" and 'startYear' in extended_data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(extended_data, 'startYear')]
            selected_year = st.selectbox("年度", years, key="corr_year")
        else:
            selected_year = "全て"
    
    with col2:
        # 季節選択（アニメのみ）
        if genre == "アニメ" and 'season' in extended_data.columns:
            seasons = ["全て"] + get_unique_values(extended_data, 'season')
            selected_season = st.selectbox("季節", seasons, key="corr_season")
        else:
            selected_season = "全て"
    
    with col3:
        # 原作選択
        if 'source' in extended_data.columns:
            sources = ["全て"] + get_unique_values(extended_data, 'source')
            selected_source = st.selectbox("原作", sources, key="corr_source")
        else:
            selected_source = "全て"
    
    # 追加フィルター
    col4, col5 = st.columns(2)
    
    with col4:
        # フォーマット選択
        if 'format' in extended_data.columns:
            formats = ["全て"] + get_unique_values(extended_data, 'format')
            selected_format = st.selectbox("フォーマット", formats, key="corr_format")
        else:
            selected_format = "全て"
    
    with col5:
        # ジャンル選択（データベースから取得）
        if genre == "アニメ":
            try:
                available_genres = get_genres_data(db_path)
                genres_options = ["全て"] + available_genres
                selected_genre_filter = st.selectbox("ジャンル", genres_options, key="corr_genre_filter")
            except:
                selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="corr_genre_filter")
        else:
            # マンガの場合は今後実装予定
            selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="corr_genre_filter")
    
    # フィルター適用
    filters = {}
    if genre == "アニメ":
        if selected_year != "全て":
            try:
                filters['seasonYear'] = float(selected_year)
            except ValueError:
                pass
        if selected_season != "全て":
            filters['season'] = selected_season
    elif genre == "漫画":
        if selected_year != "全て":
            try:
                filters['startYear'] = float(selected_year)
            except ValueError:
                pass
    
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_genre_filter != "全て":
        filters['genre'] = selected_genre_filter
    
    # フィルター適用
    filtered_data = filter_data(extended_data, filters, db_path if db_path.exists() else None)
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を表示
    filtered_count = len(filtered_data)
    st.info(f"📊 フィルター適用後のデータ件数: {filtered_count:,}件")
    
    # 相関分析設定
    st.subheader("🔧 相関分析設定")
    
    # 分析モード選択
    analysis_mode = st.radio(
        "分析モード",
        ["単一相関分析", "複数相関分析"],
        key="analysis_mode",
        horizontal=True
    )
    
    if analysis_mode == "単一相関分析":
        # 単一相関分析
        col1, col2 = st.columns(2)
        
        with col1:
            # 選択肢1（数値のみ）
            selected_var1 = st.selectbox(
                "選択肢1（数値項目）",
                list(numerical_options.keys()),
                format_func=lambda x: numerical_options.get(x, x),
                key="single_var1"
            )
        
        with col2:
            # 選択肢2（数値のみ）
            selected_var2 = st.selectbox(
                "選択肢2（数値項目）",
                list(numerical_options.keys()),
                format_func=lambda x: numerical_options.get(x, x),
                key="single_var2"
            )
        
        # 単一相関分析の実行
        if selected_var1 != selected_var2:
            show_numerical_correlation(filtered_data, selected_var1, selected_var2, numerical_options, numerical_options)
        else:
            st.warning("同じ項目同士の相関は分析できません。異なる項目を選択してください。")
    
    else:
        # 複数相関分析
        st.markdown("**複数項目間の相関係数を一度に表示します**")
        
        # 分析対象項目の選択
        selected_vars = st.multiselect(
            "分析する項目を選択（2つ以上）",
            list(numerical_options.keys()),
            default=list(numerical_options.keys())[:3],  # デフォルトで最初の3項目を選択
            format_func=lambda x: numerical_options.get(x, x),
            key="multi_vars"
        )
        
        if len(selected_vars) < 2:
            st.warning("2つ以上の項目を選択してください。")
        else:
            # 複数相関分析の実行
            show_multiple_correlation(filtered_data, selected_vars, numerical_options)

def show_numerical_correlation(data, var1, var2, options1, options2):
    """数値変数同士の相関分析"""
    # データクリーニング
    clean_data = data[[var1, var2, 'title_romaji']].dropna()
    
    if len(clean_data) < 2:
        st.error("相関分析に十分なデータがありません。")
        return
    
    # 相関係数の計算
    correlation = clean_data[var1].corr(clean_data[var2])
    
    # 散布図の作成（対数スケール）
    fig = px.scatter(
        clean_data,
        x=var1,
        y=var2,
        hover_name='title_romaji',
        title=f"{options1.get(var1)} vs {options2.get(var2)} の相関分析（対数スケール）",
        labels={
            var1: options1.get(var1),
            var2: options2.get(var2)
        },
        log_x=True,
        log_y=True
    )
    
    # 回帰線の追加（対数スケール）
    try:
        fig.add_traces(
            px.scatter(clean_data, x=var1, y=var2, trendline="ols", log_x=True, log_y=True).data[1:]
        )
    except:
        # 回帰線の追加に失敗した場合はスキップ
        pass
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, width='stretch')
    
    # 相関係数を散布図の下に表示
    st.subheader("📊 相関係数")
    
    # 相関係数
    st.metric("相関係数", f"{correlation:.4f}")
    
    # 相関の強さ判定
    abs_corr = abs(correlation)
    if abs_corr >= 0.8:
        strength = "非常に強い"
        color = "🔴"
    elif abs_corr >= 0.6:
        strength = "強い"
        color = "🟠"
    elif abs_corr >= 0.4:
        strength = "中程度"
        color = "🟡"
    elif abs_corr >= 0.2:
        strength = "弱い"
        color = "🟢"
    else:
        strength = "非常に弱い"
        color = "⚪"
    
    st.metric("相関の強さ", f"{color} {strength}")
    
    # 相関の方向
    direction = "正の相関" if correlation > 0 else "負の相関"
    st.metric("相関の方向", direction)
    
    # データ数
    st.metric("分析データ数", f"{len(clean_data):,}件")

def show_multiple_correlation(data, selected_vars, numerical_options):
    """複数変数間の相関分析"""
    # データクリーニング
    analysis_columns = selected_vars + ['title_romaji']
    clean_data = data[analysis_columns].dropna()
    
    if len(clean_data) < 2:
        st.error("相関分析に十分なデータがありません。")
        return
    
    # 相関行列の計算
    corr_matrix = clean_data[selected_vars].corr()
    
    # 相関行列のヒートマップ
    st.subheader("📊 相関行列ヒートマップ")
    
    fig_heatmap = px.imshow(
        corr_matrix,
        labels=dict(x="項目", y="項目", color="相関係数"),
        x=[numerical_options.get(var, var) for var in selected_vars],
        y=[numerical_options.get(var, var) for var in selected_vars],
        color_continuous_scale="RdBu",
        aspect="auto",
        title="相関係数ヒートマップ"
    )
    
    # 相関係数を各セルに表示
    for i in range(len(selected_vars)):
        for j in range(len(selected_vars)):
            fig_heatmap.add_annotation(
                x=j, y=i,
                text=f"{corr_matrix.iloc[i, j]:.3f}",
                showarrow=False,
                font=dict(color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black")
            )
    
    fig_heatmap.update_layout(height=500)
    st.plotly_chart(fig_heatmap, width='stretch')
    
    # 個別の散布図（強い相関のペアのみ）
    st.subheader("🔍 主要な相関関係の散布図")
    
    # 強い相関（絶対値0.3以上）のペアを抽出
    strong_correlations = []
    for i in range(len(selected_vars)):
        for j in range(i+1, len(selected_vars)):
            corr_value = corr_matrix.iloc[i, j]
            if abs(corr_value) >= 0.3:
                strong_correlations.append({
                    'var1': selected_vars[i],
                    'var2': selected_vars[j],
                    'correlation': corr_value,
                    'abs_correlation': abs(corr_value)
                })
    
    # 相関の強さでソート
    strong_correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)
    
    if not strong_correlations:
        st.info("相関係数の絶対値が0.3以上のペアが見つかりませんでした。")
        st.info("すべてのペアの相関係数は上のヒートマップで確認できます。")
    else:
        # 上位の相関ペアの散布図を表示（最大3ペア）
        for idx, corr_info in enumerate(strong_correlations[:3]):
            var1, var2 = corr_info['var1'], corr_info['var2']
            correlation = corr_info['correlation']
            
            st.write(f"**{numerical_options.get(var1)} vs {numerical_options.get(var2)}**")
            
            # 散布図の作成（対数スケール）
            pair_data = clean_data[[var1, var2, 'title_romaji']].dropna()
            
            if len(pair_data) >= 2:
                fig = px.scatter(
                    pair_data,
                    x=var1,
                    y=var2,
                    hover_name='title_romaji',
                    labels={
                        var1: numerical_options.get(var1),
                        var2: numerical_options.get(var2)
                    },
                    log_x=True,
                    log_y=True
                )
                
                # 回帰線の追加（対数スケール）
                try:
                    fig.add_traces(
                        px.scatter(pair_data, x=var1, y=var2, trendline="ols", log_x=True, log_y=True).data[1:]
                    )
                except:
                    # 回帰線の追加に失敗した場合はスキップ
                    pass
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, width='stretch')
                
                # 相関係数を表示
                st.metric("相関係数", f"{correlation:.4f}")
                
                # 相関の強さ判定
                abs_corr = abs(correlation)
                if abs_corr >= 0.8:
                    strength = "非常に強い"
                    color = "🔴"
                elif abs_corr >= 0.6:
                    strength = "強い"
                    color = "🟠"
                elif abs_corr >= 0.4:
                    strength = "中程度"
                    color = "🟡"
                elif abs_corr >= 0.2:
                    strength = "弱い"
                    color = "🟢"
                else:
                    strength = "非常に弱い"
                    color = "⚪"
                
                st.metric("相関の強さ", f"{color} {strength}")
                
                # 相関の方向と データ数
                direction = "正の相関" if correlation > 0 else "負の相関"
                st.metric("相関の方向", direction)
                
                st.metric("分析データ数", f"{len(pair_data):,}件")
                
                if idx < len(strong_correlations[:3]) - 1:
                    st.markdown("---")
    
    # 全ペアの相関係数一覧表示
    st.subheader("📋 全ペア相関係数一覧")
    correlation_list = []
    for i in range(len(selected_vars)):
        for j in range(i+1, len(selected_vars)):
            correlation_list.append({
                '項目1': numerical_options.get(selected_vars[i]),
                '項目2': numerical_options.get(selected_vars[j]),
                '相関係数': f"{corr_matrix.iloc[i, j]:.4f}"
            })
    
    correlation_df = pd.DataFrame(correlation_list)
    correlation_df = correlation_df.sort_values('相関係数', key=lambda x: x.astype(float).abs(), ascending=False)
    st.dataframe(correlation_df, width='stretch', height=300)

def main():
    """メイン関数"""
    st.title("📊 AniList ランキング分析")
    st.markdown("---")
    
    # サイドバーメニュー
    st.sidebar.title("📋 メニュー")
    
    # 統合メニュー
    menu = st.sidebar.radio(
        "分析項目を選択:",
        [
            "🎬 アニメ - タイトル",
            "🎬 アニメ - キャラ",
            "🎬 アニメ - 声優",
            "🎬 アニメ - スタッフ",
            "🎬 アニメ - スタジオ",
            "🎬 アニメ - 原作",
            "🎬 アニメ - ジャンル",
            "🎬 アニメ - エピソード数",
            "📚 マンガ - タイトル",
            "📚 マンガ - キャラ",
            "📚 マンガ - スタッフ",
            "📚 マンガ - ジャンル",
            "📚 マンガ - エピソード数"
        ],
        key="main_menu"
    )
    
    # 選択されたメニューに応じて処理を分岐
    if menu == "🎬 アニメ - タイトル":
        # アニメタイトル分析（ランキングのみ）
        data = load_anime_data()
        if data is None:
            st.error("アニメデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_ranking_tab(data, "アニメ")
    
    elif menu == "🎬 アニメ - キャラ":
        # キャラクター分析
        data = load_character_data()
        if data is None:
            st.error("キャラクターデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_character_ranking_tab(data)
    
    elif menu == "🎬 アニメ - 声優":
        # 声優分析
        data = load_voiceactor_data()
        if data is None:
            st.error("声優データを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_voiceactor_ranking_tab(data)
    
    elif menu == "🎬 アニメ - スタッフ":
        # スタッフ分析
        data = load_staff_data()
        if data is None:
            st.error("スタッフデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_staff_ranking_tab(data)
    
    elif menu == "🎬 アニメ - スタジオ":
        # スタジオ分析
        data = load_studios_data()
        if data is None:
            st.error("スタジオデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_studios_ranking_tab(data)
    
    elif menu == "🎬 アニメ - 原作":
        # 原作分析
        data = load_source_data()
        if data is None:
            st.error("原作データを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_source_ranking_tab(data)
    
    elif menu == "🎬 アニメ - ジャンル":
        # ジャンル分析
        data = load_genre_data()
        if data is None:
            st.error("ジャンルデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_genre_ranking_tab(data)
    
    elif menu == "📚 マンガ - タイトル":
        # マンガタイトル分析
        data = load_manga_data()
        if data is None:
            st.error("マンガデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # メイン画面のタブ分離
        tab1, tab2, tab3 = st.tabs(["ランキング", "基礎統計", "相関分析"])
        
        with tab1:
            show_ranking_tab(data, "漫画")
        
        with tab2:
            show_statistics_tab(data, "漫画")
        
        with tab3:
            show_scatter_tab(data, "漫画")
    
    elif menu == "📚 マンガ - キャラ":
        # マンガキャラクター分析
        data = load_manga_character_data()
        if data is None:
            st.error("マンガキャラクターデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_manga_character_ranking_tab(data)
    
    elif menu == "📚 マンガ - スタッフ":
        # マンガスタッフ分析
        data = load_manga_staff_data()
        if data is None:
            st.error("マンガスタッフデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_manga_staff_ranking_tab(data)
    
    elif menu == "📚 マンガ - ジャンル":
        # マンガジャンル分析
        data = load_manga_genre_data()
        if data is None:
            st.error("マンガジャンルデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # ランキングのみ表示
        show_manga_genre_ranking_tab(data)
    
    else:
        # その他のメニュー項目（今後実装予定）
        st.header(f"{menu} 分析")
        st.info("この機能は今後実装予定です。")

if __name__ == "__main__":
    main()