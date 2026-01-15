"""
Travel Agent using Azure AI Foundry for itinerary planning
"""
import json
import os
from typing import Optional, List, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from loguru import logger

from ..config import settings
from ..models import User, ItineraryRequest, TravelItinerary
from ..services import travel_service, itinerary_service, knowledge_graph_service, rag_service


class TravelAgent:
    """
    Travel planning agent using Azure AI Foundry
    Handles flight booking, hotel reservations, and itinerary planning
    """

    def __init__(self):
        """Initialize the travel agent"""
        self.client: Optional[AIProjectClient] = None
        self.agent: Optional[Any] = None
        self.vector_store_id: Optional[str] = None
        self.active_threads: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the Azure AI travel agent"""
        try:
            logger.info("Initializing Travel Agent...")

            # Initialize Azure AI Project Client
            if settings.AZURE_AI_PROJECT_CONNECTION_STRING:
                self.client = AIProjectClient.from_connection_string(
                    credential=DefaultAzureCredential(),
                    conn_str=settings.AZURE_AI_PROJECT_CONNECTION_STRING,
                )

                # Create the agent
                await self._create_agent()

                # Set up vector store for travel data
                await self._setup_vector_store()

                logger.info(f"Travel Agent initialized successfully: {self.agent.id}")
            else:
                logger.warning(
                    "AZURE_AI_PROJECT_CONNECTION_STRING not set. "
                    "Travel Agent will run in local mode."
                )

        except Exception as e:
            logger.error(f"Error initializing Travel Agent: {str(e)}")
            raise

    async def _create_agent(self):
        """Create the travel agent"""
        try:
            instructions = """You are an expert travel planning agent. Your role is to:

1. Help users plan complete travel itineraries
2. Search and recommend flights based on preferences and budget
3. Find suitable hotels and accommodations
4. Suggest activities and attractions at destinations
5. Create day-by-day itineraries optimized for the user's pace preference
6. Provide travel tips and best time to visit information
7. Consider user's budget and preferences when planning

Always provide detailed, practical travel advice. When creating itineraries:
- Balance activities with rest time
- Consider travel time between locations
- Suggest meal times and restaurant types
- Include must-see attractions and hidden gems
- Provide estimated costs for transparency
- Consider the user's travel style (relaxed, moderate, packed)

Be friendly, enthusiastic about travel, and provide realistic, achievable plans."""

            self.agent = self.client.agents.create_agent(
                model=settings.DEFAULT_MODEL,
                name="TravelPlanningAgent",
                instructions=instructions,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_stores": []
                    }
                },
            )
            logger.info(f"Travel Agent created: {self.agent.id}")

        except Exception as e:
            logger.error(f"Error creating travel agent: {str(e)}")
            raise

    async def _setup_vector_store(self):
        """Set up vector store with travel data"""
        try:
            # Create vector store
            vector_store = self.client.agents.create_vector_store(
                name="travel_knowledge_base",
                file_ids=[],
            )
            self.vector_store_id = vector_store.id
            logger.info(f"Travel vector store created: {self.vector_store_id}")

            # Upload travel data files
            data_files = [
                "flights_data.json",
                "hotels_data.json",
                "destinations_data.json",
            ]

            for filename in data_files:
                file_path = os.path.join(settings.DATA_DIR, filename)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_upload = self.client.agents.upload_file(
                            file=f,
                            purpose="assistants",  # Use string instead of FilePurpose enum
                        )

                    self.client.agents.create_vector_store_file(
                        vector_store_id=self.vector_store_id,
                        file_id=file_upload.id,
                    )
                    logger.info(f"Uploaded {filename} to vector store")

            # Update agent with vector store
            self.agent = self.client.agents.update_agent(
                assistant_id=self.agent.id,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                },
            )
            logger.info("Travel Agent updated with vector store")

        except Exception as e:
            logger.error(f"Error setting up vector store: {str(e)}")
            raise

    async def create_thread(self, user: Optional[User] = None) -> str:
        """Create a new conversation thread"""
        try:
            messages = []
            if user:
                user_context = f"""User Profile:
Name: {user.profile.name}
Location: {user.profile.location}

