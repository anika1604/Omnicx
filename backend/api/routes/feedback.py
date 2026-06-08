from fastapi import APIRouter
from db.schemas import FeedbackSchema

router = APIRouter()

@router.post("/")
async def submit_feedback(fb: FeedbackSchema):
    # In production: write to DB and trigger RLHF queue
    return {"status": "received", "session_id": fb.session_id, "csat": fb.csat_score}
