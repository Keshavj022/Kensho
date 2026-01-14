"""
User service for managing user profiles and preferences
"""
import json
from typing import Optional, Dict, Any
from loguru import logger

from ..config import settings
from ..models import User, DietaryType, RestrictionType
from .knowledge_graph_service import knowledge_graph_service


class UserService:
    """Service for managing user data"""

    def __init__(self):
        """Initialize user service"""
        self.users_cache: Dict[str, User] = {}
        self._load_default_user()

    def _load_default_user(self):
        """Load default user from user_data.json"""
        try:
            user_data_path = settings.USER_DATA_PATH
            with open(user_data_path, "r") as f:
                data = json.load(f)
                user = User(**data["user"])
                self.users_cache["default"] = user
                logger.info(f"Loaded default user: {user.profile.name}")
        except FileNotFoundError:
            logger.warning(f"User data file not found: {settings.USER_DATA_PATH}")
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}")

    def get_user(self, user_id: str = "default") -> Optional[User]:
        """Get user by ID"""
        return self.users_cache.get(user_id)

    def create_user(self, user_id: str, user: User) -> User:
        """Create or update user"""
        self.users_cache[user_id] = user
        
        # Store in knowledge graph
        if knowledge_graph_service.driver:
            knowledge_graph_service.create_user(
                user_id=user_id,
                name=user.profile.name,
                age=user.profile.age,
                location=user.profile.location,
                dietary_type=user.dietary.type.value if user.dietary.type else None
            )
            
            # Add dietary restrictions
            for restriction in user.dietary.restrictions:
                knowledge_graph_service.add_dietary_restriction(
                    user_id=user_id,
                    restriction_type=restriction.type.value,
                    restriction_value=restriction.value
                )
            
            # Add dietary goals
            for goal in user.dietary.goals:
                knowledge_graph_service.add_dietary_goal(user_id, goal)
            
            # Add food preferences
            for food_name, pref in user.preferences.foods.items():
                knowledge_graph_service.add_food_preference(
                    user_id=user_id,
                    food_name=food_name,
                    preference_level=pref.preference,
                    weight=pref.weight
                )
            
            # Add cuisine preferences
            for cuisine_name, pref in user.preferences.cuisines.items():
                knowledge_graph_service.add_cuisine_preference(
                    user_id=user_id,
                    cuisine_name=cuisine_name,
                    preference_level=pref.preference,
                    weight=pref.weight
                )
        
        logger.info(f"User created/updated: {user_id}")
        return user

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """Update user data"""
        user = self.users_cache.get(user_id)
        if not user:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # Update knowledge graph
        if knowledge_graph_service.driver and user:
            knowledge_graph_service.create_user(
                user_id=user_id,
                name=user.profile.name,
                age=user.profile.age,
                location=user.profile.location,
                dietary_type=user.dietary.type.value if user.dietary.type else None
            )

        logger.info(f"User updated: {user_id}")
        return user
    
    def learn_preference(
        self,
        user_id: str,
        preference_type: str,  # 'food' or 'cuisine'
        item_name: str,
        preference_level: str,  # 'love', 'like', 'neutral', 'dislike', 'hate'
        weight: int = 3
    ) -> bool:
        """Learn and store user preference"""
        if not knowledge_graph_service.driver:
            return False
        
        if preference_type == 'food':
            return knowledge_graph_service.add_food_preference(
                user_id=user_id,
                food_name=item_name,
                preference_level=preference_level,
                weight=weight
            )
        elif preference_type == 'cuisine':
            return knowledge_graph_service.add_cuisine_preference(
                user_id=user_id,
                cuisine_name=item_name,
                preference_level=preference_level,
                weight=weight
            )
        return False
    
    def get_personalized_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get personalized preferences from knowledge graph"""
        if not knowledge_graph_service.driver:
            return {}
        
        return knowledge_graph_service.get_user_preferences(user_id)

    def get_user_context(self, user_id: str = "default") -> str:
        """Get formatted user context for agent"""
        user = self.get_user(user_id)
        if not user:
            return ""

        context = f"""
User Profile:
- Name: {user.profile.name}
- Location: {user.profile.location}
- Dietary Type: {user.dietary.type.value}
"""

        if user.dietary.restrictions:
            restrictions = [f"{r.type.value}: {r.value}" for r in user.dietary.restrictions]
            context += f"- Restrictions: {', '.join(restrictions)}\n"

        if user.dietary.goals:
            context += f"- Goals: {', '.join(user.dietary.goals)}\n"

        if user.preferences.foods:
            liked_foods = [
                food for food, pref in user.preferences.foods.items()
                if pref.preference in ["love", "like"]
            ]
            if liked_foods:
                context += f"- Favorite Foods: {', '.join(liked_foods[:5])}\n"

        return context


# Global user service instance
user_service = UserService()
