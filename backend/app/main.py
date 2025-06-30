# backend/app/main.py
import asyncio
import logging
from app.config import app_settings
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# .env ファイルをロード (他のインポートより先が安全)
load_dotenv()

# --- typing.Partial の互換性対応 (応急処置) ---
import typing
import functools

if not hasattr(typing, 'Partial'):
    typing.Partial = functools.partial
# --- 応急処置ここまで ---

# --- ロギング設定 ---
# アプリケーション全体のログレベルを設定 (WARNINGレベル以上のログを表示)
# 環境変数からログレベルを取得 (デフォルトはWARNING)
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.WARNING),
    format='%(levelname)s:%(name)s:%(message)s'
)

# 全てのloggerのレベルを統一設定
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, log_level, logging.WARNING))

# 特定のloggerを強制的にWARNING以上に設定
for logger_name in ['urllib3', 'sentence_transformers', 'faiss', 'transformers']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# フロントエンドへの送信内容を確認するため、特定のモジュールでDEBUGログを有効化
for logger_name in ['app.api.v1.endpoints.chat', 'app.api.v1.endpoints.heartbeat', 
                   'app.agents.safety_beacon_agent.handlers.response_generator']:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- Firebase Admin SDK 初期化 ---
import firebase_admin
import json
from firebase_admin import credentials
try:
    if not firebase_admin._apps:
        # 環境変数からサービスアカウント情報を取得
        # まずファイルベースの認証を試行
        service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not service_account_path:
            # デフォルトパスを環境変数から取得
            service_account_path = os.getenv("DEFAULT_SERVICE_ACCOUNT_PATH")
        
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            # プロジェクトIDを明示的に指定
            firebase_admin.initialize_app(cred, {
                'projectId': os.getenv("GCP_PROJECT_ID")
            })
            logger.info("Firebase Admin SDK initialized successfully with key file.")
        else:
            # 環境変数からサービスアカウント情報を取得（フォールバック）
            service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
            if service_account_info:
                try:
                    # 直接JSONをパースを試行
                    service_account_dict = json.loads(service_account_info)
                    
                    # 一時的なサービスアカウントファイルを作成
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                        json.dump(service_account_dict, temp_file, indent=2)
                        temp_file_path = temp_file.name
                    
                    try:
                        cred = credentials.Certificate(temp_file_path)
                        # プロジェクトIDを明示的に指定
                        firebase_admin.initialize_app(cred, {
                            'projectId': os.getenv("GCP_PROJECT_ID")
                        })
                        logger.info("Firebase Admin SDK initialized successfully with service account.")
                    finally:
                        # 一時ファイルを削除
                        import os as temp_os
                        try:
                            temp_os.unlink(temp_file_path)
                        except:
                            pass
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse service account JSON: {e}")
                    logger.info("Attempting to clean JSON string...")
                    try:
                        # 制御文字を削除
                        import re
                        cleaned_info = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', service_account_info)
                        service_account_dict = json.loads(cleaned_info)
                        
                        # 一時的なサービスアカウントファイルを作成
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                            json.dump(service_account_dict, temp_file, indent=2)
                            temp_file_path = temp_file.name
                        
                        try:
                            cred = credentials.Certificate(temp_file_path)
                            # プロジェクトIDを明示的に指定
                            firebase_admin.initialize_app(cred, {
                                'projectId': os.getenv("GCP_PROJECT_ID")
                            })
                            logger.info("Firebase Admin SDK initialized successfully with cleaned service account.")
                        finally:
                            # 一時ファイルを削除
                            import os as temp_os
                            try:
                                temp_os.unlink(temp_file_path)
                            except:
                                pass
                                
                    except (json.JSONDecodeError, ValueError, Exception) as final_error:
                        logger.error(f"All service account parsing attempts failed: {final_error}")
                        logger.warning("Using default credentials (emulator mode)")
                        try:
                            firebase_admin.initialize_app()
                            logger.info("Firebase Admin SDK initialized with default credentials.")
                        except Exception as default_error:
                            logger.error(f"Failed to initialize with default credentials: {default_error}")
                            raise default_error
            else:
                # ADC (Application Default Credentials) を使用（エミュレーター用）
                logger.warning("No service account found. Initializing with default credentials (emulator mode)")
                firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized with default credentials.")
    else:
        logger.info("Firebase Admin SDK already initialized.")
