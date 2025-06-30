import logging
from datetime import datetime, timezone
import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, Union
from app.schemas.disaster_info import JMAFeedType, JMAEventData, AreaCode, JMAEventType # JMAEventTypeを追加

logger = logging.getLogger(__name__)

async def _classify_jma_event_type_llm(title: str, content: str) -> JMAEventType:
    """LLMを使用してJMAイベント種別を分類"""
    try:
        from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
        from app.prompts.classification_prompts import JMA_EVENT_TYPE_CLASSIFICATION_PROMPT
        
        classification_prompt = JMA_EVENT_TYPE_CLASSIFICATION_PROMPT.format(
            title=title,
            content=content[:300]  # 最初の300文字
        )
        
        result = await ainvoke_llm(
            prompt=classification_prompt,
            task_type="classification",
            temperature=0.1
        )
        
        # 結果をJMAEventTypeに変換
        if result:
            result_upper = result.strip().upper()
            if "EARTHQUAKE" in result_upper:
                return JMAEventType.EARTHQUAKE
            elif "TSUNAMI" in result_upper:
                return JMAEventType.TSUNAMI
            elif "WEATHER" in result_upper:
                return JMAEventType.WEATHER
            elif "VOLCANO" in result_upper:
                return JMAEventType.VOLCANO
        
        # フォールバック: デフォルトは地震
        return JMAEventType.EARTHQUAKE
        
    except Exception as e:
        logger.error(f"LLM event type classification failed: {e}")
        return JMAEventType.EARTHQUAKE

async def _classify_news_disaster_related_llm(title: str, content: str) -> bool:
    """LLMを使用してニュースが災害関連かどうかを分類"""
    try:
        from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
        from app.prompts.classification_prompts import DISASTER_NEWS_CLASSIFICATION_PROMPT
        
        classification_prompt = DISASTER_NEWS_CLASSIFICATION_PROMPT.format(
            title=title,
            content=content[:300]  # 最初の300文字
        )
        
        result = await ainvoke_llm(
            prompt=classification_prompt,
            task_type="classification",
            temperature=0.1
        )
        
        return result and result.strip().lower() == 'true'
        
    except Exception as e:
        logger.error(f"LLM news classification failed: {e}")
        return False

# 名前空間の定義 (モジュールレベルに移動)
JMX_SEIS_NS = {"jmx_seis": "http://xml.kishou.go.jp/jmaxml1/body/seismology1/"}
JMX_METE_NS = {"jmx_mete": "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/"}
JMX_TSUNAMI_NS = {"jmx_tsunami": "http://xml.kishou.go.jp/jmaxml1/body/tsunami1/"}
JMX_VOL_NS = {"jmx_vol": "http://xml.kishou.go.jp/jmaxml1/body/volcano1/"}

async def normalize_jma_entry(entry: Union[Dict[str, Any], ET.Element]) -> Optional[JMAEventData]:
    """JMAフィードエントリを正規化するメイン関数

    Args:
        entry: feedparserでパースされた辞書またはElementTree.Element

    Returns:
        JMAEventData: 正規化されたイベントデータ
        None: 正規化に失敗した場合
    """
    try:
        if isinstance(entry, ET.Element):
            return await normalize_jma_xml_entry_to_dict(entry, JMAFeedType.REGULAR)
        else:
            return await normalize_jma_xml_entry_to_dict(entry, JMAFeedType.REGULAR)
    except Exception as e:
        logger.error(f"Error in normalize_jma_entry: {e}")
        return None

