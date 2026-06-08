"""
Knowledge Agent — RAG pipeline over the company knowledge base.

Flow: embed query → ChromaDB similarity search → LLM with retrieved context → answer
"""

import asyncio
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from config import get_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

settings = get_settings()

RAG_SYSTEM = """You are a knowledgeable customer support agent.
Answer the customer's question using ONLY the provided context.
If the context doesn't contain the answer, say so honestly.
Be concise, warm, and helpful. Do not make things up."""


class KnowledgeAgent(BaseAgent):
    name = "knowledge"

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            transport="rest",
            temperature=0.2,
        )
        self._vector_store = None

    def _get_vector_store(self):
        if self._vector_store is None:
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            ef = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
            self._vector_store = client.get_or_create_collection(
                name=settings.chroma_collection,
                embedding_function=ef,
            )
        return self._vector_store

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        # Retrieve relevant chunks
        try:
            collection = self._get_vector_store()
            results = collection.query(query_texts=[inp.message], n_results=4)
            docs = results.get("documents", [[]])[0]
            context = "\n\n---\n\n".join(docs) if docs else "No relevant documents found."
        except Exception:
            context = "Knowledge base unavailable."

        # Generate grounded response
        messages = [
            SystemMessage(content=RAG_SYSTEM),
            HumanMessage(content=f"Context:\n{context}\n\nCustomer question: {inp.message}"),
        ]
        response = await asyncio.get_event_loop().run_in_executor(None, self.llm.invoke, messages)

        return AgentOutput(
            agent_name=self.name,
            result={"answer": response.content, "sources_used": len(docs) if "docs" in dir() else 0},
            confidence=0.9,
        )
