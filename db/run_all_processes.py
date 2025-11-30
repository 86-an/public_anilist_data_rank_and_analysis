import sqlite3
from pathlib import Path
import numpy as np
import json


def month_to_season(month):
    """月を季節に変換"""
    if month is None:
        return None
    
    if 1 <= month <= 3:
        return 'WINTER'
    elif 4 <= month <= 6:
        return 'SPRING'
    elif 7 <= month <= 9:
        return 'SUMMER'
    elif 10 <= month <= 12:
        return 'FALL'
    else:
        return None


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


class DatabaseManager:
    """データベース操作を管理するクラス"""
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """データベースに接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self.cursor
    
    def commit(self):
        """変更をコミット"""
        if self.conn:
            self.conn.commit()
    
    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()


class AnimeDataProcessor:
    """アニメデータの処理クラス"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def create_anime_table(self):
        """アニメデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime (
                anilist_id INTEGER PRIMARY KEY,
                title_romaji TEXT,
                title_native TEXT,
                format TEXT,
                season TEXT,
                seasonYear INTEGER,
                favorites INTEGER,
                meanScore REAL,
                popularity INTEGER,
                source TEXT,
                episode INTEGER,
                contry TEXT
            )
        ''')
    
    def create_studios_table(self):
        """スタジオデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS studios (
                studios_id INTEGER,
                studios_name TEXT,
                anilist_id INTEGER,
                PRIMARY KEY (studios_id, anilist_id),
                FOREIGN KEY (anilist_id) REFERENCES anime(anilist_id)
            )
        ''')
    
    def create_characters_table(self):
        """キャラクターデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                chara_id INTEGER,
                chara_name TEXT,
                favorites INTEGER,
                anilist_id INTEGER,
                PRIMARY KEY (chara_id, anilist_id),
                FOREIGN KEY (anilist_id) REFERENCES anime(anilist_id)
            )
        ''')
    
    def create_voiceactors_table(self):
        """声優データ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS voiceactors (
                voiceactor_id INTEGER,
                voiceactor_name TEXT,
                favorites INTEGER,
                anilist_id INTEGER,
                chara_id INTEGER,
                PRIMARY KEY (voiceactor_id, anilist_id, chara_id),
                FOREIGN KEY (anilist_id) REFERENCES anime(anilist_id),
                FOREIGN KEY (chara_id) REFERENCES characters(chara_id)
            )
        ''')
    
    def create_genres_table(self):
        """ジャンルデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                anilist_id INTEGER,
                genre_name TEXT,
                PRIMARY KEY (anilist_id, genre_name),
                FOREIGN KEY (anilist_id) REFERENCES anime(anilist_id)
            )
        ''')
    
    def create_staff_table(self):
        """スタッフデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_id INTEGER,
                role TEXT,
                staff_name TEXT,
                favorites INTEGER,
                anilist_id INTEGER,
                PRIMARY KEY (staff_id, anilist_id, role),
                FOREIGN KEY (anilist_id) REFERENCES anime(anilist_id)
            )
        ''')
    
    def extract_staff_data(self, json_data):
        """スタッフデータを抽出（Director, Character Design, Theme Song, Musicの部分一致のみ）"""
        staff_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            staff_data = item.get('staff', {})
            
            if isinstance(staff_data, dict) and 'edges' in staff_data:
                for edge in staff_data['edges']:
                    if isinstance(edge, dict):
                        role = edge.get('role')
                        node = edge.get('node')
                        
                        if role and isinstance(node, dict):
                            # ロールの統一処理
                            unified_role = None
                            role_lower = role.lower()
                            
                            if 'director' in role_lower:
                                unified_role = 'Director'
                            elif 'character design' in role_lower:
                                unified_role = 'Character Design'
                            elif 'theme song' in role_lower or 'music' in role_lower:
                                unified_role = 'Music'
                            
                            if unified_role:
                                name_data = node.get('name', {})
                                staff_name = None
                                if isinstance(name_data, dict):
                                    staff_name = name_data.get('full') or name_data.get('native')
                                
                                staff_records.append({
                                    'staff_id': node.get('id'),
                                    'role': unified_role,
                                    'staff_name': staff_name,
                                    'favorites': node.get('favourites'),
                                    'anilist_id': anilist_id
                                })
        
        return staff_records
    
    def transform_anime_data(self, json_data):
        """JSONデータをデータベース用に変換"""
        transformed = []
        
        for item in json_data:
            anime_record = {
                'anilist_id': item.get('id'),
                'title_romaji': item.get('title', {}).get('romaji') if isinstance(item.get('title'), dict) else None,
                'title_native': item.get('title', {}).get('native') if isinstance(item.get('title'), dict) else None,
                'format': item.get('format'),
                'season': item.get('season'),
                'seasonYear': item.get('seasonYear'),
                'favorites': item.get('favourites'),
                'meanScore': item.get('meanScore'),
                'popularity': item.get('popularity'),
                'source': item.get('source'),
                'episode': item.get('episodes'),
                'contry': item.get('countryOfOrigin')
            }
            transformed.append(anime_record)
        
        return transformed
    
    def extract_studios_data(self, json_data):
        """スタジオデータを抽出（isAnimationStudio=Trueのみ）"""
        studios_records = []

        for item in json_data:
            anilist_id = item.get('id')
            studios = item.get('studios', {})

            if isinstance(studios, dict) and 'edges' in studios:
                for edge in studios['edges']:
                    node = edge.get('node')
                    if isinstance(node, dict) and node.get('isAnimationStudio') is True:
                        studios_records.append({
                            'studios_id': node.get('id'),
                            'studios_name': node.get('name'),
                            'anilist_id': anilist_id
                        })

        return studios_records
    
    def extract_characters_data(self, json_data):
        """キャラクターデータを抽出"""
        characters_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            characters = item.get('characters', {})
            
            if isinstance(characters, dict) and 'edges' in characters:
                for edge in characters['edges']:
                    if isinstance(edge, dict) and 'node' in edge:
                        node = edge['node']
                        if isinstance(node, dict):
                            name_data = node.get('name', {})
                            chara_name = None
                            if isinstance(name_data, dict):
                                chara_name = name_data.get('full') or name_data.get('native')
                            
                            characters_records.append({
                                'chara_id': node.get('id'),
                                'chara_name': chara_name,
                                'favorites': node.get('favourites'),
                                'anilist_id': anilist_id
                            })
        
        return characters_records
    
    def extract_voiceactors_data(self, json_data):
        """声優データを抽出"""
        voiceactors_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            characters = item.get('characters', {})
            
            if isinstance(characters, dict) and 'edges' in characters:
                for edge in characters['edges']:
                    if isinstance(edge, dict) and 'node' in edge:
                        node = edge['node']
                        chara_id = node.get('id') if isinstance(node, dict) else None
                        
                        voice_actors = edge.get('voiceActors', [])
                        if isinstance(voice_actors, list):
                            for va in voice_actors:
                                if isinstance(va, dict):
                                    name_data = va.get('name', {})
                                    va_name = None
                                    if isinstance(name_data, dict):
                                        va_name = name_data.get('full') or name_data.get('native')
                                    
                                    voiceactors_records.append({
                                        'voiceactor_id': va.get('id'),
                                        'voiceactor_name': va_name,
                                        'favorites': va.get('favourites'),
                                        'anilist_id': anilist_id,
                                        'chara_id': chara_id
                                    })
        
        return voiceactors_records
    
    def extract_genres_data(self, json_data):
        """ジャンルデータを抽出"""
        genres_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            genres = item.get('genres', [])
            
            if isinstance(genres, list):
                for genre in genres:
                    if genre:
                        genres_records.append({
                            'anilist_id': anilist_id,
                            'genre_name': genre
                        })
        
        return genres_records

    def process_anime_data(self, json_file_path):
        """アニメデータを処理"""
        print(f"アニメJSONファイルを読み込み中: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"読み込んだレコード数: {len(json_data)}")
        
        # テーブル作成
        print("アニメテーブルを作成中...")
        self.create_anime_table()
        self.create_studios_table()
        self.create_characters_table()
        self.create_voiceactors_table()
        self.create_genres_table()
        self.create_staff_table()
        
        # データ変換
        print("\n=== データを変換中 ===")
        print("1. アニメデータを変換中...")
        anime_records = self.transform_anime_data(json_data)
        print(f"   変換完了: {len(anime_records)}件")
        
        print("2. スタジオデータを抽出中...")
        studios_records = self.extract_studios_data(json_data)
        print(f"   抽出完了: {len(studios_records)}件")
        
        print("3. キャラクターデータを抽出中...")
        characters_records = self.extract_characters_data(json_data)
        print(f"   抽出完了: {len(characters_records)}件")
        
        print("4. 声優データを抽出中...")
        voiceactors_records = self.extract_voiceactors_data(json_data)
        print(f"   抽出完了: {len(voiceactors_records)}件")
        
        print("5. ジャンルデータを抽出中...")
        genres_records = self.extract_genres_data(json_data)
        print(f"   抽出完了: {len(genres_records)}件")
        
        print("6. スタッフデータを抽出中...")
        staff_records = self.extract_staff_data(json_data)
        print(f"   抽出完了: {len(staff_records)}件")
        
        # データ挿入
        print("\n=== データを挿入中 ===")
        print("1. アニメデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO anime (
                anilist_id, title_romaji, title_native, format, season, 
                seasonYear, favorites, meanScore, popularity, source, 
                episode, contry
            ) VALUES (
                :anilist_id, :title_romaji, :title_native, :format, :season,
                :seasonYear, :favorites, :meanScore, :popularity, :source,
                :episode, :contry
            )
        ''', anime_records)
        print(f"   挿入完了: {len(anime_records)}件")
        
        print("2. スタジオデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO studios (
                studios_id, studios_name, anilist_id
            ) VALUES (
                :studios_id, :studios_name, :anilist_id
            )
        ''', studios_records)
        print(f"   挿入完了: {len(studios_records)}件")
        
        print("3. キャラクターデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO characters (
                chara_id, chara_name, favorites, anilist_id
            ) VALUES (
                :chara_id, :chara_name, :favorites, :anilist_id
            )
        ''', characters_records)
        print(f"   挿入完了: {len(characters_records)}件")
        
        print("4. 声優データを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO voiceactors (
                voiceactor_id, voiceactor_name, favorites, anilist_id, chara_id
            ) VALUES (
                :voiceactor_id, :voiceactor_name, :favorites, :anilist_id, :chara_id
            )
        ''', voiceactors_records)
        print(f"   挿入完了: {len(voiceactors_records)}件")
        
        print("5. ジャンルデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO genres (
                anilist_id, genre_name
            ) VALUES (
                :anilist_id, :genre_name
            )
        ''', genres_records)
        print(f"   挿入完了: {len(genres_records)}件")
        
        print("6. スタッフデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO staff (
                staff_id, role, staff_name, favorites, anilist_id
            ) VALUES (
                :staff_id, :role, :staff_name, :favorites, :anilist_id
            )
        ''', staff_records)
        print(f"   挿入完了: {len(staff_records)}件")
        
        return len(json_data)