This user is looking for travel recommendations and planning assistance."""
                messages.append({
                    "role": "user",
                    "content": user_context,
                })

            thread = self.client.agents.create_thread(messages=messages)
            self.active_threads[thread.id] = thread
            logger.info(f"Travel thread created: {thread.id}")
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
        """Send a message to the travel agent"""
        try:
            # Track search query in knowledge graph
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_search_query(
                    user_id=user_id,
                    query=message,
                    agent_type="travel",
                    results_count=0
                )

            # Build RAG context if available (with KG integration)
            enhanced_message = message
            if rag_service.chroma_client:
                try:
                    user_context = f"User Location: {user.profile.location}" if user else ""
                    rag_context = rag_service.build_context(
                        query=message,
                        agent_type="travel",
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
                raise Exception(f"Travel agent run failed: {run.last_error}")

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

    async def plan_itinerary(
        self,
        request: ItineraryRequest,
        user: Optional[User] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plan a complete travel itinerary"""
        try:
            # Create itinerary using local service first
            itinerary = itinerary_service.create_itinerary(request)

            # Track destination interaction in knowledge graph
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_destination_interaction(
                    user_id=user_id,
                    destination_id=request.destination.lower().replace(" ", "_"),
                    destination_name=request.destination,
                    country=request.destination,  # Could be enhanced to extract country
                    interaction_type="searched",
                    context={
                        "start_date": request.start_date,
                        "end_date": request.end_date,
                        "travelers": request.travelers,
                        "budget": request.budget,
                        "pace": request.pace
                    }
                )

            # If agent is available, enhance with AI recommendations
            if self.agent:
                thread_id = await self.create_thread(user)

                # Build detailed query
                query = f"""Please help me plan a detailed trip to {request.destination}.

Trip Details:
- Dates: {request.start_date} to {request.end_date}
- Travelers: {request.travelers}
- Budget: ${request.budget if request.budget else 'Flexible'}
- Pace: {request.pace}
- Interests: {', '.join([i.value for i in request.interests]) if request.interests else 'General sightseeing'}

Please provide:
1. Best activities and attractions for each day
2. Restaurant recommendations
3. Local tips and transportation advice
4. Any special considerations for this time of year
5. Budget optimization suggestions
"""

                # Get AI enhancement
                ai_response = await self.send_message(thread_id, query, user, user_id)

                return {
                    "itinerary": itinerary,
                    "ai_recommendations": ai_response,
                    "thread_id": thread_id,
                }
            else:
                # Return itinerary without AI enhancement
                return {
                    "itinerary": itinerary,
                    "ai_recommendations": None,
                    "thread_id": None,
                }

        except Exception as e:
            logger.error(f"Error planning itinerary: {str(e)}")
            raise

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        passengers: int = 1,
    ) -> List[Dict[str, Any]]:
        """Search for flights"""
        try:
            flights = travel_service.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                passengers=passengers,
            )

            # If agent available, get AI recommendations
            if self.agent and flights:
                thread_id = await self.create_thread()
                query = f"""I found these flights from {origin} to {destination}:
{json.dumps(flights[:3], indent=2)}

Which flight would you recommend and why? Consider price, duration, and airline quality."""

                recommendation = await self.send_message(thread_id, query)

                return {
                    "flights": flights,
                    "recommendation": recommendation,
                    "thread_id": thread_id,
                }

            return {"flights": flights}

        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            raise

    async def search_hotels(
        self,
        location: str,
        check_in: str,
        check_out: str,
        guests: int = 1,
    ) -> List[Dict[str, Any]]:
        """Search for hotels"""
        try:
            hotels = travel_service.search_hotels(
                location=location,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
            )

            # If agent available, get AI recommendations
            if self.agent and hotels:
                thread_id = await self.create_thread()
                query = f"""I found these hotels in {location}:
{json.dumps(hotels[:3], indent=2)}

Which hotel would you recommend and why? Consider value, location, and amenities."""

                recommendation = await self.send_message(thread_id, query)

                return {
                    "hotels": hotels,
                    "recommendation": recommendation,
                    "thread_id": thread_id,
                }

            return {"hotels": hotels}

        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.agent and self.client:
                self.client.agents.delete_agent(self.agent.id)
                logger.info("Travel Agent deleted")

            if self.vector_store_id and self.client:
                self.client.agents.delete_vector_store(self.vector_store_id)
                logger.info("Travel vector store deleted")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global travel agent instance
travel_agent = TravelAgent()
