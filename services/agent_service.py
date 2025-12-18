import anthropic
from typing import List, Dict, Any, Optional
import logging
from config.settings import settings
from models.query import Citation

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        # Check for available AI providers and initialize the first available one
        if settings.anthropic_api_key:
            self.provider = "anthropic"
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self.model = "claude-3-sonnet-20240229"
        elif settings.gemini_api_key:
            self.provider = "gemini"
            # Import and initialize Gemini via OpenAI-compatible endpoint
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=settings.gemini_api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                self.model = "gemini-2.5-flash"  # Use the appropriate Gemini model via OpenAI-compatible endpoint
            except ImportError:
                logger.error("OpenAI library not installed. Install with: pip install openai")
                raise ValueError("GEMINI_API_KEY provided but openai library not installed")
        elif settings.openai_api_key:
            self.provider = "openai"
            # Import and initialize OpenAI if available
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.model = "gpt-3.5-turbo"  # or another appropriate model
            except ImportError:
                logger.error("OpenAI library not installed. Install with: pip install openai")
                raise ValueError("OPENAI_API_KEY provided but openai library not installed")
        else:
            # For development/testing, we can proceed without an API key
            logger.warning("No AI provider API key found. Using mock responses for development.")
            self.provider = "mock"
            self.model = None

    def generate_response(self, query: str, context: List[Dict[str, Any]], selected_text: str = "") -> Dict[str, Any]:
        """
        Generate a response using the configured AI provider with provided context
        """
        try:
            # Format the context into a readable format for the agent
            context_text = ""
            citations = []

            for i, doc in enumerate(context):
                doc_text = doc.get("content", "")[:1000]  # Limit context size
                context_text += f"\n\nDocument {i+1}:\n{doc_text}\n"

                # Create citation object
                citation = Citation(
                    document_id=doc.get("document_id", f"doc_{i}"),
                    title=doc.get("title", "Unknown Title"),
                    url=doc.get("url", ""),
                    text_snippet=doc.get("text_snippet", doc.get("content", "")[:200]),
                    relevance_score=doc.get("relevance_score", 0.0)
                )
                citations.append(citation)

            # Build the full prompt
            prompt_parts = []

            if selected_text:
                prompt_parts.append(f"User selected this text: {selected_text}\n\n")

            prompt_parts.append(f"Context:\n{context_text}\n\n")
            prompt_parts.append(f"Question: {query}\n\n")
            prompt_parts.append("Please provide a comprehensive answer based on the provided context. If the context doesn't contain enough information to answer the question, please say so. Always cite your sources from the provided context.")

            full_prompt = "".join(prompt_parts)

            if self.provider == "anthropic":
                # Generate response using Anthropic Claude
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    temperature=0.3,
                    system="You are a helpful assistant that answers questions based on provided documentation. Always cite your sources from the provided context. If the context doesn't contain enough information to answer the question, please say so.",
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                )

                # Extract the response text
                response_text = message.content[0].text if message.content else "I couldn't generate a response based on the provided context."

                result = {
                    "answer": response_text,
                    "citations": citations,
                    "model_used": self.model,
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }

            elif self.provider == "gemini":
                # Generate response using Gemini via OpenAI-compatible endpoint
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided documentation. Always cite your sources from the provided context. If the context doesn't contain enough information to answer the question, please say so."
                        },
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ],
                    max_tokens=1024,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content if response.choices[0].message.content else "I couldn't generate a response based on the provided context."

                result = {
                    "answer": response_text,
                    "citations": citations,
                    "model_used": self.model,
                }

            elif self.provider == "openai":
                # Generate response using OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided documentation. Always cite your sources from the provided context. If the context doesn't contain enough information to answer the question, please say so."
                        },
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ],
                    max_tokens=1024,
                    temperature=0.3
                )

                response_text = response.choices[0].message.content if response.choices[0].message.content else "I couldn't generate a response based on the provided context."

                result = {
                    "answer": response_text,
                    "citations": citations,
                    "model_used": self.model,
                }

            elif self.provider == "mock":
                # For development/testing, return a mock response
                result = {
                    "answer": f"This is a mock response for your query: '{query}'. In a real implementation, this would be generated by an AI model using the provided context.",
                    "citations": citations,
                    "model_used": "mock",
                }

            logger.info(f"Generated response using {self.provider}")
            return result

        except Exception as e:
            logger.error(f"Error generating response with {self.provider}: {e}")
            return {
                "answer": "Sorry, I encountered an error while processing your request.",
                "citations": [],
                "error": str(e)
            }

    def validate_query(self, query: str) -> bool:
        """
        Basic validation of the query
        """
        if not query or len(query.strip()) == 0:
            return False
        if len(query) > 2000:  # Max length from data model
            return False
        return True

# Create a singleton instance with lazy initialization
class AgentServiceManager:
    def __init__(self):
        self._instance = None

    def get_instance(self):
        if self._instance is None:
            self._instance = AgentService()
        return self._instance

agent_service = AgentServiceManager()