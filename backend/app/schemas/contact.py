from pydantic import BaseModel, Field, validator
from typing import Optional

class EmergencyContactSchema(BaseModel):
    id: Optional[str] = None # フロントエンドで生成・管理されるID
    name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., description="E.164 formatted phone number.")
    relationship: Optional[str] = Field(default=None, max_length=30) # 例: 家族, 親戚, 友人

    @validator('phone_number')
    def validate_phone_number_format(cls, v):
        if not (v.startswith('+') and v[1:].isdigit() and len(v) > 7): # より簡易なチェック
            raise ValueError("Invalid phone number format. Must be E.164 like format (e.g., +819012345678).")
        return v
