# backend/app/agents/safety_beacon_agent/suggestion_generators/template_generator.py
# Template-based suggestion generator for proactive suggestions (welcome, onboarding, reminders, etc.)
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.schemas.agent.suggestions import (
    ProactiveSuggestion,
    ProactiveTriggerType,
    SuggestionPriority,
    ActionType,
    TriggerEvaluation
)

logger = logging.getLogger(__name__)

class SuggestionGenerator:
    """Generates proactive suggestions based on trigger evaluations"""
    
    def __init__(self):
        self.suggestion_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[ProactiveTriggerType, Dict[str, Any]]:
        """Initialize suggestion templates for each trigger type"""
        return {
            ProactiveTriggerType.WELCOME_NEW_USER: {
                "title": "LinguaSafeTripへようこそ！",
                "message_template": "初回起動ありがとうございます。簡単な設定で、すぐに安心してご利用いただけます。",
                "action_type": ActionType.OPEN_SETTINGS,
                "action_label": "設定を始める",
                "icon_type": "welcome",
                "expires_hours": 168  # 1週間
            },
            
            ProactiveTriggerType.ONBOARDING_REMINDER: {
                "title": "設定を完了しませんか？",
                "message_template": "残り{remaining_steps}ステップで設定完了です。あと{estimated_time}分で終わります。",
                "action_type": ActionType.OPEN_SETTINGS,
                "action_label": "設定を続ける",
                "icon_type": "setup",
                "expires_hours": 72
            },
            
            ProactiveTriggerType.ONBOARDING_COMPLETED: {
                "title": "設定完了！LinguaSafeTripへようこそ🎉",
                "message_template": "初期設定が完了しました！これで安心してLinguaSafeTripをご利用いただけます。{next_action_message}",
                "message_with_recommendations": "初期設定が完了しました！より安全にご利用いただくため、{recommended_count}つの追加設定をおすすめします。",
                "action_type": ActionType.EXPLORE_APP,
                "action_label": "アプリを使い始める",
                "action_label_with_recommendations": "おすすめ設定を見る",
                "icon_type": "celebration",
                "expires_hours": 48
            },
            
            # ProactiveTriggerType.QUIZ_REMINDER: 無効化
            # {
            #     "title": "防災クイズに挑戦！",
            #     "message_template": "防災クイズに挑戦しませんか？知識を確認して、いざという時に備えましょう。",
            #     "message_first_time": "LinguaSafeTripの防災クイズで、楽しく防災知識を身につけましょう！",
            #     "action_type": ActionType.OPEN_QUIZ,
            #     "action_label": "クイズを始める",
            #     "icon_type": "quiz",
            #     "expires_hours": 48
            # },
            
            ProactiveTriggerType.LOW_BATTERY_WARNING: {
                "title": "バッテリー残量低下",
                "message_template": "バッテリー残量が{battery_level}%になっています。災害時は電源の確保が難しくなります。今のうちに充電しておきませんか？",
                "action_type": ActionType.CHARGE_BATTERY,
                "action_label": "充電方法を確認",
                "icon_type": "battery_low",
                "expires_hours": 2
            },
            
            ProactiveTriggerType.GUIDE_INTRODUCTION: {
                "title": "災害ガイドのご案内",
                "message_template": "災害ガイドには、いざという時に役立つ情報が載っています。一度確認しておきませんか？",
                "action_type": ActionType.VIEW_GUIDE,
                "action_label": "ガイドを見る",
                "icon_type": "guide",
                "expires_hours": 72
            },
            
            ProactiveTriggerType.EMERGENCY_CONTACT_SETUP: {
                "title": "緊急連絡先の登録",
                "message_template": "緊急時のために、家族など大切な人の連絡先を登録しておきませんか？",
                "action_type": ActionType.REGISTER_CONTACTS,
                "action_label": "連絡先を登録",
                "icon_type": "contacts",
                "expires_hours": 168  # 1週間
            },
            
            ProactiveTriggerType.NEW_DISASTER_NEWS: {
                "title": "🚨 緊急災害情報更新",
                "message_template": "【緊急】{disaster_related_count}件の重要な災害関連情報が更新されました！状況が変化している可能性があります。今すぐ最新情報を確認してください！",
                "message_template_single": "【緊急更新】「{sample_title}」\n重要な災害情報です。今すぐ確認してください！",
                "action_type": ActionType.VIEW_NEWS,
                "action_label": "緊急情報を確認",
                "action_label_single": "緊急記事を確認",
                "icon_type": "news",
                "expires_hours": 6  # 6時間
            },
            
            ProactiveTriggerType.EMERGENCY_ALERT: {
                "title": "【緊急警報】即座に行動してください",
                "message_template": "【危険】{alert_title}が発表されました！直ちに身の安全を確保し、避難準備をしてください！",
                "action_type": ActionType.VIEW_ALERT_DETAILS,
                "action_label": "緊急詳細を確認",
                "icon_type": "emergency",
                "expires_hours": 6
            },
            
            ProactiveTriggerType.DISASTER_UPDATE: {
                "title": "【重要】災害情報緊急更新",
                "message_template": "【注意】災害情報が緊急更新されました（{update_count}件）！状況が変化している可能性があります。今すぐ最新情報を確認してください！",
                "action_type": ActionType.CHECK_UPDATES,
                "action_label": "緊急情報を確認",
                "icon_type": "update",
                "expires_hours": 3
            },
            
            ProactiveTriggerType.RESOURCE_CONSERVATION: {
                "title": "電源確保のお願い",
                "message_template": "バッテリー残量: {battery_level}%\n通信が不安定になる前に、必要な情報を確認しておきましょう。バッテリー節約モードをONにしますか？",
                "action_type": ActionType.ENABLE_POWER_SAVING,
                "action_label": "節約モードON",
                "icon_type": "power_saving",
                "expires_hours": 1
            },
            
            ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE: {
                "title": "安否確認",
                "message_template_with_contacts": "大規模な災害が発生しました。登録された{contact_count}件の連絡先に安否メッセージを送信しますか？",
                "message_template_no_contacts": "大規模な災害が発生しました。安否連絡のために、緊急連絡先を登録しませんか？",
                "action_type": ActionType.SEND_SAFETY_MESSAGE,
                "action_label_with_contacts": "安否メッセージ作成",
                "action_label_no_contacts": "連絡先を登録",
                "icon_type": "safety_check",
                "expires_hours": 12
            }
        }
    
    async def generate_suggestions(
        self, evaluations: List[TriggerEvaluation]
    ) -> List[ProactiveSuggestion]:
        """Generate suggestions from trigger evaluations"""
        suggestions = []
        
        # 優先度とスコアでソート
        sorted_evaluations = sorted(
            evaluations,
            key=lambda e: (
                self._priority_to_number(e.priority),
                e.urgency_score * e.relevance_score
            ),
            reverse=True
        )
        
        # 各評価に対して提案を生成
        for evaluation in sorted_evaluations:
            if evaluation.triggered:
                suggestion = await self._create_suggestion(evaluation)
                if suggestion:
                    suggestions.append(suggestion)
        
        # 最大3件まで
        return suggestions[:3]
    
    async def _create_suggestion(
        self, evaluation: TriggerEvaluation
    ) -> Optional[ProactiveSuggestion]:
        """Create a suggestion from evaluation"""
        template = self.suggestion_templates.get(evaluation.trigger_type)
        if not template:
            logger.warning(f"No template found for trigger type: {evaluation.trigger_type}")
            return None
        
        try:
            # メッセージの生成
            message = self._format_message(template, evaluation)
            
            # アクションタイプとラベルの決定
            action_type, action_label = self._determine_action(template, evaluation)
            
            # 有効期限の計算
            expires_at = datetime.utcnow() + timedelta(
                hours=template.get("expires_hours", 24)
            )
            
            return ProactiveSuggestion(
                id=str(uuid.uuid4()),
                trigger_type=evaluation.trigger_type,
                priority=evaluation.priority,
                title=template["title"],
                message=message,
                action_type=action_type,
                action_label=action_label,
                action_data=evaluation.suggestion_data,
                icon_type=template.get("icon_type"),
                expires_at=expires_at
            )
            
        except Exception as e:
            logger.error(f"Failed to create suggestion: {e}", exc_info=True)
            return None
    
    def _format_message(
        self, template: Dict[str, Any], evaluation: TriggerEvaluation
    ) -> str:
        """Format message based on template and evaluation data"""
        data = evaluation.suggestion_data or {}
        
        # 特殊なケースの処理
        if evaluation.trigger_type == ProactiveTriggerType.WELCOME_NEW_USER:
            # ウェルカムメッセージはカスタマイズされたメッセージを使用
            welcome_data = data.get("welcome_message", {})
            if welcome_data:
                return welcome_data.get("message", template["message_template"])
            else:
                return template["message_template"]
        
        elif evaluation.trigger_type == ProactiveTriggerType.ONBOARDING_COMPLETED:
            # オンボーディング完了の特殊処理
            next_actions = data.get("next_recommended_actions", [])
            filtered_actions = [action for action in next_actions if action is not None]
            
            if filtered_actions:
                action_messages = {
                    "emergency_contacts": "緊急連絡先の追加",
                    "take_quiz": "防災クイズへの挑戦",
                    "explore_guides": "防災ガイドの確認"
                }
                recommended_count = len(filtered_actions)
                return template["message_with_recommendations"].format(
                    recommended_count=recommended_count
                )
            else:
                return template["message_template"].format(
                    next_action_message="今すぐアプリの各機能をお試しください。"
                )
        
        elif evaluation.trigger_type == ProactiveTriggerType.QUIZ_REMINDER:
            if data.get("first_time"):
                return template["message_first_time"]
            else:
                return template["message_template"]
        
        elif evaluation.trigger_type == ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE:
            if data.get("has_contacts"):
                return template["message_template_with_contacts"].format(
                    contact_count=data.get("contact_count", 0)
                )
            else:
                return template["message_template_no_contacts"]
        
        elif evaluation.trigger_type == ProactiveTriggerType.NEW_DISASTER_NEWS:
            disaster_count = data.get("disaster_related_count", 0)
            sample_titles = data.get("sample_titles", [])
            
            if disaster_count == 1 and sample_titles:
                # 1件の場合は記事タイトルを表示
                return template["message_template_single"].format(
                    sample_title=sample_titles[0][:50] + ("..." if len(sample_titles[0]) > 50 else "")
                )
            else:
                # 複数件の場合は件数を表示
                return template["message_template"].format(
                    disaster_related_count=disaster_count
                )
        
        # 通常のテンプレート処理
        message_template = template.get("message_template", "")
        try:
            return message_template.format(**data)
        except Exception as e:
            logger.error(f"Failed to format message: {e}")
            return message_template
    
    def _determine_action(
        self, template: Dict[str, Any], evaluation: TriggerEvaluation
    ) -> tuple[Optional[ActionType], Optional[str]]:
        """Determine action type and label based on evaluation"""
        data = evaluation.suggestion_data or {}
        
        # オンボーディング関連の特殊処理
        if evaluation.trigger_type in [ProactiveTriggerType.WELCOME_NEW_USER, ProactiveTriggerType.ONBOARDING_REMINDER]:
            current_step = data.get("current_step", {})
            if current_step:
                step_action = current_step.get("action_type")
                step_label = current_step.get("action_label")
                if step_action and step_label:
                    return (step_action, step_label)
            return (template.get("action_type"), template.get("action_label"))
        
        # オンボーディング完了の特殊処理
        elif evaluation.trigger_type == ProactiveTriggerType.ONBOARDING_COMPLETED:
            next_actions = data.get("next_recommended_actions", [])
            filtered_actions = [action for action in next_actions if action is not None]
            
            if filtered_actions:
                # 推奨アクションがある場合
                return (
                    ActionType.VIEW_RECOMMENDATIONS,
                    template.get("action_label_with_recommendations", "おすすめ設定を見る")
                )
            else:
                # 推奨アクションがない場合
                return (
                    template.get("action_type", ActionType.EXPLORE_APP),
                    template.get("action_label", "アプリを使い始める")
                )
        
        # 安否確認の特殊処理
        elif evaluation.trigger_type == ProactiveTriggerType.SAFETY_CHECK_ASSISTANCE:
            if data.get("has_contacts"):
                return (
                    ActionType.SEND_SAFETY_MESSAGE,
                    template["action_label_with_contacts"]
                )
            else:
                return (
                    ActionType.REGISTER_CONTACTS,
                    template["action_label_no_contacts"]
                )
        
        # 新しいニュースの特殊処理
        elif evaluation.trigger_type == ProactiveTriggerType.NEW_DISASTER_NEWS:
            disaster_count = data.get("disaster_related_count", 0)
            if disaster_count == 1:
                return (
                    ActionType.VIEW_NEWS,
                    template.get("action_label_single", "記事を読む")
                )
            else:
                return (
                    ActionType.VIEW_NEWS,
                    template.get("action_label", "最新情報を見る")
                )
        
        # 通常のアクション
        return (
            template.get("action_type"),
            template.get("action_label")
        )
    
    def _priority_to_number(self, priority: SuggestionPriority) -> int:
        """Convert priority to number for sorting"""
        mapping = {
            SuggestionPriority.CRITICAL: 4,
            SuggestionPriority.HIGH: 3,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 1
        }
        return mapping.get(priority, 0)