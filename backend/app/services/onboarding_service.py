# backend/app/services/onboarding_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.schemas.onboarding import (
    OnboardingStep,
    OnboardingStepType,
    WelcomeMessage,
    FeatureGuide,
    OnboardingProgress,
    OnboardingResponse,
    OnboardingStepComplete,
    QuickSetupRequest,
    OnboardingStatusResponse,
    OnboardingCompleteResponse
)
from app.db.firestore_client import get_db

logger = logging.getLogger(__name__)

class OnboardingService:
    """Service for managing user onboarding and welcome flow"""
    
    def __init__(self):
        self.welcome_messages = self._initialize_welcome_messages()
        self.onboarding_steps = self._initialize_onboarding_steps()
        self.feature_guides = self._initialize_feature_guides()
    
    def _initialize_welcome_messages(self) -> Dict[str, WelcomeMessage]:
        """Initialize welcome messages for different languages"""
        return {
            "ja": WelcomeMessage(
                title="LinguaSafeTripへようこそ！",
                message="災害時の安全をサポートする防災アプリです。いざという時に備えて、一緒に準備をしましょう。",
                app_introduction="LinguaSafeTripは、平常時の防災準備から災害時の緊急対応まで、あなたの安全を総合的にサポートします。",
                key_features=[
                    "🚨 災害情報の即座な通知",
                    "🗺️ 最寄りの避難所案内", 
                    "📱 緊急時の安否確認支援",
                    "📚 防災ガイドと知識習得",
                    "🔋 災害時のデバイス管理"
                ],
                getting_started_tip="まずは緊急連絡先の登録から始めることをお勧めします。",
                language="ja"
            ),
            
            "en": WelcomeMessage(
                title="Welcome to LinguaSafeTrip!",
                message="A disaster preparedness app that supports your safety during emergencies. Let's prepare together for when it matters most.",
                app_introduction="LinguaSafeTrip provides comprehensive safety support from daily disaster preparedness to emergency response.",
                key_features=[
                    "🚨 Instant disaster alerts",
                    "🗺️ Nearest shelter guidance",
                    "📱 Emergency safety check assistance", 
                    "📚 Disaster preparedness guides",
                    "🔋 Emergency device management"
                ],
                getting_started_tip="We recommend starting by registering your emergency contacts.",
                language="en"
            ),
            
            "zh": WelcomeMessage(
                title="欢迎使用LinguaSafeTrip！",
                message="支援您在灾害时安全的防灾应用。让我们一起为关键时刻做好准备。",
                app_introduction="LinguaSafeTrip从日常防灾准备到灾害时的紧急应对，为您提供全面的安全支持。",
                key_features=[
                    "🚨 灾害信息即时通知",
                    "🗺️ 最近避难所指引",
                    "📱 紧急时安全确认支援",
                    "📚 防灾指南和知识学习",
                    "🔋 灾害时设备管理"
                ],
                getting_started_tip="建议首先从注册紧急联系人开始。",
                language="zh"
            ),
            
            "ko": WelcomeMessage(
                title="LinguaSafeTrip에 오신 것을 환영합니다!",
                message="재해 시 안전을 지원하는 방재 앱입니다. 중요한 순간에 대비해 함께 준비해보세요.",
                app_introduction="LinguaSafeTrip는 평상시 방재 준비부터 재해 시 긴급 대응까지 종합적인 안전 지원을 제공합니다.",
                key_features=[
                    "🚨 재해 정보 즉시 알림",
                    "🗺️ 가까운 대피소 안내",
                    "📱 긴급 시 안부 확인 지원", 
                    "📚 방재 가이드와 지식 습득",
                    "🔋 재해 시 기기 관리"
                ],
                getting_started_tip="먼저 긴급 연락처 등록부터 시작하는 것을 추천합니다.",
                language="ko"
            )
        }
    
    def _initialize_onboarding_steps(self) -> Dict[str, List[OnboardingStep]]:
        """Initialize onboarding steps for different languages"""
        steps_ja = [
            OnboardingStep(
                id="welcome",
                type=OnboardingStepType.WELCOME,
                title="LinguaSafeTripへようこそ",
                description="防災アプリの基本的な使い方をご案内します",
                icon="welcome",
                action_label="はじめる",
                action_type="next_step",
                is_required=True,
                estimated_time_minutes=1,
                order=1
            ),
            OnboardingStep(
                id="permissions",
                type=OnboardingStepType.PERMISSIONS,
                title="アプリの権限設定",
                description="位置情報と通知の許可をお願いします",
                icon="permissions",
                action_label="権限を設定",
                action_type="request_permissions",
                action_data={"permissions": ["location", "notifications"]},
                is_required=True,
                estimated_time_minutes=2,
                order=2
            ),
            OnboardingStep(
                id="emergency_contacts",
                type=OnboardingStepType.EMERGENCY_CONTACTS,
                title="緊急連絡先の登録",
                description="災害時の安否確認のため、大切な人の連絡先を登録しましょう",
                icon="contacts",
                action_label="連絡先を登録",
                action_type="add_contact",
                is_required=False,
                estimated_time_minutes=3,
                order=3
            ),
            OnboardingStep(
                id="guide_intro",
                type=OnboardingStepType.GUIDE_INTRO,
                title="防災ガイドのご紹介",
                description="災害別の対処法や避難方法を学べます",
                icon="guide",
                action_label="ガイドを見る",
                action_type="view_guides",
                is_required=False,
                estimated_time_minutes=2,
                order=4
            ),
            OnboardingStep(
                id="quiz_intro",
                type=OnboardingStepType.QUIZ_INTRO,
                title="防災クイズで知識チェック",
                description="楽しく防災知識を身につけることができます",
                icon="quiz",
                action_label="クイズを試す",
                action_type="start_quiz",
                is_required=False,
                estimated_time_minutes=3,
                order=5
            ),
            OnboardingStep(
                id="completion",
                type=OnboardingStepType.COMPLETION,
                title="設定完了！",
                description="LinguaSafeTripの準備が整いました。いつでも安心してお使いください。",
                icon="success",
                action_label="アプリを開始",
                action_type="complete_onboarding",
                is_required=True,
                estimated_time_minutes=1,
                order=6
            )
        ]
        
        # English steps (simplified for this example)
        steps_en = [
            OnboardingStep(
                id="welcome",
                type=OnboardingStepType.WELCOME,
                title="Welcome to LinguaSafeTrip",
                description="Let's get you started with the disaster preparedness app",
                icon="welcome",
                action_label="Get Started",
                action_type="next_step",
                is_required=True,
                estimated_time_minutes=1,
                order=1
            ),
            OnboardingStep(
                id="permissions",
                type=OnboardingStepType.PERMISSIONS,
                title="App Permissions",
                description="Please allow location and notification access",
                icon="permissions",
                action_label="Setup Permissions",
                action_type="request_permissions",
                action_data={"permissions": ["location", "notifications"]},
                is_required=True,
                estimated_time_minutes=2,
                order=2
            ),
            OnboardingStep(
                id="emergency_contacts",
                type=OnboardingStepType.EMERGENCY_CONTACTS,
                title="Emergency Contacts",
                description="Add important contacts for safety checks during disasters",
                icon="contacts",
                action_label="Add Contacts",
                action_type="add_contact",
                is_required=False,
                estimated_time_minutes=3,
                order=3
            ),
            OnboardingStep(
                id="completion",
                type=OnboardingStepType.COMPLETION,
                title="All Set!",
                description="LinguaSafeTrip is ready to keep you safe.",
                icon="success",
                action_label="Start Using App",
                action_type="complete_onboarding",
                is_required=True,
                estimated_time_minutes=1,
                order=4
            )
        ]
        
        return {
            "ja": steps_ja,
            "en": steps_en,
            "zh": steps_ja,  # 簡略化のため日本語版を使用
            "ko": steps_ja   # 簡略化のため日本語版を使用
        }
    
    def _initialize_feature_guides(self) -> Dict[str, List[FeatureGuide]]:
        """Initialize feature guides for different languages"""
        guides_ja = [
            FeatureGuide(
                feature_id="disaster_alerts",
                name="災害アラート",
                description="気象庁の情報に基づく災害情報をリアルタイムで受信",
                icon="alert",
                demo_action="view_recent_alerts",
                importance_level="high",
                category="safety"
            ),
            FeatureGuide(
                feature_id="shelter_guidance",
                name="避難所案内",
                description="現在地から最寄りの避難所までのルートを案内",
                icon="shelter",
                demo_action="find_nearby_shelters",
                importance_level="high",
                category="safety"
            ),
            FeatureGuide(
                feature_id="safety_check_sms",
                name="安否確認SMS",
                description="災害時に家族や友人に安否を知らせるSMSを簡単送信",
                icon="sms",
                demo_action="preview_safety_sms",
                importance_level="medium",
                category="communication"
            ),
            FeatureGuide(
                feature_id="disaster_guides",
                name="防災ガイド",
                description="災害別の対処法や準備リストを詳しく解説",
                icon="guide",
                demo_action="browse_guides",
                importance_level="medium",
                category="preparation"
            ),
            FeatureGuide(
                feature_id="quiz_system",
                name="防災クイズ",
                description="楽しく学べる防災知識クイズで実力チェック",
                icon="quiz",
                demo_action="start_sample_quiz",
                importance_level="low",
                category="education"
            ),
            FeatureGuide(
                feature_id="proactive_suggestions",
                name="プロアクティブ提案",
                description="状況に応じた防災アクションを自動提案",
                icon="suggestions",
                demo_action="view_suggestions",
                importance_level="medium",
                category="smart_features"
            )
        ]
        
        return {
            "ja": guides_ja,
            "en": guides_ja,  # 簡略化
            "zh": guides_ja,  # 簡略化
            "ko": guides_ja   # 簡略化
        }
    
    async def get_onboarding_status(
        self, 
        user_id: Optional[str] = None, 
        device_id: str = None,
        language: str = "ja"
    ) -> OnboardingStatusResponse:
        """Get user's onboarding status and next steps"""
        try:
            # Check if user is first-time
            progress = await self._get_onboarding_progress(user_id, device_id)
            
            if progress.is_first_time:
                # Return welcome flow for first-time users
                welcome_message = self.welcome_messages.get(language, self.welcome_messages["ja"])
                steps = self.onboarding_steps.get(language, self.onboarding_steps["ja"])
                feature_guides = self.feature_guides.get(language, self.feature_guides["ja"])
                
                # Find current step
                current_step = None
                remaining_steps = []
                
                for step in steps:
                    if step.id not in progress.completed_steps:
                        if current_step is None:
                            current_step = step
                        else:
                            remaining_steps.append(step)
                
                # Calculate progress
                total_steps = len(steps)
                completed_count = len(progress.completed_steps)
                progress_percentage = (completed_count / total_steps) * 100 if total_steps > 0 else 0
                
                # Calculate estimated time
                estimated_time = sum(step.estimated_time_minutes for step in remaining_steps)
                if current_step:
                    estimated_time += current_step.estimated_time_minutes
                
                return OnboardingStatusResponse(
                    is_first_time=True,
                    welcome_message=welcome_message,
                    current_step=current_step,
                    remaining_steps=remaining_steps,
                    progress_percentage=progress_percentage,
                    estimated_remaining_time=estimated_time,
                    feature_guides=feature_guides
                )
            else:
                # Returning user - no onboarding needed
                return OnboardingStatusResponse(
                    is_first_time=False,
                    welcome_message=None,
                    current_step=None,
                    remaining_steps=[],
                    progress_percentage=100.0,
                    estimated_remaining_time=0,
                    feature_guides=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to get onboarding status: {e}", exc_info=True)
            # Return basic first-time flow on error
            return OnboardingStatusResponse(
                is_first_time=True,
                welcome_message=self.welcome_messages.get(language, self.welcome_messages["ja"]),
                current_step=self.onboarding_steps.get(language, self.onboarding_steps["ja"])[0],
                remaining_steps=[],
                progress_percentage=0.0,
                estimated_remaining_time=10,
                feature_guides=[]
            )
    
    async def complete_onboarding_step(
        self,
        user_id: Optional[str],
        device_id: str,
        step_id: str,
        step_data: Optional[Dict[str, Any]] = None
    ) -> OnboardingCompleteResponse:
        """Mark an onboarding step as complete and return next step"""
        try:
            # Get current progress
            progress = await self._get_onboarding_progress(user_id, device_id)
            
            # Mark step as complete
            if step_id not in progress.completed_steps:
                progress.completed_steps.append(step_id)
            
            # Find next step
            steps = self.onboarding_steps.get(progress.language, self.onboarding_steps["ja"])
            next_step = None
            for i, step in enumerate(steps):
                if step.id == step_id and i + 1 < len(steps):
                    next_step = steps[i + 1]
                    break
            
            # Check if onboarding is now complete
            steps = self.onboarding_steps.get(progress.language, self.onboarding_steps["ja"])
            required_steps = [step.id for step in steps if step.is_required]
            completed_required_steps = [step for step in required_steps if step in progress.completed_steps]
            
            if len(completed_required_steps) == len(required_steps) and not progress.completed_at:
                progress.completed_at = datetime.utcnow()
                progress.is_first_time = False
            
            # Save progress
            await self._save_onboarding_progress(progress)
            
            # Calculate new progress percentage
            total_steps = len(steps)
            completed_count = len(progress.completed_steps)
            progress_percentage = (completed_count / total_steps * 100) if total_steps > 0 else 0
            
            return OnboardingCompleteResponse(
                success=True,
                progress_percentage=progress_percentage,
                next_step=next_step,
                is_complete=progress.completed_at is not None
            )
            
        except Exception as e:
            logger.error(f"Failed to complete onboarding step: {e}", exc_info=True)
            raise
    
    async def quick_setup(
        self,
        user_id: Optional[str],
        device_id: str,
        setup_request: QuickSetupRequest
    ) -> OnboardingResponse:
        """Complete quick setup for essential features"""
        try:
            # Get current progress
            progress = await self._get_onboarding_progress(user_id, device_id)
            
            # Mark relevant steps as complete based on quick setup
            if setup_request.enable_location or setup_request.enable_notifications:
                progress.completed_steps.append("permissions")
            
            if setup_request.add_emergency_contact:
                progress.completed_steps.append("emergency_contacts")
            
            if setup_request.skip_tutorial:
                # Mark all optional steps as complete
                progress.completed_steps.extend(["guide_intro", "quiz_intro"])
            
            # Update language
            progress.language = setup_request.language
            
            # Save progress
            await self._save_onboarding_progress(progress)
            
            return await self.get_onboarding_status(user_id, device_id, setup_request.language)
            
        except Exception as e:
            logger.error(f"Failed to complete quick setup: {e}", exc_info=True)
            raise
    
    async def _get_onboarding_progress(
        self, 
        user_id: Optional[str], 
        device_id: str
    ) -> OnboardingProgress:
        """Get user's onboarding progress from database"""
        try:
            db = get_db()
            
            # Use device_id as primary key if user_id is not available
            doc_id = user_id if user_id else f"device_{device_id}"
            doc = db.collection("onboarding_progress").document(doc_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                return OnboardingProgress(**data)
            else:
                # Create new progress for first-time user
                return OnboardingProgress(
                    user_id=user_id or "",
                    device_id=device_id,
                    is_first_time=True,
                    completed_steps=[],
                    current_step_id="welcome"
                )
                
        except Exception as e:
            logger.error(f"Failed to get onboarding progress: {e}", exc_info=True)
            # Return default first-time progress
            return OnboardingProgress(
                user_id=user_id or "",
                device_id=device_id,
                is_first_time=True
            )
    
    async def _save_onboarding_progress(self, progress: OnboardingProgress):
        """Save onboarding progress to database"""
        try:
            db = get_db()
            
            doc_id = progress.user_id if progress.user_id else f"device_{progress.device_id}"
            progress_dict = progress.dict()
            progress_dict["updated_at"] = datetime.utcnow()
            
            db.collection("onboarding_progress").document(doc_id).set(progress_dict, merge=True)
            
        except Exception as e:
            logger.error(f"Failed to save onboarding progress: {e}", exc_info=True)
            raise
    
    async def skip_onboarding(
        self,
        user_id: Optional[str],
        device_id: str
    ):
        """Skip the entire onboarding process"""
        try:
            progress = await self._get_onboarding_progress(user_id, device_id)
            
            # Mark all steps as skipped except required ones
            steps = self.onboarding_steps.get(progress.language, self.onboarding_steps["ja"])
            for step in steps:
                if not step.is_required and step.id not in progress.completed_steps:
                    progress.skipped_steps.append(step.id)
                elif step.is_required and step.id not in progress.completed_steps:
                    progress.completed_steps.append(step.id)
            
            progress.completed_at = datetime.utcnow()
            progress.is_first_time = False
            progress.current_step_id = None
            
            await self._save_onboarding_progress(progress)
            
        except Exception as e:
            logger.error(f"Failed to skip onboarding: {e}", exc_info=True)
            raise