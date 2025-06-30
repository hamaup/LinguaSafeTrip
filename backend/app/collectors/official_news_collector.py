import logging
import asyncio
import httpx # For asynchronous HTTP requests
import feedparser # For parsing RSS/Atom feeds
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.utils.pubsub_utils import PubSubPublisher
# from app.db.redis_client import get_redis_client # Redisクライアント (重複排除用)

logger = logging.getLogger(__name__)

# NHKニュースRSSフィードURL (カテゴリ0: 主要ニュース)
NHK_NEWS_RSS_URL_CAT0 = "https://www3.nhk.or.jp/rss/news/cat0.xml"
# NHK生活・防災情報XアカウントのRSSフィード (例: Nitter経由など、公式RSSがない場合)
# X API v2 filtered-stream を使うのが望ましいが、ここではRSSポーリングの例としてコメントアウト
# NHK_SEIKATSU_BOUSAI_RSS_URL = "https://example-nitter-instance/nhk_seikatsu_bousai/rss"

# nTool 地震 API (代替情報源として記載あり)
NTOOL_EARTHQUAKE_API_URL = "https://dev.narikakun.net/webapi/earthquake/post_data.json"


# PubSub発行クライアントの初期化
try:
    pubsub_publisher = PubSubPublisher()
    # トピック名は汎用的なものにするか、情報源ごとに分けるか検討
    # ここでは "official-news-events" のような汎用トピックを仮定
    OFFICIAL_NEWS_PUBSUB_TOPIC = "official-news-events"
except ValueError as e:
    logger.error(f"Failed to initialize PubSubPublisher for Official News collector: {e}")
    pubsub_publisher = None
except Exception as e:
    logger.error(f"Unexpected error initializing PubSubPublisher for Official News collector: {e}")
    pubsub_publisher = None

# Redisクライアント (重複排除用)
# redis_client = get_redis_client()
SEEN_ARTICLE_KEY_PREFIX = "official_news:seen_ids:" # プレフィックス + 情報源名
SEEN_ID_EXPIRY_SECONDS = 3 * 24 * 60 * 60 # 3日間


async def fetch_feed_entries(session: httpx.AsyncClient, feed_url: str) -> List[feedparser.FeedParserDict]:
    """RSS/Atomフィードを取得し、エントリをパースして返す。"""
    try:
        response = await session.get(feed_url, timeout=120.0, follow_redirects=True)
        response.raise_for_status()

        # feedparserは同期的に動作するため、asyncio.to_threadで実行
        feed_data_str = response.text
        parsed_feed = await asyncio.to_thread(feedparser.parse, feed_data_str)

        if parsed_feed.bozo: # bozoが1の場合、何らかのパースエラーがある
            logger.warning(f"Feed at {feed_url} might be ill-formed. Bozo bit set. Error: {parsed_feed.get('bozo_exception')}")

        logger.info(f"Fetched {len(parsed_feed.entries)} entries from {feed_url}")
        return parsed_feed.entries
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching feed from {feed_url}: {e.response.status_code} - {e.response.text}", exc_info=True)
        return []
    except httpx.RequestError as e:
        logger.error(f"Request error fetching feed from {feed_url}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing feed from {feed_url}: {e}", exc_info=True)
        return []


