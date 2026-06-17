"""
Sentiment Agent — Uses pretrained RoBERTa for emotion classification.
Falls back to keyword heuristic if model unavailable.
"""
import re
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from config import get_settings

settings = get_settings()

FRUSTRATED_KEYWORDS = re.compile(
    r"\b(angry|frustrated|awful|terrible|worst|useless|refund|cancel|"
    r"never again|ridiculous|unacceptable|disgusting|hate|pathetic|worst)\b",
    re.IGNORECASE,
)
POSITIVE_KEYWORDS = re.compile(
    r"\b(great|excellent|love|amazing|fantastic|thanks|helpful|perfect|happy)\b",
    re.IGNORECASE,
)

def _heuristic_sentiment(text: str) -> dict:
    if FRUSTRATED_KEYWORDS.search(text):
        return {"label": "frustrated", "score": 0.82, "fallback": True}
    if POSITIVE_KEYWORDS.search(text):
        return {"label": "positive",   "score": 0.78, "fallback": True}
    return {"label": "neutral", "score": 0.60, "fallback": True}


class SentimentAgent(BaseAgent):
    name = "sentiment"

    def __init__(self):
        self._pipe = None
        self._try_load_model()

    def _try_load_model(self):
        try:
            from transformers import pipeline
            import os
            model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'ml', 'sentiment', 'model')
            )
            if os.path.exists(model_path):
                self._pipe = pipeline(
                    "text-classification",
                    model=model_path,
                    top_k=None,
                    device=-1,
                )
                print("✅ Sentiment model loaded (Fine-tuned RoBERTa 96% accuracy)")
            else:
                # Fallback to pretrained
                self._pipe = pipeline(
                    "text-classification",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    top_k=None,
                    device=-1,
                )
                print("✅ Sentiment model loaded (RoBERTa pretrained)")
        except Exception as e:
            print(f"⚠️  Sentiment model not available, using heuristic: {e}")

    def _map_label(self, label: str) -> str:
        label = label.lower()
        if label in ("negative", "neg"):
            return "frustrated"
        if label in ("positive", "pos"):
            return "positive"
        return "neutral"

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        if self._pipe is None:
            result = _heuristic_sentiment(inp.message)
        else:
            try:
                raw    = self._pipe(inp.message[:512])[0]
                top    = max(raw, key=lambda x: x["score"])
                label  = self._map_label(top["label"])
                score  = round(top["score"], 4)

                # Upgrade to frustrated if score is high negative
                if label == "frustrated" and score < 0.6:
                    label = "negative"

                result = {"label": label, "score": score, "fallback": False}
            except Exception:
                result = _heuristic_sentiment(inp.message)

        result["threshold"]          = settings.sentiment_threshold
        result["trigger_escalation"] = (
            result["label"] in ("frustrated", "negative")
            and result["score"] >= settings.sentiment_threshold
        )

        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=result["score"],
        )
