from fastapi import APIRouter
from db.schemas import FeedbackSchema
import json, os

router = APIRouter()

METRICS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'metrics_store.json'))


@router.post("/")
async def submit_feedback(fb: FeedbackSchema):
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = []

        # Find the matching session and update CSAT
        updated = False
        for m in reversed(data):
            if m.get('session_id') == fb.session_id:
                m['csat_score'] = fb.csat_score
                updated = True
                break

        # If no matching session found, append a new entry
        if not updated:
            data.append({
                'session_id':  fb.session_id,
                'channel':     'web',
                'intent':      'feedback',
                'sentiment':   'neutral',
                'resolved':    True,
                'handle_time': 0,
                'csat_score':  fb.csat_score,
                'ts':          0,
            })

        with open(METRICS_FILE, 'w') as f:
            json.dump(data, f)

        print(f"[Feedback] session={fb.session_id} csat={fb.csat_score}")

    except Exception as e:
        print(f"[Feedback] error: {e}")

    return {"status": "received", "session_id": fb.session_id, "csat": fb.csat_score}