class MangaDataProcessor:
    """マンガデータの処理クラス"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def create_manga_table(self):
        """マンガデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga (
                anilist_id INTEGER PRIMARY KEY,
                title_romaji TEXT,
                title_native TEXT,
                format TEXT,
                season TEXT,
                seasonYear INTEGER,
                favorites INTEGER,
                meanScore REAL,
                popularity INTEGER,
                source TEXT,
                episode INTEGER,
                contry TEXT
            )
        ''')
    
    def create_genres_table(self):
        """ジャンルデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                anilist_id INTEGER,
                genre_name TEXT,
                PRIMARY KEY (anilist_id, genre_name),
                FOREIGN KEY (anilist_id) REFERENCES manga(anilist_id)
            )
        ''')
    
    def create_characters_table(self):
        """キャラクターデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                chara_id INTEGER,
                chara_name TEXT,
                favorites INTEGER,
                anilist_id INTEGER,
                PRIMARY KEY (chara_id, anilist_id),
                FOREIGN KEY (anilist_id) REFERENCES manga(anilist_id)
            )
        ''')
    
    def create_staff_table(self):
        """スタッフデータ用のテーブルを作成"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_id INTEGER,
                role TEXT,
                staff_name TEXT,
                favorites INTEGER,
                anilist_id INTEGER,
                PRIMARY KEY (staff_id, anilist_id, role),
                FOREIGN KEY (anilist_id) REFERENCES manga(anilist_id)
            )
        ''')
    
    def extract_genres_data(self, json_data):
        """ジャンルデータを抽出"""
        genres_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            genres = item.get('genres', [])
            
            if isinstance(genres, list):
                for genre in genres:
                    if genre:
                        genres_records.append({
                            'anilist_id': anilist_id,
                            'genre_name': genre
                        })
        
        return genres_records
    
    def extract_characters_data(self, json_data):
        """キャラクターデータを抽出"""
        characters_records = []
        
        for item in json_data:
            anilist_id = item.get('id')
            characters = item.get('characters', {})
            
            if isinstance(characters, dict):
                edges = characters.get('edges', [])
                if isinstance(edges, list):
                    for edge in edges:
                        if isinstance(edge, dict):
                            node = edge.get('node', {})
                            if isinstance(node, dict):
                                chara_id = node.get('id')
                                name_data = node.get('name', {})
                                chara_name = name_data.get('native') or name_data.get('full') or name_data.get('native')
                                favorites = node.get('favourites')
                                
                                if chara_id and chara_name:
                                    characters_records.append({
                                        'chara_id': chara_id,
                                        'chara_name': chara_name,
                                        'favorites': favorites,
                                        'anilist_id': anilist_id
                                    })
        
        return characters_records
    
    def extract_staff_data(self, json_data):
        """スタッフデータを抽出（Director, Character Design, Theme Song, Musicの部分一致のみ）"""
        staff_records = []
        target_roles = ['Director', 'Character Design', 'Theme Song', 'Music']
        
        for item in json_data:
            anilist_id = item.get('id')
            if not anilist_id:
                continue
            
            staff = item.get('staff', {})
            if not staff:
                continue
            
            if isinstance(staff, dict):
                edges = staff.get('edges', [])
                if isinstance(edges, list):
                    for edge in edges:
                        if not isinstance(edge, dict):
                            continue
                        
                        role = edge.get('role')
                        if not role:
                            continue
                        
                        # 対象ロールの部分一致チェック
                        if not any(target in role for target in target_roles):
                            continue
                        
                        node = edge.get('node', {})
                        if not isinstance(node, dict):
                            continue
                        
                        staff_id = node.get('id')
                        name_data = node.get('name', {})
                        staff_name = name_data.get('native') if isinstance(name_data, dict) else None
                        favorites = node.get('favourites')
                        
                        if staff_id and staff_name:
                            staff_records.append({
                                'staff_id': staff_id,
                                'role': role,
                                'staff_name': staff_name,
                                'favorites': favorites,
                                'anilist_id': anilist_id
                            })
        
        return staff_records
    
    def process_manga_data(self, json_file_path):
        """マンガデータを処理"""
        print(f"マンガJSONファイルを読み込み中: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"読み込んだレコード数: {len(json_data)}")
        
        # テーブル作成
        print("マンガテーブルを作成中...")
        self.create_manga_table()
        self.create_genres_table()
        self.create_characters_table()
        self.create_staff_table()
        
        # データ変換
        print("\n=== データを変換中 ===")
        print("1. マンガデータを変換中...")
        transformed = []
        for item in json_data:
            start_date = item.get('startDate', {})
            season_year = None
            season = None
            
            if isinstance(start_date, dict):
                season_year = start_date.get('year')
                month = start_date.get('month')
                season = month_to_season(month)
            
            manga_record = {
                'anilist_id': item.get('id'),
                'title_romaji': item.get('title', {}).get('romaji') if isinstance(item.get('title'), dict) else None,
                'title_native': item.get('title', {}).get('native') if isinstance(item.get('title'), dict) else None,
                'format': item.get('format'),
                'season': season,
                'seasonYear': season_year,
                'favorites': item.get('favourites'),
                'meanScore': item.get('meanScore'),
                'popularity': item.get('popularity'),
                'source': item.get('source'),
                'episode': item.get('episodes'),
                'contry': item.get('countryOfOrigin')
            }
            transformed.append(manga_record)
        
        print(f"   変換完了: {len(transformed)}件")
        
        print("2. ジャンルデータを抽出中...")
        genres_records = self.extract_genres_data(json_data)
        print(f"   抽出完了: {len(genres_records)}件")
        
        print("3. キャラクターデータを抽出中...")
        characters_records = self.extract_characters_data(json_data)
        print(f"   抽出完了: {len(characters_records)}件")
        
        print("4. スタッフデータを抽出中...")
        staff_records = self.extract_staff_data(json_data)
        print(f"   抽出完了: {len(staff_records)}件")
        
        # データ挿入
        print("\n=== データを挿入中 ===")
        print("1. マンガデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO manga (
                anilist_id, title_romaji, title_native, format, season, 
                seasonYear, favorites, meanScore, popularity, source, 
                episode, contry
            ) VALUES (
                :anilist_id, :title_romaji, :title_native, :format, :season,
                :seasonYear, :favorites, :meanScore, :popularity, :source,
                :episode, :contry
            )
        ''', transformed)
        print(f"   挿入完了: {len(transformed)}件")
        
        print("2. ジャンルデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO genres (
                anilist_id, genre_name
            ) VALUES (
                :anilist_id, :genre_name
            )
        ''', genres_records)
        print(f"   挿入完了: {len(genres_records)}件")
        
        print("3. キャラクターデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO characters (
                chara_id, chara_name, favorites, anilist_id
            ) VALUES (
                :chara_id, :chara_name, :favorites, :anilist_id
            )
        ''', characters_records)
        print(f"   挿入完了: {len(characters_records)}件")
        
        print("4. スタッフデータを挿入中...")
        self.cursor.executemany('''
            INSERT OR REPLACE INTO staff (
                staff_id, role, staff_name, favorites, anilist_id
            ) VALUES (
                :staff_id, :role, :staff_name, :favorites, :anilist_id
            )
        ''', staff_records)
        print(f"   挿入完了: {len(staff_records)}件")
        
        return len(transformed)


