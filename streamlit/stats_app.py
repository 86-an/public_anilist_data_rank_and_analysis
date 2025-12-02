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
    page_title="AniList 基礎統計",
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_anime_data():
    """アニメデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                a.anilist_id, a.title_romaji, a.title_native, a.format, 
                a.season, a.seasonYear, a.favorites, a.meanScore, 
                a.popularity, a.source
            FROM anime a
            WHERE a.title_romaji IS NOT NULL
            ORDER BY a.meanScore DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ アニメデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def get_genres_data(db_path):
    """データベースからジャンルデータを取得"""
    try:
        conn = sqlite3.connect(str(db_path))
        query = "SELECT DISTINCT genre_name FROM genres ORDER BY genre_name"
        cursor = conn.cursor()
        cursor.execute(query)
        genres = [row[0] for row in cursor.fetchall()]
        conn.close()
        return genres
    except sqlite3.Error as e:
        st.error(f"❌ ジャンルデータ取得エラー: {e}")
        return []
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return []

@st.cache_data
def load_character_data():
    """キャラクターデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                c.chara_id, c.chara_name, c.favorites as char_favorites,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format, a.source
            FROM characters c
            JOIN anime a ON c.anilist_id = a.anilist_id
            WHERE c.chara_name IS NOT NULL
            ORDER BY c.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ キャラクターデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_voiceactor_data():
    """声優データの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                v.voiceactor_id, v.voiceactor_name, v.favorites as va_favorites,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format, a.source,
                vb.voiceactor_count, vb.count_per_year
            FROM voiceactors v
            JOIN anime a ON v.anilist_id = a.anilist_id
            LEFT JOIN voiceactor_basic vb ON v.voiceactor_id = vb.voiceactor_id
            WHERE v.voiceactor_name IS NOT NULL
            ORDER BY v.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ 声優データ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_staff_data():
    """スタッフデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                s.staff_id, s.staff_name, s.role, s.favorites as staff_favorites,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format, a.source,
                sb.staff_count, sb.count_per_year
            FROM staff s
            JOIN anime a ON s.anilist_id = a.anilist_id
            LEFT JOIN staff_basic sb ON s.staff_id = sb.staff_id
            WHERE s.staff_name IS NOT NULL
            ORDER BY s.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ スタッフデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_studios_data():
    """スタジオデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
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
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_genre_data():
    """アニメジャンルデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                g.genre_name,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format, a.source
            FROM genres g
            JOIN anime a ON g.anilist_id = a.anilist_id
            WHERE g.genre_name IS NOT NULL AND a.title_romaji IS NOT NULL
            ORDER BY a.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ ジャンルデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_source_data():
    """アニメ原作データの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                a.source,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format
            FROM anime a
            WHERE a.source IS NOT NULL AND a.title_romaji IS NOT NULL
            ORDER BY a.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ 原作データ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_studio_data():
    """アニメスタジオデータの読み込み（ジャンル情報含む）"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'anime_data.db'
        
        if not db_path.exists():
            st.error(f"❌ anime_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        
        # スタジオとアニメの基本情報を取得
        query_studio = """
            SELECT 
                s.studios_name,
                a.anilist_id, a.title_romaji, a.title_native, 
                a.season, a.seasonYear, a.favorites, 
                a.meanScore, a.popularity, a.format, a.source
            FROM studios s
            JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.studios_name IS NOT NULL AND a.title_romaji IS NOT NULL
            ORDER BY a.favorites DESC NULLS LAST
        """
        studio_data = pd.read_sql_query(query_studio, conn)
        
        # ジャンル情報を取得
        query_genres = """
            SELECT anilist_id, genre_name
            FROM genres
            WHERE genre_name IS NOT NULL
        """
        genres_data = pd.read_sql_query(query_genres, conn)
        conn.close()
        
        # ジャンルを集約（複数ジャンルをカンマ区切りで結合）
        genres_agg = genres_data.groupby('anilist_id')['genre_name'].apply(lambda x: ', '.join(sorted(set(x)))).reset_index()
        genres_agg.columns = ['anilist_id', 'genres']
        
        # スタジオデータとジャンルをマージ
        data = studio_data.merge(genres_agg, on='anilist_id', how='left')
        data['genres'] = data['genres'].fillna('Unknown')
        
        st.success(f"✅ スタジオデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_manga_data():
    """マンガデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'manga_data.db'
        
        if not db_path.exists():
            st.error(f"❌ manga_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                m.anilist_id, m.title_romaji, m.title_native, m.format,
                m.seasonYear, m.meanScore, m.favorites, m.popularity
            FROM manga m
            WHERE m.title_romaji IS NOT NULL
            ORDER BY m.meanScore DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ マンガデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_manga_genre_data():
    """マンガジャンルデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'manga_data.db'
        
        if not db_path.exists():
            st.error(f"❌ manga_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                g.genre_name,
                m.anilist_id, m.title_romaji, m.title_native, 
                m.seasonYear, m.favorites, 
                m.meanScore, m.popularity, m.format
            FROM genres g
            JOIN manga m ON g.anilist_id = m.anilist_id
            WHERE g.genre_name IS NOT NULL AND m.title_romaji IS NOT NULL
            ORDER BY m.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ マンガジャンルデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_manga_character_data():
    """マンガキャラクターデータの読み込み"""
    try:
        # 絶対パスでデータベースの場所を指定
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
        
        # バックアップ: 相対パスでも試行
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'manga_data.db'
        
        if not db_path.exists():
            st.error(f"❌ manga_data.db が見つかりません")
            st.error(f"確認した場所: {db_path}")
            return None
        
        st.info(f"📂 データベース接続: {db_path}")
        
        conn = sqlite3.connect(str(db_path))
        query = """
            SELECT 
                c.chara_id, c.chara_name, c.favorites as char_favorites,
                m.anilist_id, m.title_romaji, m.title_native, 
                m.seasonYear, m.favorites, 
                m.meanScore, m.popularity, m.format, m.source
            FROM characters c
            JOIN manga m ON c.anilist_id = m.anilist_id
            WHERE c.chara_name IS NOT NULL
            ORDER BY c.favorites DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        st.success(f"✅ マンガキャラクターデータ読み込み成功: {len(data):,}件")
        return data
        
    except sqlite3.Error as e:
        st.error(f"❌ データベースエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {e}")
        return None

@st.cache_data
def load_manga_staff_data():
    """マンガスタッフデータの読み込み"""
    try:
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
        
        if not db_path.exists():
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            db_path = project_root / 'db' / 'manga_data.db'
        
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
                    m.seasonYear, m.favorites as manga_favorites, 
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
                    m.seasonYear, m.favorites as manga_favorites, 
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

def create_decade_filter(data, selected_decade, year_column='seasonYear'):
    """年代フィルターを適用してデータを絞り込む
    
    Args:
        data: データフレーム
        selected_decade: 選択された年代（'全期間', '1900年代', '2000年代', '2010年代', '2020年代'）
        year_column: 年度を表す列名（'seasonYear' or 'seasonYear'）
    
    Returns:
        フィルター適用後のデータフレーム
    """
    if selected_decade == "全期間" or year_column not in data.columns:
        return data
    
    # 年代の範囲を定義
    decade_ranges = {
        "1900年代": (1900, 1999),
        "2000年代": (2000, 2009),
        "2010年代": (2010, 2019),
        "2020年代": (2020, 2029)
    }
    
    if selected_decade in decade_ranges:
        start_year, end_year = decade_ranges[selected_decade]
        return data[(data[year_column] >= start_year) & (data[year_column] <= end_year)]
    
    return data

def calculate_statistics_by_period(data, metric_col='favorites', year_column='seasonYear'):
    """期間別統計を計算する汎用関数
    
    Args:
        data: データフレーム
        metric_col: 統計を計算する列名
        year_column: 年度を表す列名（'seasonYear' or 'seasonYear'）
    
    Returns:
        dict: {
            'overall': 全期間統計のdict,
            'period_total': 選択期間合計統計のdict,
            'yearly': 年別統計のDataFrame,
            'decade': 年代別統計のDataFrame
        }
    """
    if metric_col not in data.columns or year_column not in data.columns:
        return None
    
    # メトリック列のデータ取得
    metric_data = data[metric_col].dropna()
    
    # 全期間統計（10項目）
    overall_stats = {
        '合計': float(metric_data.sum()),
        'カウント': len(metric_data),
        '最大': float(metric_data.max()),
        '最小': float(metric_data.min()),
        '平均': float(metric_data.mean()),
        '中央値': float(metric_data.median()),
        '1/4分位': float(metric_data.quantile(0.25)),
        '3/4分位': float(metric_data.quantile(0.75))
    }
    
    # 標準偏差と分散（データ数が2以上の場合のみ計算）
    if len(metric_data) > 1:
        overall_stats['標準偏差'] = float(metric_data.std())
        overall_stats['分散'] = float(metric_data.var())
    else:
        overall_stats['標準偏差'] = 0.0
        overall_stats['分散'] = 0.0
    
    # 選択期間合計統計（全期間と同じ）
    period_total_stats = overall_stats.copy()
    
    # 年別統計（10項目）
    yearly_data = []
    for year in sorted(data[year_column].dropna().unique(), reverse=True):
        year_data = data[data[year_column] == year]
        year_metric = year_data[metric_col].dropna()
        
        if len(year_metric) == 0:
            continue
        
        year_stats = {
            '年度': int(year),
            '合計': float(year_metric.sum()),
            'カウント': len(year_metric),
            '最大': float(year_metric.max()),
            '最小': float(year_metric.min()),
            '平均': float(year_metric.mean()),
            '中央値': float(year_metric.median()),
            '1/4分位': float(year_metric.quantile(0.25)),
            '3/4分位': float(year_metric.quantile(0.75))
        }
        
        # 標準偏差と分散
        if len(year_metric) > 1:
            year_stats['標準偏差'] = float(year_metric.std())
            year_stats['分散'] = float(year_metric.var())
        else:
            year_stats['標準偏差'] = 0.0
            year_stats['分散'] = 0.0
        
        yearly_data.append(year_stats)
    
    yearly_df = pd.DataFrame(yearly_data)
    
    # 年代別統計（10項目）
    decade_data = []
    decade_ranges = {
        "1900年代": (1900, 1999),
        "2000年代": (2000, 2009),
        "2010年代": (2010, 2019),
        "2020年代": (2020, 2029)
    }
    
    for decade_name, (start_year, end_year) in decade_ranges.items():
        decade_filtered = data[(data[year_column] >= start_year) & (data[year_column] <= end_year)]
        decade_metric = decade_filtered[metric_col].dropna()
        
        if len(decade_metric) == 0:
            continue
        
        decade_stats = {
            '年代': decade_name,
            '合計': float(decade_metric.sum()),
            'カウント': len(decade_metric),
            '最大': float(decade_metric.max()),
            '最小': float(decade_metric.min()),
            '平均': float(decade_metric.mean()),
            '中央値': float(decade_metric.median()),
            '1/4分位': float(decade_metric.quantile(0.25)),
            '3/4分位': float(decade_metric.quantile(0.75))
        }
        
        # 標準偏差と分散
        if len(decade_metric) > 1:
            decade_stats['標準偏差'] = float(decade_metric.std())
            decade_stats['分散'] = float(decade_metric.var())
        else:
            decade_stats['標準偏差'] = 0.0
            decade_stats['分散'] = 0.0
        
        decade_data.append(decade_stats)
    
    decade_df = pd.DataFrame(decade_data)
    
    return {
        'overall': overall_stats,
        'period_total': period_total_stats,
        'yearly': yearly_df,
        'decade': decade_df
    }

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

def show_studios_ranking_tab(data):
    """スタジオランキングタブの表示"""
    st.header("🏢 スタジオ ランキング")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 年度選択
        if 'seasonYear' in data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(data, 'seasonYear')]
            selected_year = st.selectbox("年度", years, key="studios_rank_year")
        else:
            selected_year = "全て"
    
    with col2:
        # 季節選択
        if 'season' in data.columns:
            seasons = ["全て"] + get_unique_values(data, 'season')
            selected_season = st.selectbox("季節", seasons, key="studios_rank_season")
        else:
            selected_season = "全て"
    
    with col3:
        # 原作選択
        if 'source' in data.columns:
            sources = ["全て"] + get_unique_values(data, 'source')
            selected_source = st.selectbox("原作", sources, key="studios_rank_source")
        else:
            selected_source = "全て"
    
    # 追加フィルター
    col4, col5 = st.columns(2)
    
    with col4:
        # フォーマット選択
        if 'format' in data.columns:
            formats = ["全て"] + get_unique_values(data, 'format')
            selected_format = st.selectbox("フォーマット", formats, key="studios_rank_format")
        else:
            selected_format = "全て"
    
    with col5:
        # ジャンル選択（データベースから取得）
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        if db_path.exists():
            available_genres = get_genres_data(db_path)
            genres_options = ["全て"] + available_genres
            selected_genre_filter = st.selectbox("ジャンル", genres_options, key="studios_rank_genre")
        else:
            selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="studios_rank_genre")
    
    # フィルター適用
    filters = {}
    if selected_year != "全て":
        try:
            filters['seasonYear'] = float(selected_year)
        except ValueError:
            pass
    if selected_season != "全て":
        filters['season'] = selected_season
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_genre_filter != "全て":
        filters['genre'] = selected_genre_filter
    
    # フィルター適用（ジャンルフィルターはanilist_idベースで処理）
    filtered_data = data.copy()
    
    # ジャンルフィルターの処理
    if 'genre' in filters and filters['genre']:
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
                filtered_data = filtered_data.iloc[0:0]
        except Exception as e:
            st.error(f"ジャンルフィルター適用エラー: {e}")
    
    # その他のフィルター処理
    for key, value in filters.items():
        if key != 'genre' and value and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
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
        'total_anime_meanScore': 'anime_meanScore合計',
        'avg_value_anime_meanScore': 'anime_meanScore平均'
    }
    
    # 数値フォーマット
    numeric_columns = ['studios_count', 'count_per_year', 'anime_favorites', 'meanScore'] + stat_columns
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = display_data[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "")
    
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
        
    return filtered_data

def show_studios_statistics_tab(data):
    """スタジオ基礎統計タブの表示"""
    st.header("📊 スタジオ 基礎統計")
    st.markdown("**このタブでは選択された条件に基づくスタジオの基礎統計情報を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 年度選択
        if 'seasonYear' in data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(data, 'seasonYear')]
            selected_year = st.selectbox("年度", years, key="studios_stats_year")
        else:
            selected_year = "全て"
    
    with col2:
        # 季節選択
        if 'season' in data.columns:
            seasons = ["全て"] + get_unique_values(data, 'season')
            selected_season = st.selectbox("季節", seasons, key="studios_stats_season")
        else:
            selected_season = "全て"
    
    with col3:
        # 原作選択
        if 'source' in data.columns:
            sources = ["全て"] + get_unique_values(data, 'source')
            selected_source = st.selectbox("原作", sources, key="studios_stats_source")
        else:
            selected_source = "全て"
    
    # 追加フィルター
    col4, col5 = st.columns(2)
    
    with col4:
        # フォーマット選択
        if 'format' in data.columns:
            formats = ["全て"] + get_unique_values(data, 'format')
            selected_format = st.selectbox("フォーマット", formats, key="studios_stats_format")
        else:
            selected_format = "全て"
    
    with col5:
        # ジャンル選択（データベースから取得）
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        
        if db_path.exists():
            available_genres = get_genres_data(db_path)
            genres_options = ["全て"] + available_genres
            selected_genre_filter = st.selectbox("ジャンル", genres_options, key="studios_stats_genre")
        else:
            selected_genre_filter = st.selectbox("ジャンル", ["全て"], key="studios_stats_genre")
    
    # フィルター適用
    filters = {}
    if selected_year != "全て":
        try:
            filters['seasonYear'] = float(selected_year)
        except ValueError:
            pass
    if selected_season != "全て":
        filters['season'] = selected_season
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_genre_filter != "全て":
        filters['genre'] = selected_genre_filter
    
    # フィルター適用（ジャンルフィルターはanilist_idベースで処理）
    filtered_data = data.copy()
    
    # ジャンルフィルターの処理
    if 'genre' in filters and filters['genre']:
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
                filtered_data = filtered_data.iloc[0:0]
        except Exception as e:
            st.error(f"ジャンルフィルター適用エラー: {e}")
    
    # その他のフィルター処理
    for key, value in filters.items():
        if key != 'genre' and value and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
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
    """声優基礎統計タブの表示 - 3つの指標の基礎統計"""
    st.header("📊 声優 基礎統計")
    st.markdown("**このタブでは声優のお気に入り数、回数、平均回数の基礎統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 年代選択
        decade_options = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decade_options, key="va_stats_decade")
    
    with col2:
        # フォーマット選択
        format_options = ["全て"] + get_unique_values(data, 'format')
        selected_format = st.selectbox("フォーマット", format_options, key="va_stats_format")
    
    with col3:
        # 原作選択
        source_options = ["全て"] + get_unique_values(data, 'source')
        selected_source = st.selectbox("原作", source_options, key="va_stats_source")
    
    with col4:
        # ジャンル選択
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        if db_path.exists():
            available_genres = get_genres_data(db_path)
            genre_options = ["全て"] + available_genres
        else:
            genre_options = ["全て"]
        selected_genre = st.selectbox("ジャンル", genre_options, key="va_stats_genre")
    
    # データ型変換
    data['va_favorites'] = pd.to_numeric(data['va_favorites'], errors='coerce')
    data['voiceactor_count'] = pd.to_numeric(data['voiceactor_count'], errors='coerce')
    data['count_per_year'] = pd.to_numeric(data['count_per_year'], errors='coerce')
    data['seasonYear'] = pd.to_numeric(data['seasonYear'], errors='coerce')
    
    # フィルター適用
    filters = {}
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_genre != "全て":
        filters['genre'] = selected_genre
    
    filtered_data = filter_data(data, filters, db_path=db_path)
    
    # 年代フィルター適用
    if selected_decade != "全期間":
        filtered_data = create_decade_filter(filtered_data, selected_decade, year_column='seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 声優IDごとに集約（重複削除）
    va_aggregated = filtered_data.groupby('voiceactor_id').agg({
        'va_favorites': 'first',
        'voiceactor_count': 'first',
        'count_per_year': 'first'
    }).reset_index()
    
    # 3つの指標の統計計算
    def calculate_basic_stats(series):
        """基礎統計を計算"""
        series = series.dropna()
        if len(series) == 0:
            return {}
        
        stats = {
            "合計": float(series.sum()),
            "カウント": int(len(series)),
            "最大": float(series.max()),
            "最小": float(series.min()),
            "平均": float(series.mean()),
            "中央値": float(series.median()),
            "1/4分位": float(series.quantile(0.25)),
            "3/4分位": float(series.quantile(0.75))
        }
        
        if len(series) > 1:
            stats["標準偏差"] = float(series.std())
            stats["分散"] = float(series.var())
        else:
            stats["標準偏差"] = 0.0
            stats["分散"] = 0.0
        
        return stats
    
    # 統計情報の表示
    st.subheader(f"📈 声優統計（{len(va_aggregated):,}名）")
    
    # 表1: お気に入り数の統計
    st.markdown("### 📊 表1: お気に入り数の基礎統計")
    favorites_stats = calculate_basic_stats(va_aggregated['va_favorites'])
    if favorites_stats:
        favorites_df = pd.DataFrame(
            [(key, value) for key, value in favorites_stats.items()],
            columns=["統計項目", "お気に入り数"]
        )
        st.dataframe(favorites_df, use_container_width=True, height=400)
    else:
        st.warning("お気に入り数のデータがありません")
    
    # 表2: 回数の統計
    st.markdown("### 📊 表2: 回数の基礎統計")
    count_stats = calculate_basic_stats(va_aggregated['voiceactor_count'])
    if count_stats:
        count_df = pd.DataFrame(
            [(key, value) for key, value in count_stats.items()],
            columns=["統計項目", "回数"]
        )
        st.dataframe(count_df, use_container_width=True, height=400)
    else:
        st.warning("回数のデータがありません")
    
    # 表3: 平均回数の統計
    st.markdown("### 📊 表3: 平均回数の基礎統計")
    avg_count_stats = calculate_basic_stats(va_aggregated['count_per_year'])
    if avg_count_stats:
        avg_count_df = pd.DataFrame(
            [(key, value) for key, value in avg_count_stats.items()],
            columns=["統計項目", "平均回数"]
        )
        st.dataframe(avg_count_df, use_container_width=True, height=400)
    else:
        st.warning("平均回数のデータがありません")

def show_staff_statistics_tab(data):
    """スタッフ基礎統計タブの表示 - 3つの指標の基礎統計"""
    st.header("📊 スタッフ 基礎統計")
    st.markdown("**このタブではスタッフのお気に入り数、回数、平均回数の基礎統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # 役割選択
        role_options = ["全て"] + get_unique_values(data, 'role')
        selected_role = st.selectbox("役割", role_options, key="staff_stats_role")
    
    with col2:
        # 年代選択
        decade_options = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decade_options, key="staff_stats_decade")
    
    with col3:
        # フォーマット選択
        format_options = ["全て"] + get_unique_values(data, 'format')
        selected_format = st.selectbox("フォーマット", format_options, key="staff_stats_format")
    
    with col4:
        # 原作選択
        source_options = ["全て"] + get_unique_values(data, 'source')
        selected_source = st.selectbox("原作", source_options, key="staff_stats_source")
    
    with col5:
        # ジャンル選択
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        if db_path.exists():
            available_genres = get_genres_data(db_path)
            genre_options = ["全て"] + available_genres
        else:
            genre_options = ["全て"]
        selected_genre = st.selectbox("ジャンル", genre_options, key="staff_stats_genre")
    
    # データ型変換
    data['staff_favorites'] = pd.to_numeric(data['staff_favorites'], errors='coerce')
    data['staff_count'] = pd.to_numeric(data['staff_count'], errors='coerce')
    data['count_per_year'] = pd.to_numeric(data['count_per_year'], errors='coerce')
    data['seasonYear'] = pd.to_numeric(data['seasonYear'], errors='coerce')
    
    # フィルター適用
    filtered_data = data.copy()
    
    # 役割フィルター
    if selected_role != "全て":
        filtered_data = filtered_data[filtered_data['role'] == selected_role]
    
    # その他のフィルター
    filters = {}
    if selected_format != "全て":
        filters['format'] = selected_format
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_genre != "全て":
        filters['genre'] = selected_genre
    
    filtered_data = filter_data(filtered_data, filters, db_path=db_path)
    
    # 年代フィルター適用
    if selected_decade != "全期間":
        filtered_data = create_decade_filter(filtered_data, selected_decade, year_column='seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # スタッフIDごとに集約（重複削除）
    staff_aggregated = filtered_data.groupby('staff_id').agg({
        'staff_favorites': 'first',
        'staff_count': 'first',
        'count_per_year': 'first'
    }).reset_index()
    
    # 3つの指標の統計計算
    def calculate_basic_stats(series):
        """基礎統計を計算"""
        series = series.dropna()
        if len(series) == 0:
            return {}
        
        stats = {
            "合計": float(series.sum()),
            "カウント": int(len(series)),
            "最大": float(series.max()),
            "最小": float(series.min()),
            "平均": float(series.mean()),
            "中央値": float(series.median()),
            "1/4分位": float(series.quantile(0.25)),
            "3/4分位": float(series.quantile(0.75))
        }
        
        if len(series) > 1:
            stats["標準偏差"] = float(series.std())
            stats["分散"] = float(series.var())
        else:
            stats["標準偏差"] = 0.0
            stats["分散"] = 0.0
        
        return stats
    
    # 統計情報の表示
    st.subheader(f"📈 スタッフ統計（{len(staff_aggregated):,}名）")
    
    # 表1: お気に入り数の統計
    st.markdown("### 📊 表1: お気に入り数の基礎統計")
    favorites_stats = calculate_basic_stats(staff_aggregated['staff_favorites'])
    if favorites_stats:
        favorites_df = pd.DataFrame(
            [(key, value) for key, value in favorites_stats.items()],
            columns=["統計項目", "お気に入り数"]
        )
        st.dataframe(favorites_df, use_container_width=True, height=400)
    else:
        st.warning("お気に入り数のデータがありません")
    
    # 表2: 回数の統計
    st.markdown("### 📊 表2: 回数の基礎統計")
    count_stats = calculate_basic_stats(staff_aggregated['staff_count'])
    if count_stats:
        count_df = pd.DataFrame(
            [(key, value) for key, value in count_stats.items()],
            columns=["統計項目", "回数"]
        )
        st.dataframe(count_df, use_container_width=True, height=400)
    else:
        st.warning("回数のデータがありません")
    
    # 表3: 平均回数の統計
    st.markdown("### 📊 表3: 平均回数の基礎統計")
    avg_count_stats = calculate_basic_stats(staff_aggregated['count_per_year'])
    if avg_count_stats:
        avg_count_df = pd.DataFrame(
            [(key, value) for key, value in avg_count_stats.items()],
            columns=["統計項目", "平均回数"]
        )
        st.dataframe(avg_count_df, use_container_width=True, height=400)
    else:
        st.warning("平均回数のデータがありません")

def calculate_basic_stats(series):
    """基礎統計を計算（グローバルヘルパー関数）"""
    series = series.dropna()
    if len(series) == 0:
        return {}
    
    stats = {
        "合計": float(series.sum()),
        "カウント": int(len(series)),
        "最大": float(series.max()),
        "最小": float(series.min()),
        "平均": float(series.mean()),
        "中央値": float(series.median()),
        "1/4分位": float(series.quantile(0.25)),
        "3/4分位": float(series.quantile(0.75))
    }
    
    if len(series) > 1:
        stats["標準偏差"] = float(series.std())
        stats["分散"] = float(series.var())
    else:
        stats["標準偏差"] = 0.0
        stats["分散"] = 0.0
    
    return stats

def show_character_statistics_tab(data):
    """キャラクター基礎統計タブの表示 - キャラクターお気に入り数のみ"""
    st.header("📊 キャラクター 基礎統計")
    st.markdown("**このタブではキャラクターのお気に入り数の全体統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # char_favoritesカラムの確認とデータ型変換
    if 'char_favorites' not in data.columns:
        st.error("char_favoritesカラムが見つかりません。")
        return
    
    data['char_favorites'] = pd.to_numeric(data['char_favorites'], errors='coerce')
    
    # 統計情報の計算
    char_favorites_data = data['char_favorites'].dropna()
    
    if len(char_favorites_data) == 0:
        st.warning("キャラクターお気に入り数のデータがありません。")
        return
    
    stats = calculate_basic_stats(char_favorites_data)
    
    # 統計情報の表示
    st.subheader(f"📈 キャラクターお気に入り数の統計（{len(char_favorites_data):,}件）")
    
    # 全体統計
    st.markdown("### 📊 全体統計")
    overall_stats_df = pd.DataFrame(
        [(key, value) for key, value in stats.items()],
        columns=["統計項目", "値"]
    )
    st.dataframe(overall_stats_df, use_container_width=True, height=400)

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
        # 年代選択
        decades = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decades, key="stats_decade")
    
    with col3:
        # フォーマット選択（ユニークな要素から動的生成）
        if 'format' in data.columns:
            unique_formats = sorted(data['format'].dropna().unique())
            formats = ["全て"] + list(unique_formats)
            selected_format = st.selectbox("フォーマット", formats, key="stats_format")
        else:
            selected_format = "全て"
    
    # フィルター適用
    filters = {}
    if selected_format != "全て":
        filters['format'] = selected_format
    
    # データベースパスを絶対パスで指定
    if genre == "アニメ":
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
    else:
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
    
    # 通常のフィルター適用
    filtered_data = filter_data(data, filters, db_path if db_path.exists() else None)
    
    # 年代フィルター適用（アニメはseasonYear、マンガはseasonYear）
    year_column = 'seasonYear' 
    filtered_data = create_decade_filter(filtered_data, selected_decade, year_column)
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # フィルター適用後のデータ件数を取得
    filtered_count = len(filtered_data)
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果 ({filtered_count:,}件)")
    st.markdown(f"**選択年代**: {selected_decade} | **選択フォーマット**: {selected_format}")
    
    # 期間別統計を計算
    stats_result = calculate_statistics_by_period(filtered_data, selected_metric, year_column)
    
    if stats_result is None:
        st.error(f"選択された条件では{metric_labels.get(selected_metric, selected_metric)}のデータが存在しません。")
        return
    
    # 1. 全期間の基礎統計表
    st.markdown("---")
    st.subheader("📊 表1: 全期間の基礎統計")
    overall_df = pd.DataFrame(
        [(key, value) for key, value in stats_result['overall'].items()],
        columns=["統計項目", "値"]
    )
    # 数値型に変換
    for col in overall_df.columns:
        if col != "統計項目":
            overall_df[col] = pd.to_numeric(overall_df[col], errors='ignore')
    st.dataframe(overall_df, width='stretch', height=300)
    
    # 2. 年代別の基礎統計（全期間選択時のみ表示）
    if selected_decade == "全期間" and not stats_result['decade'].empty:
        st.markdown("---")
        st.subheader("📊 表2: 年代別の基礎統計")
        decade_df = stats_result['decade'].copy()
        # 数値型に変換
        for col in decade_df.columns:
            if col != "年代":
                decade_df[col] = pd.to_numeric(decade_df[col], errors='ignore')
        st.dataframe(decade_df, width='stretch', height=300)
        
        # 年代別推移グラフ
        st.markdown("---")
        st.subheader("📈 年代別推移グラフ")
        
        # グラフ用データの準備
        plot_data = decade_df.copy()
        
        # 選択指標の推移グラフ
        fig = go.Figure()
        
        # 平均値の推移
        fig.add_trace(go.Scatter(
            x=plot_data['年代'],
            y=plot_data['平均'],
            mode='lines+markers',
            name=f'{metric_labels.get(selected_metric, selected_metric)} 平均',
            line=dict(width=3, color='#1f77b4')
        ))
        
        # カウント数の推移（右軸）
        fig.add_trace(go.Scatter(
            x=plot_data['年代'],
            y=plot_data['カウント'],
            mode='lines+markers',
            name='タイトル数',
            line=dict(width=2, dash='dash', color='#ff7f0e'),
            yaxis='y2'
        ))
        
        # レイアウト設定（2軸）
        fig.update_layout(
            title=f'年代別推移 - {metric_labels.get(selected_metric, selected_metric)}',
            xaxis=dict(title='年代'),
            yaxis=dict(
                title=f'{metric_labels.get(selected_metric, selected_metric)}',
                side='left'
            ),
            yaxis2=dict(
                title='タイトル数',
                overlaying='y',
                side='right'
            ),
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 3. 選択期間の合計統計（全期間以外の場合のみ表示）
    if selected_decade != "全期間":
        st.markdown("---")
        st.subheader(f"📊 表2: {selected_decade}の合計統計")
        period_df = pd.DataFrame(
            [(key, value) for key, value in stats_result['period_total'].items()],
            columns=["統計項目", "値"]
        )
        # 数値型に変換
        for col in period_df.columns:
            if col != "統計項目":
                period_df[col] = pd.to_numeric(period_df[col], errors='ignore')
        st.dataframe(period_df, width='stretch', height=300)
    
    # 4. 1年ごとの基礎統計表（全期間以外の場合のみ表示）
    if selected_decade != "全期間" and not stats_result['yearly'].empty:
        st.markdown("---")
        st.subheader("📊 表3: 1年ごとの基礎統計")
        yearly_df = stats_result['yearly'].copy()
        # 数値型に変換
        for col in yearly_df.columns:
            if col != "年度":
                yearly_df[col] = pd.to_numeric(yearly_df[col], errors='ignore')
        st.dataframe(yearly_df, width='stretch', height=400)
        
        # 年別推移グラフ
        st.markdown("---")
        st.subheader("📈 年別推移グラフ")
        
        # グラフ用データの準備（年度を昇順にソート）
        plot_data = yearly_df.sort_values('年度')
        
        # 選択指標の推移グラフ
        fig = go.Figure()
        
        # 平均値の推移
        fig.add_trace(go.Scatter(
            x=plot_data['年度'],
            y=plot_data['平均'],
            mode='lines+markers',
            name=f'{metric_labels.get(selected_metric, selected_metric)} 平均',
            line=dict(width=3, color='#1f77b4')
        ))
        
        # カウント数の推移（右軸）
        fig.add_trace(go.Scatter(
            x=plot_data['年度'],
            y=plot_data['カウント'],
            mode='lines+markers',
            name='タイトル数',
            line=dict(width=2, dash='dash', color='#ff7f0e'),
            yaxis='y2'
        ))
        
        # レイアウト設定（2軸）
        fig.update_layout(
            title=f'{selected_decade}の年別推移 - {metric_labels.get(selected_metric, selected_metric)}',
            xaxis=dict(title='年度'),
            yaxis=dict(
                title=f'{metric_labels.get(selected_metric, selected_metric)}',
                side='left'
            ),
            yaxis2=dict(
                title='タイトル数',
                overlaying='y',
                side='right'
            ),
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_genre_statistics_tab(data):
    """ジャンル基礎統計タブの表示"""
    st.header("🎭 ジャンル 基礎統計")
    st.markdown("**このタブでは全ジャンルの基礎統計情報を一括表示します**")
    
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
            key="genre_stats_metric"
        )
    
    with col2:
        # 年代選択
        decades = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decades, key="genre_stats_decade")
    
    with col3:
        # フォーマット選択（ユニークな要素から動的生成）
        if 'format' in data.columns:
            unique_formats = sorted(data['format'].dropna().unique())
            formats = ["全て"] + list(unique_formats)
            selected_format = st.selectbox("フォーマット", formats, key="genre_stats_format")
        else:
            selected_format = "全て"
    
    # フォーマットフィルター適用
    filtered_data = data.copy()
    if selected_format != "全て":
        filtered_data = filtered_data[filtered_data['format'] == selected_format]
    
    # 年代フィルター適用
    filtered_data = create_decade_filter(filtered_data, selected_decade, 'seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 全ジャンルのユニークリストを取得
    if 'genre_name' not in filtered_data.columns:
        st.error("ジャンルデータが利用できません。")
        return
    
    unique_genres = sorted(filtered_data['genre_name'].dropna().unique())
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果")
    st.markdown(f"**選択年代**: {selected_decade} | **選択フォーマット**: {selected_format} | **ジャンル数**: {len(unique_genres)}種類")
    
    # 各ジャンルの統計を計算
    genre_stats_list = []
    
    for genre in unique_genres:
        genre_data = filtered_data[filtered_data['genre_name'] == genre].copy()
        
        if genre_data.empty:
            continue
        
        # 指標の値を取得
        metric_values = pd.to_numeric(genre_data[selected_metric], errors='coerce').dropna()
        
        if len(metric_values) == 0:
            continue
        
        # 統計を計算
        stats = {
            'ジャンル': genre,
            '合計': metric_values.sum(),
            'カウント': len(metric_values),
            '最大': metric_values.max(),
            '最小': metric_values.min(),
            '平均': metric_values.mean(),
            '中央値': metric_values.median(),
            '1/4分位': metric_values.quantile(0.25),
            '3/4分位': metric_values.quantile(0.75),
            '標準偏差': metric_values.std(),
            '分散': metric_values.var()
        }
        genre_stats_list.append(stats)
    
    if not genre_stats_list:
        st.warning("選択された条件に一致する統計データがありません。")
        return
    
    # DataFrameに変換
    genre_stats_df = pd.DataFrame(genre_stats_list)
    
    # 数値型に変換
    for col in genre_stats_df.columns:
        if col != "ジャンル":
            genre_stats_df[col] = pd.to_numeric(genre_stats_df[col], errors='ignore')
    
    # 1. 全ジャンルの基礎統計表（平均でソート）
    st.markdown("---")
    st.subheader(f"📊 表1: 全ジャンルの基礎統計 ({selected_metric})")
    sorted_df = genre_stats_df.sort_values('平均', ascending=False)
    st.dataframe(sorted_df, width='stretch', height=600)
    
    # 2. 年代別・年次別の詳細統計（全期間以外の場合）
    if selected_decade != "全期間":
        st.markdown("---")
        st.subheader(f"📊 表2: {selected_decade} - 各年度のジャンル別統計")
        
        # 年度ごとにジャンル別統計を計算
        if 'seasonYear' in filtered_data.columns:
            # 年度のユニークリストを取得（降順）
            years = sorted(filtered_data['seasonYear'].dropna().unique(), reverse=True)
            
            # 各年度の統計を計算
            yearly_genre_stats = []
            
            for year in years:
                year_data = filtered_data[filtered_data['seasonYear'] == year]
                
                for genre in unique_genres:
                    genre_year_data = year_data[year_data['genre_name'] == genre]
                    
                    if genre_year_data.empty:
                        continue
                    
                    metric_values = pd.to_numeric(genre_year_data[selected_metric], errors='coerce').dropna()
                    
                    if len(metric_values) == 0:
                        continue
                    
                    stats = {
                        '年度': int(year),
                        'ジャンル': genre,
                        '合計': metric_values.sum(),
                        'カウント': len(metric_values),
                        '最大': metric_values.max(),
                        '最小': metric_values.min(),
                        '平均': metric_values.mean(),
                        '中央値': metric_values.median(),
                        '1/4分位': metric_values.quantile(0.25),
                        '3/4分位': metric_values.quantile(0.75),
                        '標準偏差': metric_values.std(),
                        '分散': metric_values.var()
                    }
                    yearly_genre_stats.append(stats)
            
            if yearly_genre_stats:
                yearly_genre_df = pd.DataFrame(yearly_genre_stats)
                
                # 数値型に変換
                for col in yearly_genre_df.columns:
                    if col not in ["年度", "ジャンル"]:
                        yearly_genre_df[col] = pd.to_numeric(yearly_genre_df[col], errors='ignore')
                
                st.dataframe(yearly_genre_df, width='stretch', height=600)
                
                # 年度別推移グラフ（上位5ジャンルのみ）
                st.markdown("---")
                st.subheader(f"📈 年度別推移 - 上位5ジャンル")
                
                # 全体で平均が高い上位5ジャンルを取得
                top_5_genres = sorted_df.head(5)['ジャンル'].tolist()
                
                # 上位5ジャンルのデータのみフィルター
                top_5_data = yearly_genre_df[yearly_genre_df['ジャンル'].isin(top_5_genres)]
                
                if not top_5_data.empty:
                    fig = px.line(
                        top_5_data,
                        x='年度',
                        y='平均',
                        color='ジャンル',
                        markers=True,
                        title=f'{selected_decade} - 上位5ジャンルの年度別推移',
                        labels={
                            '年度': '年度',
                            '平均': metric_labels.get(selected_metric, selected_metric)
                        }
                    )
                    fig.update_layout(height=500, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # ヒートマップ（年度 x ジャンル）
                    st.markdown("---")
                    st.subheader(f"🔥 ヒートマップ - 年度別ジャンル平均値")
                    
                    # ピボットテーブル作成
                    pivot_data = top_5_data.pivot(index='ジャンル', columns='年度', values='平均')
                    
                    fig_heatmap = px.imshow(
                        pivot_data,
                        labels=dict(x="年度", y="ジャンル", color=metric_labels.get(selected_metric, selected_metric)),
                        x=pivot_data.columns,
                        y=pivot_data.index,
                        color_continuous_scale='RdYlBu_r',
                        aspect='auto'
                    )
                    fig_heatmap.update_layout(height=400)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("選択された年代のデータがありません。")
    
    # 3. 上位・下位ジャンルの可視化
    st.markdown("---")
    st.subheader("📊 上位・下位ジャンル比較")
    
    # 上位10ジャンル
    top_10 = sorted_df.head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**上位10ジャンル ({metric_labels.get(selected_metric, selected_metric)})**")
        fig_top = px.bar(
            top_10,
            x='平均',
            y='ジャンル',
            orientation='h',
            text='平均',
            color='平均',
            color_continuous_scale='Blues'
        )
        fig_top.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_top.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        # 下位10ジャンル
        bottom_10 = sorted_df.tail(10)
        st.markdown(f"**下位10ジャンル ({metric_labels.get(selected_metric, selected_metric)})**")
        fig_bottom = px.bar(
            bottom_10,
            x='平均',
            y='ジャンル',
            orientation='h',
            text='平均',
            color='平均',
            color_continuous_scale='Reds'
        )
        fig_bottom.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bottom.update_layout(
            height=400,
            yaxis={'categoryorder': 'total descending'},
            showlegend=False
        )
        st.plotly_chart(fig_bottom, use_container_width=True)
    
    # 4. 全ジャンルの平均値分布
    st.markdown("---")
    st.subheader("📊 全ジャンルの分布")
    
    fig_dist = px.histogram(
        genre_stats_df,
        x='平均',
        nbins=30,
        title=f'{metric_labels.get(selected_metric, selected_metric)}の分布',
        labels={'平均': metric_labels.get(selected_metric, selected_metric), 'count': 'ジャンル数'}
    )
    fig_dist.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # 5. カウント vs 平均の散布図
    st.markdown("---")
    st.subheader("📊 タイトル数 vs 平均値")
    
    fig_scatter = px.scatter(
        genre_stats_df,
        x='カウント',
        y='平均',
        text='ジャンル',
        size='カウント',
        color='平均',
        color_continuous_scale='Viridis',
        labels={
            'カウント': 'タイトル数',
            '平均': metric_labels.get(selected_metric, selected_metric)
        },
        title=f'ジャンル別タイトル数と{metric_labels.get(selected_metric, selected_metric)}の関係'
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)


def show_manga_character_statistics_tab(data):
    """マンガキャラクター基礎統計タブの表示 - キャラクターお気に入り数のみ"""
    st.header("📚 マンガキャラクター 基礎統計")
    st.markdown("**このタブではキャラクターのお気に入り数の全体統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # char_favoritesカラムの確認とデータ型変換
    if 'char_favorites' not in data.columns:
        st.error("char_favoritesカラムが見つかりません。")
        return
    
    data['char_favorites'] = pd.to_numeric(data['char_favorites'], errors='coerce')
    
    # 統計情報の計算
    char_favorites_data = data['char_favorites'].dropna()
    
    if len(char_favorites_data) == 0:
        st.warning("キャラクターお気に入り数のデータがありません。")
        return
    
    stats = calculate_basic_stats(char_favorites_data)
    
    # 統計情報の表示
    st.subheader(f"📈 キャラクターお気に入り数の統計（{len(char_favorites_data):,}件）")
    
    # 全体統計
    st.markdown("### 📊 全体統計")
    overall_stats_df = pd.DataFrame(
        [(key, value) for key, value in stats.items()],
        columns=["統計項目", "値"]
    )
    st.dataframe(overall_stats_df, use_container_width=True, height=400)

def show_manga_staff_statistics_tab(data):
    """マンガスタッフ基礎統計タブの表示"""
    st.header("📚 マンガスタッフ 基礎統計")
    st.markdown("**このタブではスタッフのお気に入り数、回数、平均回数の基礎統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 役割選択
        role_options = ["全て"] + sorted(data['role'].dropna().unique().tolist())
        selected_role = st.selectbox("役割", role_options, key="manga_staff_stats_role")
    
    with col2:
        # 年代選択
        decade_options = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decade_options, key="manga_staff_stats_decade")
    
    with col3:
        # フォーマット選択
        format_options = ["全て"] + get_unique_values(data, 'format')
        selected_format = st.selectbox("フォーマット", format_options, key="manga_staff_stats_format")
    
    with col4:
        # ジャンル選択
        db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT genre_name FROM genres ORDER BY genre_name")
                available_genres = [row[0] for row in cursor.fetchall()]
                conn.close()
                genre_options = ["全て"] + available_genres
            except:
                genre_options = ["全て"]
        else:
            genre_options = ["全て"]
        selected_genre = st.selectbox("ジャンル", genre_options, key="manga_staff_stats_genre")
    
    # データ型変換
    data['staff_favorites'] = pd.to_numeric(data['staff_favorites'], errors='coerce')
    data['seasonYear'] = pd.to_numeric(data['seasonYear'], errors='coerce')
    
    # staff_count と count_per_year の処理
    if 'staff_count' in data.columns:
        data['staff_count'] = pd.to_numeric(data['staff_count'], errors='coerce')
    if 'count_per_year' in data.columns:
        data['count_per_year'] = pd.to_numeric(data['count_per_year'], errors='coerce')
    
    # フィルター適用
    filtered_data = data.copy()
    
    if selected_role != "全て":
        filtered_data = filtered_data[filtered_data['role'] == selected_role]
    
    if selected_format != "全て":
        filtered_data = filtered_data[filtered_data['format'] == selected_format]
    
    # ジャンルフィルター
    if selected_genre != "全て":
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT anilist_id 
                FROM genres 
                WHERE genre_name = ?
            """, (selected_genre,))
            genre_manga_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if genre_manga_ids:
                filtered_data = filtered_data[filtered_data['anilist_id'].isin(genre_manga_ids)]
            else:
                filtered_data = filtered_data.iloc[0:0]
        except Exception as e:
            st.error(f"ジャンルフィルター適用エラー: {e}")
    
    # 年代フィルター適用
    if selected_decade != "全期間":
        filtered_data = create_decade_filter(filtered_data, selected_decade, year_column='seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # スタッフIDでグループ化して集計
    staff_aggregated = filtered_data.groupby('staff_id').agg({
        'staff_name': 'first',
        'staff_favorites': 'first',
        'staff_count': 'first' if 'staff_count' in filtered_data.columns else lambda x: len(x),
        'count_per_year': 'first' if 'count_per_year' in filtered_data.columns else lambda x: len(x) / max((filtered_data.loc[x.index, 'seasonYear'].max() - filtered_data.loc[x.index, 'seasonYear'].min() + 1), 1)
    }).reset_index()
    
    # staff_count と count_per_year が存在しない場合の処理
    if 'staff_count' not in data.columns:
        # 各スタッフの出演回数を計算
        staff_counts = filtered_data.groupby('staff_id').size().reset_index(name='staff_count')
        staff_aggregated = staff_aggregated.merge(staff_counts, on='staff_id', how='left', suffixes=('', '_new'))
        if 'staff_count_new' in staff_aggregated.columns:
            staff_aggregated['staff_count'] = staff_aggregated['staff_count_new']
            staff_aggregated.drop('staff_count_new', axis=1, inplace=True)
    
    if 'count_per_year' not in data.columns:
        # 各スタッフの平均回数を計算
        def calc_count_per_year(group):
            years = group['seasonYear'].dropna()
            if len(years) == 0:
                return 0
            year_range = years.max() - years.min() + 1
            return len(group) / max(year_range, 1)
        
        count_per_year_data = filtered_data.groupby('staff_id').apply(calc_count_per_year).reset_index(name='count_per_year')
        staff_aggregated = staff_aggregated.merge(count_per_year_data, on='staff_id', how='left', suffixes=('', '_new'))
        if 'count_per_year_new' in staff_aggregated.columns:
            staff_aggregated['count_per_year'] = staff_aggregated['count_per_year_new']
            staff_aggregated.drop('count_per_year_new', axis=1, inplace=True)
    
    # 3つの指標の統計計算用ヘルパー関数
    def calculate_basic_stats_for_staff(series):
        """基礎統計を計算"""
        series = series.dropna()
        if len(series) == 0:
            return {}
        
        stats = {
            "合計": float(series.sum()),
            "カウント": int(len(series)),
            "最大": float(series.max()),
            "最小": float(series.min()),
            "平均": float(series.mean()),
            "中央値": float(series.median()),
            "1/4分位": float(series.quantile(0.25)),
            "3/4分位": float(series.quantile(0.75))
        }
        
        if len(series) > 1:
            stats["標準偏差"] = float(series.std())
            stats["分散"] = float(series.var())
        else:
            stats["標準偏差"] = 0.0
            stats["分散"] = 0.0
        
        return stats
    
    # 統計情報の表示
    st.subheader(f"📈 スタッフ統計（{len(staff_aggregated):,}名）")
    
    # 3つの指標を行として表示
    st.markdown("### 📊 基礎統計（全期間）")
    
    # 各指標の統計を計算
    favorites_stats = calculate_basic_stats_for_staff(staff_aggregated['staff_favorites'])
    count_stats = calculate_basic_stats_for_staff(staff_aggregated['staff_count'])
    avg_count_stats = calculate_basic_stats_for_staff(staff_aggregated['count_per_year'])
    
    # データフレームを作成（行: 指標、列: 統計項目）
    stats_data = {
        "指標": ["お気に入り数", "回数", "平均回数"],
        "合計": [favorites_stats.get("合計", 0), count_stats.get("合計", 0), avg_count_stats.get("合計", 0)],
        "カウント": [favorites_stats.get("カウント", 0), count_stats.get("カウント", 0), avg_count_stats.get("カウント", 0)],
        "最大": [favorites_stats.get("最大", 0), count_stats.get("最大", 0), avg_count_stats.get("最大", 0)],
        "最小": [favorites_stats.get("最小", 0), count_stats.get("最小", 0), avg_count_stats.get("最小", 0)],
        "平均": [favorites_stats.get("平均", 0), count_stats.get("平均", 0), avg_count_stats.get("平均", 0)],
        "中央値": [favorites_stats.get("中央値", 0), count_stats.get("中央値", 0), avg_count_stats.get("中央値", 0)],
        "1/4分位": [favorites_stats.get("1/4分位", 0), count_stats.get("1/4分位", 0), avg_count_stats.get("1/4分位", 0)],
        "3/4分位": [favorites_stats.get("3/4分位", 0), count_stats.get("3/4分位", 0), avg_count_stats.get("3/4分位", 0)],
        "標準偏差": [favorites_stats.get("標準偏差", 0), count_stats.get("標準偏差", 0), avg_count_stats.get("標準偏差", 0)],
        "分散": [favorites_stats.get("分散", 0), count_stats.get("分散", 0), avg_count_stats.get("分散", 0)]
    }
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True, height=150)
    
    # 全期間選択時は年代別統計を追加表示
    if selected_decade == "全期間":
        st.markdown("### 📅 年代別基礎統計")
        
        # 年代を追加
        def assign_decade(year):
            if pd.isna(year):
                return None
            year = int(year)
            if year < 2000:
                return "1900年代"
            elif year < 2010:
                return "2000年代"
            elif year < 2020:
                return "2010年代"
            else:
                return "2020年代"
        
        filtered_data['decade'] = filtered_data['seasonYear'].apply(assign_decade)
        
        # 年代ごとに統計を計算
        decade_stats_list = []
        
        for decade in ["1900年代", "2000年代", "2010年代", "2020年代"]:
            decade_data = filtered_data[filtered_data['decade'] == decade]
            
            if decade_data.empty:
                continue
            
            # 年代ごとにスタッフIDでグループ化
            decade_staff_agg = decade_data.groupby('staff_id').agg({
                'staff_favorites': 'first',
                'staff_count': 'first' if 'staff_count' in decade_data.columns else lambda x: len(x),
                'count_per_year': 'first' if 'count_per_year' in decade_data.columns else lambda x: len(x) / max((decade_data.loc[x.index, 'seasonYear'].max() - decade_data.loc[x.index, 'seasonYear'].min() + 1), 1)
            }).reset_index()
            
            # 各指標の統計を計算
            fav_stats = calculate_basic_stats_for_staff(decade_staff_agg['staff_favorites'])
            cnt_stats = calculate_basic_stats_for_staff(decade_staff_agg['staff_count'])
            avg_stats = calculate_basic_stats_for_staff(decade_staff_agg['count_per_year'])
            
            # 年代別データを追加
            for metric, stats in [("お気に入り数", fav_stats), ("回数", cnt_stats), ("平均回数", avg_stats)]:
                decade_stats_list.append({
                    "年代": decade,
                    "指標": metric,
                    "合計": stats.get("合計", 0),
                    "カウント": stats.get("カウント", 0),
                    "最大": stats.get("最大", 0),
                    "最小": stats.get("最小", 0),
                    "平均": stats.get("平均", 0),
                    "中央値": stats.get("中央値", 0),
                    "1/4分位": stats.get("1/4分位", 0),
                    "3/4分位": stats.get("3/4分位", 0),
                    "標準偏差": stats.get("標準偏差", 0),
                    "分散": stats.get("分散", 0)
                })
        
        if decade_stats_list:
            decade_stats_df = pd.DataFrame(decade_stats_list)
            st.dataframe(decade_stats_df, use_container_width=True)
        else:
            st.info("年代別統計データがありません")

def show_manga_genre_statistics_tab(data):
    """マンガジャンル基礎統計タブの表示"""
    st.header("📚 マンガジャンル 基礎統計")
    st.markdown("**このタブでは全マンガジャンルの基礎統計情報を一括表示します**")
    
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
            key="manga_genre_stats_metric"
        )
    
    with col2:
        # 年代選択
        decades = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decades, key="manga_genre_stats_decade")
    
    with col3:
        # フォーマット選択（ユニークな要素から動的生成）
        if 'format' in data.columns:
            unique_formats = sorted(data['format'].dropna().unique())
            formats = ["全て"] + list(unique_formats)
            selected_format = st.selectbox("フォーマット", formats, key="manga_genre_stats_format")
        else:
            selected_format = "全て"
    
    # フォーマットフィルター適用
    filtered_data = data.copy()
    if selected_format != "全て":
        filtered_data = filtered_data[filtered_data['format'] == selected_format]
    
    # 年代フィルター適用
    filtered_data = create_decade_filter(filtered_data, selected_decade, 'seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 全ジャンルのユニークリストを取得
    if 'genre_name' not in filtered_data.columns:
        st.error("ジャンルデータが利用できません。")
        return
    
    unique_genres = sorted(filtered_data['genre_name'].dropna().unique())
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果")
    st.markdown(f"**選択年代**: {selected_decade} | **選択フォーマット**: {selected_format} | **ジャンル数**: {len(unique_genres)}種類")
    
    # 各ジャンルの統計を計算
    genre_stats_list = []
    
    for genre in unique_genres:
        genre_data = filtered_data[filtered_data['genre_name'] == genre].copy()
        
        if genre_data.empty:
            continue
        
        # 指標の値を取得
        metric_values = pd.to_numeric(genre_data[selected_metric], errors='coerce').dropna()
        
        if len(metric_values) == 0:
            continue
        
        # 統計を計算
        stats = {
            'ジャンル': genre,
            '合計': metric_values.sum(),
            'カウント': len(metric_values),
            '最大': metric_values.max(),
            '最小': metric_values.min(),
            '平均': metric_values.mean(),
            '中央値': metric_values.median(),
            '1/4分位': metric_values.quantile(0.25),
            '3/4分位': metric_values.quantile(0.75),
            '標準偏差': metric_values.std(),
            '分散': metric_values.var()
        }
        genre_stats_list.append(stats)
    
    if not genre_stats_list:
        st.warning("選択された条件に一致する統計データがありません。")
        return
    
    # DataFrameに変換
    genre_stats_df = pd.DataFrame(genre_stats_list)
    
    # 数値型に変換
    for col in genre_stats_df.columns:
        if col != "ジャンル":
            genre_stats_df[col] = pd.to_numeric(genre_stats_df[col], errors='ignore')
    
    # 1. 全ジャンルの基礎統計表（平均でソート）
    st.markdown("---")
    st.subheader(f"📊 表1: 全ジャンルの基礎統計 ({selected_metric})")
    sorted_df = genre_stats_df.sort_values('平均', ascending=False)
    st.dataframe(sorted_df, width='stretch', height=600)
    
    # 2. 年代別・年次別の詳細統計（全期間以外の場合）
    if selected_decade != "全期間":
        st.markdown("---")
        st.subheader(f"📊 表2: {selected_decade} - 各年度のジャンル別統計")
        
        # 年度ごとにジャンル別統計を計算
        if 'seasonYear' in filtered_data.columns:
            # 年度のユニークリストを取得（降順）
            years = sorted(filtered_data['seasonYear'].dropna().unique(), reverse=True)
            
            # 各年度の統計を計算
            yearly_genre_stats = []
            
            for year in years:
                year_data = filtered_data[filtered_data['seasonYear'] == year]
                
                for genre in unique_genres:
                    genre_year_data = year_data[year_data['genre_name'] == genre]
                    
                    if genre_year_data.empty:
                        continue
                    
                    metric_values = pd.to_numeric(genre_year_data[selected_metric], errors='coerce').dropna()
                    
                    if len(metric_values) == 0:
                        continue
                    
                    stats = {
                        '年度': int(year),
                        'ジャンル': genre,
                        '合計': metric_values.sum(),
                        'カウント': len(metric_values),
                        '最大': metric_values.max(),
                        '最小': metric_values.min(),
                        '平均': metric_values.mean(),
                        '中央値': metric_values.median(),
                        '1/4分位': metric_values.quantile(0.25),
                        '3/4分位': metric_values.quantile(0.75),
                        '標準偏差': metric_values.std(),
                        '分散': metric_values.var()
                    }
                    yearly_genre_stats.append(stats)
            
            if yearly_genre_stats:
                yearly_genre_df = pd.DataFrame(yearly_genre_stats)
                
                # 数値型に変換
                for col in yearly_genre_df.columns:
                    if col not in ["年度", "ジャンル"]:
                        yearly_genre_df[col] = pd.to_numeric(yearly_genre_df[col], errors='ignore')
                
                st.dataframe(yearly_genre_df, width='stretch', height=600)
                
                # 年度別推移グラフ（上位5ジャンルのみ）
                st.markdown("---")
                st.subheader(f"📈 年度別推移 - 上位5ジャンル")
                
                # 全体で平均が高い上位5ジャンルを取得
                top_5_genres = sorted_df.head(5)['ジャンル'].tolist()
                
                # 上位5ジャンルのデータのみフィルター
                top_5_data = yearly_genre_df[yearly_genre_df['ジャンル'].isin(top_5_genres)]
                
                if not top_5_data.empty:
                    fig = px.line(
                        top_5_data,
                        x='年度',
                        y='平均',
                        color='ジャンル',
                        markers=True,
                        title=f'{selected_decade} - 上位5ジャンルの年度別推移',
                        labels={
                            '年度': '年度',
                            '平均': metric_labels.get(selected_metric, selected_metric)
                        }
                    )
                    fig.update_layout(height=500, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # ヒートマップ（年度 x ジャンル）
                    st.markdown("---")
                    st.subheader(f"🔥 ヒートマップ - 年度別ジャンル平均値")
                    
                    # ピボットテーブル作成
                    pivot_data = top_5_data.pivot(index='ジャンル', columns='年度', values='平均')
                    
                    fig_heatmap = px.imshow(
                        pivot_data,
                        labels=dict(x="年度", y="ジャンル", color=metric_labels.get(selected_metric, selected_metric)),
                        x=pivot_data.columns,
                        y=pivot_data.index,
                        color_continuous_scale='RdYlBu_r',
                        aspect='auto'
                    )
                    fig_heatmap.update_layout(height=400)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("選択された年代のデータがありません。")
    
    # 3. 上位・下位ジャンルの可視化
    st.markdown("---")
    st.subheader("📊 上位・下位ジャンル比較")
    
    # 上位10ジャンル
    top_10 = sorted_df.head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**上位10ジャンル ({metric_labels.get(selected_metric, selected_metric)})**")
        fig_top = px.bar(
            top_10,
            x='平均',
            y='ジャンル',
            orientation='h',
            text='平均',
            color='平均',
            color_continuous_scale='Blues'
        )
        fig_top.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_top.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    with col2:
        # 下位10ジャンル
        bottom_10 = sorted_df.tail(10)
        st.markdown(f"**下位10ジャンル ({metric_labels.get(selected_metric, selected_metric)})**")
        fig_bottom = px.bar(
            bottom_10,
            x='平均',
            y='ジャンル',
            orientation='h',
            text='平均',
            color='平均',
            color_continuous_scale='Reds'
        )
        fig_bottom.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bottom.update_layout(
            height=400,
            yaxis={'categoryorder': 'total descending'},
            showlegend=False
        )
        st.plotly_chart(fig_bottom, use_container_width=True)
    
    # 4. 全ジャンルの平均値分布
    st.markdown("---")
    st.subheader("📊 全ジャンルの分布")
    
    fig_dist = px.histogram(
        genre_stats_df,
        x='平均',
        nbins=30,
        title=f'{metric_labels.get(selected_metric, selected_metric)}の分布',
        labels={'平均': metric_labels.get(selected_metric, selected_metric), 'count': 'ジャンル数'}
    )
    fig_dist.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # 5. カウント vs 平均の散布図
    st.markdown("---")
    st.subheader("📊 タイトル数 vs 平均値")
    
    fig_scatter = px.scatter(
        genre_stats_df,
        x='カウント',
        y='平均',
        text='ジャンル',
        size='カウント',
        color='平均',
        color_continuous_scale='Viridis',
        labels={
            'カウント': 'タイトル数',
            '平均': metric_labels.get(selected_metric, selected_metric)
        },
        title=f'ジャンル別タイトル数と{metric_labels.get(selected_metric, selected_metric)}の関係'
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)


def show_source_statistics_tab(data):
    """アニメ原作基礎統計タブの表示"""
    st.header("📖 アニメ原作 基礎統計")
    st.markdown("**このタブでは全原作タイプの基礎統計情報を一括表示します**")
    
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
            key="source_stats_metric"
        )
    
    with col2:
        # 年代選択
        decades = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decades, key="source_stats_decade")
    
    with col3:
        # フォーマット選択（ユニークな要素から動的生成）
        if 'format' in data.columns:
            unique_formats = sorted(data['format'].dropna().unique())
            formats = ["全て"] + list(unique_formats)
            selected_format = st.selectbox("フォーマット", formats, key="source_stats_format")
        else:
            selected_format = "全て"
    
    # フォーマットフィルター適用
    filtered_data = data.copy()
    if selected_format != "全て":
        filtered_data = filtered_data[filtered_data['format'] == selected_format]
    
    # 年代フィルター適用
    filtered_data = create_decade_filter(filtered_data, selected_decade, 'seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # 全原作タイプのユニークリストを取得
    if 'source' not in filtered_data.columns:
        st.error("原作データが利用できません。")
        return
    
    unique_sources = sorted(filtered_data['source'].dropna().unique())
    
    # 統計情報表示
    st.subheader(f"📈 統計分析結果")
    st.markdown(f"**選択年代**: {selected_decade} | **選択フォーマット**: {selected_format} | **原作タイプ数**: {len(unique_sources)}種類")
    
    # 各原作タイプの統計を計算
    source_stats_list = []
    
    for source in unique_sources:
        source_data = filtered_data[filtered_data['source'] == source].copy()
        
        if source_data.empty:
            continue
        
        # 指標の値を取得
        metric_values = pd.to_numeric(source_data[selected_metric], errors='coerce').dropna()
        
        if len(metric_values) == 0:
            continue
        
        # 統計を計算
        stats = {
            '原作': source,
            '合計': metric_values.sum(),
            'カウント': len(metric_values),
            '最大': metric_values.max(),
            '最小': metric_values.min(),
            '平均': metric_values.mean(),
            '中央値': metric_values.median(),
            '1/4分位': metric_values.quantile(0.25),
            '3/4分位': metric_values.quantile(0.75),
            '標準偏差': metric_values.std(),
            '分散': metric_values.var()
        }
        source_stats_list.append(stats)
    
    if not source_stats_list:
        st.warning("選択された条件に一致する統計データがありません。")
        return
    
    # DataFrameに変換
    source_stats_df = pd.DataFrame(source_stats_list)
    
    # 数値型に変換
    for col in source_stats_df.columns:
        if col != "原作":
            source_stats_df[col] = pd.to_numeric(source_stats_df[col], errors='ignore')
    
    # 1. 全原作タイプの基礎統計表（平均でソート）
    st.markdown("---")
    st.subheader(f"📊 表1: 全原作タイプの基礎統計 ({selected_metric})")
    sorted_df = source_stats_df.sort_values('平均', ascending=False)
    st.dataframe(sorted_df, width='stretch', height=400)
    
    # 2. 年代別・年次別の詳細統計（全期間以外の場合）
    if selected_decade != "全期間":
        st.markdown("---")
        st.subheader(f"📊 表2: {selected_decade} - 各年度の原作別統計")
        
        # 年度ごとに原作別統計を計算
        if 'seasonYear' in filtered_data.columns:
            # 年度のユニークリストを取得（降順）
            years = sorted(filtered_data['seasonYear'].dropna().unique(), reverse=True)
            
            # 各年度の統計を計算
            yearly_source_stats = []
            
            for year in years:
                year_data = filtered_data[filtered_data['seasonYear'] == year]
                
                for source in unique_sources:
                    source_year_data = year_data[year_data['source'] == source]
                    
                    if source_year_data.empty:
                        continue
                    
                    metric_values = pd.to_numeric(source_year_data[selected_metric], errors='coerce').dropna()
                    
                    if len(metric_values) == 0:
                        continue
                    
                    stats = {
                        '年度': int(year),
                        '原作': source,
                        '合計': metric_values.sum(),
                        'カウント': len(metric_values),
                        '最大': metric_values.max(),
                        '最小': metric_values.min(),
                        '平均': metric_values.mean(),
                        '中央値': metric_values.median(),
                        '1/4分位': metric_values.quantile(0.25),
                        '3/4分位': metric_values.quantile(0.75),
                        '標準偏差': metric_values.std(),
                        '分散': metric_values.var()
                    }
                    yearly_source_stats.append(stats)
            
            if yearly_source_stats:
                yearly_source_df = pd.DataFrame(yearly_source_stats)
                
                # 数値型に変換
                for col in yearly_source_df.columns:
                    if col not in ["年度", "原作"]:
                        yearly_source_df[col] = pd.to_numeric(yearly_source_df[col], errors='ignore')
                
                st.dataframe(yearly_source_df, width='stretch', height=600)
                
                # 年度別推移グラフ（全原作タイプ）
                st.markdown("---")
                st.subheader(f"📈 年度別推移 - 全原作タイプ")
                
                if not yearly_source_df.empty:
                    fig = px.line(
                        yearly_source_df,
                        x='年度',
                        y='平均',
                        color='原作',
                        markers=True,
                        title=f'{selected_decade} - 原作別の年度別推移',
                        labels={
                            '年度': '年度',
                            '平均': metric_labels.get(selected_metric, selected_metric)
                        }
                    )
                    fig.update_layout(height=500, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # ヒートマップ（年度 x 原作）
                    st.markdown("---")
                    st.subheader(f"🔥 ヒートマップ - 年度別原作平均値")
                    
                    # ピボットテーブル作成
                    pivot_data = yearly_source_df.pivot(index='原作', columns='年度', values='平均')
                    
                    fig_heatmap = px.imshow(
                        pivot_data,
                        labels=dict(x="年度", y="原作", color=metric_labels.get(selected_metric, selected_metric)),
                        x=pivot_data.columns,
                        y=pivot_data.index,
                        color_continuous_scale='RdYlBu_r',
                        aspect='auto'
                    )
                    fig_heatmap.update_layout(height=400)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("選択された年代のデータがありません。")
    
    # 3. 全期間選択時の年代別統計
    if selected_decade == "全期間":
        st.markdown("---")
        st.subheader("📊 表2: 年代別の原作別統計")
        
        # 年代定義
        decade_ranges = {
            "1900年代": (1900, 1999),
            "2000年代": (2000, 2009),
            "2010年代": (2010, 2019),
            "2020年代": (2020, 2029)
        }
        
        decade_source_stats = []
        
        for decade_name, (start_year, end_year) in decade_ranges.items():
            decade_data = filtered_data[
                (filtered_data['seasonYear'] >= start_year) & 
                (filtered_data['seasonYear'] <= end_year)
            ]
            
            if decade_data.empty:
                continue
            
            for source in unique_sources:
                source_decade_data = decade_data[decade_data['source'] == source]
                
                if source_decade_data.empty:
                    continue
                
                metric_values = pd.to_numeric(source_decade_data[selected_metric], errors='coerce').dropna()
                
                if len(metric_values) == 0:
                    continue
                
                stats = {
                    '年代': decade_name,
                    '原作': source,
                    '合計': metric_values.sum(),
                    'カウント': len(metric_values),
                    '最大': metric_values.max(),
                    '最小': metric_values.min(),
                    '平均': metric_values.mean(),
                    '中央値': metric_values.median(),
                    '1/4分位': metric_values.quantile(0.25),
                    '3/4分位': metric_values.quantile(0.75),
                    '標準偏差': metric_values.std(),
                    '分散': metric_values.var()
                }
                decade_source_stats.append(stats)
        
        if decade_source_stats:
            decade_source_df = pd.DataFrame(decade_source_stats)
            
            # 数値型に変換
            for col in decade_source_df.columns:
                if col not in ["年代", "原作"]:
                    decade_source_df[col] = pd.to_numeric(decade_source_df[col], errors='ignore')
            
            st.dataframe(decade_source_df, width='stretch', height=600)
            
            # 年代別推移グラフ
            st.markdown("---")
            st.subheader("📈 年代別推移 - 全原作タイプ")
            
            fig_decade = px.line(
                decade_source_df,
                x='年代',
                y='平均',
                color='原作',
                markers=True,
                title=f'年代別原作タイプ別推移',
                labels={
                    '年代': '年代',
                    '平均': metric_labels.get(selected_metric, selected_metric)
                }
            )
            fig_decade.update_layout(height=500, hovermode='x unified')
            st.plotly_chart(fig_decade, use_container_width=True)
        else:
            st.info("年代別のデータがありません。")
    
    # 4. 原作タイプ比較の横棒グラフ
    st.markdown("---")
    st.subheader("📊 原作タイプ別比較")
    
    fig_bar = px.bar(
        sorted_df,
        x='平均',
        y='原作',
        orientation='h',
        text='平均',
        color='平均',
        color_continuous_scale='Viridis',
        title=f'原作タイプ別 {metric_labels.get(selected_metric, selected_metric)} 平均値'
    )
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_bar.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # 5. カウント vs 平均の散布図
    st.markdown("---")
    st.subheader("📊 タイトル数 vs 平均値")
    
    fig_scatter = px.scatter(
        source_stats_df,
        x='カウント',
        y='平均',
        text='原作',
        size='カウント',
        color='平均',
        color_continuous_scale='Viridis',
        labels={
            'カウント': 'タイトル数',
            '平均': metric_labels.get(selected_metric, selected_metric)
        },
        title=f'原作別タイトル数と{metric_labels.get(selected_metric, selected_metric)}の関係'
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)


def show_studio_statistics_tab(data):
    """アニメスタジオ基礎統計タブの表示 - スタジオの回数の基礎統計"""
    st.header("🎬 アニメスタジオ 基礎統計")
    st.markdown("**このタブではスタジオの回数（作品数）の基礎統計を表示します**")
    
    if data is None or data.empty:
        st.warning("データが利用できません。")
        return
    
    # フィルター設定
    st.subheader("🔧 フィルター設定")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 年代選択
        decades = ["全期間", "1900年代", "2000年代", "2010年代", "2020年代"]
        selected_decade = st.selectbox("年代", decades, key="studio_stats_decade")
    
    with col2:
        # フォーマット選択
        if 'format' in data.columns:
            unique_formats = sorted(data['format'].dropna().unique())
            formats = ["全て"] + list(unique_formats)
            selected_format = st.selectbox("フォーマット", formats, key="studio_stats_format")
        else:
            selected_format = "全て"
    
    with col3:
        # 原作選択
        if 'source' in data.columns:
            unique_sources = sorted(data['source'].dropna().unique())
            sources = ["全て"] + list(unique_sources)
            selected_source = st.selectbox("原作", sources, key="studio_stats_source")
        else:
            selected_source = "全て"
    
    with col4:
        # ジャンル選択（複数ジャンルを持つ作品があるため、単一ジャンルでフィルタ）
        if 'genres' in data.columns:
            # 全ジャンルを抽出
            all_genres = set()
            for genres_str in data['genres'].dropna():
                if genres_str != 'Unknown':
                    all_genres.update([g.strip() for g in genres_str.split(',')])
            unique_genres = sorted(list(all_genres))
            genres = ["全て"] + unique_genres
            selected_genre = st.selectbox("ジャンル", genres, key="studio_stats_genre")
        else:
            selected_genre = "全て"
    
    # フィルター適用
    filtered_data = data.copy()
    
    if selected_format != "全て":
        filtered_data = filtered_data[filtered_data['format'] == selected_format]
    
    if selected_source != "全て":
        filtered_data = filtered_data[filtered_data['source'] == selected_source]
    
    if selected_genre != "全て":
        # ジャンルが含まれている作品をフィルタ
        filtered_data = filtered_data[filtered_data['genres'].str.contains(selected_genre, na=False)]
    
    # 年代フィルター適用
    filtered_data = create_decade_filter(filtered_data, selected_decade, 'seasonYear')
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # スタジオごとの作品数を集計
    if 'studios_name' not in filtered_data.columns:
        st.error("スタジオデータが利用できません。")
        return
    
    # 各スタジオの作品数をカウント
    studio_counts = filtered_data.groupby('studios_name').size().reset_index(name='作品数')
    
    # 基礎統計を計算
    def calculate_basic_stats(series):
        """基礎統計を計算"""
        series = series.dropna()
        if len(series) == 0:
            return {}
        
        stats = {
            "合計": float(series.sum()),
            "カウント": int(len(series)),
            "最大": float(series.max()),
            "最小": float(series.min()),
            "平均": float(series.mean()),
            "中央値": float(series.median()),
            "1/4分位": float(series.quantile(0.25)),
            "3/4分位": float(series.quantile(0.75))
        }
        
        if len(series) > 1:
            stats["標準偏差"] = float(series.std())
            stats["分散"] = float(series.var())
        else:
            stats["標準偏差"] = 0.0
            stats["分散"] = 0.0
        
        return stats
    
    # 統計情報表示
    st.subheader(f"📈 スタジオ統計（{len(studio_counts):,}社）")
    
    # 基礎統計表
    st.markdown("### 📊 スタジオの回数（作品数）の基礎統計")
    count_stats = calculate_basic_stats(studio_counts['作品数'])
    if count_stats:
        count_df = pd.DataFrame(
            [(key, value) for key, value in count_stats.items()],
            columns=["統計項目", "作品数"]
        )
        st.dataframe(count_df, use_container_width=True, height=400)
    else:
        st.warning("作品数のデータがありません")


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
            db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
            extended_data = data.copy()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        if genre == "アニメ":
            db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\anime_data.db')
        else:
            db_path = Path(r'C:\Users\PC_User\Desktop\GitHub\public_anilist_data_rank_and_analysis\db\manga_data.db')
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
        elif genre == "漫画" and 'seasonYear' in extended_data.columns:
            years = ["全て"] + [str(int(year)) for year in get_unique_values(extended_data, 'seasonYear')]
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
                filters['seasonYear'] = float(selected_year)
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
    
    # 統合メニュー（アニメとマンガを1つのラジオボタンに）
    menu_options = [
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
    ]
    
    selected_menu = st.sidebar.radio(
        "分析項目を選択:",
        menu_options,
        key="main_menu"
    )
    
    # 選択されたメニューに応じて処理を分岐
    if selected_menu == "🎬 アニメ - タイトル":
        # 既存のアニメタイトル分析（ランキング、基礎統計、相関分析）
        data = load_anime_data()
        if data is None:
            st.error("アニメデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # メイン画面のタブ分離
        tab1, tab2 = st.tabs(["基礎統計", "相関分析"])
        
        with tab1:
            show_statistics_tab(data, "アニメ")
        
        with tab2:
            show_scatter_tab(data, "アニメ")
    
    elif selected_menu == "🎬 アニメ - キャラ":
        # キャラクター分析
        data = load_character_data()
        if data is None:
            st.error("キャラクターデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_character_statistics_tab(data)
    
    elif selected_menu == "🎬 アニメ - 声優":
        # 声優分析
        data = load_voiceactor_data()
        if data is None:
            st.error("声優データを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_voiceactor_statistics_tab(data)
    
    elif selected_menu == "🎬 アニメ - スタッフ":
        # スタッフ分析
        data = load_staff_data()
        if data is None:
            st.error("スタッフデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_staff_statistics_tab(data)
    
    elif selected_menu == "🎬 アニメ - スタジオ":
        # スタジオ分析
        data = load_studio_data()
        if data is None:
            st.error("スタジオデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_studio_statistics_tab(data)
    
    elif selected_menu == "🎬 アニメ - ジャンル":
        # ジャンル分析
        data = load_genre_data()
        if data is None:
            st.error("ジャンルデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_genre_statistics_tab(data)
    
    elif selected_menu == "🎬 アニメ - 原作":
        # 原作分析
        data = load_source_data()
        if data is None:
            st.error("原作データを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_source_statistics_tab(data)
    
    elif selected_menu == "📚 マンガ - タイトル":
        # マンガタイトル分析
        data = load_manga_data()
        if data is None:
            st.error("マンガデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # メイン画面のタブ分離
        tab1, tab2 = st.tabs(["基礎統計", "相関分析"])
        
        with tab1:
            show_statistics_tab(data, "漫画")
        
        with tab2:
            show_scatter_tab(data, "漫画")
    
    elif selected_menu == "📚 マンガ - キャラ":
        # マンガキャラクター分析
        data = load_manga_character_data()
        if data is None:
            st.error("マンガキャラクターデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_manga_character_statistics_tab(data)
    
    elif selected_menu == "📚 マンガ - スタッフ":
        # マンガスタッフ分析
        data = load_manga_staff_data()
        if data is None:
            st.error("マンガスタッフデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_manga_staff_statistics_tab(data)
    
    elif selected_menu == "📚 マンガ - ジャンル":
        # マンガジャンル分析
        data = load_manga_genre_data()
        if data is None:
            st.error("マンガジャンルデータを読み込めませんでした。")
            st.info("データベースファイルが存在することを確認してください。")
            return
        
        # 基礎統計のみ表示
        show_manga_genre_statistics_tab(data)
    
    else:
        # その他のメニュー項目（今後実装予定）
        menu_parts = selected_menu.split(" - ")
        if len(menu_parts) == 2:
            category = menu_parts[0]  # "🎬 アニメ" or "📚 マンガ"
            item = menu_parts[1]  # "原作", "ジャンル", etc.
            st.header(f"{category} {item} 分析")
            st.info(f"{category}の{item}分析機能は今後実装予定です。")
        else:
            st.info("選択された機能は今後実装予定です。")

if __name__ == "__main__":
    main()