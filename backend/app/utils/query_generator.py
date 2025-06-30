# backend/app/utils/query_generator.py
import logging
from typing import Optional, List, Dict, Set # Set を追加 (重複排除のため)

logger = logging.getLogger(__name__)

# 災害種別とその関連キーワードのマッピング
# より多くの災害種別に対応する場合や、キーワードを充実させる場合にここを編集
DISASTER_KEYWORDS_MAP: Dict[str, List[str]] = {
    "earthquake": ["最新情報", "被害状況", "震度", "避難所", "安否確認", "津波の可能性"],
    "地震": ["最新情報", "被害状況", "震度", "避難所", "安否確認", "津波の可能性"],
    "flood": ["洪水警報", "浸水被害", "河川氾濫", "避難情報", "冠水道路", "排水状況"],
    "洪水": ["洪水警報", "浸水被害", "河川氾濫", "避難情報", "冠水道路", "排水状況"],
    "浸水": ["浸水被害", "冠水情報", "避難経路", "排水ポンプ", "土砂災害警戒"],
    "typhoon": ["台風情報 最新経路", "暴風警報", "大雨警報", "交通機関 影響", "避難準備", "停電情報"],
    "台風": ["台風情報 最新経路", "暴風警報", "大雨警報", "交通機関 影響", "避難準備", "停電情報"],
    "heavy_rain": ["大雨警報", "土砂災害警戒情報", "浸水注意", "河川増水", "避難指示"],
    "大雨": ["大雨警報", "土砂災害警戒情報", "浸水注意", "河川増水", "避難指示"],
    "landslide": ["土砂災害警戒情報", "がけ崩れ", "土石流", "避難場所", "兆候"],
    "土砂災害": ["土砂災害警戒情報", "がけ崩れ", "土石流", "避難場所", "兆候"],
    "tsunami": ["津波警報", "津波注意報", "到達時刻", "避難場所 高台", "引き潮"],
    "津波": ["津波警報", "津波注意報", "到達時刻", "避難場所 高台", "引き潮"],
    "volcanic_eruption": ["火山情報", "噴火警戒レベル", "降灰予報", "避難計画", "火山ガス"],
    "噴火": ["火山情報", "噴火警戒レベル", "降灰予報", "避難計画", "火山ガス"],
    "heavy_snow": ["大雪警報", "積雪情報", "交通規制", "雪崩注意報", "除雪状況"],
    "大雪": ["大雪警報", "積雪情報", "交通規制", "雪崩注意報", "除雪状況"],
    # 必要に応じて他の災害種別を追加
}

# 一般的な災害時に有用なキーワード
GENERAL_DISASTER_KEYWORDS: List[str] = [
    "災害情報 最新",
    "被害状況まとめ",
    "避難所 開設状況",
    "ライフライン情報", # 電気、ガス、水道
    "交通情報 影響",
    "支援物資",
    "安否確認方法",
    "緊急連絡先"
]

# 信頼性の高い情報源を検索するためのサイト指定子
OFFICIAL_SITE_SPECIFIERS: List[str] = [
    "site:go.jp",    # 日本国政府機関
    "site:lg.jp",    # 地方公共団体
    "site:jma.go.jp", # 気象庁
    # "site:fdma.go.jp", # 総務省消防庁
    # "site:mod.go.jp/js", # 自衛隊
    # "site:*.pref.自治体名.jp" # 例: site:*.pref.tokyo.jp (都道府県のドメイン構造に依存)
    # "site:city.市町村名.jp" # 例: site:city.shibuya.tokyo.jp (市区町村のドメイン構造に依存)
]

