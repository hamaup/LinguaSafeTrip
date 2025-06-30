from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class SearchResultItem(BaseModel):
    title: str
    link: HttpUrl
    snippet: Optional[str] = None
    source_domain: Optional[str] = None # 検索結果のドメイン
    content_summary: Optional[str] = None # (オプション) 取得・要約されたページコンテンツ
    relevance_score: Optional[float] = None # (オプション) LLMなどによる関連度や信頼性のスコア
