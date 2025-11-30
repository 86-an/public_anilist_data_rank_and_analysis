import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ページ設定
st.set_page_config(
    page_title="AniList ランキング分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_anime_data():
    """アニメデータの読み込み"""
    try:
        conn = sqlite3.connect('anime_data.db')
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
        return data
    except Exception as e:
        st.error(f"アニメデータの読み込みに失敗しました: {e}")
        return None

@st.cache_data
def load_manga_data():
    """マンガデータの読み込み"""
    try:
        conn = sqlite3.connect('manga_data.db')
        query = """
            SELECT 
                m.anilist_id, m.title_romaji, m.title_native, m.format,
                m.status, m.startYear, m.meanScore, m.favorites, m.popularity
            FROM manga m
            WHERE m.title_romaji IS NOT NULL
            ORDER BY m.meanScore DESC NULLS LAST
        """
        data = pd.read_sql_query(query, conn)
        conn.close()
        return data
    except Exception as e:
        st.error(f"マンガデータの読み込みに失敗しました: {e}")
        return None

def get_unique_values(data, column):
    """指定されたカラムのユニークな値を取得"""
    if column in data.columns:
        return sorted(data[column].dropna().unique().tolist())
    return []

def filter_data(data, filters):
    """フィルター条件に基づいてデータを絞り込み"""
    filtered_data = data.copy()
    
    for key, value in filters.items():
        if value and value != "全て" and key in filtered_data.columns:
            filtered_data = filtered_data[filtered_data[key] == value]
    
    return filtered_data

def show_ranking_tab(data, genre):
    """ランキングタブの表示"""
    st.header(f"🏆 {genre} ランキング")
    
    # フィルター設定
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
            format_func=lambda x: metric_labels.get(x, x)
        )
    
    with col2:
        # 年度選択
        if genre == "アニメ" and 'seasonYear' in data.columns:
            years = ["全て"] + get_unique_values(data, 'seasonYear')
            selected_year = st.selectbox("年度", years)
        elif genre == "漫画" and 'startYear' in data.columns:
            years = ["全て"] + get_unique_values(data, 'startYear')
            selected_year = st.selectbox("年度", years)
        else:
            selected_year = "全て"
    
    with col3:
        # 季節選択（アニメのみ）
        if genre == "アニメ" and 'season' in data.columns:
            seasons = ["全て"] + get_unique_values(data, 'season')
            selected_season = st.selectbox("季節", seasons)
        else:
            selected_season = "全て"
    
    # 追加フィルター
    col4, col5, col6 = st.columns(3)
    
    with col4:
        # 原作選択
        if 'source' in data.columns:
            sources = ["全て"] + get_unique_values(data, 'source')
            selected_source = st.selectbox("原作", sources)
        else:
            selected_source = "全て"
    
    with col5:
        # フォーマット選択
        if 'format' in data.columns:
            formats = ["全て"] + get_unique_values(data, 'format')
            selected_format = st.selectbox("フォーマット", formats)
        else:
            selected_format = "全て"
    
    with col6:
        # ジャンル選択（今後実装予定）
        selected_genre_filter = st.selectbox("ジャンル", ["全て"])
    
    # フィルター適用
    filters = {}
    if genre == "アニメ":
        if selected_year != "全て":
            filters['seasonYear'] = selected_year
        if selected_season != "全て":
            filters['season'] = selected_season
    elif genre == "漫画":
        if selected_year != "全て":
            filters['startYear'] = selected_year
    
    if selected_source != "全て":
        filters['source'] = selected_source
    if selected_format != "全て":
        filters['format'] = selected_format
    
    filtered_data = filter_data(data, filters)
    
    if filtered_data.empty:
        st.warning("選択された条件に一致するデータがありません。")
        return
    
    # ランキング表示
    st.subheader(f"📋 ランキング結果 ({len(filtered_data)}件)")
    
    # データをソート
    sorted_data = filtered_data.sort_values(selected_metric, ascending=False)
    
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
        display_columns = ['title_native', 'startYear', 'favorites', 'meanScore', 'popularity']
        available_columns = [col for col in display_columns if col in sorted_data.columns]
        display_data = sorted_data[available_columns].copy()
        
        # カラム名を日本語に変更
        column_mapping = {
            'title_native': 'タイトル（日本語）',
            'startYear': '開始年',
            'favorites': 'お気に入り数',
            'meanScore': '平均スコア',
            'popularity': '人気度'
        }
    
    # カラム名を変更
    display_data = display_data.rename(columns=column_mapping)
    
    # インデックスを順位に設定
    display_data.index = range(1, len(display_data) + 1)
    display_data.index.name = "順位"
    
    # 表示
    st.dataframe(display_data, use_container_width=True)
    
    # トップ10のチャート表示
    if len(sorted_data) >= 10:
        st.subheader("📊 トップ10チャート")
        
        top10_data = sorted_data.head(10)
        
        fig = px.bar(
            top10_data,
            x='title_romaji',
            y=selected_metric,
            title=f"トップ10 - {metric_labels.get(selected_metric, selected_metric)}",
            labels={
                'title_romaji': 'タイトル',
                selected_metric: metric_labels.get(selected_metric, selected_metric)
            }
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

def show_statistics_tab(data, genre):
    """基礎統計タブの表示"""
    st.header(f"📊 {genre} 基礎統計")
    st.info("基礎統計機能は今後実装予定です")

def show_histogram_tab(data, genre):
    """ヒストグラムタブの表示"""
    st.header(f"📈 {genre} ヒストグラム")
    st.info("ヒストグラム機能は今後実装予定です")

def show_scatter_tab(data, genre):
    """散布図タブの表示"""
    st.header(f"🔍 {genre} 散布図")
    st.info("散布図機能は今後実装予定です")

def main():
    """メイン関数"""
    st.title("📊 AniList ランキング分析")
    st.markdown("---")
    
    # サイドバーでジャンル選択
    genre = st.sidebar.selectbox("ジャンルを選択", ["アニメ", "漫画"])
    
    # データ読み込み
    if genre == "アニメ":
        data = load_anime_data()
        if data is not None:
            # タイトルリスト表示
            title_list = data['title_romaji'].tolist()
            if st.sidebar.button("タイトル一覧を表示"):
                st.sidebar.write(f"アニメタイトル数: {len(title_list)}")
    else:
        data = load_manga_data()
        if data is not None:
            # タイトルリスト表示
            manga_title_list = data['title_romaji'].tolist()
            if st.sidebar.button("タイトル一覧を表示"):
                st.sidebar.write(f"マンガタイトル数: {len(manga_title_list)}")
    
    if data is None:
        st.error(f"{genre}のデータを読み込めませんでした。")
        return
    
    # メイン画面のタブ分離
    tab1, tab2, tab3, tab4 = st.tabs(["ランキング", "基礎統計", "ヒストグラム", "散布図"])
    
    with tab1:
        show_ranking_tab(data, genre)
    
    with tab2:
        show_statistics_tab(data, genre)
    
    with tab3:
        show_histogram_tab(data, genre)
    
    with tab4:
        show_scatter_tab(data, genre)

if __name__ == "__main__":
    main()
