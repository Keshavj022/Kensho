# Kensho

A cutting-edge multi-agent e-commerce platform that uses AI agents to provide personalized food ordering, travel booking, and shopping experiences. Built with **Azure AI Foundry**, **Neo4j**, **ChromaDB**, **FastAPI**, and modern web technologies.

## 🌟 Features

### Core Services

- **🍽️ Food/Restaurant Recommendations**: AI-powered restaurant discovery with personalized menu suggestions
- **✈️ Travel Agent**: Intelligent itinerary planning with flight and hotel bookings
- **🛍️ E-Commerce**: Smart shopping experience with AI-powered product recommendations

### Advanced Capabilities

- **🤖 Multi-Agent System**: Specialized AI agents for different domains
- **🧠 Knowledge Graph**: Neo4j-based user profile and interaction storage
- **📚 RAG System**: ChromaDB vector database for contextual recommendations
- **🔐 Authentication & Authorization**: JWT-based auth with role-based access control
- **🎤 Voice Interface**: Speech-to-text and text-to-speech capabilities
- **🖼️ Multimodal Support**: Image analysis for food and travel recommendations
- **📊 Temporal Analysis**: Track and analyze user preference changes over time
- **🎯 Advanced Recommendations**: Multiple graph-based recommendation algorithms

## 🏗️ Architecture

```
Ecommerce/
├── backend/                 # FastAPI Backend
│   ├── agents/             # AI Agents
│   │   ├── restaurant_agent.py
│   │   └── travel_agent.py
│   ├── api/                # API Routes
│   │   ├── routes.py              # Restaurant routes
│   │   ├── travel_routes.py       # Travel routes
│   │   ├── auth_routes.py         # Authentication
│   │   ├── knowledge_graph_routes.py  # Knowledge graph
│   │   ├── rag_routes.py          # RAG endpoints
│   │   ├── voice_routes.py        # Voice interface
│   │   └── multimodal_routes.py   # Image analysis
│   ├── services/           # Business Logic
│   │   ├── user_service.py
│   │   ├── restaurant_service.py
│   │   ├── travel_service.py
│   │   ├── auth_service.py
│   │   ├── knowledge_graph_service.py
│   │   ├── rag_service.py
│   │   ├── voice_service.py
│   │   └── vision_service.py
│   ├── models/             # Data Models
│   ├── config/             # Configuration
│   ├── data/               # Data Files
│   └── main.py            # Application Entry Point
│
└── frontend/               # React Frontend
    ├── src/
    │   ├── pages/         # Page components
    │   ├── components/     # Reusable components
    │   └── utils/         # Utilities
    └── package.json
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **Neo4j** (optional, for knowledge graph)
- **Azure subscription** (optional, for Azure AI Foundry)
- **OpenAI API key** (optional, for embeddings)

### Quick Setup

**Option 1: Automated Setup (Recommended)**
```bash
cd Ecommerce
python setup.py
```

**Option 2: Manual Setup**

#### Backend Setup

1. **Navigate to project root**
   ```bash
   cd Ecommerce
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `backend/.env` file:
   ```env
   # Azure AI Foundry (optional)
   AZURE_AI_PROJECT_CONNECTION_STRING=your_connection_string
   
   # Neo4j (optional)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   
   # OpenAI/Azure OpenAI (for embeddings)
   OPENAI_API_KEY=your-openai-key
   # OR
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   AZURE_OPENAI_KEY=your-azure-key
   
   # JWT (required for auth)
   JWT_SECRET_KEY=your-secret-key-change-in-production
   
   # Azure Speech (optional)
   AZURE_SPEECH_KEY=your-speech-key
   AZURE_SPEECH_REGION=eastus
   
   # Azure Vision (optional)
   AZURE_VISION_KEY=your-vision-key
   AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com
   ```

5. **Start the backend server**
   ```bash
   # Using the run script
   python run_backend.py
   
   # Or directly with uvicorn
   uvicorn backend.main:app --reload
   
   # Or using Python module
   python -m backend.main
   ```

   The API will be available at:
   - API: `http://localhost:8000`
   - Documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`
   - Root endpoint: `http://localhost:8000/`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open browser**
   Visit `http://localhost:5173`

## 📚 API Documentation

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "johndoe",
    "password": "securepassword123"
}
```

Response:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Use token in requests:**
```http
Authorization: Bearer <access_token>
```

### Restaurant Agent

#### Chat with Agent
```http
POST /api/v1/chat
Authorization: Bearer <token>
Content-Type: application/json