except ValueError as e:
    # よくある初期化済みエラーは Warning にする
    if "The default Firebase app already exists" in str(e):
        logger.warning("Firebase Admin SDK already initialized.")
    else:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
except Exception as e:
    logger.error(f"An unexpected error occurred during Firebase Admin SDK initialization: {e}", exc_info=True)

# --- Firestore Client 初期化関数のインポート ---
try:
    from app.db.firestore_client import get_db # initialize_firestore_client から get_db に変更
    firestore_imported = True
except ImportError as e:
     logger.error(f"Failed to import Firestore client: {e}")
     firestore_imported = False

# --- API ルーターのインポート ---
# エラーハンドリングのため try...except で囲むのは良いアプローチ
try:
    from app.api.v1.endpoints import health, chat, push, agent_suggestions, debug, devices, heartbeat
    routers_imported = True
except ImportError as e:
    logger.error(f"Failed to import routers: {e}. Ensure endpoint files and router instances exist.")
    routers_imported = False

# --- 設定のインポート ---
config_imported = False

# --- バックグラウンドワーカーのインポート ---
try:
    from app.services.background_disaster_worker import background_disaster_worker
    worker_imported = True
except ImportError as e:
    logger.error(f"Failed to import background disaster worker: {e}")
    worker_imported = False

# --- アプリケーションのライフスパン管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 最小限の起動（HTTPサーバー優先）
    logger.info("🚀 Minimal startup - HTTP server first")
    
    # 全ての初期化を遅延実行（完全非ブロッキング）
    async def background_init():
        await asyncio.sleep(3)  # HTTPサーバー完全起動まで待機（短縮）
        logger.info("💼 Starting background services...")
        
        # 安全な初期化（エラーがあっても続行）
        try:
            if firestore_imported:
                await asyncio.to_thread(get_db)
                logger.info("✅ Firestore initialized")
        except Exception as e:
            logger.warning(f"⚠️ Firestore skip: {e}")
        
        # ツールの事前初期化（ユーザーの待機時間を減らす）
        try:
            from app.agents.safety_beacon_agent.tool_definitions import preload_tools
            await asyncio.to_thread(preload_tools)
            logger.info("✅ Tools preloaded in background")
        except Exception as e:
            logger.warning(f"⚠️ Tool preload failed: {e}")
        
        logger.info("✅ Background services ready")
    
    # 全てを非同期バックグラウンドで実行
    asyncio.create_task(background_init())
    
    logger.info("🎯 HTTP server ready for requests (tools loading in background)")
    yield
    
    # アプリケーション終了時（最小限のクリーンアップ）
    logger.info("Application shutdown initiated...")
    
    # 基本的なクリーンアップのみ
    try:
        if worker_imported:
            await asyncio.wait_for(background_disaster_worker.stop(), timeout=2.0)
        logger.info("Essential cleanup completed")
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")
    
    logger.info("Application shutdown complete")
    

# --- リクエストロギングミドルウェア ---
async def log_requests(request: Request, call_next):
    start_time = datetime.now(timezone.utc)
    response = await call_next(request)

    process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    # Only log slow requests or errors
    if response.status_code >= 400 or process_time > 2000:
        logger.info(f"Request: {request.method} {request.url.path} - Status: {response.status_code} - {process_time:.2f}ms")

    return response

