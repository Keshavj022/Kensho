"""
RAG (Retrieval-Augmented Generation) Service
Handles document ingestion, embedding generation, and retrieval for both agents
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not installed. RAG will use in-memory storage.")
    CHROMADB_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI SDK not installed. Will use Azure embeddings if available.")
    OPENAI_AVAILABLE = False

from ..config import settings

try:
    from .knowledge_graph_service import knowledge_graph_service
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False
    knowledge_graph_service = None


class RAGService:
    """RAG service for document retrieval and context building"""

    def __init__(self):
        """Initialize RAG service"""
        self.chroma_client = None
        self.embedding_client = None
        self.collections: Dict[str, Any] = {}
        self._initialize_chromadb()
        self._initialize_embeddings()

    def _initialize_chromadb(self):
        """Initialize ChromaDB client"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available. RAG features will be limited.")
            return

        try:
            chroma_path = Path(settings.CHROMADB_PATH)
            chroma_path.mkdir(parents=True, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB initialized at {chroma_path}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            self.chroma_client = None

    def _initialize_embeddings(self):
        """Initialize embedding client - Uses Azure OpenAI as primary"""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT_URL")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        if azure_endpoint and azure_key:
            try:
                from openai import AzureOpenAI
                self.embedding_client = AzureOpenAI(
                    api_key=azure_key,
                    api_version=azure_api_version,
                    azure_endpoint=azure_endpoint
                )
                logger.info("Azure OpenAI embedding client initialized")
                return
            except Exception as e:
                logger.warning(f"Could not initialize Azure OpenAI client: {str(e)}")

        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.embedding_client = OpenAI(api_key=api_key)
                    logger.warning("Using OpenAI as fallback. Consider configuring Azure OpenAI for production.")
                    logger.info("OpenAI embedding client initialized")
                    return
                except Exception as e:
                    logger.warning(f"Could not initialize OpenAI client: {str(e)}")

        logger.warning("No embedding client available. RAG will use keyword matching.")

    def _get_collection(self, collection_name: str, create: bool = True):
        """Get or create a ChromaDB collection"""
        if not self.chroma_client:
            return None

        try:
            if collection_name not in self.collections:
                if create:
                    self.collections[collection_name] = self.chroma_client.get_or_create_collection(
                        name=collection_name,
                        metadata={"description": f"RAG collection for {collection_name}"}
                    )
                    logger.info(f"Collection '{collection_name}' ready")
                else:
                    self.collections[collection_name] = self.chroma_client.get_collection(collection_name)
            return self.collections[collection_name]
        except Exception as e:
            logger.error(f"Error getting collection {collection_name}: {str(e)}")
            return None

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Azure OpenAI"""
        if not self.embedding_client:
            return None

        try:
            deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME or settings.EMBEDDING_MODEL
            
            response = self.embedding_client.embeddings.create(
                model=deployment_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    def _chunk_document(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split document into chunks"""
        words = content.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks

    def _create_document_id(self, source: str, index: int) -> str:
        """Create a unique document ID"""
        content = f"{source}_{index}"
        return hashlib.md5(content.encode()).hexdigest()

    def ingest_restaurant_data(self, data_path: Optional[str] = None) -> bool:
        """Ingest restaurant data into RAG system"""
        try:
            if not self.chroma_client:
                logger.warning("ChromaDB not available. Cannot ingest restaurant data.")
                return False

            collection = self._get_collection("restaurants")
            if not collection:
                return False

            if not data_path:
                data_path = settings.RESTAURANT_DATA_PATH

            if not os.path.exists(data_path):
                logger.warning(f"Restaurant data file not found: {data_path}")
                return False

            with open(data_path, "r") as f:
                data = json.load(f)

            if "local_results" in data:
                restaurants = data.get("local_results", [])
            elif "restaurants" in data:
                restaurants = data.get("restaurants", [])
            else:
                restaurants = []
            
            logger.info(f"Ingesting {len(restaurants)} restaurants into RAG system...")

            documents = []
            embeddings = []
            ids = []
            metadatas = []

            for idx, restaurant in enumerate(restaurants):
                doc_parts = []
                
                if "title" in restaurant:
                    doc_parts.append(f"Restaurant: {restaurant.get('title', 'Unknown')}")
                    doc_parts.append(f"Type: {restaurant.get('type', 'Unknown')}")
                    if restaurant.get('types'):
                        doc_parts.append(f"Categories: {', '.join(restaurant['types'])}")
                    doc_parts.append(f"Address: {restaurant.get('address', 'Unknown')}")
                    if restaurant.get('rating'):
                        doc_parts.append(f"Rating: {restaurant['rating']} ({restaurant.get('reviews', 0)} reviews)")
                    if restaurant.get('price'):
                        doc_parts.append(f"Price: {restaurant['price']}")
                    if restaurant.get('extensions'):
                        for ext in restaurant['extensions']:
                            if 'service_options' in ext:
                                doc_parts.append(f"Services: {', '.join(ext['service_options'])}")
                            if 'offerings' in ext:
                                doc_parts.append(f"Offerings: {', '.join(ext['offerings'])}")
                    if restaurant.get('operating_hours'):
                        hours = restaurant['operating_hours']
                        hours_str = ", ".join([f"{k}: {v}" for k, v in hours.items()])
                        doc_parts.append(f"Hours: {hours_str}")
                else:
                    doc_parts.append(f"Restaurant: {restaurant.get('name', 'Unknown')}")
                    doc_parts.append(f"Cuisine: {restaurant.get('cuisine', 'Unknown')}")
                    doc_parts.append(f"Location: {restaurant.get('location', 'Unknown')}")
                    if restaurant.get('description'):
                        doc_parts.append(f"Description: {restaurant['description']}")
                    if restaurant.get('dietary_options'):
                        doc_parts.append(f"Dietary Options: {', '.join(restaurant['dietary_options'])}")
                    if restaurant.get('popular_dishes'):
                        doc_parts.append(f"Popular Dishes: {', '.join(restaurant['popular_dishes'])}")
                    if restaurant.get('price_range'):
                        doc_parts.append(f"Price Range: {restaurant['price_range']}")
                    if restaurant.get('rating'):
                        doc_parts.append(f"Rating: {restaurant['rating']}")

                doc_text = " | ".join(doc_parts)

                embedding = self._generate_embedding(doc_text)
                if not embedding:
                    continue

                restaurant_name = restaurant.get('name') or restaurant.get('title', 'unknown')
                doc_id = self._create_document_id(f"restaurant_{restaurant_name}", idx)

                documents.append(doc_text)
                embeddings.append(embedding)
                ids.append(doc_id)
                
                if "title" in restaurant:
                    metadatas.append({
                        "name": restaurant.get("title", ""),
                        "type": restaurant.get("type", ""),
                        "address": restaurant.get("address", ""),
                        "rating": restaurant.get("rating", 0),
                        "price": restaurant.get("price", ""),
                        "source": "restaurant_data.json"
                    })
                else:
                    metadatas.append({
                        "name": restaurant.get("name", ""),
                        "cuisine": restaurant.get("cuisine", ""),
                        "location": restaurant.get("location", ""),
                        "rating": restaurant.get("rating", 0),
                        "price_range": restaurant.get("price_range", ""),
                        "source": "restaurant_data.json"
                    })

            if documents:
                collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    ids=ids,
                    metadatas=metadatas
                )
                logger.info(f"Successfully ingested {len(documents)} restaurant documents")
                return True

            return False

        except Exception as e:
            logger.error(f"Error ingesting restaurant data: {str(e)}")
            return False

    def ingest_travel_data(self, data_dir: Optional[str] = None) -> bool:
        """Ingest travel data (destinations, hotels, flights) into RAG system"""
        try:
            if not self.chroma_client:
                logger.warning("ChromaDB not available. Cannot ingest travel data.")
                return False

            collection = self._get_collection("travel")
            if not collection:
                return False

            if not data_dir:
                data_dir = settings.DATA_DIR

            data_files = {
                "destinations": "destinations_data.json",
                "hotels": "hotels_data.json",
                "flights": "flights_data.json"
            }

            all_documents = []
            all_embeddings = []
            all_ids = []
            all_metadatas = []

            for data_type, filename in data_files.items():
                file_path = os.path.join(data_dir, filename)
                if not os.path.exists(file_path):
                    logger.warning(f"Travel data file not found: {file_path}")
                    continue

                with open(file_path, "r") as f:
                    data = json.load(f)

                items = data.get(data_type, []) if isinstance(data, dict) else data
                logger.info(f"Ingesting {len(items)} {data_type} into RAG system...")

                for idx, item in enumerate(items):
                    if data_type == "destinations":
                        doc_parts = [
                            f"Destination: {item.get('name', 'Unknown')}",
                            f"Country: {item.get('country', 'Unknown')}",
                            f"Description: {item.get('description', '')}",
                        ]
                        if item.get('best_time_to_visit'):
                            doc_parts.append(f"Best Time to Visit: {item['best_time_to_visit']}")
                        if item.get('attractions'):
                            doc_parts.append(f"Attractions: {', '.join(item['attractions'])}")
                        if item.get('activities'):
                            doc_parts.append(f"Activities: {', '.join(item['activities'])}")

                    elif data_type == "hotels":
                        doc_parts = [
                            f"Hotel: {item.get('name', 'Unknown')}",
                            f"Location: {item.get('location', 'Unknown')}",
                            f"Description: {item.get('description', '')}",
                        ]
                        if item.get('amenities'):
                            doc_parts.append(f"Amenities: {', '.join(item['amenities'])}")
                        if item.get('rating'):
                            doc_parts.append(f"Rating: {item['rating']}")
                        if item.get('price_per_night'):
                            doc_parts.append(f"Price per Night: ${item['price_per_night']}")

                    elif data_type == "flights":
                        doc_parts = [
                            f"Flight: {item.get('airline', 'Unknown')}",
                            f"Route: {item.get('origin', '')} to {item.get('destination', '')}",
                            f"Duration: {item.get('duration', '')}",
                        ]
                        if item.get('price'):
                            doc_parts.append(f"Price: ${item['price']}")
                        if item.get('stops'):
                            doc_parts.append(f"Stops: {item['stops']}")

                    doc_text = " | ".join(doc_parts)

                    embedding = self._generate_embedding(doc_text)
                    if not embedding:
                        continue

                    doc_id = self._create_document_id(f"{data_type}_{item.get('name', item.get('id', 'unknown'))}", idx)

                    all_documents.append(doc_text)
                    all_embeddings.append(embedding)
                    all_ids.append(doc_id)
                    all_metadatas.append({
                        "type": data_type,
                        "name": item.get("name", item.get("id", "")),
                        "source": filename
                    })

            if all_documents:
                collection.add(
                    documents=all_documents,
                    embeddings=all_embeddings,
                    ids=all_ids,
                    metadatas=all_metadatas
                )
                logger.info(f"Successfully ingested {len(all_documents)} travel documents")
                return True

            return False

        except Exception as e:
            logger.error(f"Error ingesting travel data: {str(e)}")
            return False

    def retrieve_restaurants(
        self,
        query: str,
        location: Optional[str] = None,
        cuisine: Optional[str] = None,
        max_results: int = 5,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant restaurants using RAG"""
        try:
            collection = self._get_collection("restaurants", create=False)
            if not collection:
                logger.warning("Restaurant collection not found. Run ingestion first.")
                return []

            enhanced_query = query
            if KG_AVAILABLE and knowledge_graph_service and knowledge_graph_service.driver and user_id:
                try:
                    preferences = knowledge_graph_service.get_user_preferences(user_id)
                    if preferences:
                        cuisine_prefs = preferences.get("cuisine_preferences", [])
                        favorites = [c["cuisine"] for c in cuisine_prefs if c.get("level") in ["love", "like"]]
                        if favorites:
                            enhanced_query = f"{query} {' '.join(favorites[:3])}"
                except Exception as e:
                    logger.warning(f"Error enhancing query with KG: {str(e)}")

            query_embedding = self._generate_embedding(enhanced_query)
            if not query_embedding:
                results = collection.query(
                    query_texts=[enhanced_query],
                    n_results=max_results
                )
            else:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_results
                )

            retrieved = []
            if results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0

                    retrieved.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0 - distance,  # Convert distance to similarity
                        "source": metadata.get("source", "restaurant_data.json")
                    })

            if location or cuisine:
                filtered = []
                for item in retrieved:
                    meta = item["metadata"]
                    if location and location.lower() not in meta.get("location", "").lower():
                        continue
                    if cuisine and cuisine.lower() not in meta.get("cuisine", "").lower():
                        continue
                    filtered.append(item)
                return filtered[:max_results]

            return retrieved

        except Exception as e:
            logger.error(f"Error retrieving restaurants: {str(e)}")
            return []

    def retrieve_travel_info(
        self,
        query: str,
        data_type: Optional[str] = None,  # "destinations", "hotels", "flights"
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant travel information using RAG"""
        try:
            collection = self._get_collection("travel", create=False)
            if not collection:
                logger.warning("Travel collection not found. Run ingestion first.")
                return []

            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                results = collection.query(
                    query_texts=[query],
                    n_results=max_results
                )
            else:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_results
                )

            retrieved = []
            if results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0

                    if data_type and metadata.get("type") != data_type:
                        continue

                    retrieved.append({
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0 - distance,
                        "source": metadata.get("source", "travel_data.json")
                    })

            return retrieved[:max_results]

        except Exception as e:
            logger.error(f"Error retrieving travel info: {str(e)}")
            return []

    def build_context(
        self,
        query: str,
        agent_type: str,
        user_context: Optional[str] = None,
        max_chunks: int = 3,
        user_id: Optional[str] = None
    ) -> str:
        """Build context string for agent using RAG with KG enhancement"""
        try:
            if agent_type == "restaurant":
                retrieved = self.retrieve_restaurants(query, max_results=max_chunks)
            elif agent_type == "travel":
                retrieved = self.retrieve_travel_info(query, max_results=max_chunks)
            else:
                logger.warning(f"Unknown agent type: {agent_type}")
                return ""

            kg_context = ""
            if KG_AVAILABLE and knowledge_graph_service and knowledge_graph_service.driver and user_id:
                try:
                    preferences = knowledge_graph_service.get_user_preferences(user_id)
                    
                    if preferences:
                        kg_parts = []
                        
                        cuisine_prefs = preferences.get("cuisine_preferences", [])
                        if cuisine_prefs:
                            favorites = [c["cuisine"] for c in cuisine_prefs if c.get("level") in ["love", "like"]]
                            if favorites:
                                kg_parts.append(f"User's Favorite Cuisines: {', '.join(favorites[:5])}")
                        
                        food_prefs = preferences.get("food_preferences", [])
                        if food_prefs:
                            favorites = [f["food"] for f in food_prefs if f.get("level") in ["love", "like"]]
                            if favorites:
                                kg_parts.append(f"User's Favorite Foods: {', '.join(favorites[:5])}")
                        
                        restrictions = preferences.get("dietary_restrictions", [])
                        if restrictions:
                            rest_list = [r.get("name", "") for r in restrictions]
                            if rest_list:
                                kg_parts.append(f"Dietary Restrictions: {', '.join(rest_list)}")
                        
                        if kg_parts:
                            kg_context = "\n".join(kg_parts)
                            
                except Exception as e:
                    logger.warning(f"Error getting KG preferences: {str(e)}")

            if not retrieved and not kg_context:
                return user_context or ""

            context_parts = []
            
            if user_context:
                context_parts.append(f"User Context:\n{user_context}\n")
            
            if kg_context:
                context_parts.append(f"User Preferences (from Knowledge Graph):\n{kg_context}\n")

            if retrieved:
                context_parts.append("Relevant Information from Knowledge Base:")
                for i, item in enumerate(retrieved, 1):
                    context_parts.append(f"\n{i}. {item['content']}")
                    if item.get('metadata'):
                        meta = item['metadata']
                        if meta.get('rating'):
                            context_parts.append(f"   Rating: {meta['rating']}")
                        if meta.get('price_range') or meta.get('price'):
                            price = meta.get('price_range') or meta.get('price', '')
                            context_parts.append(f"   Price: {price}")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return user_context or ""

    def reset_collection(self, collection_name: str) -> bool:
        """Reset a collection (delete all documents)"""
        try:
            if not self.chroma_client:
                return False

            if collection_name in self.collections:
                del self.collections[collection_name]

            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' reset")
            return True

        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection"""
        try:
            collection = self._get_collection(collection_name, create=False)
            if not collection:
                return {"error": "Collection not found"}

            count = collection.count()
            return {
                "collection_name": collection_name,
                "document_count": count,
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}


rag_service = RAGService()
