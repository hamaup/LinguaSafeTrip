"""
動的リスク評価サービス
静的ハザード情報とリアルタイム警報を統合してリスク評価
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

from app.schemas.hazard import Location, HazardInfo, HazardLevel, HazardType
from app.services.hazard_map_service import HazardMapService
from app.services.realtime_warning_service import RealTimeWarningService, WarningInfo
from app.services.elevation_service import ElevationService

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """総合リスクレベル"""
    SAFE = "safe"  # 安全
    CAUTION = "caution"  # 注意
    WARNING = "warning"  # 警戒
    DANGER = "danger"  # 危険
    CRITICAL = "critical"  # 緊急


class DynamicRiskAssessment:
    """動的リスク評価結果"""
    def __init__(self):
        self.location: Location = None
        self.risk_level: RiskLevel = RiskLevel.SAFE
        self.static_hazards: Optional[HazardInfo] = None
        self.active_warnings: List[WarningInfo] = []
        self.elevation: Optional[float] = None
        self.risk_factors: List[str] = []
        self.recommendations: List[str] = []
        self.urgency_hours: Optional[float] = None  # 対応が必要になるまでの時間
        self.assessed_at: datetime = datetime.now(timezone.utc)
        
    def to_dict(self) -> dict:
        return {
            "location": {
                "latitude": self.location.latitude,
                "longitude": self.location.longitude
            } if self.location else None,
            "risk_level": self.risk_level.value,
            "static_hazards": {
                "overall_risk": self.static_hazards.overall_risk_level.value if self.static_hazards else "none",
                "hazards": [h.dict() for h in self.static_hazards.hazards] if self.static_hazards else []
            },
            "active_warnings": [w.to_dict() for w in self.active_warnings],
            "elevation": self.elevation,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "urgency_hours": self.urgency_hours,
            "assessed_at": self.assessed_at.isoformat()
        }


class DynamicRiskAssessmentService:
    """動的リスク評価サービス"""
    
    # 警報種別と危険度の重み付け
    WARNING_WEIGHTS = {
        "特別警報": 5.0,
        "警報": 3.0,
        "注意報": 1.0
    }
    
    # 警報タイプと関連するハザードタイプ
    WARNING_HAZARD_MAPPING = {
        "大雨": [HazardType.FLOOD, HazardType.LANDSLIDE],
        "洪水": [HazardType.FLOOD],
        "高潮": [HazardType.HIGH_TIDE],
        "波浪": [HazardType.HIGH_TIDE],
        "土砂災害": [HazardType.LANDSLIDE]
    }
    
    def __init__(self):
        """サービスの初期化"""
        self.hazard_service = HazardMapService()
        self.warning_service = RealTimeWarningService()
        self.elevation_service = ElevationService()
        
    async def assess_risk(self, location: Location) -> DynamicRiskAssessment:
        """
        位置情報に基づいて動的リスク評価を実施
        
        Args:
            location: 評価対象の位置
            
        Returns:
            動的リスク評価結果
        """
        from app.services.cache_service import cache_service, CacheType, get_cached_or_fetch
        
        # キャッシュパラメータ
        cache_params = {
            "latitude": location.latitude,
            "longitude": location.longitude
        }
        
        async def fetch_assessment():
            assessment = DynamicRiskAssessment()
            assessment.location = location
            
            try:
                # 並行して情報を取得
                tasks = [
                    self._get_static_hazards(location),
                    self._get_active_warnings(location),
                    self._get_elevation(location)
                ]
                
                static_hazards, active_warnings, elevation = await asyncio.gather(*tasks)
                
                assessment.static_hazards = static_hazards
                assessment.active_warnings = active_warnings
                assessment.elevation = elevation
                
                # リスク評価
                self._evaluate_static_risks(assessment)
                self._evaluate_dynamic_risks(assessment)
                self._calculate_overall_risk(assessment)
                self._generate_recommendations(assessment)
                
            except Exception as e:
                logger.error(f"Error in risk assessment: {e}")
                assessment.risk_factors.append("評価中にエラーが発生しました")
                assessment.recommendations.append("最新の災害情報を確認してください")
            
            # 辞書形式で返す（キャッシュ用）
            return assessment.to_dict()
        
        # キャッシュまたはフェッチ（リスク評価は5分キャッシュ）
        assessment_data = await get_cached_or_fetch(
            CacheType.RISK_ASSESSMENT,
            cache_params,
            fetch_assessment
        )
        
        # DynamicRiskAssessmentオブジェクトを再構築
        assessment = DynamicRiskAssessment()
        assessment.location = location
        assessment.risk_level = RiskLevel(assessment_data.get('risk_level', 'safe'))
        assessment.elevation = assessment_data.get('elevation')
        assessment.risk_factors = assessment_data.get('risk_factors', [])
        assessment.recommendations = assessment_data.get('recommendations', [])
        assessment.urgency_hours = assessment_data.get('urgency_hours')
        
        # 警報情報を再構築
        assessment.active_warnings = []
        for w_data in assessment_data.get('active_warnings', []):
            warning = WarningInfo()
            warning.warning_type = w_data.get('warning_type', '')
            warning.severity = w_data.get('severity', '')
            warning.area_name = w_data.get('area_name', '')
            assessment.active_warnings.append(warning)
        
        return assessment
    
    async def _get_static_hazards(self, location: Location) -> Optional[HazardInfo]:
        """静的ハザード情報を取得"""
        try:
            return await self.hazard_service.get_hazard_info(location)
        except Exception as e:
            logger.error(f"Failed to get static hazards: {e}")
            return None
    
    async def _get_active_warnings(self, location: Location) -> List[WarningInfo]:
        """アクティブな警報・注意報を取得"""
        try:
            return await self.warning_service.get_warnings_for_location(location)
        except Exception as e:
            logger.error(f"Failed to get active warnings: {e}")
            return []
    
    async def _get_elevation(self, location: Location) -> Optional[float]:
        """標高を取得"""
        try:
            return await self.elevation_service.get_elevation(location)
        except Exception as e:
            logger.error(f"Failed to get elevation: {e}")
            return None
    
    def _evaluate_static_risks(self, assessment: DynamicRiskAssessment):
        """静的リスクを評価"""
        if not assessment.static_hazards:
            return
            
        # 静的ハザードレベルに基づくリスク評価
        for hazard in assessment.static_hazards.hazards:
            if hazard.level == HazardLevel.HIGH or hazard.level == HazardLevel.EXTREME:
                risk_text = f"{hazard.hazard_type.value}リスク: {hazard.description}"
                assessment.risk_factors.append(risk_text)
                
                # 低地での洪水リスク
                if hazard.hazard_type == HazardType.FLOOD and assessment.elevation is not None:
                    if assessment.elevation < 5.0:
                        assessment.risk_factors.append(f"低地（標高{assessment.elevation:.1f}m）のため浸水リスクが高い")
    
    def _evaluate_dynamic_risks(self, assessment: DynamicRiskAssessment):
        """動的リスク（警報）を評価"""
        if not assessment.active_warnings:
            return
            
        # 警報の重要度を集計
        warning_score = 0.0
        critical_warnings = []
        
        for warning in assessment.active_warnings:
            weight = self.WARNING_WEIGHTS.get(warning.severity, 0.5)
            warning_score += weight
            
            # 重要な警報を記録
            if warning.severity in ["特別警報", "警報"]:
                critical_warnings.append(warning)
                assessment.risk_factors.append(
                    f"{warning.area_name}に{warning.warning_type}（{warning.severity}）が発令中"
                )
        
        # 緊急度の判定
        if critical_warnings:
            assessment.urgency_hours = 0.0  # 即座の対応が必要
        elif warning_score > 2.0:
            assessment.urgency_hours = 3.0  # 3時間以内の対応推奨
        elif warning_score > 0:
            assessment.urgency_hours = 6.0  # 6時間以内の対応推奨
    
    def _calculate_overall_risk(self, assessment: DynamicRiskAssessment):
        """総合リスクレベルを計算"""
        # 基本はSAFE
        risk_score = 0
        
        # 静的ハザードによるスコア
        if assessment.static_hazards:
            if assessment.static_hazards.overall_risk_level == HazardLevel.EXTREME:
                risk_score += 4
            elif assessment.static_hazards.overall_risk_level == HazardLevel.HIGH:
                risk_score += 3
            elif assessment.static_hazards.overall_risk_level == HazardLevel.MEDIUM:
                risk_score += 2
            elif assessment.static_hazards.overall_risk_level == HazardLevel.LOW:
                risk_score += 1
        
        # 警報によるスコア
        for warning in assessment.active_warnings:
            if warning.severity == "特別警報":
                risk_score += 5
            elif warning.severity == "警報":
                risk_score += 3
            elif warning.severity == "注意報":
                risk_score += 1
        
        # リスクレベルの判定
        if risk_score >= 8:
            assessment.risk_level = RiskLevel.CRITICAL
        elif risk_score >= 6:
            assessment.risk_level = RiskLevel.DANGER
        elif risk_score >= 4:
            assessment.risk_level = RiskLevel.WARNING
        elif risk_score >= 2:
            assessment.risk_level = RiskLevel.CAUTION
        else:
            assessment.risk_level = RiskLevel.SAFE
    
    def _generate_recommendations(self, assessment: DynamicRiskAssessment):
        """推奨行動を生成"""
        if assessment.risk_level == RiskLevel.CRITICAL:
            assessment.recommendations.extend([
                "直ちに安全な場所へ避難してください",
                "避難指示・勧告に従ってください",
                "命を守る行動を取ってください"
            ])
        elif assessment.risk_level == RiskLevel.DANGER:
            assessment.recommendations.extend([
                "避難の準備を開始してください",
                "避難所の場所を確認してください",
                "非常用持ち出し品を準備してください"
            ])
        elif assessment.risk_level == RiskLevel.WARNING:
            assessment.recommendations.extend([
                "最新の災害情報に注意してください",
                "避難経路を確認してください",
                "家族との連絡方法を確認してください"
            ])
        elif assessment.risk_level == RiskLevel.CAUTION:
            assessment.recommendations.extend([
                "今後の気象情報に注意してください",
                "備蓄品の確認をしてください"
            ])
        else:
            assessment.recommendations.append("現在、差し迫った危険はありません")
        
        # 低地での追加推奨
        if assessment.elevation is not None and assessment.elevation < 5.0:
            has_flood_risk = False
            if assessment.static_hazards:
                for hazard in assessment.static_hazards.hazards:
                    if hazard.hazard_type in [HazardType.FLOOD, HazardType.TSUNAMI]:
                        has_flood_risk = True
                        break
            
            if has_flood_risk or any("洪水" in w.warning_type or "高潮" in w.warning_type for w in assessment.active_warnings):
                assessment.recommendations.append("低地のため、早めの避難を心がけてください")
    
    async def close(self):
        """サービスのクリーンアップ"""
        await self.hazard_service.close()
        await self.warning_service.close()
        await self.elevation_service.close()


# asyncioのインポート
import asyncio