class StatsProcessor:
    """統計処理クラス"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def create_unique_tables(self):
        """ユニークテーブルを作成"""
        # ジャンル
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unique_genres (
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # シーズン
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unique_seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # 年
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unique_season_years (
                year_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_year INTEGER UNIQUE NOT NULL
            )
        ''')
    
    def create_voiceactor_tables(self):
        """声優統計テーブルを作成"""
        # 基本統計
        self.cursor.execute('''
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
        
        # 詳細統計
        self.cursor.execute('''
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
    
    def create_studios_tables(self):
        """スタジオ統計テーブルを作成"""
        # 基本統計
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS studios_basic (
                studios_id INTEGER PRIMARY KEY,
                studios_name TEXT,
                studios_count INTEGER,
                first_year INTEGER,
                year_count INTEGER,
                count_per_year REAL
            )
        ''')
        
        # 詳細統計
        self.cursor.execute('''
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
    
    def create_staff_tables(self):
        """スタッフ統計テーブルを作成"""
        # 基本統計
        self.cursor.execute('''
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
        
        # 詳細統計
        self.cursor.execute('''
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
        
        # ロール
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_role (
                staff_id INTEGER,
                role TEXT,
                PRIMARY KEY (staff_id, role),
                FOREIGN KEY (staff_id) REFERENCES staff_basic(staff_id)
            )
        ''')
    
    def create_enhanced_staff_table(self):
        """拡張スタッフ統計テーブルを作成"""
        self.cursor.execute('''DROP TABLE IF EXISTS staff_basic_enhanced''')
        self.cursor.execute('''
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
    
    def populate_unique_tables(self):
        """ユニークテーブルにデータを投入"""
        self.cursor.execute('''
            INSERT OR IGNORE INTO unique_genres (genre_name)
            SELECT DISTINCT genre_name FROM genres WHERE genre_name IS NOT NULL
        ''')
        
        self.cursor.execute('''
            INSERT OR IGNORE INTO unique_seasons (season_name)
            SELECT DISTINCT season FROM anime WHERE season IS NOT NULL
        ''')
        
        self.cursor.execute('''
            INSERT OR IGNORE INTO unique_season_years (season_year)
            SELECT DISTINCT seasonYear FROM anime WHERE seasonYear IS NOT NULL
        ''')
    
    def populate_voiceactor_stats(self):
        """声優統計を生成"""
        print("声優統計を生成中...")
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO voiceactor_basic (
                voiceactor_id, voiceactor_name, favorites, voiceactor_count,
                first_year, year_count, count_per_year
            )
            SELECT 
                v.voiceactor_id,
                v.voiceactor_name,
                v.favorites,
                COUNT(DISTINCT v.anilist_id) as voiceactor_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count,
                CAST(COUNT(DISTINCT v.anilist_id) AS FLOAT) / COUNT(DISTINCT a.seasonYear) as count_per_year
            FROM voiceactors v
            LEFT JOIN anime a ON v.anilist_id = a.anilist_id
            WHERE v.voiceactor_id IS NOT NULL
            GROUP BY v.voiceactor_id, v.voiceactor_name, v.favorites
        ''')
    
    def populate_studios_stats(self):
        """スタジオ統計を生成"""
        print("スタジオ統計を生成中...")
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO studios_basic (
                studios_id, studios_name, studios_count, first_year, year_count, count_per_year
            )
            SELECT 
                s.studios_id,
                s.studios_name,
                COUNT(DISTINCT s.anilist_id) as studios_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count,
                CAST(COUNT(DISTINCT s.anilist_id) AS FLOAT) / COUNT(DISTINCT a.seasonYear) as count_per_year
            FROM studios s
            LEFT JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.studios_id IS NOT NULL
            GROUP BY s.studios_id, s.studios_name
        ''')
    
    def populate_staff_stats(self):
        """スタッフ統計を生成"""
        print("スタッフ統計を生成中...")
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO staff_basic (
                staff_id, staff_name, favorites, staff_count, first_year, year_count, count_per_year
            )
            SELECT 
                s.staff_id,
                s.staff_name,
                s.favorites,
                COUNT(DISTINCT s.anilist_id) as staff_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count,
                CAST(COUNT(DISTINCT s.anilist_id) AS FLOAT) / COUNT(DISTINCT a.seasonYear) as count_per_year
            FROM staff s
            LEFT JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id IS NOT NULL
            GROUP BY s.staff_id, s.staff_name, s.favorites
        ''')
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO staff_role (staff_id, role)
            SELECT DISTINCT staff_id, role
            FROM staff
            WHERE staff_id IS NOT NULL AND role IS NOT NULL
        ''')
    
    def populate_enhanced_staff_stats(self, anime_cursor, manga_cursor=None):
        """拡張スタッフ統計を生成（アニメ+マンガ）"""
        print("拡張スタッフ統計を生成中...")
        
        # 基本データを取得
        anime_cursor.execute('''
            SELECT 
                s.staff_id,
                s.staff_name,
                s.favorites,
                COUNT(DISTINCT s.anilist_id) as total_count,
                MIN(a.seasonYear) as first_year,
                COUNT(DISTINCT a.seasonYear) as year_count,
                CAST(COUNT(DISTINCT s.anilist_id) AS FLOAT) / COUNT(DISTINCT a.seasonYear) as count_per_year
            FROM staff s
            LEFT JOIN anime a ON s.anilist_id = a.anilist_id
            WHERE s.staff_id IS NOT NULL
            GROUP BY s.staff_id, s.staff_name, s.favorites
        ''')
        
        enhanced_records = []
        for row in anime_cursor.fetchall():
            enhanced_records.append({
                'staff_id': row[0],
                'staff_name': row[1],
                'favorites': row[2],
                'total_count': row[3],
                'first_year': row[4],
                'year_count': row[5],
                'count_per_year': row[6],
                # アニメ統計（簡易版）
                'anime_favorites_total': None,
                'anime_favorites_max': None,
                'anime_favorites_min': None,
                'anime_favorites_avg': None,
                'anime_favorites_median': None,
                'anime_favorites_q1': None,
                'anime_favorites_q3': None,
                'anime_meanscore_total': None,
                'anime_meanscore_max': None,
                'anime_meanscore_min': None,
                'anime_meanscore_avg': None,
                'anime_meanscore_median': None,
                'anime_meanscore_q1': None,
                'anime_meanscore_q3': None,
                # マンガ統計（NULL）
                'manga_favorites_total': None,
                'manga_favorites_max': None,
                'manga_favorites_min': None,
                'manga_favorites_avg': None,
                'manga_favorites_median': None,
                'manga_favorites_q1': None,
                'manga_favorites_q3': None,
                'manga_meanscore_total': None,
                'manga_meanscore_max': None,
                'manga_meanscore_min': None,
                'manga_meanscore_avg': None,
                'manga_meanscore_median': None,
                'manga_meanscore_q1': None,
                'manga_meanscore_q3': None
            })
        
        if enhanced_records:
            self.cursor.executemany('''
                INSERT OR REPLACE INTO staff_basic_enhanced (
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
            ''', enhanced_records)
        
        return len(enhanced_records)


def main():
    """メイン処理"""
    print("="*70)
    print("統合データベース作成・分析ツール")
    print("="*70)
    
    # ファイルパスの設定
    base_dir = Path(__file__).parent
    data_dir = base_dir.parent / 'data'
    
    anime_json_file = data_dir / 'anilist_rank_data_analysis_popular_all_anime.json'
    manga_json_file = data_dir / 'anilist_rank_data_analysis_popular_all_manga.json'
    
    anime_db_file = base_dir / 'anime_data.db'
    manga_db_file = base_dir / 'manga_data.db'
    
    try:
        # アニメデータベースの処理
        if anime_json_file.exists():
            print(f"\n{'='*50}")
            print("【アニメデータベース処理】")
            print(f"{'='*50}")
            
            anime_db = DatabaseManager(anime_db_file)
            anime_cursor = anime_db.connect()
            
            anime_processor = AnimeDataProcessor(anime_cursor)
            anime_count = anime_processor.process_anime_data(anime_json_file)
            
            # 統計テーブル作成
            stats_processor = StatsProcessor(anime_cursor)
            print("統計テーブルを作成中...")
            stats_processor.create_unique_tables()
            stats_processor.create_voiceactor_tables()
            stats_processor.create_studios_tables()
            stats_processor.create_staff_tables()
            stats_processor.create_enhanced_staff_table()
            
            anime_db.commit()
            anime_db.close()
            
            print(f"アニメデータベース処理完了: {anime_count}件")
        else:
            print(f"警告: アニメJSONファイルが見つかりません: {anime_json_file}")
        
        # マンガデータベースの処理
        if manga_json_file.exists():
            print(f"\n{'='*50}")
            print("【マンガデータベース処理】")
            print(f"{'='*50}")
            
            manga_db = DatabaseManager(manga_db_file)
            manga_cursor = manga_db.connect()
            
            manga_processor = MangaDataProcessor(manga_cursor)
            manga_count = manga_processor.process_manga_data(manga_json_file)
            
            # 統計テーブル作成
            stats_processor = StatsProcessor(manga_cursor)
            print("統計テーブルを作成中...")
            stats_processor.create_unique_tables()
            
            # ユニークテーブルにデータを投入
            print("ユニークテーブルにデータを投入中...")
            manga_cursor.execute('''
                INSERT OR IGNORE INTO unique_genres (genre_name)
                SELECT DISTINCT genre_name FROM genres WHERE genre_name IS NOT NULL
            ''')
            manga_cursor.execute('''
                INSERT OR IGNORE INTO unique_seasons (season_name)
                SELECT DISTINCT season FROM manga WHERE season IS NOT NULL
            ''')
            manga_cursor.execute('''
                INSERT OR IGNORE INTO unique_season_years (season_year)
                SELECT DISTINCT seasonYear FROM manga WHERE seasonYear IS NOT NULL
            ''')
            
            manga_db.commit()
            manga_db.close()
            
            print(f"マンガデータベース処理完了: {manga_count}件")
        else:
            print(f"警告: マンガJSONファイルが見つかりません: {manga_json_file}")
        
        # 統合処理の実行確認
        print(f"\n{'='*50}")
        print("【処理完了】")
        print(f"{'='*50}")
        
        if anime_db_file.exists():
            print(f"✓ アニメデータベース: {anime_db_file}")
        
        if manga_db_file.exists():
            print(f"✓ マンガデータベース: {manga_db_file}")
        
        # 統計処理とデータ分析の実行
        if anime_db_file.exists():
            print(f"\n{'='*50}")
            print("【統計処理・データ分析】")
            print(f"{'='*50}")
            
            anime_db = DatabaseManager(anime_db_file)
            anime_cursor = anime_db.connect()
            
            manga_cursor = None
            if manga_db_file.exists():
                manga_db = DatabaseManager(manga_db_file)
                manga_cursor = manga_db.connect()
            
            stats_processor = StatsProcessor(anime_cursor)
            
            # ユニークテーブルにデータを投入
            print("ユニークテーブルにデータを投入中...")
            stats_processor.populate_unique_tables()
            
            # 統計データを生成
            stats_processor.populate_voiceactor_stats()
            stats_processor.populate_studios_stats()
            stats_processor.populate_staff_stats()
            
            # 拡張スタッフ統計を生成
            enhanced_count = stats_processor.populate_enhanced_staff_stats(anime_cursor, manga_cursor)
            print(f"拡張スタッフ統計完了: {enhanced_count}件")
            
            anime_db.commit()
            anime_db.close()
            
            if manga_cursor:
                manga_db.close()
            
            print("統計処理完了！")
        
        print("\n各データベースには以下のテーブルが作成されています:")
        print("  - 基本データテーブル (anime/manga, studios, characters, etc.)")
        print("  - ユニークマスターテーブル (genres, seasons, years)")
        print("  - 統計テーブル (voiceactor_*, studios_*, staff_*)")
        print("  - 拡張統計テーブル (staff_basic_enhanced)")
        
        print(f"\n個別の処理を実行する場合は、以下のスクリプトを使用してください:")
        print(f"  - アニメDB作成: python json_to_db_anime.py")
        print(f"  - マンガDB作成: python json_to_db_manga.py")
        print(f"  - ユニークテーブル: python create_unique_tables.py")
        print(f"  - 声優統計: python create_voiceactor_stats.py")
        print(f"  - スタジオ・スタッフ統計: python create_studios_staff_stats.py")
        print(f"  - 拡張スタッフ統計: python create_enhanced_staff_with_manga.py")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1
    
    print(f"\n{'='*70}")
    print("すべての処理が完了しました！")
    print(f"{'='*70}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)