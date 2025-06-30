from pydantic import BaseModel
from typing import List, Optional, Dict

class GuideSection(BaseModel):
    heading: Optional[str] = None # セクションの見出し
    content: Optional[str] = None # セクションの本文 (Markdown形式も可)
    items: Optional[List[str]] = None # 箇条書きリストなど

class GuideContent(BaseModel):
    id: str # ガイドコンテンツの一意なID (例: "earthquake_initial_action")
    title: str # ガイドのタイトル (例: "地震発生！まず取るべき行動")
    keywords: List[str] # 検索用キーワード (例: ["地震", "初期行動", "安全確保"])
    summary: Optional[str] = None # ガイドの短い要約
    sections: List[GuideSection] # ガイドの本文コンテンツ
    source_info: Optional[str] = None # 情報源 (例: "内閣府防災担当")
    last_updated: Optional[str] = None # 最終更新日 (YYYY-MM-DD形式)
