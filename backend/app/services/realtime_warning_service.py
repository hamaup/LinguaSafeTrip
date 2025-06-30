"""
リアルタイム警報・注意報サービス
JMAのXMLフィードから最新の警報・注意報情報を取得
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
import httpx
import re

from app.schemas.hazard import Location
from app.db.firestore_client import get_db
from app.config import app_settings

logger = logging.getLogger(__name__)


class WarningInfo:
    """警報・注意報情報"""
    def __init__(self):
        self.warning_type: str = ""  # 警報・注意報の種類
        self.warning_code: str = ""  # 警報コード
        self.area_name: str = ""  # 対象地域名
        self.area_code: str = ""  # 地域コード
        self.condition: Optional[str] = None  # 条件（土砂災害など）
        self.severity: str = ""  # 重要度（警報/注意報）
        self.issued_at: datetime = datetime.now(timezone.utc)
        self.expires_at: Optional[datetime] = None
        
    def to_dict(self) -> dict:
        return {
            "warning_type": self.warning_type,
            "warning_code": self.warning_code,
            "area_name": self.area_name,
            "area_code": self.area_code,
            "condition": self.condition,
            "severity": self.severity,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class RealTimeWarningService:
    """リアルタイム警報・注意報サービス"""
    
    # JMA XMLフィードURL
    EXTRA_FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"
    
    # 警報コードと重要度のマッピング
    WARNING_SEVERITY = {
        "02": "特別警報",  # 大雨特別警報
        "03": "警報",      # 大雨警報
        "10": "注意報",    # 大雨注意報
        "04": "警報",      # 洪水警報
        "12": "注意報",    # 洪水注意報
        "05": "警報",      # 暴風警報
        "15": "注意報",    # 強風注意報
        "06": "警報",      # 暴風雪警報
        "16": "注意報",    # 風雪注意報
        "07": "警報",      # 大雪警報
        "17": "注意報",    # 大雪注意報
        "08": "警報",      # 波浪警報
        "18": "注意報",    # 波浪注意報
        "09": "警報",      # 高潮警報
        "19": "注意報",    # 高潮注意報
        "33": "特別警報",  # 土砂災害警戒情報
    }
    
    def __init__(self):
        """サービスの初期化"""
        self.client = httpx.AsyncClient(timeout=30.0)
        self.firestore_db = get_db()
        self.cache_collection = self.firestore_db.collection("warning_cache")
        self.area_code_collection = self.firestore_db.collection("area_codes")
        
    async def fetch_warnings_feed(self) -> str:
        """警報・注意報フィードを取得"""
        try:
            response = await self.client.get(self.EXTRA_FEED_URL)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch JMA feed: {e}")
            raise
    
    def parse_feed_entries(self, feed_xml: str) -> List[Dict[str, str]]:
        """フィードからエントリーを抽出"""
        entries = []
        
        # 正規表現でエントリーを抽出（名前空間の問題を回避）
        pattern = r'<entry>.*?<title>([^<]+)</title>.*?<id>([^<]+)</id>.*?<updated>([^<]+)</updated>.*?<link[^>]+href="([^"]+)".*?</entry>'
        matches = re.findall(pattern, feed_xml, re.DOTALL)
        
        for title, entry_id, updated, link in matches:
            if '警報' in title or '注意報' in title:
                entries.append({
                    'title': title,
                    'id': entry_id,
                    'updated': updated,
                    'link': link
                })
        
        return entries
    
    async def fetch_warning_detail(self, url: str) -> str:
        """警報詳細XMLを取得"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch warning detail: {e}")
            raise
    
    def parse_warning_xml(self, xml_content: str) -> List[WarningInfo]:
        """警報XMLを解析してWarningInfoのリストを返す"""
        warnings = []
        
        try:
            # Control情報から基本情報を取得
            control_match = re.search(r'<Control>(.*?)</Control>', xml_content, re.DOTALL)
            if not control_match:
                logger.warning("No Control section found in XML")
                return warnings
            
            # 発表時刻を取得
            datetime_match = re.search(r'<DateTime>([^<]+)</DateTime>', control_match.group(1))
            issued_at = None
            if datetime_match:
                try:
                    issued_at = datetime.fromisoformat(datetime_match.group(1).replace('Z', '+00:00'))
                except:
                    issued_at = datetime.now(timezone.utc)
            
            # Body部分から警報情報を抽出
            body_match = re.search(r'<Body.*?>(.*?)</Body>', xml_content, re.DOTALL)
            if not body_match:
                logger.warning("No Body section found in XML")
                return warnings
            
            body_content = body_match.group(1)
            
            # Warning要素を抽出
            warning_pattern = r'<Warning type="([^"]+)">(.*?)</Warning>'
            warning_matches = re.findall(warning_pattern, body_content, re.DOTALL)
            
            for warning_type, warning_content in warning_matches:
                # Item要素を抽出
                item_pattern = r'<Item>(.*?)</Item>'
                item_matches = re.findall(item_pattern, warning_content, re.DOTALL)
                
                for item_content in item_matches:
                    # Kind（警報種別）を抽出
                    kind_name_match = re.search(r'<Kind>.*?<Name>([^<]+)</Name>', item_content, re.DOTALL)
                    kind_code_match = re.search(r'<Kind>.*?<Code>([^<]+)</Code>', item_content, re.DOTALL)
                    kind_condition_match = re.search(r'<Kind>.*?<Condition>([^<]+)</Condition>', item_content, re.DOTALL)
                    
                    if not kind_name_match:
                        continue
                    
                    # Area（対象地域）を抽出
                    area_pattern = r'<Area>.*?<Name>([^<]+)</Name>.*?<Code>([^<]+)</Code>.*?</Area>'
                    area_matches = re.findall(area_pattern, item_content, re.DOTALL)
                    
                    for area_name, area_code in area_matches:
                        warning_info = WarningInfo()
                        warning_info.warning_type = kind_name_match.group(1)
                        warning_info.warning_code = kind_code_match.group(1) if kind_code_match else ""
                        warning_info.area_name = area_name
                        warning_info.area_code = area_code
                        warning_info.condition = kind_condition_match.group(1) if kind_condition_match else None
                        warning_info.severity = self.WARNING_SEVERITY.get(warning_info.warning_code, "注意報")
                        warning_info.issued_at = issued_at or datetime.now(timezone.utc)
                        
                        warnings.append(warning_info)
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error parsing warning XML: {e}")
            return warnings
    
    async def get_latest_warnings(self, area_code: Optional[str] = None) -> List[WarningInfo]:
        """最新の警報・注意報を取得"""
        from app.services.cache_service import cache_service, CacheType, get_cached_or_fetch
        
        try:
            # キャッシュパラメータ
            cache_params = {"area_code": area_code or "all"}
            
            async def fetch_warnings():
                # フィードを取得
                feed_xml = await self.fetch_warnings_feed()
                entries = self.parse_feed_entries(feed_xml)
                
                if not entries:
                    logger.info("No warning entries found in feed")
                    return []
                
                # 最新のエントリーから警報情報を取得
                all_warnings = []
                for entry in entries[:5]:  # 最新5件をチェック
                    try:
                        detail_xml = await self.fetch_warning_detail(entry['link'])
                        warnings = self.parse_warning_xml(detail_xml)
                        all_warnings.extend(warnings)
                    except Exception as e:
                        logger.error(f"Failed to process entry {entry['title']}: {e}")
                        continue
                
                # 地域コードでフィルタリング
                if area_code:
                    # 完全一致または親地域コードでフィルタ
                    filtered_warnings = []
                    for warning in all_warnings:
                        if (warning.area_code == area_code or 
                            area_code.startswith(warning.area_code[:2]) or  # 都道府県レベル
                            warning.area_code.startswith(area_code[:2])):   # 都道府県レベル
                            filtered_warnings.append(warning)
                    all_warnings = filtered_warnings
                
                # 辞書形式で返す（キャッシュ用）
                return [w.to_dict() for w in all_warnings]
            
            # キャッシュまたはフェッチ
            warnings_data = await get_cached_or_fetch(
                CacheType.WARNING,
                cache_params,
                fetch_warnings
            )
            
            # WarningInfoオブジェクトに変換
            warnings = []
            for warning_data in warnings_data:
                warning = WarningInfo()
                warning.warning_type = warning_data.get('warning_type', '')
                warning.warning_code = warning_data.get('warning_code', '')
                warning.area_name = warning_data.get('area_name', '')
                warning.area_code = warning_data.get('area_code', '')
                warning.condition = warning_data.get('condition')
                warning.severity = warning_data.get('severity', '')
                if warning_data.get('issued_at'):
                    warning.issued_at = datetime.fromisoformat(warning_data['issued_at'])
                warnings.append(warning)
            
            return warnings
            
        except Exception as e:
            logger.error(f"Failed to get latest warnings: {e}")
            return []
    
    async def get_warnings_for_location(self, location: Location) -> List[WarningInfo]:
        """位置情報から該当地域の警報・注意報を取得"""
        # 位置情報から地域コードを取得
        area_code = await self.get_area_code_from_location(location)
        
        if not area_code:
            logger.warning(f"Could not determine area code for location: {location.latitude}, {location.longitude}")
            return []
        
        # 地域コードで警報を取得
        return await self.get_latest_warnings(area_code)
    
    async def get_area_code_from_location(self, location: Location) -> Optional[str]:
        """位置情報から地域コードを取得"""
        from app.services.area_code_service import area_code_service
        return area_code_service.get_area_code_from_location(location)
    
    
    async def close(self):
        """HTTPクライアントを閉じる"""
        await self.client.aclose()