# ユーザーの位置情報と災害種別、追加キーワードからWeb検索クエリを生成するユーティリティ
# (この関数はCM-004で詳細に設計・実装される想定)
def generate_disaster_web_search_queries(
    user_location_name: Optional[str] = None, # 例: "東京都千代田区", "渋谷駅周辺", "大阪市北区"
    disaster_type: Optional[str] = None,      # 例: "地震", "洪水", "台風", "earthquake", "flood" (日本語または英語のキー)
    additional_keywords: Optional[List[str]] = None,
    max_queries: int = 5  # 生成するクエリの最大数
) -> List[str]:
    """
    ユーザーの場所、災害の種類、追加のキーワードに基づいて、
    Web検索に適したクエリのリストを生成します。
    信頼性の高い情報源を優先するクエリも生成に含めることを試みます。

    Args:
        user_location_name (Optional[str]): 検索クエリに含める地名。
        disaster_type (Optional[str]): 災害の種類 (日本語または英語)。
                                      DISASTER_KEYWORDS_MAP に定義されているキーと照合。
        additional_keywords (Optional[List[str]]): クエリに追加する自由なキーワードのリスト。
        max_queries (int): 返すクエリの最大数。

    Returns:
        List[str]: 生成されたWeb検索クエリのリスト。
                   場所情報がない場合は空のリストを返すことがあります。
    """
    # Generating web search queries

    if not user_location_name or not user_location_name.strip():
        logger.warning("User location name is not provided or empty. Cannot generate location-specific queries.")
        # 場所が不明な場合、災害種別のみでの検索も考えられるが、現在の設計では場所名を必須とする。
        # もし汎用的なクエリが必要な場合は、別途 disaster_type のみで生成するロジックを追加。
        return []

    # 場所名の前後の空白を除去
    cleaned_location_name = user_location_name.strip()
    base_query_prefix = f"{cleaned_location_name} " # クエリの基本部分（場所名 + 半角スペース）

    queries_set: Set[str] = set() # 重複を避けるためにセットを使用

    # 1. 災害種別に基づいたクエリ生成
    specific_disaster_keywords: List[str] = []
    if disaster_type:
        dt_lower = disaster_type.lower() # 大文字・小文字を区別しないために小文字化
        # マップから該当する災害種別のキーワードリストを取得
        specific_disaster_keywords = DISASTER_KEYWORDS_MAP.get(dt_lower, [])
        if not specific_disaster_keywords and disaster_type: # マップにないがdisaster_typeが指定されている場合
             # その災害種別名をそのままキーワードとして使用
            specific_disaster_keywords = [disaster_type]

        for keyword in specific_disaster_keywords:
            queries_set.add(f"{base_query_prefix}{keyword}".strip())
            # 災害種別と場所名を逆にしたパターンも有効な場合がある
            # queries_set.add(f"{keyword} {cleaned_location_name}".strip())

    # 2. 災害種別が不明、または補足として一般的な災害キーワードも追加
    # (災害種別が特定されている場合でも、一般的な情報を補完する意味でいくつか追加も検討可能)
    if not disaster_type or not specific_disaster_keywords: # 災害タイプ未指定か、上記でキーワードが見つからなかった場合
        for general_keyword in GENERAL_DISASTER_KEYWORDS:
            queries_set.add(f"{base_query_prefix}{general_keyword}".strip())

    # 3. 追加のキーワードに基づくクエリ生成
    if additional_keywords:
        for extra_keyword in additional_keywords:
            if extra_keyword and extra_keyword.strip():
                # 場所名 + 追加キーワード
                queries_set.add(f"{base_query_prefix}{extra_keyword.strip()}".strip())
                # 場所名 + 災害種別 (もしあれば) + 追加キーワード
                if disaster_type and specific_disaster_keywords: # specific_disaster_keywords があれば、より具体的な災害名が取れる
                    for dk in specific_disaster_keywords[:1]: # 代表的な災害キーワードを1つ使う
                        queries_set.add(f"{base_query_prefix}{dk} {extra_keyword.strip()}".strip())
                elif disaster_type: # specific_disaster_keywords がなくても disaster_type があればそれを使う
                     queries_set.add(f"{base_query_prefix}{disaster_type} {extra_keyword.strip()}".strip())


    # 4. 公式サイトを優先するクエリの生成
    #    場所名と言葉（"災害情報"、"避難情報"、または災害種別名）の組み合わせを公式ドメインで検索
    official_search_terms: List[str] = ["災害情報", "避難情報"]
    if disaster_type:
        # マップに定義された災害名を使う (例: "地震"、"洪水")
        # disaster_type が英語の場合、日本語名に変換するロジックがあればより良い
        # ここでは簡単のため、直接 disaster_type を使うか、マップのキーから探す
        dt_lower = disaster_type.lower()
        mapped_keywords = DISASTER_KEYWORDS_MAP.get(dt_lower)
        if mapped_keywords and mapped_keywords[0]: # マップにあれば、その代表的なキーワードを使う
            official_search_terms.append(mapped_keywords[0].split(" ")[0]) # "地震 最新情報" -> "地震"
        elif disaster_type: # マップになくてもdisaster_typeが指定されていればそれを使う
            official_search_terms.append(disaster_type)

    for term in set(official_search_terms): # 重複する可能性のある用語を除去
        for site_specifier in OFFICIAL_SITE_SPECIFIERS:
            queries_set.add(f"{site_specifier} {cleaned_location_name} {term}".strip())
            # 順番を変えたクエリも追加 (例: "東京都 site:go.jp 地震")
            queries_set.add(f"{cleaned_location_name} {site_specifier} {term}".strip())


    # 生成されたクエリのリスト化と最大数制限
    # (セットからリストに変換することで順序は保証されなくなるが、ここでは問題ないと判断)
    final_queries = list(queries_set)

    # クエリが長すぎる場合の調整（Google検索は一般的に非常に長いクエリも扱えるが、常識的な範囲で）
    # ここでは特に制限しないが、必要であれば文字数チェックなどを追加

    # 生成されたクエリの優先順位付け (例: 具体的なもの、公式サイト指定のものを優先)
    # 現在はセットからの変換順だが、より洗練された優先順位付けも可能
    # 例えば、disaster_type が明確なものを先頭に、次に general、最後に site: 指定など。
    # 現状の実装では、セットに追加された順序にある程度依存する。

    if not final_queries:
        logger.info(f"No specific queries generated for location='{cleaned_location_name}', disaster_type='{disaster_type}'. "
                    f"Consider adding a default query.")
        # フォールバックとして、場所名だけのクエリや、場所名＋一般的な"災害情報"を追加することも可能
        # queries_set.add(f"{cleaned_location_name} 災害情報 最新".strip())
        # final_queries = list(queries_set)


    # 最大クエリ数に制限
    limited_queries = final_queries[:max_queries]

    logger.info(f"Generated {len(limited_queries)} web search queries (limit {max_queries}): {limited_queries}")
    return limited_queries

