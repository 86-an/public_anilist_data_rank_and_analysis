import json
from pathlib import Path
from collections import defaultdict


def analyze_staff_roles(json_file, is_anime=True):
    """JSONファイルからスタッフロールを分析"""
    print(f"\n{'='*70}")
    print(f"ファイル: {json_file.name}")
    print(f"{'='*70}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 対象ロールの定義（アニメとマンガで異なる）
        if is_anime:
            target_roles = {
                'Director': {'partial': 0, 'exact': 0, 'ids': set()},
                'Character Design': {'partial': 0, 'exact': 0, 'ids': set()},
                'Theme Song': {'partial': 0, 'exact': 0, 'ids': set()},
                'Music': {'partial': 0, 'exact': 0, 'ids': set()}
            }
        else:  # manga
            target_roles = {
                'Story & Art': {'partial': 0, 'exact': 0, 'ids': set()},
                'Assistant': {'partial': 0, 'exact': 0, 'ids': set()},
                'Story': {'partial': 0, 'exact': 0, 'ids': set()},
                'Art': {'partial': 0, 'exact': 0, 'ids': set()},
                'Illustration': {'partial': 0, 'exact': 0, 'ids': set()}
            }
        
        # 全ロールのカウント
        all_roles = defaultdict(int)
        
        # データを走査
        for item in data:
            if isinstance(item, dict):
                item_id = item.get('id')
                staff_data = item.get('staff', {})
                
                if isinstance(staff_data, dict) and 'edges' in staff_data:
                    for edge in staff_data['edges']:
                        if isinstance(edge, dict) and 'role' in edge:
                            role = edge['role']
                            if role:
                                all_roles[role] += 1
                                
                                # 対象ロールとの照合
                                for target_role in target_roles:
                                    # 完全一致
                                    if role == target_role:
                                        target_roles[target_role]['exact'] += 1
                                        target_roles[target_role]['ids'].add(item_id)
                                    # 部分一致
                                    elif target_role.lower() in role.lower():
                                        target_roles[target_role]['partial'] += 1
                                        target_roles[target_role]['ids'].add(item_id)
        
        # 結果表示
        media_type = "アニメ" if is_anime else "マンガ"
        print(f"\n総{media_type}数: {len(data)}件")
        print(f"総ロール記録数: {sum(all_roles.values())}件")
        print(f"ユニークなロール種類数: {len(all_roles)}種類")
        
        print(f"\n{'='*70}")
        print(f"対象ロールの分析結果")
        print(f"{'='*70}")
        
        for role_name, counts in target_roles.items():
            item_count = len(counts['ids'])
            print(f"\n【{role_name}】")
            print(f"  完全一致: {counts['exact']:5d} 件")
            print(f"  部分一致: {counts['partial']:5d} 件 (完全一致を除く)")
            print(f"  合計:     {counts['exact'] + counts['partial']:5d} 件")
            print(f"  関連{media_type}数: {item_count} 作品")
        
        return target_roles, all_roles
        
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません")
        return None, None
    except json.JSONDecodeError:
        print(f"エラー: JSONの解析に失敗しました")
        return None, None
    except Exception as e:
        print(f"エラー: {e}")
        return None, None


def show_detailed_matches(all_roles, target_role):
    """特定ロールの詳細な一致結果を表示"""
    print(f"\n{'='*70}")
    print(f"【{target_role}】に一致するロールの詳細")
    print(f"{'='*70}")
    
    matches = []
    for role, count in all_roles.items():
        if target_role.lower() in role.lower():
            matches.append((role, count))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n一致したロール数: {len(matches)}種類")
    print(f"{'No.':<5} {'ロール名':<50} {'件数':>10}")
    print("-" * 70)
    
    for i, (role, count) in enumerate(matches, 1):
        is_exact = "(完全一致)" if role == target_role else ""
        print(f"{i:<5} {role:<50} {count:>10} {is_exact}")


def main():
    # dataディレクトリ内のJSONファイルを検索
    data_dir = Path(__file__).parent
    
    # アニメとマンガのファイルを分類
    anime_file = data_dir / 'anilist_rank_data_analysis_popular_all_anime.json'
    manga_file = data_dir / 'anilist_rank_data_analysis_popular_all_manga.json'
    
    print(f"\n{'#'*70}")
    print(f"# スタッフロール分析ツール")
    print(f"{'#'*70}")
    
    # アニメデータを処理
    if anime_file.exists():
        print(f"\n{'='*70}")
        print(f"【アニメデータの分析】")
        print(f"{'='*70}")
        target_roles, all_roles = analyze_staff_roles(anime_file, is_anime=True)
        
        if all_roles:
            # 各対象ロールの詳細を表示
            for role_name in ['Director', 'Character Design', 'Theme Song', 'Music']:
                show_detailed_matches(all_roles, role_name)
    else:
        print(f"\nアニメファイルが見つかりません: {anime_file}")
    
    # マンガデータを処理
    if manga_file.exists():
        print(f"\n{'='*70}")
        print(f"【マンガデータの分析】")
        print(f"{'='*70}")
        target_roles, all_roles = analyze_staff_roles(manga_file, is_anime=False)
        
        if all_roles:
            # 各対象ロールの詳細を表示
            for role_name in ['Story & Art', 'Assistant', 'Story', 'Art', 'Illustration']:
                show_detailed_matches(all_roles, role_name)
    else:
        print(f"\nマンガファイルが見つかりません: {manga_file}")
    
    print(f"\n{'='*70}")
    print("分析完了")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
