"""
Seed the ChromaDB knowledge base with sample support documents.
Run: python scripts/seed_vectordb.py
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from config import get_settings

SAMPLE_DOCS = [
    {"id": "kb-001", "text": "Return policy: Customers may return any item within 30 days of purchase for a full refund. Items must be in original condition. Digital products are non-refundable.", "meta": {"category": "returns"}},
    {"id": "kb-002", "text": "Refund processing time: Once a return is received and inspected, refunds are processed within 3–5 business days to the original payment method.", "meta": {"category": "refunds"}},
    {"id": "kb-003", "text": "Shipping policy: Standard shipping takes 5–7 business days. Express shipping takes 1–2 business days. Free shipping on orders over $50.", "meta": {"category": "shipping"}},
    {"id": "kb-004", "text": "Account management: To update your account details, go to Settings > Profile. To delete your account, contact support@omnicx.ai.", "meta": {"category": "account"}},
    {"id": "kb-005", "text": "Subscription cancellation: You can cancel your subscription at any time. Cancellation takes effect at the end of the current billing period. No partial refunds for unused time.", "meta": {"category": "subscriptions"}},
    {"id": "kb-006", "text": "Order tracking: Once your order ships, you'll receive a tracking number via email. Track your package at our website under Orders > Track.", "meta": {"category": "orders"}},
    {"id": "kb-007", "text": "Business hours: Our support team is available Monday–Friday 9am–6pm EST. For urgent issues outside business hours, use our 24/7 chat bot.", "meta": {"category": "support"}},
    {"id": "kb-008", "text": "Warranty: All products come with a 12-month manufacturer warranty. Extended warranty plans are available for purchase at checkout.", "meta": {"category": "warranty"}},
]

def seed():
    settings = get_settings()
    ef = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    collection = client.get_or_create_collection(name=settings.chroma_collection, embedding_function=ef)

    collection.upsert(
        ids=[d["id"] for d in SAMPLE_DOCS],
        documents=[d["text"] for d in SAMPLE_DOCS],
        metadatas=[d["meta"] for d in SAMPLE_DOCS],
    )
    print(f"✅ Seeded {len(SAMPLE_DOCS)} documents into '{settings.chroma_collection}'")

if __name__ == "__main__":
    seed()