# --- 関数のテスト用 (直接実行された場合) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    test_cases = [
        {"location": "東京都港区", "disaster": "地震", "keywords": ["高層マンション", "ペット"], "max_q": 7},
        {"location": "大阪市中央区", "disaster": "flood", "keywords": None, "max_q": 5},
        {"location": "札幌市", "disaster": "大雪", "keywords": ["孤立", "暖房"], "max_q": 6},
        {"location": "福岡市博多区", "disaster": None, "keywords": ["緊急避難場所"], "max_q": 4},
        {"location": "名古屋市中村区", "disaster": "unknown_disaster", "keywords": ["帰宅困難"], "max_q": 5}, # マップにない災害
        {"location": "  横浜市西区  ", "disaster": "台風 ", "keywords": ["停電"], "max_q": 5}, # 前後にスペース
        {"location": "京都府京都市", "disaster": "earthquake", "keywords": ["文化財", "観光客"], "max_q": 8},
        {"location": "沖縄県那覇市", "disaster": "津波", "keywords": None, "max_q": 3},
        {"location": "仙台市青葉区", "disaster": "地震", "keywords": [], "max_q": 5}, # keywordsが空リスト
        {"location": "広島市中区", "disaster": "大雨", "max_q": 4},
        {"location": "神戸市", "max_q": 3}, # disaster_type と keywords が None
        {"location": None, "disaster": "地震", "max_q": 5}, # 場所がない
        {"location": "  ", "disaster": "地震", "max_q": 5}, # 場所が空白
    ]

    for i, case in enumerate(test_cases):
        generated_q = generate_disaster_web_search_queries(
            user_location_name=case.get("location"),
            disaster_type=case.get("disaster"),
            additional_keywords=case.get("keywords"),
            max_queries=case.get("max_q", 5) # デフォルト値を設定
        )
        if generated_q:
            for q_item in generated_q:
                pass
        else:
            pass
