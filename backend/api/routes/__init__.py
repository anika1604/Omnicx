from fastapi import APIRouter
from api.routes.chat     import router as chat_router
from api.routes.metrics  import router as metrics_router
from api.routes.sessions import router as sessions_router
from api.routes.webhooks import router as webhooks_router
from api.routes.feedback import router as feedback_router

router = APIRouter()
router.include_router(chat_router,     prefix="/chat",     tags=["Chat"])
router.include_router(metrics_router,  prefix="/metrics",  tags=["Metrics"])
router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])