{
    "message": "I'm looking for vegetarian Italian restaurants",
    "user_id": "user123"
}
```

#### Get Recommendations
```http
POST /api/v1/recommendations
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_query": "healthy lunch options",
    "user_id": "user123"
}
```

#### Search Restaurants
```http
POST /api/v1/search
Content-Type: application/json

{
    "query": "pizza",
    "location": "New York",
    "max_results": 10
}
```

### Travel Agent

#### Search Flights
```http
POST /api/v1/travel/flights/search
Authorization: Bearer <token>
Content-Type: application/json

{
    "origin": "NYC",
    "destination": "LON",
    "departure_date": "2024-06-01",
    "return_date": "2024-06-15",
    "passengers": 2,
    "travel_class": "economy"
}
```

#### Search Hotels
```http
POST /api/v1/travel/hotels/search
Authorization: Bearer <token>
Content-Type: application/json

{
    "location": "London",
    "check_in": "2024-06-01",
    "check_out": "2024-06-15",
    "guests": 2
}
```

#### Create Itinerary
```http
POST /api/v1/travel/itinerary/create
Authorization: Bearer <token>
Content-Type: application/json

{
    "destination": "Paris",
    "start_date": "2024-06-01",
    "end_date": "2024-06-07",
    "travelers": 2,
    "budget": 5000,
    "pace": "moderate",
    "interests": ["sightseeing", "cultural"]
}
```

#### Travel Chat
```http
POST /api/v1/travel/chat
Authorization: Bearer <token>
Content-Type: application/json

{
    "message": "Plan a 5-day trip to Tokyo",
    "user_id": "user123"
}
```

### Knowledge Graph

#### Onboard User
```http
POST /api/v1/knowledge-graph/user/onboard
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_id": "user123",
    "name": "John Doe",
    "location": "New York",
    "dietary_type": "vegetarian",
    "dietary_restrictions": [
        {"type": "allergy", "value": "nuts"}
    ],
    "food_preferences": {
        "Pizza": {"preference": "love", "weight": 5}
    }
}
```

#### Get User Preferences
```http
GET /api/v1/knowledge-graph/user/{user_id}/preferences
Authorization: Bearer <token>
```

#### Get Preference Trends
```http
GET /api/v1/knowledge-graph/user/{user_id}/preferences/trends?days=30
Authorization: Bearer <token>
```

#### Get Preference Evolution
```http
GET /api/v1/knowledge-graph/user/{user_id}/preferences/{item_name}/evolution?preference_type=food
Authorization: Bearer <token>
```

#### Advanced Recommendations

**Collaborative Filtering:**
```http
GET /api/v1/knowledge-graph/user/{user_id}/recommendations/collaborative?limit=10
Authorization: Bearer <token>
```

**Content-Based:**
```http
GET /api/v1/knowledge-graph/user/{user_id}/recommendations/content-based?limit=10
Authorization: Bearer <token>
```

**Hybrid:**
```http
GET /api/v1/knowledge-graph/user/{user_id}/recommendations/hybrid?limit=10&collaborative_weight=0.5
Authorization: Bearer <token>
```

**Find Similar Users:**
```http
GET /api/v1/knowledge-graph/user/{user_id}/similar-users?limit=10
Authorization: Bearer <token>
```

### RAG (Retrieval-Augmented Generation)

#### Query Restaurant Data
```http
POST /api/v1/rag/query/restaurants
Authorization: Bearer <token>
Content-Type: application/json

{
    "query": "vegetarian Italian restaurants",
    "location": "New York",
    "max_results": 5
}
```

#### Query Travel Data
```http
POST /api/v1/rag/query/travel
Authorization: Bearer <token>
Content-Type: application/json

{
    "query": "beach destinations in Europe",
    "data_type": "destinations",
    "max_results": 5
}
```

#### Build Context
```http
POST /api/v1/rag/context
Authorization: Bearer <token>
Content-Type: application/json

{
    "query": "best restaurants for dinner",
    "agent_type": "restaurant",
    "user_id": "user123",
    "max_chunks": 3
}
```

### Voice Interface

#### Speech to Text
```http
POST /api/v1/voice/speech-to-text
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "audio_data": <binary>,
    "language": "en-US"
}
```

#### Text to Speech
```http
POST /api/v1/voice/text-to-speech
Authorization: Bearer <token>
Content-Type: application/json