# --- FastAPIアプリケーションインスタンスを作成 ---
app = FastAPI(
    title="LinguaSafeTrip Backend API",
    description="API for the LinguaSafeTrip PWA, providing AI-powered multilingual disaster assistance.",
    version="4.0.0", # Version updated to match project
    lifespan=lifespan # lifespan を設定
    # docs_url="/api/docs", # 必要なら API ドキュメントのパスを変更
    # redoc_url="/api/redoc"
)

# ミドルウェアを追加 (CORSの前に追加するのが一般的)
app.middleware("http")(log_requests)

# バリデーションエラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーの詳細ログ"""
    logger.error(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# --- ミドルウェア設定 (CORS) ---
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ルーターの登録 ---
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# ルーターのインポートが成功した場合のみ登録処理を行う
if routers_imported:
    # Health Check ルーター
    if 'health' in locals() and hasattr(health, 'router'):
        app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
        logger.info("Health router registered.")
    else:
        logger.warning("Health router not found or invalid.")

    # Chat ルーターは v1 ルーターで統合管理

    # Push Handler ルーター
    if 'push' in locals() and hasattr(push, 'router'):
        app.include_router(push.router, prefix=API_PREFIX, tags=["Push"])
        logger.info("Push router registered.")
    else:
        logger.warning("Push router not found or invalid.")

    # Network Recovery ルーターは v1 ルーターで統合管理

    # Agent Suggestions, Debug, Devices ルーターは v1 ルーターで統合管理
    # 個別登録はコメントアウト

    # Shelters ルーターは削除済み


    # v1 API ルーターを明示的に登録
    from app.api.v1 import router as v1_router, include_routers
    include_routers()
    app.include_router(v1_router, prefix=API_PREFIX)
    logger.info("All v1 API routers registered successfully")
    
    # Vertex AI Search キルスイッチルーターを登録
    try:
        from app.api.killswitch_routes import router as killswitch_router
        app.include_router(killswitch_router, prefix=API_PREFIX, tags=["Vertex AI Search"])
        logger.info("Vertex AI Search killswitch router registered.")
    except ImportError as e:
        logger.warning(f"Vertex AI Search killswitch router not available: {e}")

    # Disaster Chat ルーターも v1 ルーターで統合管理
    # 個別登録はコメントアウト

    # Disaster Shelter Info router は削除済み
    
    # Unified Disaster Management ルーターは削除済み
    
    # Heartbeat API ルーターは v1 ルーターで統合管理
    

    # Route registration logging removed for cleaner output

else:
    logger.error("Could not register routers due to import errors. API endpoints will be unavailable.")


# --- ルートパス ---
@app.get("/", tags=["Root"])
async def read_root():
    """ルートパスへのアクセス"""
    return {
        "message": "Welcome to the LinguaSafeTrip Backend API!",
        "version": "4.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "tools_status": "/tools-status"
        }
    }

# --- バックグラウンドタスク状態エンドポイント ---
@app.get("/tools-status", tags=["Diagnostics"])
async def tools_status():
    """ツールの初期化状態を確認"""
    try:
        from app.agents.safety_beacon_agent.tool_definitions import is_tools_ready
        ready = is_tools_ready()
        return {
            "tools_ready": ready,
            "status": "ready" if ready else "loading",
            "message": "ツールが使用可能です" if ready else "ツールをバックグラウンドでロード中..."
        }
    except Exception as e:
        return {
            "tools_ready": False,
            "status": "error",
            "error": str(e)
        }

# --- uvicorn 実行設定 (オプション) ---
# このファイル自体を直接 python main.py で実行する場合に使う
# 通常は uvicorn main:app --reload コマンドで起動する
# if __name__ == "__main__":
#    import uvicorn
#    # 環境変数 PORT があればそれを使い、なければ 8000 を使う (Cloud Run 等での利用を想定)
#    port = int(os.getenv("PORT", 8000))
#    logger.info(f"Starting uvicorn server on port {port}...")
#    # reload=True は開発時のみ有効にするのが一般的
#    # is_development = os.getenv("ENV", "production").lower() == "development"
#    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) # reload は開発時