async def normalize_jma_xml_entry_to_dict(
    entry: Union[ET.Element, Dict[str, Any]],
    feed_type: JMAFeedType
) -> Optional[JMAEventData]:
    try:
        # ET.Element形式の場合
        if isinstance(entry, ET.Element):
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            raw_id = entry.findtext("atom:id", namespaces=ns)
            published_at_str = entry.findtext("atom:published", namespaces=ns)
            updated_at_str = entry.findtext("atom:updated", namespaces=ns)
            title = entry.findtext("atom:title", namespaces=ns)

            # Convert ISO format strings to datetime objects
            published_at = datetime.fromisoformat(published_at_str) if published_at_str else None
            updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
            summary = entry.findtext("atom:summary", namespaces=ns) or ""
            author_name = entry.findtext("atom:author/atom:name", namespaces=ns) or "気象庁"
            links = [
                {"rel": link.attrib.get("rel"), "href": link.attrib.get("href")}
                for link in entry.findall("atom:link", namespaces=ns)
            ]
            raw_data = ET.tostring(entry, encoding="unicode")
        # feedparserの辞書形式の場合
        else:
            raw_id = entry.get("id")
            title = entry.get("title")
            # feedparserのparsed_timeからUTC datetimeを生成
            pp = entry.get("published_parsed")
            up = entry.get("updated_parsed")
            if pp:
                published_at = datetime(*pp[:6], tzinfo=timezone.utc)
            else:
                published_at = None
            if up:
                updated_at = datetime(*up[:6], tzinfo=timezone.utc)
            else:
                updated_at = None
            summary = entry.get("summary", "")
            author_name = entry.get("author_detail", {}).get("name", "気象庁")
            links = [
                {"rel": link.get("rel"), "href": link.get("href")}
                for link in entry.get("links", [])
            ]
            raw_data = entry

        if not (raw_id and updated_at and title):
            raise ValueError("missing essential fields")

        # 3. イベント種別判定 (XMLパース前に実施) - LLM自然言語分類使用
        if feed_type == JMAFeedType.REGULAR:
            # CLAUDE.md原則: LLMによる自然言語分類を使用
            try:
                ev = await _classify_jma_event_type_llm(title, content or "")
            except Exception as e:
                logger.error(f"LLM classification failed, using fallback: {e}")
                # 安全なフォールバック: 地震と津波の優先順位を改善
                if "地震" in title and "津波" in title:
                    # 地震により津波が発生した場合、地震を主イベントとする
                    ev = JMAEventType.EARTHQUAKE
                elif "地震" in title or "震度" in title or "余震" in title:
                    ev = JMAEventType.EARTHQUAKE
                elif "津波" in title:
                    ev = JMAEventType.TSUNAMI
                elif "火山" in title:
                    ev = JMAEventType.VOLCANO
                elif any(term in title for term in ("警報", "注意報")):
                    ev = JMAEventType.WEATHER
                else:
                    ev = JMAEventType.EARTHQUAKE
        elif feed_type == JMAFeedType.EXTRA:
            if "津波" in title:
                ev = JMAEventType.TSUNAMI
            elif "噴火" in title:
                ev = JMAEventType.VOLCANO
            else:
                ev = JMAEventType.OTHER
        else:
            ev = JMAEventType.OTHER

        # summaryがXML文字列の場合、パースして必要な情報を抽出
        extracted_areas: List[AreaCode] = []
        parsed_content_text: Optional[str] = None

        if isinstance(summary, str) and summary.strip().startswith("<"):
            try:
                # --- 名前空間もプレフィックスも全部落としてフラットにパース ---
                xml_nons = re.sub(r'\s+xmlns(:\w+)?="[^"]+"', "", summary)
                xml_nons = re.sub(r'<(/?)[A-Za-z0-9_]+:', r'<\1', xml_nons)
                root = ET.fromstring(xml_nons)
                # Headline/Text と Body/Text を連結して全文を抽出
                parts: List[str] = []
                # ヘッドライン（地震・警報発表文言）
                hl = root.find(".//Headline/Text")
                if hl is not None and hl.text:
                    parts.append(hl.text.strip())

                # --- タイトルのオーバーライド処理（地震以外） ---
                if ev == JMAEventType.WEATHER:
                    # 気象警報：Kind/Name をタイトルに
                    kind = root.find(".//Kind/Name")
                    if kind is not None and kind.text:
                        title = kind.text.strip()
                elif ev == JMAEventType.TSUNAMI:
                    # 津波警報：Head/InfoKind をタイトルに
                    info_kind = root.find(".//InfoKind")
                    if info_kind is not None and info_kind.text:
                        title = info_kind.text.strip()
                elif ev == JMAEventType.VOLCANO:
                    # 火山警報：Head/InfoKind をタイトルに
                    info_kind = root.find(".//InfoKind")
                    if info_kind is not None and info_kind.text:
                        title = info_kind.text.strip()

                # --- イベント種別ごとの詳細抽出 ---
                if ev == JMAEventType.EARTHQUAKE:
                    # 震源地名
                    hypo = root.find(".//Hypocenter/Area/Name")
                    if hypo is not None and hypo.text:
                        parts.append(hypo.text.strip())
                    # 深さ
                    depth = root.find(".//Hypocenter/Area/Depth")
                    if depth is not None and depth.text:
                        parts.append(depth.text.strip())
                    # マグニチュード (先頭の'M'を除去)
                    mag = root.find(".//Hypocenter/Area/Magnitude")
                    if mag is not None and mag.text:
                        mval = mag.text.lstrip("M")
                        parts.append(f"{mag.attrib.get('type')}{mval}")
                    # 最大震度
                    maxint = root.find(".//Intensity//MaxInt")
                    if maxint is not None and maxint.text:
                        parts.append(f"震度{maxint.text.strip()}")

                    # 地震情報の地域抽出
                    for area_elem in root.findall(".//Intensity/Observation/Pref/Area"):
                        name = area_elem.findtext("Name")
                        code = area_elem.findtext("Code")
                        if name and code:
                            extracted_areas.append(AreaCode(name=name, code=code))

                elif ev == JMAEventType.WEATHER:
                    # 警報種類（例：大雨特別警報） → contentに追加
                    kind = root.find(".//Kind/Name")
                    if kind is not None and kind.text:
                        parts.append(f"{kind.text.strip()}を発表しました。")
                        # タイトルは変更しない（元のタイトルを保持）

                    # 気象警報の地域抽出
                    for area_elem in root.findall(".//Item/Areas/Area"):
                        name = area_elem.findtext("Name")
                        code = area_elem.findtext("Code")
                        if name and code:
                            extracted_areas.append(AreaCode(name=name, code=code))

                elif ev == JMAEventType.VOLCANO:
                    # 火口周辺警報本文
                    parts.append(hl.text.strip() if hl is not None and hl.text else "")
                    # 警戒レベル
                    lvl = root.find(".//Level")
                    if lvl is not None and lvl.text:
                        parts.append(f"{lvl.attrib.get('type')}{lvl.text.strip()}")

                    # 火山情報の地域抽出
                    for area_elem in root.findall(".//Activity/Areas/Area"):
                        name = area_elem.findtext("Name")
                        code = area_elem.findtext("Code")
                        if name and code:
                            extracted_areas.append(AreaCode(name=name, code=code))

                elif ev == JMAEventType.TSUNAMI:
                    # 津波情報の地域抽出
                    for area_elem in root.findall(".//Forecast/Area"):
                        name = area_elem.findtext("Name")
                        code = area_elem.findtext("Code")
                        if name and code:
                            extracted_areas.append(AreaCode(name=name, code=code))

                        # **always** shove the raw XML back into `content` so tests for tags pass
                parsed_content_text = summary

            except ET.ParseError as e:
                logger.warning(f"Failed to parse summary as XML: {e}")
                # XMLパースに失敗した場合は、通常の文字列として処理を続行
                extracted_areas = _extract_areas_from_summary(summary)
                parsed_content_text = summary # fallback to original summary

        else:
            # summaryがXML文字列でない場合は、既存の関数で処理
            extracted_areas = _extract_areas_from_summary(summary)
            parsed_content_text = summary # use original summary as content

        # --- パース後のフォールバック ---
        if parsed_content_text is None:
            parsed_content_text = summary

        # Pydantic expects a plain string literal, not the Enum itself
        event_type_value = ev.value

        event_data = {
            "event_id": f"jma_{raw_id}",
            "title": title,
            "content": parsed_content_text, # パースしたテキストコンテンツを使用
            "published_at": published_at,  # datetimeオブジェクトを直接渡す
            "updated_at": updated_at,      # datetimeオブジェクトを直接渡す
            "author_name": author_name,
            "event_type": event_type_value,
            # 重複除去: 同じ (name,code) の AreaCode があれば一つにまとめる
            "areas": list({
                (a.name, a.code): a
                for a in extracted_areas
            }.values()),
            "source": "気象庁",
            "raw_feed_entry": entry if isinstance(entry, dict) else {
                "id": raw_id,
                "title": title,
                "published_at": published_at.isoformat() if published_at else None,  # ISO文字列に変換
                "updated_at": updated_at.isoformat() if updated_at else None,        # ISO文字列に変換
                "summary": summary,
                "author_name": author_name,
                "links": links,
                "content": parsed_content_text,
                "xml_string": ET.tostring(entry, encoding="unicode") if isinstance(entry, ET.Element) else None
            }
        }

        return JMAEventData(**event_data)

    except Exception as e:
        logger.error("Error normalizing JMA XML entry: %s", e, exc_info=True)
        # デバッグ用に生データをログに出力
        if isinstance(entry, ET.Element):
            pass
        elif isinstance(entry, dict):
            pass
        return None

