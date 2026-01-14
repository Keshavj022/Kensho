"""
Tests for Kensho Restaurant Agent
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.agents.restaurant_agent import RestaurantAgent
from backend.models import User, UserProfile, DietaryInfo, UserPreferences, DietaryType


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        profile=UserProfile(
            name="Test User",
            age=25,
            location="New York"
        ),
        dietary=DietaryInfo(
            type=DietaryType.VEGETARIAN,
            restrictions=[],
            goals=["healthy"]
        ),
        preferences=UserPreferences(
            foods={},
            cuisines={}
        )
    )


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization"""
    agent = RestaurantAgent()
    assert agent.client is None
    assert agent.agent is None
    assert agent.vector_store_id is None


@pytest.mark.asyncio
async def test_build_user_context(sample_user):
    """Test user context building"""
    agent = RestaurantAgent()
    context = agent._build_user_context(sample_user)

    assert "Test User" in context
    assert "New York" in context
    assert "vegetarian" in context.lower()


@pytest.mark.asyncio
async def test_build_recommendation_query(sample_user):
    """Test recommendation query building"""
    agent = RestaurantAgent()
    query = agent._build_recommendation_query("pizza places", sample_user)

    assert "pizza places" in query
    assert "dietary preferences" in query.lower()


def test_parse_recommendations():
    """Test recommendation parsing"""
    agent = RestaurantAgent()
    response = "I recommend Restaurant A and Restaurant B"
    recommendations = agent._parse_recommendations(response)

    assert isinstance(recommendations, list)
