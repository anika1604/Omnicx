"""Knowledge Agent — RAG pipeline over the company knowledge base."""
import asyncio
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from config import get_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

settings = get_settings()


class KnowledgeAgent(BaseAgent):
    name = "knowledge"

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            transport="rest",
            temperature=0.2,
        )

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        # Try ChromaDB — silently skip if unavailable
        context = ""
        sources = 0
        try:
            import chromadb
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            ef = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
            collection = client.get_or_create_collection(name=settings.chroma_collection, embedding_function=ef)
            results = collection.query(query_texts=[inp.message], n_results=3)
            docs = results.get("documents", [[]])[0]
            if docs:
                context = "\n\n".join(docs)
                sources = len(docs)
        except Exception:
            pass  # No KB available — use conversation history only

        # Build history string
        history_lines = []
        for turn in inp.history[-10:]:
            role = "Customer" if turn.get("role") == "user" else "Agent"
            history_lines.append(f"{role}: {turn.get('content', '')}")
        history_ctx = "\n".join(history_lines) if history_lines else ""

        # System prompt — use KB if available, otherwise use history
        if context:
            system = (
                "You are a helpful customer support agent. "
                "Answer using the context below. If the answer isn't in the context, use your general knowledge.\n\n"
                f"Knowledge Base:\n{context}"
            )
        else:
            system = (
                "You are a helpful customer support agent. "
                "Use the conversation history to personalize your response. "
                "If the customer mentioned their name, use it. "
                "Answer helpfully from your general knowledge."
            )

        # Build messages
        content = ""
        if history_ctx:
            content += f"Conversation so far:\n{history_ctx}\n\n"
        content += f"Customer: {inp.message}"

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=content),
        ]

        response = await asyncio.get_event_loop().run_in_executor(
            None, self.llm.invoke, messages
        )

        return AgentOutput(
            agent_name=self.name,
            result={"answer": response.content, "sources_used": sources},
            confidence=0.9,
        )
