"""
Restaurant Agent for Kensho using Azure AI Foundry
"""
import json
import os
from typing import Optional, List, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from loguru import logger

from ..config import settings
from ..models import User, Restaurant
from ..services import knowledge_graph_service, rag_service


class RestaurantAgent:
    """
    Restaurant recommendation agent using Azure AI Foundry
    """

    def __init__(self):
        """Initialize the restaurant agent"""
        self.client: Optional[AIProjectClient] = None
        self.agent: Optional[Any] = None
        self.vector_store_id: Optional[str] = None
        self.active_threads: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the Azure AI agent"""
        try:
            logger.info("Initializing Restaurant Agent...")

            # Initialize Azure AI Project Client
            if settings.AZURE_AI_PROJECT_CONNECTION_STRING:
                # Use connection string if provided
                self.client = AIProjectClient.from_connection_string(
                    credential=DefaultAzureCredential(),
                    conn_str=settings.AZURE_AI_PROJECT_CONNECTION_STRING,
                )
            else:
                # Fallback to manual configuration
                logger.warning(
                    "AZURE_AI_PROJECT_CONNECTION_STRING not set. "
                    "Agent will run in mock mode for development."
                )
                return

            # Create or get the agent
            await self._create_agent()

            # Set up vector store for RAG
            await self._setup_vector_store()

            logger.info(f"Restaurant Agent initialized successfully: {self.agent.id}")

        except Exception as e:
            logger.error(f"Error initializing Restaurant Agent: {str(e)}")
            raise

    async def _create_agent(self):
        """Create the restaurant agent"""
        try:
            # Create agent with file search capabilities
            self.agent = self.client.agents.create_agent(
                model=settings.DEFAULT_MODEL,
                name=settings.AGENT_NAME,
                instructions=settings.AGENT_INSTRUCTIONS,
                tools=[{"type": "file_search"}],  # Enable file search for RAG
                tool_resources={
                    "file_search": {
                        "vector_stores": []  # Will be populated after vector store creation
                    }
                },
            )
            logger.info(f"Agent created: {self.agent.id}")

        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise

    async def _setup_vector_store(self):
        """Set up vector store with restaurant data"""
        try:
            # Create vector store
            vector_store = self.client.agents.create_vector_store(
                name="restaurant_knowledge_base",
                file_ids=[],  # Will upload files next
            )
            self.vector_store_id = vector_store.id
            logger.info(f"Vector store created: {self.vector_store_id}")

            # Upload restaurant data
            restaurant_data_path = settings.RESTAURANT_DATA_PATH
            if os.path.exists(restaurant_data_path):
                # Upload file to Azure
                with open(restaurant_data_path, "rb") as f:
                    file_upload = self.client.agents.upload_file(
                        file=f,
                        purpose="assistants",  # Use string instead of FilePurpose enum
                    )

                # Add file to vector store
                self.client.agents.create_vector_store_file(
                    vector_store_id=self.vector_store_id,
                    file_id=file_upload.id,
                )
                logger.info(f"Restaurant data uploaded to vector store")

            # Update agent to use this vector store
            self.agent = self.client.agents.update_agent(
                assistant_id=self.agent.id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                },
            )
            logger.info("Agent updated with vector store")

        except Exception as e:
            logger.error(f"Error setting up vector store: {str(e)}")
            raise

    async def create_thread(self, user: Optional[User] = None) -> str:
        """Create a new conversation thread"""
        try:
            # Create thread with user context
            messages = []
            if user:
                user_context = self._build_user_context(user)
                messages.append({
                    "role": "user",
                    "content": f"Here is my profile information:\n{user_context}",
                })

            thread = self.client.agents.create_thread(messages=messages)
            self.active_threads[thread.id] = thread
            logger.info(f"Thread created: {thread.id}")
            return thread.id

        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise

    async def send_message(
        self,
        thread_id: str,
        message: str,
        user: Optional[User] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Send a message to the agent and get response"""
        try:
            # Track search query in knowledge graph
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_search_query(
                    user_id=user_id,
                    query=message,
                    agent_type="restaurant",
                    results_count=0  # Will be updated after response
                )

            # Build RAG context if available (with KG integration)
            enhanced_message = message
            if rag_service.chroma_client:
                try:
                    user_context = self._build_user_context(user) if user else ""
                    rag_context = rag_service.build_context(
                        query=message,
                        agent_type="restaurant",
                        user_context=user_context,
                        max_chunks=3,
                        user_id=user_id
                    )
                    if rag_context:
                        enhanced_message = f"{rag_context}\n\nUser Question: {message}"
                except Exception as e:
                    logger.warning(f"Error building RAG context: {str(e)}")

            # Add message to thread
            self.client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=enhanced_message,
            )

            # Run the agent
            run = self.client.agents.create_run(
                thread_id=thread_id,
                assistant_id=self.agent.id,
            )

            # Wait for completion
            while run.status in ["queued", "in_progress", "cancelling"]:
                run = self.client.agents.get_run(
                    thread_id=thread_id,
                    run_id=run.id,
                )

            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                raise Exception(f"Agent run failed: {run.last_error}")

            # Get the latest message
            messages = self.client.agents.list_messages(thread_id=thread_id)
            latest_message = messages.data[0]

            # Extract text content
            response_text = ""
            if hasattr(latest_message, 'content'):
                for content in latest_message.content:
                    # Handle different content types
                    if hasattr(content, 'text'):
                        # MessageTextContent-like object
                        if hasattr(content.text, 'value'):
                            response_text += content.text.value
                        elif isinstance(content.text, str):
                            response_text += content.text
                    elif isinstance(content, dict):
                        # Dictionary format
                        if 'text' in content:
                            text_obj = content['text']
                            if isinstance(text_obj, dict) and 'value' in text_obj:
                                response_text += text_obj['value']
                            elif isinstance(text_obj, str):
                                response_text += text_obj
                    elif isinstance(content, str):
                        response_text += content

            return response_text

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def get_recommendations(
        self,
        query: str,
        user: Optional[User] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get restaurant recommendations"""
        try:
            # Create thread if not provided
            if not thread_id:
                thread_id = await self.create_thread(user)

            # Build the recommendation query
            recommendation_query = self._build_recommendation_query(query, user)

            # Get response from agent
            response = await self.send_message(thread_id, recommendation_query, user, user_id)

            # Parse recommendations
            recommendations = self._parse_recommendations(response)

            # Track restaurant interactions in knowledge graph
            if knowledge_graph_service.driver and user_id and recommendations:
                for rec in recommendations:
                    if isinstance(rec, dict) and "name" in rec:
                        knowledge_graph_service.track_restaurant_interaction(
                            user_id=user_id,
                            restaurant_id=rec.get("id", rec.get("name", "")),
                            restaurant_name=rec.get("name", ""),
                            cuisine=rec.get("cuisine", ""),
                            interaction_type="recommended",
                            context={"query": query}
                        )

            return {
                "thread_id": thread_id,
                "response": response,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise

    def _build_user_context(self, user: User) -> str:
        """Build user context string"""
        context = f"""
Name: {user.profile.name}
Location: {user.profile.location}
Dietary Type: {user.dietary.type.value}
"""
        if user.dietary.restrictions:
            restrictions = [f"{r.type.value}: {r.value}" for r in user.dietary.restrictions]
            context += f"Dietary Restrictions: {', '.join(restrictions)}\n"

        if user.dietary.goals:
            context += f"Dietary Goals: {', '.join(user.dietary.goals)}\n"

        if user.preferences.foods:
            liked_foods = [
                food for food, pref in user.preferences.foods.items()
                if pref.preference in ["love", "like"]
            ]
            if liked_foods:
                context += f"Favorite Foods: {', '.join(liked_foods)}\n"

        return context

    def _build_recommendation_query(self, query: str, user: Optional[User]) -> str:
        """Build recommendation query with context"""
        if user:
            return f"""
Based on my dietary preferences and restrictions, {query}

Please provide:
1. Restaurant recommendations that match my dietary requirements
2. Specific dish suggestions from each restaurant
3. Why each recommendation suits my preferences
4. Any important notes about dietary restrictions
"""
        else:
            return query

    def _parse_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """Parse recommendations from agent response"""
        # This is a simple parser - can be enhanced with structured output
        recommendations = []

        # Extract restaurant names and details from response
        # For now, return a structured placeholder
        # In production, you might want to use structured output from the agent

        return recommendations

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.agent and self.client:
                # Delete agent
                self.client.agents.delete_agent(self.agent.id)
                logger.info("Agent deleted")

            if self.vector_store_id and self.client:
                # Delete vector store
                self.client.agents.delete_vector_store(self.vector_store_id)
                logger.info("Vector store deleted")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global agent instance
restaurant_agent = RestaurantAgent()
