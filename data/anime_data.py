import requests
import time
import json

# 保存用リスト（取得したすべてのアニメデータを格納）
all_anime_data = []

url = "https://graphql.anilist.co"

query = """
query ($page: Int) {
  Page(page: $page, perPage: 50) {
    pageInfo {
      hasNextPage
    }
    media(type: ANIME, sort: POPULARITY_DESC) {
      id
      title {
        romaji
        native
      }
      format
      season
      seasonYear
      favourites
      meanScore
      popularity
      genres
      source
      episodes
      description
      countryOfOrigin
      studios {
        edges {
          node {
            id
            name
            isAnimationStudio
          }
        }
      }
      characters(sort: FAVOURITES_DESC) {
        edges {
          node {
            id
            name {
              userPreferred
              native
            }
            favourites
          }
          voiceActors(language: JAPANESE, sort: FAVOURITES_DESC) {
            id
            name {
              userPreferred
              native
            }
            favourites
          }
        }
      }
      staff(sort: FAVOURITES_DESC) {
        edges {
          role
          node {
            id
            name {
              userPreferred
              native
            }
            favourites
          }
        }
      }
    }
  }
}
"""

def fetch_anime(page):
    """指定されたページ番号のアニメデータを取得する（人気順）"""
    variables = {"page": page}
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            print(f"APIからのエラー: {data['errors']}")
            return None

        return data

    except requests.exceptions.RequestException as e:
        print(f"リクエストエラーが発生しました: {e}")
        return None

# リクエスト制限対策
request_count = 0

import re

# ページを回して取得
page = 1
is_last_page = False

while not is_last_page:
    data = fetch_anime(page)

    if data and 'data' in data and data['data']['Page']['media']:
        print(f"✅ Page {page} 取得完了")

        cleaned_media = []
        for media in data['data']['Page']['media']:
            desc = media.get("description")
            if desc:
                # HTMLタグを除去
                media["description"] = re.sub(r'<[^>]+>', '', desc)
            cleaned_media.append(media)

        all_anime_data.extend(cleaned_media)

        if not data['data']['Page']['pageInfo']['hasNextPage']:
            is_last_page = True
        page += 1
    else:
        is_last_page = True
        print(f"⚠️ Page {page} でデータが見つかりませんでした。")

    request_count += 1
    if request_count % 30 == 0:
        print("⏳ 30リクエスト到達、60秒休止中...")
        time.sleep(60)
    else:
        time.sleep(2)

print("全ての人気順データ取得処理が完了しました。")

# 🔽 JSONファイルに保存
with open("anilist_rank_data_analysis_popular_all_anime.json", "w", encoding="utf-8") as f:
    json.dump(all_anime_data, f, ensure_ascii=False, indent=2)

print("✅ anilist_rank_data_analysis_popular_all_anime.json に保存完了")