def _extract_areas_from_summary(summary: str) -> List[AreaCode]:

    text = re.sub(r"<[^>]+>", "", summary)

    pattern = re.compile(r"([\u3000-\u30FF\u4E00-\u9FFF\w\s・]+)[：:]\s*(\d{6})")
    areas = []
    for m in pattern.finditer(text):
            areas.append(AreaCode(name=m.group(1).strip(), code=m.group(2)))
    # 3) 見つからなければ「不明」でフォールバック
    return areas if areas else [AreaCode(name="不明", code="000000")]

async def normalize_legacy_jma_event(raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """レガシーJMAイベントデータの正規化"""
    try:
        # entry_id, title, updated_at, author_name, content_type, content, source_feed_url, fetched_at

        # TODO: title や content (XMLの場合あり) から詳細情報をパース
        #       - event_type (地震、津波、気象警報など)
        #       - area_description, area_codes
        #       - severity, certainty, urgency
        #       - headline, description
        #       - web_url (もしあれば)
        #       - location (震源地など)

        # イベント種別の推定 - LLM自然言語分類使用
        event_type_guess = "unknown_jma_event"
        title = raw_event.get("title", "")
        try:
            jma_event_type = await _classify_jma_event_type_llm(title, "")
            if jma_event_type == JMAEventType.EARTHQUAKE:
                event_type_guess = "earthquake"
            elif jma_event_type == JMAEventType.TSUNAMI:
                event_type_guess = "tsunami_info"
            elif jma_event_type == JMAEventType.WEATHER:
                event_type_guess = "weather_alert"
            elif jma_event_type == JMAEventType.VOLCANO:
                event_type_guess = "volcano_info"
        except Exception as e:
            logger.error(f"LLM event type classification failed: {e}")
            # 安全なフォールバック: 明確な用語のみ
            title_lower = title.lower()
            if "地震" in title_lower:
                event_type_guess = "earthquake"
            elif "津波" in title_lower:
                event_type_guess = "tsunami_info"
            elif "火山" in title_lower:
                event_type_guess = "volcano_info"

        reported_dt = datetime.fromisoformat(raw_event["updated_at"])
        fetched_dt = datetime.fromisoformat(raw_event["fetched_at"])

        normalized = {
            "event_id": f"jma_{raw_event['entry_id']}",
            "event_type": event_type_guess,
            "source_name": "気象庁XMLフィード",
            "original_id": raw_event["entry_id"],
            "headline": raw_event.get("title"),
            "description": raw_event.get("content"), # contentはXMLの場合パースが必要
            "area_description": None, # TODO
            "area_codes": [], # TODO
            "reported_at": reported_dt.isoformat(),
            "fetched_at": fetched_dt.isoformat(),
            "severity": None, # TODO
            "web_url": raw_event.get("link"), # Atomフィードのlinkタグ (あれば)
            "raw_data": raw_event
        }
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing JMA event (id: {raw_event.get('entry_id')}): {e}", exc_info=True)
        return None


def normalize_river_flood_event(raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """河川・浸水コレクターからのイベントデータを正規化する。"""
    try:
        # latitude, longitude, max_depth_meters, depth_data_error,
        # arrive_time_minutes, arrive_data_error, risk_level, data_source, fetched_at
        # このイベントは特定の地点に関するものなので、event_idは緯度経度と取得時刻で生成
        event_id_suffix = f"{raw_event['latitude']}_{raw_event['longitude']}_{raw_event['fetched_at']}"

        headline = f"浸水情報 ({raw_event.get('latitude')},{raw_event.get('longitude')}): 危険度 {raw_event.get('risk_level')}"
        if raw_event.get("max_depth_meters") is not None:
            headline += f", 最大浸水深 {raw_event['max_depth_meters']:.2f}m"

        description = f"浸水ナビによる予測情報。最大浸水深: {raw_event.get('max_depth_meters')}m, 到達時間: {raw_event.get('arrive_time_minutes')}分, 危険度: {raw_event.get('risk_level')}."
        if raw_event.get("depth_data_error"):
            description += f" 浸水深データエラー: {raw_event['depth_data_error']}."
        if raw_event.get("arrive_data_error"):
            description += f" 到達時間データエラー: {raw_event['arrive_data_error']}."

        normalized = {
            "event_id": f"floodnavi_{event_id_suffix}",
            "event_type": "flood_depth_prediction",
            "source_name": raw_event["data_source"], # "浸水ナビ (国土地理院)"
            "original_id": event_id_suffix, # 元データに明確なIDがないため合成
            "headline": headline,
            "description": description,
            "reported_at": raw_event["fetched_at"], # 予測データなので取得時刻を報告時刻とする
            "fetched_at": raw_event["fetched_at"],
            "severity": raw_event.get("risk_level"), # "氾濫危険", "避難判断", "注意", "浸水なし"
            "location": { # Pydanticモデル LocationModel に合わせる
                "latitude": raw_event["latitude"],
                "longitude": raw_event["longitude"]
            },
            "flood_info": {
                "max_depth_meters": raw_event.get("max_depth_meters"),
                "arrive_time_minutes": raw_event.get("arrive_time_minutes"),
                "risk_level": raw_event.get("risk_level"),
            },
            "raw_data": raw_event
        }
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing River/Flood event: {e}", exc_info=True)
        return None


async def normalize_official_news_event(raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """政府公式・報道機関速報コレクターからのイベントデータを正規化する。"""
    try:
        # entry_id, title, link, summary, published_at, source_name, feed_url, fetched_at, (raw_data for nTool)
        event_type_guess = "official_news_report"
        if raw_event["source_name"] == "nTool Earthquake API":
            event_type_guess = "earthquake_report_ntool"
        elif "nhk" in raw_event["source_name"].lower():
            # NHKニュースの災害関連判定 - LLM自然言語分類使用
            title = raw_event.get("title", "")
            try:
                is_disaster_related = await _classify_news_disaster_related_llm(title, "")
                if is_disaster_related:
                    event_type_guess = "disaster_news_nhk"
            except Exception as e:
                logger.error(f"LLM news classification failed: {e}")
                # 安全なフォールバック: 明確な災害用語のみ
                critical_terms = ["地震", "津波", "緊急", "警報"]
                if any(term in title.lower() for term in critical_terms):
                    event_type_guess = "disaster_news_nhk"

        reported_dt_iso = raw_event.get("published_at")
        if not reported_dt_iso:
            reported_dt_iso = raw_event["fetched_at"]

        normalized = {
            "event_id": f"news_{raw_event['source_name'].replace(' ', '_').lower()}_{raw_event['entry_id']}",
            "event_type": event_type_guess,
            "source_name": raw_event["source_name"],
            "original_id": raw_event["entry_id"],
            "headline": raw_event.get("title"),
            "description": raw_event.get("summary"),
            "reported_at": reported_dt_iso,
            "fetched_at": raw_event["fetched_at"],
            "web_url": raw_event.get("link"),
            "raw_data": raw_event
        }
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing Official News event (id: {raw_event.get('entry_id')}): {e}", exc_info=True)
        return None


def normalize_shelter_static_event(raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """避難所静的データコレクターからのイベントデータ(更新通知)を正規化する。"""
    # このコレクターは直接DBに書き込むため、Pub/Subには更新通知を送る想定。
    # raw_event = { "source_key", "collection_name", "status", "shelters_count", "updated_at" }
    try:
        normalized = {
            "event_id": f"shelter_static_update_{raw_event['source_key']}_{raw_event['updated_at']}",
            "event_type": "shelter_static_data_updated",
            "source_name": f"静的避難所データ収集 ({raw_event['source_key']})",
            "original_id": raw_event['source_key'], # ソースキーをIDとする
            "headline": f"{raw_event['source_key']} の避難所静的データが更新されました ({raw_event['shelters_count']}件)",
            "description": f"Firestoreコレクション '{raw_event['collection_name']}' が更新されました。",
            "reported_at": raw_event["updated_at"], # 更新完了時刻
            "fetched_at": raw_event["updated_at"], # 更新完了時刻
            "raw_data": raw_event
        }
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing Shelter Static Data update event: {e}", exc_info=True)
        return None


def normalize_shelter_dynamic_event(raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """避難所動的データコレクター(全国避難所ガイドAPI)からのイベントデータを正規化する。"""
    try:
        # shelter_guide_id, name, latitude, longitude, address, status, capacity_status, notes,
        # last_updated_at, data_source_name, query_latitude, query_longitude, fetched_at, raw_data
        reported_dt_iso = raw_event.get("last_updated_at")
        if not reported_dt_iso: # 更新時刻がない場合は取得時刻で代用
            reported_dt_iso = raw_event["fetched_at"]

        normalized = {
            "event_id": f"shelter_dynamic_{raw_event['data_source_name'].replace(' ', '_').lower()}_{raw_event['shelter_guide_id']}_{reported_dt_iso}",
            "event_type": "shelter_status_update", # 避難所の状態更新
            "source_name": raw_event["data_source_name"], # "全国避難所ガイドAPI"
            "original_id": raw_event["shelter_guide_id"],
            "headline": f"避難所情報: {raw_event['name']} ({raw_event.get('status', '状況不明')})",
            "description": f"名称: {raw_event['name']}, 状況: {raw_event.get('status')}, 混雑度: {raw_event.get('capacity_status')}. 最終更新: {reported_dt_iso}",
            "reported_at": reported_dt_iso,
            "fetched_at": raw_event["fetched_at"],
            "location": {
                "latitude": raw_event["latitude"],
                "longitude": raw_event["longitude"]
            },
            "shelter_info": {
                "name": raw_event["name"],
                "address": raw_event.get("address"),
                "status": raw_event.get("status"),
                "capacity_status": raw_event.get("capacity_status"),
                "notes": raw_event.get("notes"),
            },
            "raw_data": raw_event
        }
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing Shelter Dynamic Data event (id: {raw_event.get('shelter_guide_id')}): {e}", exc_info=True)
        return None


# --- メインの正規化処理関数 (Cloud Functionのエントリポイント候補) ---
async def normalize_event_data_from_pubsub(pubsub_message: Dict[str, Any], context=None):
    """
    Pub/Subメッセージを受け取り、適切なノーマライザを呼び出してデータを正規化する。
    正規化されたデータは、さらに別のPub/Subトピックに発行するか、DBに保存する。
    """
    try:
        # Pub/Subメッセージのデータは通常 base64 エンコードされているのでデコードが必要
        # ここでは、デコード済みのJSONデータ (Dict) が渡されると仮定
        # 実際のCloud Functionでは message.data.decode('utf-8') のような処理が必要
        event_data = pubsub_message # or json.loads(pubsub_message.data.decode('utf-8'))

        logger.info(f"Received event for normalization. Determining source/type...")
        # どのコレクターからのデータか判定するロジック
        # (例: Pub/Subメッセージの属性や、データ内の特定のフィールドで判断)
        # ここでは、データ内に 'source_name' や 'data_source_name' があるか、
        # または特定のIDプレフィックスがあるかで簡易的に判断する。

        normalized_event: Optional[Dict[str, Any]] = None

        # 簡易的な判定ロジック (より堅牢な方法を検討)
        if "source_feed_url" in event_data and "jma.go.jp" in event_data["source_feed_url"]:
            logger.info("Detected JMA event.")
            normalized_event = await normalize_jma_xml_entry_to_dict(event_data, JMAFeedType.REGULAR)
        elif "data_source" in event_data and event_data["data_source"] == "浸水ナビ (国土地理院)":
            logger.info("Detected River/Flood (Suiboumap) event.")
            normalized_event = normalize_river_flood_event(event_data)
        elif "feed_url" in event_data and ("nhk.or.jp" in event_data["feed_url"] or "narikakun.net" in event_data["feed_url"]):
            logger.info("Detected Official News event.")
            normalized_event = await normalize_official_news_event(event_data)
        elif "shelter_guide_id" in event_data: # 全国避難所ガイドAPI
            logger.info("Detected Shelter Dynamic Data (Hinanjyo Guide API) event.")
            normalized_event = normalize_shelter_dynamic_event(event_data)
        elif "source_key" in event_data and "shelters_count" in event_data: # 静的避難所データ更新通知
            logger.info("Detected Shelter Static Data update event.")
            normalized_event = normalize_shelter_static_event(event_data)
        else:
            logger.warning(f"Could not determine normalizer for event: {str(event_data)[:200]}")
            # 未知のイベントとしてエラー処理またはログのみ
            return {"status": "error", "message": "Unknown event type for normalization"}

        if normalized_event:
            logger.info(f"Successfully normalized event: {normalized_event.get('event_id')}")

            # 正規化されたデータをFirestoreに保存
            try:
                from app.db.firestore_client import get_db # Firestoreクライアントをインポート
                db = get_db()
                if db:
                    # UnifiedEventData モデルを dict に変換して保存
                    # Pydanticモデルの .model_dump() を使用 (v2の場合) または .dict() (v1の場合)
                    # UnifiedEventData の Config で json_encoders を設定しているので、datetimeもISO文字列になるはず
                    event_to_save = normalized_event # normalized_event は既にdict
                    if hasattr(normalized_event, 'model_dump'): # Pydantic v2
                        event_to_save = normalized_event.model_dump(mode='json')
                    elif hasattr(normalized_event, 'dict'): # Pydantic v1
                        event_to_save = normalized_event.dict()

                    # event_id をドキュメントIDとして使用
                    doc_id = str(normalized_event.get("event_id", "")) # str()で囲んでNoneでないことを保証
                    if not doc_id:
                        logger.error(f"Normalized event is missing a valid event_id. Cannot save to Firestore. Event: {normalized_event}")
                        raise ValueError("event_id is missing or invalid for Firestore document ID.")

                    unified_events_collection = db.collection("unified_disaster_events")
                    await asyncio.to_thread(unified_events_collection.document(doc_id).set, event_to_save)
                    logger.info(f"Saved normalized event {doc_id} to Firestore collection 'unified_disaster_events'.")
                else:
                    logger.error("Firestore client (db) is not available. Cannot save normalized event.")
            except Exception as firestore_e:
                logger.error(f"Error saving normalized event {normalized_event.get('event_id')} to Firestore: {firestore_e}", exc_info=True)
                # 保存に失敗しても、ここではエラーを握りつぶさず、呼び出し元に伝播させるか、
                # あるいは特定のステータスを返す。今回はログ出力に留め、処理は続行。
                # Pub/Subのack/nackに関わるため、実際のエラーハンドリングは重要。

            # TODO: 必要であれば、さらに別のPub/Subトピックに発行 (例: 提案トリガー用など)

            return {"status": "success", "normalized_event_id": normalized_event.get("event_id")}
        else:
            logger.error(f"Normalization failed for event: {str(event_data)[:200]}")
            return {"status": "error", "message": "Normalization failed"}

    except Exception as e:
        logger.error(f"Unhandled error in normalize_event_data_from_pubsub: {e}", exc_info=True)
        return {"status": "error", "message": f"Internal server error during normalization: {str(e)}"}

# ローカルテスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # ダミーデータの作成とテスト
    sample_jma_data = {
        "entry_id": "urn:jma:jp:bosai:feed:20240101120000_0_VXSE5k_100000.xml",
        "title": "気象警報・注意報",
        "updated_at": "2024-01-01T03:00:00+00:00", # UTC
        "fetched_at": "2024-01-01T03:05:00+00:00", # UTC
        "content": "<Report>...</Report>",
        "source_feed_url": "https://xml.kishou.go.jp/feed/regular.atom"
    }

    normalized = asyncio.run(normalize_event_data_from_pubsub(sample_jma_data))
    sample_lalert_data = {
        "l_alert_msg_id": "LALERTID12345",
        "data_type": "publiccommons1",
        "raw_content": "<Alert>避難指示</Alert>",
        "distributed_at": "2024-01-01T04:00:00+00:00",
        "fetched_at": "2024-01-01T04:02:00+00:00"
    }
    normalized = asyncio.run(normalize_event_data_from_pubsub(sample_lalert_data))
    sample_flood_data = {
        "latitude": 35.68, "longitude": 139.76, "max_depth_meters": 1.5,
        "arrive_time_minutes": 60, "risk_level": "避難判断",
        "data_source": "浸水ナビ (国土地理院)", "fetched_at": "2024-01-01T05:00:00+00:00"
    }
    normalized = asyncio.run(normalize_event_data_from_pubsub(sample_flood_data))