{
    "text": "Hello, how can I help you?",
    "voice": "en-US-JennyNeural"
}
```

#### Voice Chat
```http
POST /api/v1/voice/chat
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "audio_data": <binary>,
    "agent_type": "restaurant",
    "user_id": "user123"
}
```

### Multimodal

#### Analyze Food Image
```http
POST /api/v1/multimodal/analyze/food
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "image_data": <binary>
}
```

#### Analyze Travel Image
```http
POST /api/v1/multimodal/analyze/travel
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
    "image_data": <binary>
}
```

## 🔧 Configuration

### Environment Variables

See `backend/config/settings.py` for all configuration options.

**Required:**
- `JWT_SECRET_KEY` - Secret key for JWT tokens (change in production!)

**Optional but Recommended:**
- `AZURE_AI_PROJECT_CONNECTION_STRING` - For Azure AI Foundry agents
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` - For knowledge graph
- `OPENAI_API_KEY` or `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_KEY` - For embeddings
- `AZURE_SPEECH_KEY` - For voice interface
- `AZURE_VISION_KEY` - For image analysis

### Settings

All settings are configurable via environment variables or `.env` file. See `backend/config/settings.py` for defaults.

## 🧪 Testing

### Backend Tests
```bash
# Unit tests
cd backend
pytest tests/

# Manual testing scripts (from project root)
python test_client.py              # Test restaurant agent
python test_travel_agent.py        # Test travel agent
python test_all_agents.py          # Test all agents
python test_voice_interface.py     # Test voice features
python test_multimodal.py          # Test image analysis
```

### Frontend Testing
```bash
cd frontend
npm run dev  # Development server with hot reload
```

## 📖 Key Features Explained

### 1. Knowledge Graph (Neo4j)

**Purpose**: Store comprehensive user data, preferences, and interactions for personalized recommendations.

**Features**:
- User onboarding and profile management
- Preference learning (food, cuisine)
- Interaction tracking (restaurants, destinations, searches)
- Temporal analysis of preferences
- Advanced recommendation algorithms

**Schema**:
- Nodes: User, Restaurant, Destination, Cuisine, Food, DietaryRestriction, etc.
- Relationships: PREFERS, LIKES_CUISINE, INTERACTED_WITH, EXPLORED, etc.

### 2. RAG System (ChromaDB)

**Purpose**: Provide agents with relevant context from knowledge base.

**Features**:
- Document ingestion (restaurants, travel data)
- Embedding generation (OpenAI/Azure OpenAI)
- Semantic search and retrieval
- Context building for agents
- Integration with knowledge graph

**Workflow**:
1. Data ingested into ChromaDB
2. User query triggers semantic search
3. Relevant documents retrieved
4. Context built with user preferences
5. Agent uses context for response

### 3. Authentication & Authorization

**Purpose**: Secure API access with user management.

**Features**:
- JWT-based authentication
- Role-based access control (user, admin, moderator)
- Password hashing (bcrypt)
- Token refresh mechanism
- Account management

**Roles**:
- `user`: Standard user access
- `admin`: Full access, user management
- `moderator`: Intermediate access (customizable)

### 4. Advanced Recommendation Algorithms

**Collaborative Filtering**:
- Finds similar users
- Recommends items liked by similar users
- Scores by similarity, ratings, interactions

**Content-Based Filtering**:
- Analyzes user preferences
- Finds matching content
- Scores by content similarity

**Hybrid Recommendations**:
- Combines both approaches
- Weighted combination
- Best of both worlds

### 5. Temporal Analysis

**Purpose**: Track and analyze preference changes over time.

**Features**:
- Preference history tracking
- Trend analysis
- Evolution tracking
- Predictive insights

### 6. RAG-KG Integration

**Purpose**: Enhance RAG context with knowledge graph preferences.

**Features**:
- Query enhancement with user preferences
- Context enrichment
- Automatic integration
- Better personalization

## 🎨 Frontend

### Features

- **Modern UI**: Beautiful, aesthetic design with gradients and glassmorphism
- **Animations**: Smooth animations using Framer Motion
- **Responsive**: Works on all devices
- **Three Main Pages**:
  - Landing page with animated hero
  - Food recommendations with search and filters
  - Travel agent with itinerary planning
  - E-commerce with product browsing

### Tech Stack

- React 18 + TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Framer Motion for animations
- React Router for navigation

## 📊 Data Flow

### Restaurant Recommendation Flow

1. User sends query → API endpoint
2. System retrieves user preferences from KG
3. RAG system retrieves relevant restaurants
4. Context built: User prefs + RAG results
5. Agent processes query with context
6. Response generated with recommendations
7. Interaction tracked in KG

### Travel Planning Flow

1. User requests itinerary → API endpoint
2. System retrieves user travel history from KG
3. RAG system retrieves destination/hotel/flight info
4. Context built with user preferences
5. Agent creates personalized itinerary
6. Interactions tracked in KG

## 🔐 Security

