"""
Sentiment Agent — Fine-tuned RoBERTa emotion classifier.

Scores each message on:
  - label: positive | neutral | negative | frustrated
  - score: 0.0 – 1.0 (intensity)
  - emotions: {joy, anger, sadness, fear, surprise, disgust}

Falls back to a keyword heuristic when the model is not yet available.
"""
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from config import get_settings
import os, re

settings = get_settings()

# Simple keyword heuristic for MVP (replaced by fine-tuned model when available)
FRUSTRATED_KEYWORDS = re.compile(
    r"\b(angry|frustrated|awful|terrible|worst|useless|refund|cancel|"
    r"never again|ridiculous|unacceptable|disgusting|hate)\b",
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
        self._model = None
        self._tokenizer = None
        self._try_load_model()

    def _try_load_model(self):
        model_path = settings.sentiment_model_path
        if not os.path.exists(model_path):
            return  # will use heuristic
        try:
            from transformers import pipeline
            self._pipe = pipeline(
                "text-classification",
                model=model_path,
                top_k=None,
                device=-1,
            )
        except Exception:
            pass

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        if self._model is None:
            result = _heuristic_sentiment(inp.message)
        else:
            raw = self._pipe(inp.message[:512])[0]
            top = max(raw, key=lambda x: x["score"])
            result = {"label": top["label"].lower(), "score": round(top["score"], 4)}

        result["threshold"] = settings.sentiment_threshold
        result["trigger_escalation"] = (
            result["label"] == "frustrated"
            and result["score"] >= settings.sentiment_threshold
        )

        return AgentOutput(agent_name=self.name, result=result, confidence=result["score"])
