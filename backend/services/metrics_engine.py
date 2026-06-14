"""
Real-time Metrics Engine

Computes and streams:
  CSAT · NPS · FCR (first-contact resolution) · AHT · Churn probability
"""

from __future__ import annotations
import time
import json
import os
from dataclasses import dataclass, field
from collections import deque
from typing import Deque


@dataclass
class InteractionMetric:
    session_id:   str
    channel:      str
    intent:       str
    sentiment:    str
    resolved:     bool
    handle_time:  float
    csat_score:   float | None = None
    ts:           float = field(default_factory=time.time)


class MetricsEngine:
    """Rolling-window metrics over the last N interactions."""

    WINDOW = 500

    def __init__(self):
        self._buffer: Deque[InteractionMetric] = deque(maxlen=self.WINDOW)

    def record(self, metric: InteractionMetric) -> None:
        self._buffer.append(metric)

    def snapshot(self) -> dict:
        buf = list(self._buffer)
        if not buf:
            return self._empty_snapshot()

        resolved     = [m for m in buf if m.resolved]
        csat_scores  = [m.csat_score for m in buf if m.csat_score is not None]
        handle_times = [m.handle_time for m in buf]
        sentiments   = [m.sentiment for m in buf]

        fcr  = len(resolved) / len(buf)
        csat = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else None
        aht  = sum(handle_times) / len(handle_times)
        neg_ratio  = sentiments.count("frustrated") / len(sentiments)
        churn_prob = round(min(neg_ratio * 1.8, 1.0), 3)

        channels = {}
        for m in buf:
            channels.setdefault(m.channel, 0)
            channels[m.channel] += 1

        return {
            "fcr":                    round(fcr, 3),
            "csat":                   csat,
            "aht_seconds":            round(aht, 1),
            "churn_prob":             churn_prob,
            "nps":                    self._estimate_nps(csat),
            "total_interactions":     len(buf),
            "by_channel":             channels,
            "sentiment_distribution": {
                s: sentiments.count(s)
                for s in ("positive", "neutral", "negative", "frustrated")
            },
        }

    def _estimate_nps(self, csat: float | None) -> int | None:
        if csat is None:
            return None
        promoters  = csat / 5
        detractors = (5 - csat) / 5 * 0.4
        return round((promoters - detractors) * 100)

    def _empty_snapshot(self) -> dict:
        return {
            "fcr": 0, "csat": None, "aht_seconds": 0,
            "churn_prob": 0, "nps": None,
            "total_interactions": 0,
            "by_channel": {}, "sentiment_distribution": {},
        }


# ── File-based persistence (survives process reloads) ──────────────────────────

_METRICS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'metrics_store.json')
)

_engine = MetricsEngine()


def get_engine() -> MetricsEngine:
    return _engine


def record_metric(metric: InteractionMetric) -> None:
    """Write metric to file so all processes can read it."""
    try:
        data = []
        if os.path.exists(_METRICS_FILE):
            with open(_METRICS_FILE, 'r') as f:
                data = json.load(f)

        data.append({
            'session_id':  metric.session_id,
            'channel':     metric.channel,
            'intent':      metric.intent,
            'sentiment':   metric.sentiment,
            'resolved':    metric.resolved,
            'handle_time': metric.handle_time,
            'csat_score':  metric.csat_score,
            'ts':          metric.ts,
        })

        data = data[-500:]  # keep last 500

        with open(_METRICS_FILE, 'w') as f:
            json.dump(data, f)

    except Exception as e:
        print(f"[Metrics] write error: {e}")


def get_snapshot() -> dict:
    """Read metrics from file and compute live snapshot."""
    try:
        if not os.path.exists(_METRICS_FILE):
            return MetricsEngine()._empty_snapshot()

        with open(_METRICS_FILE, 'r') as f:
            data = json.load(f)

        if not data:
            return MetricsEngine()._empty_snapshot()

        resolved     = [m for m in data if m.get('resolved')]
        handle_times = [m['handle_time'] for m in data]
        sentiments   = [m['sentiment'] for m in data]
        csat_scores  = [m['csat_score'] for m in data if m.get('csat_score') is not None]

        fcr        = len(resolved) / len(data)
        aht        = sum(handle_times) / len(handle_times)
        neg_ratio  = sentiments.count('frustrated') / len(sentiments)
        csat       = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else None

        nps = None
        if csat is not None:
            promoters  = csat / 5
            detractors = (5 - csat) / 5 * 0.4
            nps        = round((promoters - detractors) * 100)

        channels = {}
        for m in data:
            channels.setdefault(m['channel'], 0)
            channels[m['channel']] += 1

        return {
            'fcr':         round(fcr, 3),
            'csat':        csat,
            'aht_seconds': round(aht, 1),
            'churn_prob':  round(min(neg_ratio * 1.8, 1.0), 3),
            'nps':         nps,
            'total_interactions': len(data),
            'by_channel':  channels,
            'sentiment_distribution': {
                s: sentiments.count(s)
                for s in ('positive', 'neutral', 'negative', 'frustrated')
            },
        }

    except Exception as e:
        print(f"[Metrics] read error: {e}")
        return MetricsEngine()._empty_snapshot()