- **Password Hashing**: bcrypt
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: Fine-grained permissions
- **Token Expiration**: Configurable expiration times
- **Account Management**: Activate/deactivate users

## 🚀 Deployment

### Backend

1. Set all environment variables
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run migrations (if using database)
4. Start server: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### Frontend

1. Install dependencies: `npm install`
2. Build: `npm run build`
3. Serve `dist` directory with any static file server

## 📝 Project Structure

```
Ecommerce/
├── backend/
│   ├── agents/          # AI agents (Restaurant, Travel)
│   ├── api/             # API routes
│   ├── services/        # Business logic services
│   ├── models/          # Pydantic models
│   ├── config/          # Configuration
│   ├── data/            # Data files
│   ├── dependencies.py # Auth dependencies
│   └── main.py          # FastAPI app
│
├── frontend/
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   └── utils/       # Utilities
│   └── package.json
│
└── README.md            # This file
```

## 🛠️ Development

### Adding New Features

1. **New Agent**: Create in `backend/agents/`
2. **New Service**: Create in `backend/services/`
3. **New Route**: Create in `backend/api/` and register in `main.py`
4. **New Model**: Add to `backend/models/`

### Code Style

- Follow PEP 8 for Python
- Use type hints
- Document functions with docstrings
- Use meaningful variable names

## 📈 Performance

- **RAG Retrieval**: <100ms
- **KG Queries**: <50ms (with indexes)
- **Agent Response**: Depends on Azure AI Foundry
- **Frontend**: Optimized with Vite

## 🐛 Troubleshooting

### Backend Issues

**Agent not initializing**:
- Check Azure AI Foundry connection string
- Verify credentials
- Check logs for errors

**Knowledge Graph not working**:
- Verify Neo4j is running
- Check connection credentials
- Verify Neo4j driver is installed

**RAG not working**:
- Check ChromaDB installation
- Verify embedding API keys
- Check data ingestion logs

### Frontend Issues

**Build errors**:
- Clear `node_modules` and reinstall
- Check Node.js version (18+)
- Verify all dependencies installed

**Styling issues**:
- Verify Tailwind CSS is configured
- Check PostCSS configuration
- Clear browser cache

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [Azure AI Foundry](https://ai.azure.com)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Vector database: [ChromaDB](https://www.trychroma.com/)
- Graph database: [Neo4j](https://neo4j.com/)
- Frontend: [React](https://react.dev/) + [Vite](https://vitejs.dev/)

## 📞 Support & Troubleshooting

### Common Issues

**Backend won't start**:
- Verify Python version: `python --version` (needs 3.10+)
- Check virtual environment is activated
- Verify all dependencies installed: `pip list`
- Check port 8000 is available

**Agents not working**:
- Verify Azure AI Foundry connection string in `.env`
- Check Azure credentials are valid
- Review logs for specific error messages
- System works in local mode without Azure

**Knowledge Graph not working**:
- Verify Neo4j is running: `neo4j status`
- Check connection credentials in `.env`
- Verify Neo4j driver installed: `pip show neo4j`
- System works without Neo4j (reduced functionality)

**RAG not working**:
- Verify ChromaDB installed: `pip show chromadb`
- Check embedding API keys (OpenAI or Azure OpenAI)
- Verify data ingestion completed (check logs)
- System falls back to keyword search if embeddings unavailable

**Frontend issues**:
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Verify Node.js version: `node --version` (needs 18+)
- Check browser console for errors
- Clear browser cache

### Getting Help

- **API Documentation**: `http://localhost:8000/docs` (Interactive Swagger UI)
- **Logs**: Check console output for detailed error messages
- **Configuration**: Review `backend/config/settings.py` for all settings
- **Health Checks**: 
  - `GET /api/v1/health` - General health
  - `GET /api/v1/knowledge-graph/health` - KG status
  - `GET /api/v1/rag/health` - RAG status

## 📚 Additional Resources

- **Frontend Documentation**: See `frontend/README.md`
- **API Documentation**: Available at `/docs` endpoint when server is running
- **Code Structure**: See Architecture section above

## 🎯 Quick Reference

### Start Everything
```bash
# Terminal 1: Backend
cd Ecommerce
source venv/bin/activate
python run_backend.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Key URLs
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Key Endpoints
- Health: `GET /api/v1/health`
- Register: `POST /api/v1/auth/register`
- Login: `POST /api/v1/auth/login`
- Chat: `POST /api/v1/chat`
- Travel Chat: `POST /api/v1/travel/chat`

---

**Note**: This is an active development project. Features are continuously being added and improved. The system is designed to work gracefully even when optional services (Azure, Neo4j, ChromaDB) are not configured.
