"""非同期HTTPクライアント - 外部APIとの通信を担当"""

import aiohttp
import ssl
import logging
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context that allows legacy renegotiation for GSI connections."""
    context = ssl.create_default_context()
    # Allow legacy renegotiation for www.gsi.go.jp
    context.set_ciphers('DEFAULT:@SECLEVEL=1')
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT
    return context

async def fetch_json(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 120
) -> Optional[Any]:
    """指定URLからJSONデータを非同期取得"""
    try:
        # Use custom SSL context for GSI URLs
        ssl_context = None
        if 'gsi.go.jp' in url.lower():
            ssl_context = create_ssl_context()
            
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_json: {e}")
        return None

async def fetch_xml(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 120
) -> Optional[ET.Element]:
    """指定URLからXMLデータを非同期取得"""
    try:
        # Use custom SSL context for GSI URLs
        ssl_context = None
        if 'gsi.go.jp' in url.lower():
            ssl_context = create_ssl_context()
            
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                xml_text = await response.text()
                return ET.fromstring(xml_text)
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except ET.ParseError as e:
        logger.error(f"XML parsing failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_xml: {e}")
        return None

async def fetch_bytes(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 120
) -> Optional[bytes]:
    """指定URLからバイナリデータを非同期取得"""
    try:
        # Use custom SSL context for GSI URLs
        ssl_context = None
        if 'gsi.go.jp' in url.lower():
            ssl_context = create_ssl_context()
            
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return await response.read()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_bytes: {e}")
        return None

async def fetch_text(
    url: str,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 120
) -> Optional[str]:
    """指定URLからテキストデータを非同期取得"""
    try:
        # Use custom SSL context for GSI URLs
        ssl_context = None
        if 'gsi.go.jp' in url.lower():
            ssl_context = create_ssl_context()
            
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                return await response.text()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_text: {e}")
        return None


class HTTPClient:
    """非同期HTTPクライアントクラス"""

    def __init__(self):
        self.session = None

    async def get(self, url: str, headers: Optional[Dict] = None, timeout: int = 120):
        """HTTP GETリクエストを実行"""
        if self.session is None:
            # Use custom SSL context for GSI URLs
            ssl_context = None
            if 'gsi.go.jp' in url.lower():
                ssl_context = create_ssl_context()
                
            connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
            self.session = aiohttp.ClientSession(connector=connector)
        
        try:
            response = await self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            )
            return response
        except Exception as e:
            logger.error(f"HTTP GET request failed: {e}")
            raise

    async def close(self):
        """セッションを閉じる"""
        if self.session:
            await self.session.close()
            self.session = None

    @classmethod
    async def get_session(cls, url: Optional[str] = None) -> aiohttp.ClientSession:
        """新しいClientSessionを取得する"""
        # Use custom SSL context for GSI URLs
        ssl_context = None
        if url and 'gsi.go.jp' in url.lower():
            ssl_context = create_ssl_context()
            
        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        return aiohttp.ClientSession(connector=connector)
