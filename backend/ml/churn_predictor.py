"""
XGBoost Churn Predictor — inference module.
Loads trained model and predicts churn probability from session features.
Falls back to sentiment-ratio heuristic if model not available.
"""
import os
import pickle
import numpy as np

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'churn', 'model.pkl')
)

CHANNEL_MAP = {'web': 0, 'email': 1, 'whatsapp': 2, 'voice': 3, 'kiosk': 4}

_model_data = None


def _load_model():
    global _model_data
    if _model_data is not None:
        return _model_data
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                _model_data = pickle.load(f)
            print("✅ XGBoost churn model loaded")
        else:
            print("⚠️  Churn model not found, using heuristic")
    except Exception as e:
        print(f"⚠️  Churn model load error: {e}")
    return _model_data


def predict_churn(
    turn_count: int,
    frustrated_ratio: float,
    resolved: bool,
    channel_switches: int,
    avg_handle_time: float,
    csat_score: float,
    escalated: bool,
    days_since_first: int,
    total_sessions: int,
    unresolved_count: int,
    primary_channel: str = 'web',
) -> float:
    """Returns churn probability between 0.0 and 1.0."""
    data = _load_model()

    if data is None:
        # Heuristic fallback
        score = frustrated_ratio * 0.5
        if not resolved:        score += 0.2
        if escalated:           score += 0.15
        if csat_score <= 2.0:   score += 0.15
        return round(min(score, 1.0), 3)

    features = np.array([[
        turn_count,
        frustrated_ratio,
        int(resolved),
        channel_switches,
        avg_handle_time,
        csat_score,
        int(escalated),
        days_since_first,
        total_sessions,
        unresolved_count,
        CHANNEL_MAP.get(primary_channel, 0),
    ]])

    prob = data['model'].predict_proba(features)[0][1]
    return round(float(prob), 3)


def predict_churn_from_history(history: list, csat_score: float = 3.0, primary_channel: str = 'web') -> float:
    """Convenience wrapper — computes features from raw session history."""
    if not history:
        return 0.0

    user_turns = [t for t in history if t.get('role') == 'user']
    sentiments = [t.get('sentiment', 'neutral') for t in user_turns]
    frustrated = sentiments.count('frustrated') + sentiments.count('negative')
    frustrated_ratio = frustrated / max(len(sentiments), 1)

    channels = list({t.get('channel', 'web') for t in history})
    channel_switches = max(len(channels) - 1, 0)

    resolved = any(t.get('intent') not in ('complaint', 'churn_signal') for t in history)
    escalated = any(t.get('intent') == 'churn_signal' for t in history)

    return predict_churn(
        turn_count=len(user_turns),
        frustrated_ratio=round(frustrated_ratio, 2),
        resolved=resolved,
        channel_switches=channel_switches,
        avg_handle_time=30.0,
        csat_score=csat_score,
        escalated=escalated,
        days_since_first=30,
        total_sessions=1,
        unresolved_count=int(not resolved),
        primary_channel=primary_channel,
    )