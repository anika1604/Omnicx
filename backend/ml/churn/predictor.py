"""XGBoost churn predictor using trained Telco model."""
import os
import pickle

_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'model.pkl'))
_payload = None


def _load():
    global _payload
    if _payload is None:
        try:
            with open(_MODEL_PATH, 'rb') as f:
                _payload = pickle.load(f)
            print("✅ Churn model loaded (XGBoost AUC=0.842)")
        except Exception as e:
            print(f"⚠️  Churn model not available: {e}")
    return _payload


def predict_churn_from_session(
    frustrated_ratio:  float = 0.0,
    turn_count:        int   = 1,
    channel_switches:  int   = 0,
    resolved:          bool  = True,
    avg_handle_time:   float = 30.0,
) -> float:
    """
    Predicts churn probability from session features.
    Maps session signals to Telco-like features for inference.
    Returns float between 0.0 and 1.0.
    """
    payload = _load()
    if payload is None:
        return round(min(frustrated_ratio * 2, 1.0), 2)

    # Map session signals to Telco dataset feature space
    # Contract: 0=Month-to-month, 1=One year, 2=Two year
    # Frustrated customers behave like month-to-month (high churn risk)
    contract = 0 if frustrated_ratio > 0.5 else (1 if frustrated_ratio > 0.2 else 2)

    # Tenure proxy — more turns = longer relationship
    tenure = max(1, 24 - (turn_count * 2))

    # Monthly charges proxy — more channel switches = higher complexity/cost
    monthly_charges = 50 + (channel_switches * 15) + (frustrated_ratio * 30)

    # Online security/tech support — resolved = has support
    online_security = 1 if resolved else 0
    tech_support    = 1 if resolved else 0

    # Internet service — assume fiber (most common churn segment)
    internet_service = 1

    features = [[
        tenure,           # tenure
        monthly_charges,  # MonthlyCharges
        monthly_charges * tenure,  # TotalCharges
        contract,         # Contract
        internet_service, # InternetService
        1,                # PaymentMethod (electronic)
        0,                # Partner
        0,                # Dependents
        1,                # PhoneService
        1,                # PaperlessBilling
        0,                # MultipleLines
        online_security,  # OnlineSecurity
        0,                # OnlineBackup
        0,                # DeviceProtection
        tech_support,     # TechSupport
        0,                # StreamingTV
        0,                # StreamingMovies
        0,                # gender
        0,                # SeniorCitizen
    ]]

    try:
        proba = payload["model"].predict_proba(features)[0][1]
        # Blend with session signal for better accuracy
        session_signal = min(frustrated_ratio * 2, 1.0)
        blended = (float(proba) * 0.6) + (session_signal * 0.4)
        return round(blended, 3)
    except Exception as e:
        print(f"[Churn] inference error: {e}")
        return round(min(frustrated_ratio * 2, 1.0), 2)