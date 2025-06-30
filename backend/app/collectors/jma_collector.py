# backend/app/collectors/jma_collector.py
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.utils.http_client import HTTPClient

logger = logging.getLogger(__name__)

# JMAXML名前空間定義
NAMESPACES = {
    'jmx': 'http://xml.kishou.go.jp/jmaxml1/',
    'jmx_eb': 'http://xml.kishou.go.jp/jmaxml1/elementBasis1/',
    'jmx_ib': 'http://xml.kishou.go.jp/jmaxml1/informationBasis1/',
    'jmx_add': 'http://xml.kishou.go.jp/jmaxml1/addition1/',
}

class JMACollector:
    def __init__(self, http_client: Any = None):
        # テスト時は外部から http_client をモックで注入
        self.http_client = http_client or HTTPClient()

    @staticmethod
    async def fetch_xml_feed(
        session: Any,  # aiohttp.ClientSession
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            # aiohttpのClientSessionを使用
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                text = await resp.text()
            
            # XMLパース
            root = ET.fromstring(text)
            
            # Atom名前空間
            ns = "{http://www.w3.org/2005/Atom}"
            
            # エントリを辞書のリストに変換
            entries = []
            for entry in root.findall(f"{ns}entry"):
                entry_dict = {
                    "id": entry.findtext(f"{ns}id"),
                    "title": entry.findtext(f"{ns}title"),
                    "updated": entry.findtext(f"{ns}updated"),
                    "author": {"name": entry.find(f"{ns}author/{ns}name").text if entry.find(f"{ns}author/{ns}name") is not None else None},
                    "link": entry.find(f"{ns}link").get("href") if entry.find(f"{ns}link") is not None else None,
                    "content": {"text": entry.findtext(f"{ns}content")}
                }
                
                # 必須フィールドチェック
                if entry_dict["id"] and entry_dict["updated"]:
                    entries.append(entry_dict)
                else:
                    logger.warning(f"Skipping entry with missing fields: {entry_dict}")
            
            return entries

        except ET.ParseError as e:
            logger.error("XML parsing error: %s", e)
            return None
        except Exception as e:
            logger.error("Failed to fetch feed from %s: %s", url, e)
            return None
    
    @staticmethod
    async def fetch_jmaxml_document(
        session: Any,  # aiohttp.ClientSession
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        個別のJMAXML電文を取得して三層構造（管理部/ヘッダ部/内容部）をパース
        
        Returns:
            Dict with keys: control, head, body
        """
        try:
            # JMAXMLドキュメントを取得
            async with session.get(url, headers=headers, timeout=10) as resp:
                resp.raise_for_status()
                text = await resp.text()
            
            # XMLパース（名前空間付き）
            root = ET.fromstring(text)
            
            # 三層構造を抽出
            result = {
                "url": url,
                "control": JMACollector._parse_control(root),
                "head": JMACollector._parse_head(root),
                "body": JMACollector._parse_body(root),
                "raw_xml": text[:1000] + "..." if len(text) > 1000 else text  # デバッグ用
            }
            
            return result
            
        except ET.ParseError as e:
            logger.error(f"JMAXML parsing error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch JMAXML from {url}: {e}")
            return None
    
    @staticmethod
    def _parse_control(root: ET.Element) -> Dict[str, Any]:
        """管理部（Control）をパース"""
        # デフォルト名前空間を使用
        ns = 'http://xml.kishou.go.jp/jmaxml1/'
        control = root.find(f'.//{{{ns}}}Control')
        if control is None:
            return {}
        
        return {
            "title": control.findtext(f'{{{ns}}}Title', ''),
            "date_time": control.findtext(f'{{{ns}}}DateTime', ''),
            "status": control.findtext(f'{{{ns}}}Status', ''),
            "editorial_office": control.findtext(f'{{{ns}}}EditorialOffice', ''),
            "publishing_office": control.findtext(f'{{{ns}}}PublishingOffice', ''),
        }
    
    @staticmethod
    def _parse_head(root: ET.Element) -> Dict[str, Any]:
        """ヘッダ部（Head）をパース"""
        ns = 'http://xml.kishou.go.jp/jmaxml1/'
        head = root.find(f'.//{{{ns}}}Head')
        if head is None:
            return {}
        
        result = {
            "title": head.findtext(f'{{{ns}}}Title', ''),
            "report_date_time": head.findtext(f'{{{ns}}}ReportDateTime', ''),
            "target_date_time": head.findtext(f'{{{ns}}}TargetDateTime', ''),
            "event_id": head.findtext(f'{{{ns}}}EventID', ''),
            "info_type": head.findtext(f'{{{ns}}}InfoType', ''),
            "serial": head.findtext(f'{{{ns}}}Serial', ''),
            "info_kind": head.findtext(f'{{{ns}}}InfoKind', ''),
            "info_kind_version": head.findtext(f'{{{ns}}}InfoKindVersion', ''),
        }
        
        # Headline（見出し）
        headline = head.find(f'{{{ns}}}Headline')
        if headline is not None:
            result["headline"] = {
                "text": headline.findtext(f'{{{ns}}}Text', ''),
                "areas": JMACollector._parse_areas(headline),
            }
        
        return result
    
    @staticmethod
    def _parse_body(root: ET.Element) -> Dict[str, Any]:
        """内容部（Body）をパース - 電文種別により内容が異なる"""
        ns = 'http://xml.kishou.go.jp/jmaxml1/'
        body = root.find(f'.//{{{ns}}}Body')
        if body is None:
            return {}
        
        result = {}
        
        # 地震情報の名前空間
        seis_ns = 'http://xml.kishou.go.jp/jmaxml1/body/seismology1/'
        mete_ns = 'http://xml.kishou.go.jp/jmaxml1/body/meteorology1/'
        
        # 警報・注意報情報
        warning = body.find(f'.//{{{mete_ns}}}Warning')
        if warning is not None:
            result["warning"] = JMACollector._parse_warning(warning)
        
        # 地震情報
        earthquake = body.find(f'.//{{{seis_ns}}}Earthquake')
        if earthquake is not None:
            result["earthquake"] = JMACollector._parse_earthquake(earthquake)
        
        # 津波情報
        tsunami = body.find(f'.//{{{seis_ns}}}Tsunami')
        if tsunami is not None:
            result["tsunami"] = JMACollector._parse_tsunami(tsunami)
        
        return result
    
    @staticmethod
    def _parse_areas(parent: ET.Element) -> List[Dict[str, Any]]:
        """地域情報をパース"""
        ns = 'http://xml.kishou.go.jp/jmaxml1/'
        areas = []
        for area in parent.findall(f'.//{{{ns}}}Area'):
            area_dict = {
                "name": area.findtext(f'{{{ns}}}Name', ''),
                "code": area.findtext(f'{{{ns}}}Code', ''),
            }
            
            # 座標情報があれば追加
            coordinate = area.findtext(f'.//{{{ns}}}Coordinate', '')
            if coordinate:
                area_dict["coordinate"] = coordinate
            
            # 空の辞書は追加しない
            if area_dict.get('name') or area_dict.get('code'):
                areas.append(area_dict)
        
        return areas
    
    @staticmethod
    def _parse_warning(warning: ET.Element) -> Dict[str, Any]:
        """警報・注意報情報をパース"""
        items = []
        for item in warning.findall('.//Item', NAMESPACES):
            item_dict = {
                "areas": JMACollector._parse_areas(item),
                "kinds": []
            }
            
            # 警報・注意報の種別
            for kind in item.findall('.//Kind', NAMESPACES):
                kind_dict = {
                    "name": kind.findtext('Name', '', NAMESPACES),
                    "code": kind.findtext('Code', '', NAMESPACES),
                    "status": kind.findtext('Status', '', NAMESPACES),
                }
                item_dict["kinds"].append(kind_dict)
            
            items.append(item_dict)
        
        return {"items": items}
    
    @staticmethod
    def _parse_earthquake(earthquake: ET.Element) -> Dict[str, Any]:
        """地震情報をパース"""
        result = {}
        
        # 震源情報
        hypocenter = earthquake.find('.//Hypocenter', NAMESPACES)
        if hypocenter is not None:
            result["hypocenter"] = {
                "name": hypocenter.findtext('.//Name', '', NAMESPACES),
                "coordinate": hypocenter.findtext('.//jmx_eb:Coordinate', '', NAMESPACES),
            }
        
        # マグニチュード
        magnitude = earthquake.findtext('.//jmx_eb:Magnitude', '', NAMESPACES)
        if magnitude:
            result["magnitude"] = magnitude
        
        return result
    
    @staticmethod
    def _parse_tsunami(tsunami: ET.Element) -> Dict[str, Any]:
        """津波情報をパース"""
        # 基本実装 - 必要に応じて詳細化
        return {
            "observation": tsunami.findtext('.//Observation', '', NAMESPACES),
            "estimation": tsunami.findtext('.//Estimation', '', NAMESPACES),
        }