def parse_rss_entry(entry: feedparser.FeedParserDict, source_name: str, feed_url: str) -> Optional[Dict[str, Any]]:
    """feedparserでパースされた単一エントリから情報を抽出する。"""
    try:
        entry_id = entry.get("id") or entry.get("link") # idがない場合はlinkを代替として使用
        title = entry.get("title")
        link = entry.get("link")
        summary = entry.get("summary")
        published_parsed = entry.get("published_parsed") # feedparserがパースしたdatetimeタプル

        if not entry_id or not title:
            logger.warning(f"Skipping RSS entry due to missing id/link or title: {entry}")
            return None

        published_at_iso = None
        if published_parsed:
            # datetimeタプルをdatetimeオブジェクトに変換し、ISO8601形式にする
            # feedparser は UTC でパースするとは限らないので、タイムゾーンを付与する必要がある
            # published_parsed は time.struct_time 形式
            try:
                # struct_time を naive datetime に変換
                dt_naive = datetime(*published_parsed[:6])
                # ここでは元フィードがJSTであると仮定し、JSTとしてタイムゾーンを付与後、UTCに変換
                # より正確にはフィードのタイムゾーン情報を確認する必要がある
                # もしフィードがタイムゾーン情報を含まない場合、発行元の標準時を仮定する
                # NHK RSSはJSTと思われる
                jst = timezone(timedelta(hours=9))
                dt_jst = dt_naive.replace(tzinfo=jst)
                published_at_iso = dt_jst.astimezone(timezone.utc).isoformat()
            except Exception as e_dt:
                logger.warning(f"Could not parse 'published_parsed' for entry {entry_id}: {published_parsed}. Error: {e_dt}")
                # パース失敗時は取得時刻を代替とするか、Noneのままにする
                published_at_iso = datetime.now(timezone.utc).isoformat() # フォールバック

        parsed_data = {
            "entry_id": entry_id, # 重複排除用キー
            "title": title,
            "link": link,
            "summary": summary,
            "published_at": published_at_iso,
            "source_name": source_name, # 例: "NHK News RSS"
            "feed_url": feed_url,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        return parsed_data
    except Exception as e:
        logger.error(f"Error parsing RSS entry: {e}. Entry: {entry}", exc_info=True)
        return None


async def fetch_ntool_earthquake_data(session: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """nTool地震APIからデータを取得する。"""
    try:
        response = await session.get(NTOOL_EARTHQUAKE_API_URL, timeout=120.0)
        response.raise_for_status()
        earthquake_data_list = response.json() # リスト形式で返ってくる想定

        if not isinstance(earthquake_data_list, list):
            logger.error(f"nTool Earthquake API did not return a list: {earthquake_data_list}")
            return []

        logger.info(f"Fetched {len(earthquake_data_list)} earthquake reports from nTool API.")

        processed_reports = []
        for report in earthquake_data_list:
            # nTool APIのデータ構造に合わせてパース
            # 例: report.get("id"), report.get("time"), report.get("hypocenter"), etc.
            # ここでは、主要な情報を抽出して共通フォーマットに近づける
            report_id = report.get("id_") # APIドキュメントによると id_
            if not report_id:
                logger.warning(f"Skipping nTool report due to missing id_: {report}")
                continue

            # 時刻情報は "YYYY/MM/DD hh:mm:ss" 形式のようなのでパース
            time_str = report.get("time")
            report_time_iso = None
            if time_str:
                try:
                    dt_naive = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
                    jst = timezone(timedelta(hours=9)) # JSTと仮定
                    report_time_iso = dt_naive.replace(tzinfo=jst).astimezone(timezone.utc).isoformat()
                except ValueError:
                    logger.warning(f"Could not parse time '{time_str}' from nTool report {report_id}")

            processed_report = {
                "entry_id": f"ntool_eq_{report_id}", # 重複排除用の一意なID
                "title": f"地震情報: {report.get('hypocenter', {}).get('name', '不明な震源地')} 最大震度{report.get('maxScale', '不明')}",
                "link": report.get("url"), # もしあれば
                "summary": f"発生時刻: {time_str}, 震源地: {report.get('hypocenter', {}).get('name')}, マグニチュード: {report.get('magnitude', {}).get('value')}, 最大震度: {report.get('maxScale')}",
                "published_at": report_time_iso,
                "source_name": "nTool Earthquake API",
                "feed_url": NTOOL_EARTHQUAKE_API_URL,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "raw_data": report # 元データも保持
            }
            processed_reports.append(processed_report)
        return processed_reports

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching nTool Earthquake API: {e.response.status_code} - {e.response.text}", exc_info=True)
        return []
    except httpx.RequestError as e:
        logger.error(f"Request error fetching nTool Earthquake API: {e}", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for nTool Earthquake API: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error processing nTool Earthquake API data: {e}", exc_info=True)
        return []


async def process_and_publish_entries(
    entries: List[Dict[str, Any]],
    source_name_for_seen_key: str
):
    """取得したエントリを処理し、Pub/Subに発行する。重複排除も行う。"""
    new_entries_count = 0
    if not entries:
        return new_entries_count

    for entry_data in entries:
        if not entry_data or not entry_data.get("entry_id"):
            continue

        # TODO: Redisを使った重複排除ロジック
        # seen_key = f"{SEEN_ARTICLE_KEY_PREFIX}{source_name_for_seen_key}"
        # if await redis_client.sismember(seen_key, entry_data["entry_id"]):
        #     logger.info(f"Skipping already seen entry_id: {entry_data['entry_id']} from {source_name_for_seen_key}")
        #     continue
        # await redis_client.sadd(seen_key, entry_data["entry_id"])
        # await redis_client.expire(seen_key, SEEN_ID_EXPIRY_SECONDS)

        if pubsub_publisher:
            publish_success = await pubsub_publisher.publish_message(OFFICIAL_NEWS_PUBSUB_TOPIC, entry_data)
            if publish_success:
                logger.info(f"Successfully published entry {entry_data['entry_id']} ({entry_data['source_name']}) to {OFFICIAL_NEWS_PUBSUB_TOPIC}")
                new_entries_count += 1
            else:
                logger.error(f"Failed to publish entry {entry_data['entry_id']}")
        else:
            logger.warning(f"PubSubPublisher not available. Entry {entry_data['entry_id']} not published.")
    return new_entries_count


async def collect_official_news_periodically(event=None, context=None):
    """
    政府公式・報道機関の速報を定期的に収集する。
    Cloud Schedulerなどから呼び出されることを想定。
    """
    logger.info("Starting Official News collection process...")
    total_new_entries = 0

    # 指数バックオフ用の状態管理 (インメモリ、永続化推奨)
    # backoff_state = {"nhk_rss": {"attempts": 0, "next_try_after": None}, ...}

    async with httpx.AsyncClient() as session:
        # 1. NHK News RSS
        try:
            logger.info(f"Fetching NHK News RSS from {NHK_NEWS_RSS_URL_CAT0}")
            nhk_entries_raw = await fetch_feed_entries(session, NHK_NEWS_RSS_URL_CAT0)
            nhk_parsed_entries = [
                parse_rss_entry(e, "NHK News RSS", NHK_NEWS_RSS_URL_CAT0) for e in nhk_entries_raw
            ]
            nhk_parsed_entries = [e for e in nhk_parsed_entries if e] # Noneを除外
            total_new_entries += await process_and_publish_entries(nhk_parsed_entries, "nhk_rss")
        except Exception as e:
            logger.error(f"Error processing NHK News RSS: {e}", exc_info=True)
            # TODO: 指数バックオフ処理

        await asyncio.sleep(1) # 負荷軽減

        # 2. nTool Earthquake API
        try:
            logger.info(f"Fetching nTool Earthquake API from {NTOOL_EARTHQUAKE_API_URL}")
            ntool_reports = await fetch_ntool_earthquake_data(session)
            total_new_entries += await process_and_publish_entries(ntool_reports, "ntool_eq")
        except Exception as e:
            logger.error(f"Error processing nTool Earthquake API: {e}", exc_info=True)
            # TODO: 指数バックオフ処理

        # 3. 首相官邸Xアカウント (X API v2 filtered-stream)
        # これはポーリングではなくストリーミング接続になるため、別の常時実行プロセスが必要。
        # ここでは一旦スキップし、別途実装する。
        logger.info("Skipping X (Twitter) stream for Kantei Saigai in this periodic collector. Requires separate stream processor.")


    logger.info(f"Official News collection process finished. Total new entries published: {total_new_entries}")
    return {"status": "completed", "new_entries_count": total_new_entries}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if os.getenv("GCP_PROJECT_ID"):
        asyncio.run(collect_official_news_periodically())
    else:
        logger.warning("GCP_PROJECT_ID is not set. Skipping Official News collector local test run.")
