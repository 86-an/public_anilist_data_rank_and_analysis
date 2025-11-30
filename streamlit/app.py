import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# ページ設定
st.set_page_config(
    page_title="AniList ランキング分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# データベース接続関数
@st.cache_data
def get_database_connection():
    """データベースに接続してデータを取得"""
    base_dir = Path(__file__).parent.parent
    anime_db = base_dir / 'db' / 'anime_data.db'
    manga_db = base_dir / 'db' / 'manga_data.db'
    
    connections = {}
    
    if anime_db.exists():
        connections['anime'] = str(anime_db)
    if manga_db.exists():
        connections['manga'] = str(manga_db)
    
    return connections

# データ取得関数
@st.cache_data
def load_anime_data():
    """アニメデータを読み込み"""
    dbs = get_database_connection()
    if 'anime' not in dbs:
        return None, {}, {}, {}, {}, {}, {}
    
    conn = sqlite3.connect(dbs['anime'])
    
    # メインのアニメデータ
    anime_df = pd.read_sql_query("""
        SELECT 
            a.anilist_id, a.title_romaji, a.title_native, a.format, 
            a.season, a.seasonYear, a.favorites, a.meanScore, 
            a.popularity, a.source, a.episode
        FROM anime a
        WHERE a.title_romaji IS NOT NULL
        ORDER BY a.meanScore DESC NULLS LAST
    """, conn)
    
    # 選択肢用のリスト取得
    titles = pd.read_sql_query("SELECT DISTINCT title_romaji FROM anime WHERE title_romaji IS NOT NULL ORDER BY title_romaji", conn)
    voiceactors = pd.read_sql_query("SELECT DISTINCT voiceactor_name FROM voiceactors WHERE voiceactor_name IS NOT NULL ORDER BY voiceactor_name", conn)
    studios = pd.read_sql_query("SELECT DISTINCT studios_name FROM studios WHERE studios_name IS NOT NULL ORDER BY studios_name", conn)
    genres = pd.read_sql_query("SELECT DISTINCT genre_name FROM genres WHERE genre_name IS NOT NULL ORDER BY genre_name", conn)
    staff = pd.read_sql_query("SELECT DISTINCT staff_name FROM staff WHERE staff_name IS NOT NULL ORDER BY staff_name", conn)
    characters = pd.read_sql_query("SELECT DISTINCT chara_name FROM characters WHERE chara_name IS NOT NULL ORDER BY chara_name", conn)
    
    conn.close()
    
    return (anime_df, 
            titles['title_romaji'].tolist(),
            voiceactors['voiceactor_name'].tolist(),
            studios['studios_name'].tolist(),
            genres['genre_name'].tolist(),
            staff['staff_name'].tolist(),
            characters['chara_name'].tolist())

@st.cache_data
def load_manga_data():
    """マンガデータを読み込み"""
    dbs = get_database_connection()
    if 'manga' not in dbs:
        return None, {}, {}
    
    conn = sqlite3.connect(dbs['manga'])
    
    # メインのマンガデータ
    manga_df = pd.read_sql_query("""
        SELECT 
            anilist_id, title_romaji, title_native, format, 
            season, seasonYear, favorites, meanScore, 
            popularity, source
        FROM manga
        WHERE title_romaji IS NOT NULL
        ORDER BY meanScore DESC NULLS LAST
    """, conn)
    
    # 選択肢用のリスト（マンガ用は限定的）
    titles = pd.read_sql_query("SELECT DISTINCT title_romaji FROM manga WHERE title_romaji IS NOT NULL ORDER BY title_romaji", conn)
    
    conn.close()
    
    return manga_df, titles['title_romaji'].tolist(), []

@st.cache_data
def get_filtered_anime_data(selected_titles=None, selected_voiceactors=None, selected_studios=None, 
                           selected_genres=None, selected_staff=None, selected_characters=None):
    """フィルター条件に基づいてアニメデータを取得"""
    dbs = get_database_connection()
    if 'anime' not in dbs:
        return pd.DataFrame()
    
    conn = sqlite3.connect(dbs['anime'])
    
    # ベースクエリ
    query = """
        SELECT DISTINCT
            a.anilist_id, a.title_romaji, a.title_native, a.format, 
            a.season, a.seasonYear, a.favorites, a.meanScore, 
            a.popularity, a.source, a.episode
        FROM anime a
    """
    
    joins = []
    conditions = ["a.title_romaji IS NOT NULL"]
    
    # フィルター条件の追加
    if selected_titles:
        conditions.append(f"a.title_romaji IN ({','.join(['?' for _ in selected_titles])})")
    
    if selected_voiceactors:
        joins.append("LEFT JOIN voiceactors v ON a.anilist_id = v.anilist_id")
        conditions.append(f"v.voiceactor_name IN ({','.join(['?' for _ in selected_voiceactors])})")
    
    if selected_studios:
        joins.append("LEFT JOIN studios s ON a.anilist_id = s.anilist_id")
        conditions.append(f"s.studios_name IN ({','.join(['?' for _ in selected_studios])})")
    
    if selected_genres:
        joins.append("LEFT JOIN genres g ON a.anilist_id = g.anilist_id")
        conditions.append(f"g.genre_name IN ({','.join(['?' for _ in selected_genres])})")
    
    if selected_staff:
        joins.append("LEFT JOIN staff st ON a.anilist_id = st.anilist_id")
        conditions.append(f"st.staff_name IN ({','.join(['?' for _ in selected_staff])})")
    
    if selected_characters:
        joins.append("LEFT JOIN characters c ON a.anilist_id = c.anilist_id")
        conditions.append(f"c.chara_name IN ({','.join(['?' for _ in selected_characters])})")
    
    # クエリ構築
    if joins:
        query += " " + " ".join(joins)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY a.meanScore DESC NULLS LAST"
    
    # パラメータ準備
    params = []
    if selected_titles:
        params.extend(selected_titles)
    if selected_voiceactors:
        params.extend(selected_voiceactors)
    if selected_studios:
        params.extend(selected_studios)
    if selected_genres:
        params.extend(selected_genres)
    if selected_staff:
        params.extend(selected_staff)
    if selected_characters:
        params.extend(selected_characters)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def main():
    """メイン関数"""
    st.title("📊 AniList ランキング分析")
    st.markdown("---")
    
    # データ読み込み
    anime_data, anime_titles, voiceactor_list, studio_list, genre_list, staff_list, character_list = load_anime_data()
    manga_data, manga_titles, manga_staff_list = load_manga_data()
    
    # サイドバーでジャンル選択
    st.sidebar.title("🎯 フィルター設定")
    genre = st.sidebar.selectbox("ジャンルを選択", ["アニメ", "漫画"])
    
    # ジャンルごとのフィルター項目
    selected_filters = {}
    
    if genre == "アニメ" and anime_data is not None:
        st.sidebar.markdown("### 📺 アニメフィルター")
        selected_filters['titles'] = st.sidebar.multiselect("タイトル", anime_titles, key="anime_titles")
        selected_filters['voiceactors'] = st.sidebar.multiselect("声優", voiceactor_list[:100], key="voiceactors")  # 上位100件に制限
        selected_filters['studios'] = st.sidebar.multiselect("スタジオ", studio_list[:50], key="studios")  # 上位50件に制限
        selected_filters['genres'] = st.sidebar.multiselect("ジャンル", genre_list, key="genres")
        selected_filters['staff'] = st.sidebar.multiselect("スタッフ", staff_list[:100], key="staff")  # 上位100件に制限
        selected_filters['characters'] = st.sidebar.multiselect("キャラクター", character_list[:100], key="characters")  # 上位100件に制限
        
        # フィルターされたデータを取得
        if any(selected_filters.values()):
            current_data = get_filtered_anime_data(
                selected_filters.get('titles'),
                selected_filters.get('voiceactors'),
                selected_filters.get('studios'),
                selected_filters.get('genres'),
                selected_filters.get('staff'),
                selected_filters.get('characters')
            )
        else:
            current_data = anime_data
            
    elif genre == "マンガ" and manga_data is not None:
        st.sidebar.markdown("### 📚 マンガフィルター")
        selected_filters['titles'] = st.sidebar.multiselect("タイトル", manga_titles, key="manga_titles")
        
        # フィルターされたデータを取得
        if selected_filters.get('titles'):
            current_data = manga_data[manga_data['title_romaji'].isin(selected_filters['titles'])]
        else:
            current_data = manga_data
    else:
        st.error("データベースファイルが見つかりません。")
        return
    
    # データが空の場合
    if current_data is None or current_data.empty:
        st.warning("選択された条件に該当するデータがありません。")
        return
    
    # メイン画面のタブ分離
    tab1, tab2, tab3, tab4 = st.tabs(["📈 ランキング", "📊 基礎統計", "📊 ヒストグラム", "🔍 散布図"])
    
    with tab1:
        show_ranking_tab(current_data, genre)
    
    with tab2:
        show_statistics_tab(current_data, genre)
    
    with tab3:
        show_histogram_tab(current_data, genre)
    
    with tab4:
        show_scatter_tab(current_data, genre)

def show_ranking_tab(data, genre):
    """ランキングタブの内容"""
    st.header(f"🏆 {genre}ランキング")
    
    # ランキング基準選択
    ranking_col1, ranking_col2 = st.columns([2, 1])
    
    with ranking_col1:
        rank_by = st.selectbox(
            "ランキング基準を選択",
            ["meanScore", "favorites", "popularity"],
            format_func=lambda x: {
                "meanScore": "平均スコア",
                "favorites": "お気に入り数",
                "popularity": "人気度"
            }[x]
        )
    
    with ranking_col2:
        top_n = st.number_input("表示件数", min_value=10, max_value=100, value=20)
    
    # データの並び替え
    if rank_by in data.columns:
        ranked_data = data.sort_values(rank_by, ascending=False).head(top_n)
        
        # ランキング表示
        st.subindex(f"Top {top_n} - {rank_by}")
        
        # データフレーム表示用にカラム名を日本語化
        display_data = ranked_data.copy()
        display_data.index = range(1, len(display_data) + 1)
        
        column_mapping = {
            'title_romaji': 'タイトル',
            'meanScore': '平均スコア',
            'favorites': 'お気に入り数',
            'popularity': '人気度',
            'seasonYear': '年',
            'season': 'シーズン',
            'format': 'フォーマット',
            'source': '原作'
        }
        
        display_columns = ['title_romaji', 'meanScore', 'favorites', 'popularity', 'seasonYear']
        if 'episode' in display_data.columns:
            display_columns.append('episode')
            column_mapping['episode'] = 'エピソード数'
        
        display_data = display_data[display_columns].rename(columns=column_mapping)
        st.dataframe(display_data, use_container_width=True)
        
        # トップ10のグラフ表示
        if len(ranked_data) >= 10:
            fig = px.bar(
                ranked_data.head(10),
                x='title_romaji',
                y=rank_by,
                title=f"Top 10 {genre} - {column_mapping.get(rank_by, rank_by)}",
                labels={'title_romaji': 'タイトル', rank_by: column_mapping.get(rank_by, rank_by)}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def show_statistics_tab(data, genre):
    """基礎統計タブの内容"""
    st.header(f"📊 {genre} 基礎統計")
    
    # 数値カラムの統計情報
    numeric_columns = ['meanScore', 'favorites', 'popularity', 'seasonYear']
    if 'episode' in data.columns:
        numeric_columns.append('episode')
    
    # 統計サマリー
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 基本統計量")
        stats_data = data[numeric_columns].describe()
        st.dataframe(stats_data)
    
    with col2:
        st.subheader("📊 データ概要")
        st.metric("総データ数", len(data))
        st.metric("年代範囲", f"{data['seasonYear'].min():.0f} - {data['seasonYear'].max():.0f}")
        
        # 平均値の表示
        if 'meanScore' in data.columns and not data['meanScore'].isna().all():
            avg_score = data['meanScore'].mean()
            st.metric("平均スコア", f"{avg_score:.2f}")
    
    # カテゴリカルデータの分析
    st.subheader("🎭 カテゴリ別分析")
    
    category_col1, category_col2 = st.columns(2)
    
    with category_col1:
        if 'format' in data.columns:
            format_counts = data['format'].value_counts()
            fig = px.pie(
                values=format_counts.values,
                names=format_counts.index,
                title="フォーマット分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with category_col2:
        if 'season' in data.columns:
            season_counts = data['season'].value_counts()
            fig = px.pie(
                values=season_counts.values,
                names=season_counts.index,
                title="シーズン分布"
            )
            st.plotly_chart(fig, use_container_width=True)

def show_histogram_tab(data, genre):
    """ヒストグラムタブの内容"""
    st.header(f"📊 {genre} ヒストグラム分析")
    
    # 分析対象カラム選択
    numeric_columns = ['meanScore', 'favorites', 'popularity', 'seasonYear']
    if 'episode' in data.columns:
        numeric_columns.append('episode')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_column = st.selectbox(
            "分析対象を選択",
            numeric_columns,
            format_func=lambda x: {
                'meanScore': '平均スコア',
                'favorites': 'お気に入り数',
                'popularity': '人気度',
                'seasonYear': '年',
                'episode': 'エピソード数'
            }.get(x, x)
        )
        
        chart_type = st.radio("グラフタイプ", ["ヒストグラム", "棒グラフ"])
        bins = st.slider("ビン数", 10, 50, 20)
    
    with col2:
        if selected_column in data.columns:
            clean_data = data[data[selected_column].notna()]
            
            if chart_type == "ヒストグラム":
                fig = px.histogram(
                    clean_data,
                    x=selected_column,
                    nbins=bins,
                    title=f"{genre} - {selected_column} 分布",
                    labels={selected_column: selected_column}
                )
            else:  # 棒グラフ
                # カテゴリごとの集計
                if selected_column in ['seasonYear', 'episode']:
                    value_counts = clean_data[selected_column].value_counts().head(20)
                else:
                    # 数値を区間に分割
                    clean_data['binned'] = pd.cut(clean_data[selected_column], bins=bins)
                    value_counts = clean_data['binned'].value_counts()
                
                fig = px.bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    title=f"{genre} - {selected_column} 分布（棒グラフ）",
                    labels={'x': selected_column, 'y': '件数'}
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 統計情報
            st.subheader("統計サマリー")
            col2_1, col2_2, col2_3, col2_4 = st.columns(4)
            with col2_1:
                st.metric("平均値", f"{clean_data[selected_column].mean():.2f}")
            with col2_2:
                st.metric("中央値", f"{clean_data[selected_column].median():.2f}")
            with col2_3:
                st.metric("最大値", f"{clean_data[selected_column].max():.2f}")
            with col2_4:
                st.metric("最小値", f"{clean_data[selected_column].min():.2f}")

def show_scatter_tab(data, genre):
    """散布図タブの内容"""
    st.header(f"🔍 {genre} 散布図分析")
    
    # 軸選択
    numeric_columns = ['meanScore', 'favorites', 'popularity', 'seasonYear']
    if 'episode' in data.columns:
        numeric_columns.append('episode')
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_axis = st.selectbox(
            "X軸を選択",
            numeric_columns,
            format_func=lambda x: {
                'meanScore': '平均スコア',
                'favorites': 'お気に入り数', 
                'popularity': '人気度',
                'seasonYear': '年',
                'episode': 'エピソード数'
            }.get(x, x),
            key="x_axis"
        )
    
    with col2:
        y_axis = st.selectbox(
            "Y軸を選択",
            numeric_columns,
            index=1,
            format_func=lambda x: {
                'meanScore': '平均スコア',
                'favorites': 'お気に入り数',
                'popularity': '人気度', 
                'seasonYear': '年',
                'episode': 'エピソード数'
            }.get(x, x),
            key="y_axis"
        )
    
    # 色分けオプション
    color_by = st.selectbox(
        "色分け基準（オプション）",
        [None, 'format', 'season', 'source'],
        format_func=lambda x: {
            None: "なし",
            'format': 'フォーマット',
            'season': 'シーズン',
            'source': '原作'
        }.get(x, x)
    )
    
    # 散布図の作成
    if x_axis in data.columns and y_axis in data.columns:
        clean_data = data[[x_axis, y_axis, 'title_romaji']].dropna()
        
        if color_by and color_by in data.columns:
            clean_data = data[[x_axis, y_axis, 'title_romaji', color_by]].dropna()
        
        fig = px.scatter(
            clean_data,
            x=x_axis,
            y=y_axis,
            color=color_by if color_by else None,
            hover_name='title_romaji',
            title=f"{genre} - {x_axis} vs {y_axis}",
            labels={
                x_axis: x_axis,
                y_axis: y_axis
            }
        )
        
        # 相関係数の計算と表示
        correlation = clean_data[x_axis].corr(clean_data[y_axis])
        fig.add_annotation(
            x=0.05,
            y=0.95,
            xref="paper",
            yref="paper",
            text=f"相関係数: {correlation:.3f}",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 相関分析サマリー
        st.subheader("📈 相関分析")
        col3_1, col3_2, col3_3 = st.columns(3)
        
        with col3_1:
            st.metric("相関係数", f"{correlation:.3f}")
        
        with col3_2:
            if abs(correlation) > 0.7:
                strength = "強い"
            elif abs(correlation) > 0.4:
                strength = "中程度"
            else:
                strength = "弱い"
            st.metric("相関の強さ", strength)
        
        with col3_3:
            direction = "正の相関" if correlation > 0 else "負の相関"
            st.metric("相関の方向", direction)

if __name__ == "__main__":
    main()