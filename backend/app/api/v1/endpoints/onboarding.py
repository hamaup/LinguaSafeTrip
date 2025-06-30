# app/api/v1/endpoints/onboarding.py
from fastapi import APIRouter, HTTPException, status
from typing import Optional
import logging

from app.schemas.onboarding import (
    OnboardingStatusRequest,
    OnboardingStatusResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse
)
from app.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
onboarding_service = OnboardingService()

# POST /onboarding/status は削除済み
# オンボーディング機能は統合ハートビートAPIまたはプロアクティブ提案で代替

# POST /onboarding/complete は削除済み
# オンボーディング進捗管理は統合ハートビートAPIまたはプロアクティブ提案で代替

# POST /onboarding/skip は削除済み
# オンボーディングスキップ機能は不要