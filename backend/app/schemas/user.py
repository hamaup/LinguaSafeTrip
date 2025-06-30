# backend/app/schemas/user.py
from pydantic import BaseModel, Field, HttpUrl # 必要に応じて EmailStr なども
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    language: str = 'en' # デフォルト値
    deviceToken: Optional[str] = None
    # lastLocation: Optional[dict] = None # GeoPointは特別な扱いが必要かも

class UserCreate(UserBase):
     # 作成時は基本的にBaseと同じか、必要なフィールドを追加
     pass

class UserResponse(UserBase):
     userId: str
     createdAt: datetime
     updatedAt: datetime

     class Config:
         from_attributes = True # Pydantic v2 (旧 orm_mode)