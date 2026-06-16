from agents.sentiment_agent import SentimentAgent
from agents.base_agent import AgentInput
import asyncio

agent = SentimentAgent()

messages = [
    "I love your service, thank you so much!",
    "My order still hasnt arrived after 3 weeks",
    "Can you tell me your business hours?",
    "This is absolutely terrible I want a refund NOW",
    "The product is okay I guess",
    "I am extremely disappointed with the quality",
]

async def test():
    for msg in messages:
        inp = AgentInput(session_id="test", customer_id="test", message=msg, channel="web")
        out = await agent.run(inp)
        label = out.result.get("label")
        score = out.result.get("score", 0)
        print(label, round(score,2), msg[:50])

asyncio.run(test())
