# backend/app/services/trigger_evaluator.py
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.schemas.agent.suggestions import (
    ProactiveTriggerType,
    SuggestionPriority,
    TriggerEvaluation,
    DeviceContext,
    UserContext,
    DisasterContext
)

logger = logging.getLogger(__name__)

class TriggerEvaluator:
    """Evaluates conditions for proactive suggestions"""
    
    def __init__(self):
        self.trigger_definitions = self._initialize_triggers()
    
    def _initialize_triggers(self) -> Dict[ProactiveTriggerType, Dict[str, Any]]:
        """Initialize trigger definitions with conditions"""
        return {
            # 平常時トリガー
            ProactiveTriggerType.QUIZ_REMINDER: {
                "name": "防災クイズリマインダー",
                "check_interval_minutes": 1440,  # 24時間
                "min_days_since_last_quiz": 7,
                "priority_base": SuggestionPriority.LOW
            },
            ProactiveTriggerType.LOW_BATTERY_WARNING: {
                "name": "低バッテリー警告",
                "check_interval_minutes": 30,
                "battery_threshold_high": 30,  # 最初の警告
                "battery_threshold_low": 20,   # 緊急警告
                "priority_base": SuggestionPriority.MEDIUM
            },
            ProactiveTriggerType.GUIDE_INTRODUCTION: {
                "name": "災害ガイド案内",
                "check_interval_minutes": 2880,  # 48時間
                "max_guide_views": 0,  # 一度も見ていない
                "priority_base": SuggestionPriority.LOW
            },
            ProactiveTriggerType.EMERGENCY_CONTACT_SETUP: {
                "name": "緊急連絡先登録促進",
                "check_interval_minutes": 1440,  # 24時間
                "priority_base": SuggestionPriority.MEDIUM
            },
            ProactiveTriggerType.NEW_DISASTER_NEWS: {
                "name": "新しい災害ニュース取得",
                "check_interval_minutes": 0,  # 即時
                "priority_base": SuggestionPriority.MEDIUM
            },
            
            # 災害時トリガー
            ProactiveTriggerType.EMERGENCY_ALERT: {
                "name": "緊急アラート通知",
                "check_interval_minutes": 0,  # 即時
                "min_earthquake_intensity": 5,  # 震度5弱以上
                "priority_base": SuggestionPriority.CRITICAL
            },
            ProactiveTriggerType.DISASTER_UPDATE: {
                "name": "災害情報更新",
                "check_interval_minutes": 15,
                "priority_base": SuggestionPriority.HIGH
            },
            ProactiveTriggerType.RESOURCE_CONSERVATION: {
                "name": "リソース確保案内",
                "check_interval_minutes": 30,
                "battery_threshold_disaster": 50,  # 災害時は50%以下で警告
                "priority_base": SuggestionPriority.HIGH
            },
            ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE: {
                "name": "安否確認支援",
                "check_interval_minutes": 60,
                "min_earthquake_intensity": 6,  # 震度6弱以上
                "priority_base": SuggestionPriority.HIGH
            }
        }
    
    async def evaluate_all_triggers(
        self,
        device_context: DeviceContext,
        user_context: UserContext,
        disaster_context: Optional[DisasterContext] = None
    ) -> List[TriggerEvaluation]:
        """Evaluate all applicable triggers"""
        evaluations = []
        
        # 平常時と災害時で評価するトリガーを分ける
        if user_context.is_in_disaster_mode and disaster_context:
            # 災害時トリガー
            evaluations.extend(await self._evaluate_disaster_triggers(
                device_context, user_context, disaster_context
            ))
        else:
            # 平常時トリガー
            evaluations.extend(await self._evaluate_normal_triggers(
                device_context, user_context
            ))
        
        # デバイス状態に関するトリガーは常に評価
        evaluations.extend(await self._evaluate_device_triggers(
            device_context, user_context
        ))
        
        return evaluations
    
    async def _evaluate_normal_triggers(
        self,
        device_context: DeviceContext,
        user_context: UserContext
    ) -> List[TriggerEvaluation]:
        """Evaluate normal (non-disaster) triggers"""
        evaluations = []
        
        # Check if user is first-time (highest priority)
        onboarding_eval = await self._evaluate_onboarding_status(device_context, user_context)
        if onboarding_eval:
            evaluations.append(onboarding_eval)
            # For first-time users, prioritize onboarding over other suggestions
            return evaluations
        
        # Seasonal warning check
        seasonal_eval = await self._evaluate_seasonal_warning(user_context)
        if seasonal_eval:
            evaluations.append(seasonal_eval)
        
        # FR-P1: 防災クイズの出題
        quiz_eval = await self._evaluate_quiz_reminder(user_context)
        if quiz_eval:
            evaluations.append(quiz_eval)
        
        # FR-P3: 災害ガイドの案内
        guide_eval = await self._evaluate_guide_introduction(user_context)
        if guide_eval:
            evaluations.append(guide_eval)
        
        # FR-P4: 緊急連絡先登録の促進
        contact_eval = await self._evaluate_emergency_contact_setup(user_context)
        if contact_eval:
            evaluations.append(contact_eval)
        
        return evaluations

    async def evaluate_new_news_trigger(
        self,
        device_context: DeviceContext,
        user_context: UserContext,
        new_articles: List[Any]
    ) -> Optional['TriggerEvaluation']:
        """FR-P5: 新しい災害ニュース取得時のトリガー評価"""
        if not new_articles:
            return None
        
        # 災害関連記事の数をカウント（非同期処理）
        import asyncio
        disaster_related_checks = await asyncio.gather(*[
            self._is_news_disaster_related(article) for article in new_articles
        ], return_exceptions=True)
        
        disaster_related_count = sum(
            1 for result in disaster_related_checks 
            if result is True and not isinstance(result, Exception)
        )
        
        if disaster_related_count > 0:
            # 緊急度は記事数と内容に基づいて計算
            urgency_score = min(0.4 + (disaster_related_count * 0.1), 0.8)
            
            # 最新記事のタイトルをサンプルとして使用
            sample_titles = [
                getattr(article, 'title', '') for article in new_articles[:3]
            ]
            
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.NEW_DISASTER_NEWS,
                triggered=True,
                priority=SuggestionPriority.MEDIUM,
                urgency_score=urgency_score,
                relevance_score=0.8,
                reason=f"{disaster_related_count}件の新しい災害関連ニュースが取得されました",
                suggestion_data={
                    "total_articles": len(new_articles),
                    "disaster_related_count": disaster_related_count,
                    "sample_titles": sample_titles,
                    "latest_article_time": getattr(new_articles[0], 'collected_at', None).isoformat() if new_articles else None
                }
            )
        
        return None

    async def _is_news_disaster_related(self, article: Any) -> bool:
        """ニュース記事が災害関連かどうか判定（LLM自然言語分類）"""
        try:
            title = getattr(article, 'title', '') or ''
            content = getattr(article, 'content', '') or ''
            
            # CLAUDE.md原則: LLMによる自然言語分類を使用
            text_to_classify = f"Title: {title}\nContent: {content[:500]}"  # 最初の500文字
            
            # LLMベースの分類
            try:
                from app.agents.safety_beacon_agent.core.llm_singleton import ainvoke_llm
                
                classification_prompt = f"""Classify whether this news article is disaster-related or not.

Article to classify:
{text_to_classify}

Disaster-related topics include:
- Natural disasters (earthquakes, tsunamis, typhoons, floods, fires, volcanic eruptions)
- Disaster prevention and preparedness
- Emergency response and evacuation
- Weather warnings and alerts
- Hazard maps and safety information

Respond with only "true" if disaster-related, "false" if not disaster-related.
"""
                
                result = await ainvoke_llm(
                    prompt=classification_prompt,
                    task_type="classification",
                    temperature=0.1  # Low temperature for consistent classification
                )
                
                return result and result.strip().lower() == 'true'
                
            except Exception as e:
                logger.error(f"LLM classification failed: {e}")
                # 安全なフォールバック: 重要なキーワードのみ
                critical_terms = ["地震", "津波", "緊急", "警報", "earthquake", "tsunami", "emergency", "alert"]
                return any(term in title.lower() or term in content.lower() for term in critical_terms)
                
        except Exception as e:
            logger.error(f"News classification error: {e}")
            return False
    
    async def _evaluate_disaster_triggers(
        self,
        device_context: DeviceContext,
        user_context: UserContext,
        disaster_context: DisasterContext
    ) -> List[TriggerEvaluation]:
        """Evaluate disaster-specific triggers"""
        evaluations = []
        
        # FR-D1: 緊急アラートの受信通知 → disaster_newsに統合
        # alert_eval = await self._evaluate_emergency_alert(disaster_context)
        # if alert_eval:
        #     evaluations.append(alert_eval)
        
        # FR-D2: 最新の災害情報の提示 → disaster_newsに統合
        # update_eval = await self._evaluate_disaster_update(disaster_context)
        # if update_eval:
        #     evaluations.append(update_eval)
        
        # FR-D4: 安否確認SMS送信の補助
        safety_eval = await self._evaluate_safety_check(
            user_context, disaster_context
        )
        if safety_eval:
            evaluations.append(safety_eval)
        
        return evaluations
    
    async def _evaluate_device_triggers(
        self,
        device_context: DeviceContext,
        user_context: UserContext
    ) -> List[TriggerEvaluation]:
        """Evaluate device-related triggers"""
        evaluations = []
        
        # FR-P2/FR-D3: バッテリー・通信確保の案内
        battery_eval = await self._evaluate_battery_status(
            device_context, user_context
        )
        if battery_eval:
            evaluations.append(battery_eval)
        
        return evaluations
    
    async def _evaluate_quiz_reminder(
        self, user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """FR-P1: 防災クイズの出題"""
        if not user_context.last_quiz_date:
            # クイズを一度も実施していない
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.QUIZ_REMINDER,
                triggered=True,
                priority=SuggestionPriority.LOW,
                urgency_score=0.3,
                relevance_score=0.7,
                reason="防災クイズをまだ実施していません",
                suggestion_data={
                    "days_since_last_quiz": None,
                    "first_time": True
                }
            )
        
        days_since = (datetime.utcnow() - user_context.last_quiz_date).days
        if days_since >= 7:
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.QUIZ_REMINDER,
                triggered=True,
                priority=SuggestionPriority.LOW,
                urgency_score=min(0.5 + (days_since - 7) * 0.05, 0.8),
                relevance_score=0.7,
                reason=f"{days_since}日間クイズを実施していません",
                suggestion_data={
                    "days_since_last_quiz": days_since,
                    "first_time": False
                }
            )
        
        return None
    
    async def _evaluate_onboarding_status(
        self,
        device_context: DeviceContext,
        user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """Check if user needs onboarding (welcome message)"""
        # Check if this is a first-time user
        if user_context.total_interactions == 0 or not user_context.has_completed_onboarding:
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.WELCOME_NEW_USER,
                is_triggered=True,
                priority=SuggestionPriority.HIGH,
                confidence=0.9,
                suggestion_data={
                    "suggestion_type": "welcome_message",
                    "is_first_time": True
                }
            )
        return None
    
    async def _evaluate_seasonal_warning(
        self, user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """Evaluate need for seasonal disaster warnings"""
        # Get current month
        current_month = datetime.utcnow().month
        
        # Define seasonal risks by month (Japan-focused)
        seasonal_risks = {
            # Winter months - snow, cold
            12: "winter_storms",
            1: "winter_storms", 
            2: "winter_storms",
            # Spring - transition
            3: "spring_transition",
            4: "spring_transition",
            5: "rainy_season_prep",
            # Summer - typhoons, heat
            6: "rainy_season",
            7: "typhoon_season",
            8: "typhoon_season",
            9: "typhoon_season",
            # Fall - typhoons, transition
            10: "autumn_typhoons",
            11: "winter_prep"
        }
        
        risk_type = seasonal_risks.get(current_month, "general")
        
        return TriggerEvaluation(
            trigger_type=ProactiveTriggerType.SEASONAL_WARNING,
            is_triggered=True,
            priority=SuggestionPriority.LOW,
            confidence=0.6,
            suggestion_data={
                "suggestion_type": "seasonal_warning",
                "season_risk": risk_type,
                "month": current_month
            }
        )
    
    async def _evaluate_battery_status(
        self,
        device_context: DeviceContext,
        user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """FR-P2/FR-D3: バッテリー・通信確保の案内"""
        if not device_context.battery_level:
            return None
        
        battery = device_context.battery_level
        is_charging = device_context.is_charging or False
        
        # 充電中は警告しない
        if is_charging:
            return None
        
        # 災害時はより高い閾値で警告
        if user_context.is_in_disaster_mode:
            if battery <= 50:
                urgency = 0.9 if battery <= 20 else 0.7
                return TriggerEvaluation(
                    trigger_type=ProactiveTriggerType.RESOURCE_CONSERVATION,
                    triggered=True,
                    priority=SuggestionPriority.HIGH if battery <= 30 else SuggestionPriority.MEDIUM,
                    urgency_score=urgency,
                    relevance_score=0.9,
                    reason=f"災害時のバッテリー残量: {battery}%",
                    suggestion_data={
                        "battery_level": battery,
                        "is_disaster_mode": True,
                        "suggest_power_saving": battery <= 30
                    }
                )
        else:
            # 平常時
            if battery <= 30:
                urgency = 0.8 if battery <= 20 else 0.5
                return TriggerEvaluation(
                    trigger_type=ProactiveTriggerType.LOW_BATTERY_WARNING,
                    triggered=True,
                    priority=SuggestionPriority.MEDIUM,
                    urgency_score=urgency,
                    relevance_score=0.6,
                    reason=f"バッテリー残量が少ない: {battery}%",
                    suggestion_data={
                        "battery_level": battery,
                        "is_disaster_mode": False
                    }
                )
        
        return None
    
    async def _evaluate_guide_introduction(
        self, user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """FR-P3: 災害ガイドの案内"""
        if len(user_context.viewed_guides) == 0:
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.GUIDE_INTRODUCTION,
                triggered=True,
                priority=SuggestionPriority.LOW,
                urgency_score=0.3,
                relevance_score=0.8,
                reason="災害ガイドをまだ閲覧していません",
                suggestion_data={
                    "viewed_count": 0,
                    "recommended_guide": "basic_disaster_guide"
                }
            )
        
        return None
    
    async def _evaluate_emergency_contact_setup(
        self, user_context: UserContext
    ) -> Optional[TriggerEvaluation]:
        """FR-P4: 緊急連絡先登録の促進"""
        if not user_context.has_emergency_contacts:
            # 最後のアクティブから日数を計算
            days_inactive = 0
            if user_context.last_active_date:
                days_inactive = (datetime.utcnow() - user_context.last_active_date).days
            
            # 長期間使用していない場合は優先度を上げる
            urgency = min(0.4 + days_inactive * 0.05, 0.8)
            
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.EMERGENCY_CONTACT_SETUP,
                triggered=True,
                priority=SuggestionPriority.MEDIUM,
                urgency_score=urgency,
                relevance_score=0.9,
                reason="緊急連絡先が登録されていません",
                suggestion_data={
                    "has_contacts": False,
                    "days_inactive": days_inactive
                }
            )
        
        return None
    
    async def _evaluate_emergency_alert(
        self, disaster_context: DisasterContext
    ) -> Optional[TriggerEvaluation]:
        """FR-D1: 緊急アラートの受信通知"""
        if not disaster_context.active_alerts:
            return None
        
        # 最も深刻なアラートを評価
        max_severity = 0
        critical_alert = None
        
        for alert in disaster_context.active_alerts:
            severity = self._calculate_alert_severity(alert)
            if severity > max_severity:
                max_severity = severity
                critical_alert = alert
        
        if critical_alert and max_severity >= 0.7:
            return TriggerEvaluation(
                trigger_type=ProactiveTriggerType.EMERGENCY_ALERT,
                triggered=True,
                priority=SuggestionPriority.CRITICAL,
                urgency_score=1.0,
                relevance_score=1.0,
                reason=f"緊急アラート: {critical_alert.get('title', '')}",
                suggestion_data={
                    "alert": critical_alert,
                    "severity": max_severity
                }
            )
        
        return None
    
    async def _evaluate_disaster_update(
        self, disaster_context: DisasterContext
    ) -> Optional[TriggerEvaluation]:
        """FR-D2: 最新の災害情報の提示"""
        if disaster_context.recent_updates:
            # 15分以内の更新がある場合
            recent_count = len([
                u for u in disaster_context.recent_updates
                if self._is_recent_update(u, minutes=15)
            ])
            
            if recent_count > 0:
                return TriggerEvaluation(
                    trigger_type=ProactiveTriggerType.DISASTER_UPDATE,
                    triggered=True,
                    priority=SuggestionPriority.HIGH,
                    urgency_score=0.8,
                    relevance_score=0.9,
                    reason=f"{recent_count}件の新しい災害情報があります",
                    suggestion_data={
                        "update_count": recent_count,
                        "updates": disaster_context.recent_updates[:3]  # 最新3件
                    }
                )
        
        return None
    
    async def _evaluate_safety_check(
        self,
        user_context: UserContext,
        disaster_context: DisasterContext
    ) -> Optional[TriggerEvaluation]:
        """FR-D4: 安否確認SMS送信の補助"""
        # 大規模災害（震度6弱以上）を検出
        major_disaster = False
        for alert in disaster_context.active_alerts:
            if self._is_major_earthquake(alert):
                major_disaster = True
                break
        
        if major_disaster:
            # 緊急連絡先の有無で内容を変える
            if user_context.has_emergency_contacts:
                return TriggerEvaluation(
                    trigger_type=ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE,
                    triggered=True,
                    priority=SuggestionPriority.HIGH,
                    urgency_score=0.9,
                    relevance_score=1.0,
                    reason="大規模災害: 安否確認メッセージの送信を支援",
                    suggestion_data={
                        "has_contacts": True,
                        "contact_count": user_context.emergency_contacts_count,
                        "template_message": "無事です。現在、安全な場所にいます。"
                    }
                )
            else:
                return TriggerEvaluation(
                    trigger_type=ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE,
                    triggered=True,
                    priority=SuggestionPriority.HIGH,
                    urgency_score=0.8,
                    relevance_score=0.9,
                    reason="大規模災害: 緊急連絡先の登録を推奨",
                    suggestion_data={
                        "has_contacts": False,
                        "contact_count": 0,
                        "prompt_registration": True
                    }
                )
        
        return None
    
    
    def _calculate_alert_severity(self, alert: Dict[str, Any]) -> float:
        """Calculate severity score for an alert (0.0-1.0)"""
        title = alert.get("title", "").lower()
        message = alert.get("message", "").lower()
        
        # 震度による評価
        if "震度7" in message:
            return 1.0
        elif "震度6強" in message:
            return 0.95
        elif "震度6弱" in message:
            return 0.9
        elif "震度5強" in message:
            return 0.8
        elif "震度5弱" in message:
            return 0.7
        
        # その他の災害
        if "大津波" in title or "大津波" in message:
            return 1.0
        elif "津波" in title or "津波" in message:
            return 0.85
        elif "特別警報" in title or "特別警報" in message:
            return 0.9
        elif "避難指示" in message:
            return 0.8
        elif "避難勧告" in message:
            return 0.7
        
        return 0.5
    
    def _is_recent_update(self, update: Dict[str, Any], minutes: int = 15) -> bool:
        """Check if update is recent"""
        if "timestamp" in update:
            try:
                update_time = datetime.fromisoformat(update["timestamp"])
                return (datetime.utcnow() - update_time).total_seconds() < minutes * 60
            except:
                pass
        return True  # 時刻不明の場合は最新として扱う
    
    def _is_major_earthquake(self, alert: Dict[str, Any]) -> bool:
        """Check if alert indicates major earthquake (震度6弱以上)"""
        message = alert.get("message", "").lower()
        return any(intensity in message for intensity in ["震度6弱", "震度6強", "震度7"])