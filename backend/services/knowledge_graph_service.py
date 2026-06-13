"""
Knowledge Graph Service using Neo4j
Stores user preferences, interactions, and builds personalized recommendations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from ..config import settings

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    logger.warning("Neo4j driver not installed")
    NEO4J_AVAILABLE = False


class KnowledgeGraphService:
    """Service for managing user knowledge graph in Neo4j"""

    def __init__(self):
        """Initialize Neo4j connection"""
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD

        if NEO4J_AVAILABLE and self.password:
            self._connect()
            self._create_constraints()
        else:
            logger.warning("Neo4j not configured. Knowledge graph features disabled.")

    def _connect(self):
        """Connect to Neo4j"""
        try:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    notifications_min_severity="OFF",
                )
            except Exception:  # older driver without the kwarg
                self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self.driver = None

    def _create_constraints(self):
        """Create database constraints and indexes"""
        if not self.driver:
            return

        constraints = [
            "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.restaurant_id IS UNIQUE",
            "CREATE CONSTRAINT destination_id IF NOT EXISTS FOR (d:Destination) REQUIRE d.destination_id IS UNIQUE",
            "CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT food_name IF NOT EXISTS FOR (f:Food) REQUIRE f.name IS UNIQUE",
            "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
            "CREATE INDEX interaction_timestamp IF NOT EXISTS FOR (i:Interaction) ON (i.timestamp)",
        ]

        try:
            with self.driver.session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception:
                        pass  # Constraint might already exist
            logger.info("Neo4j constraints and indexes created")
        except Exception as e:
            logger.error(f"Error creating constraints: {str(e)}")


    def create_user(
        self,
        user_id: str,
        name: str,
        age: Optional[int] = None,
        location: Optional[str] = None,
        dietary_type: Optional[str] = None
    ) -> bool:
        """
        Create a new user node in the graph
        """
        if not self.driver:
            return False

        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.name = $name,
            u.age = $age,
            u.location = $location,
            u.dietary_type = $dietary_type,
            u.created_at = datetime(),
            u.updated_at = datetime()
        RETURN u
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    name=name,
                    age=age,
                    location=location,
                    dietary_type=dietary_type
                )
            logger.info(f"Created user node: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False

    def add_dietary_restriction(
        self,
        user_id: str,
        restriction_type: str,
        restriction_value: str
    ) -> bool:
        """Add dietary restriction for user"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (r:DietaryRestriction {name: $restriction_value, type: $restriction_type})
        MERGE (u)-[:HAS_RESTRICTION {severity: 'high'}]->(r)
        SET u.updated_at = datetime()
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    restriction_type=restriction_type,
                    restriction_value=restriction_value
                )
            logger.info(f"Added restriction {restriction_value} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding restriction: {str(e)}")
            return False

    def add_dietary_goal(self, user_id: str, goal: str) -> bool:
        """Add dietary goal for user"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (g:DietaryGoal {name: $goal})
        MERGE (u)-[:PURSUES_GOAL]->(g)
        SET u.updated_at = datetime()
        """

        try:
            with self.driver.session() as session:
                session.run(query, user_id=user_id, goal=goal)
            return True
        except Exception as e:
            logger.error(f"Error adding goal: {str(e)}")
            return False


    def add_food_preference(
        self,
        user_id: str,
        food_name: str,
        preference_level: str,  # love, like, neutral, dislike, hate
        weight: int = 3
    ) -> bool:
        """Add or update food preference with temporal tracking"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (f:Food {name: $food_name})
        MERGE (u)-[p:PREFERS]->(f)
        
        // Store previous preference for temporal analysis
        WITH u, f, p, p.level as old_level, p.weight as old_weight
        
        SET p.level = $preference_level,
            p.weight = $weight,
            p.updated_at = datetime(),
            p.created_at = COALESCE(p.created_at, datetime()),
            u.updated_at = datetime()
        
        // Create preference history node if preference changed
        WITH u, f, p, old_level, old_weight
        WHERE old_level IS NOT NULL AND old_level <> $preference_level
        CREATE (ph:PreferenceHistory {
            timestamp: datetime(),
            item: f.name,
            item_type: 'food',
            old_level: old_level,
            new_level: $preference_level,
            old_weight: old_weight,
            new_weight: $weight
        })
        CREATE (u)-[:HAS_HISTORY]->(ph)
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    food_name=food_name,
                    preference_level=preference_level,
                    weight=weight
                )
            return True
        except Exception as e:
            logger.error(f"Error adding food preference: {str(e)}")
            return False

    def add_cuisine_preference(
        self,
        user_id: str,
        cuisine_name: str,
        preference_level: str,
        weight: int = 3
    ) -> bool:
        """Add cuisine preference with temporal tracking"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (c:Cuisine {name: $cuisine_name})
        MERGE (u)-[p:LIKES_CUISINE]->(c)
        
        // Store previous preference for temporal analysis
        WITH u, c, p, p.level as old_level, p.weight as old_weight
        
        SET p.level = $preference_level,
            p.weight = $weight,
            p.updated_at = datetime(),
            p.created_at = COALESCE(p.created_at, datetime()),
            u.updated_at = datetime()
        
        // Create preference history node if preference changed
        WITH u, c, p, old_level, old_weight
        WHERE old_level IS NOT NULL AND old_level <> $preference_level
        CREATE (ph:PreferenceHistory {
            timestamp: datetime(),
            item: c.name,
            item_type: 'cuisine',
            old_level: old_level,
            new_level: $preference_level,
            old_weight: old_weight,
            new_weight: $weight
        })
        CREATE (u)-[:HAS_HISTORY]->(ph)
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    cuisine_name=cuisine_name,
                    preference_level=preference_level,
                    weight=weight
                )
            return True
        except Exception as e:
            logger.error(f"Error adding cuisine preference: {str(e)}")
            return False


    def track_restaurant_interaction(
        self,
        user_id: str,
        restaurant_id: str,
        restaurant_name: str,
        cuisine: str,
        interaction_type: str,  # viewed, clicked, ordered, recommended
        rating: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track user interaction with restaurant"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (r:Restaurant {restaurant_id: $restaurant_id})
        ON CREATE SET r.name = $restaurant_name, r.cuisine = $cuisine
        CREATE (u)-[i:INTERACTED_WITH]->(r)
        SET i.type = $interaction_type,
            i.timestamp = datetime(),
            i.rating = $rating,
            i.context = $context,
            u.updated_at = datetime()

        // Link to cuisine
        MERGE (c:Cuisine {name: $cuisine})
        MERGE (r)-[:SERVES]->(c)

        // Update interaction count
        WITH u, r
        MATCH (u)-[rel:INTERACTED_WITH]->(r)
        WITH u, r, count(rel) as interaction_count
        SET r.user_interactions = interaction_count
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    restaurant_id=restaurant_id,
                    restaurant_name=restaurant_name,
                    cuisine=cuisine,
                    interaction_type=interaction_type,
                    rating=rating,
                    context=context
                )
            logger.info(f"Tracked {interaction_type} interaction for restaurant {restaurant_name}")
            return True
        except Exception as e:
            logger.error(f"Error tracking restaurant interaction: {str(e)}")
            return False

    def track_destination_interaction(
        self,
        user_id: str,
        destination_id: str,
        destination_name: str,
        country: str,
        interaction_type: str,  # viewed, searched, booked, saved
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track user interaction with destination"""
        if not self.driver:
            return False

        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (d:Destination {destination_id: $destination_id})
        ON CREATE SET d.name = $destination_name, d.country = $country
        CREATE (u)-[i:EXPLORED]->(d)
        SET i.type = $interaction_type,
            i.timestamp = datetime(),
            i.context = $context,
            u.updated_at = datetime()
        """

        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    user_id=user_id,
                    destination_id=destination_id,
                    destination_name=destination_name,
                    country=country,
                    interaction_type=interaction_type,
                    context=context
                )
            return True
        except Exception as e:
            logger.error(f"Error tracking destination interaction: {str(e)}")
            return False

    def track_search_query(
        self,
        user_id: str,
        query: str,
        agent_type: str,  # restaurant or travel
        results_count: int = 0
    ) -> bool:
        """Track user search queries"""
        if not self.driver:
            return False

        cypher_query = """
        MATCH (u:User {user_id: $user_id})
        CREATE (s:SearchQuery {
            query: $query,
            agent_type: $agent_type,
            timestamp: datetime(),
            results_count: $results_count
        })
        CREATE (u)-[:SEARCHED]->(s)
        SET u.updated_at = datetime()
        """

        try:
            with self.driver.session() as session:
                session.run(
                    cypher_query,
                    user_id=user_id,
                    query=query,
                    agent_type=agent_type,
                    results_count=results_count
                )
            return True
        except Exception as e:
            logger.error(f"Error tracking search: {str(e)}")
            return False


    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user preferences from graph"""
        if not self.driver:
            return {}

        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[pf:PREFERS]->(f:Food)
        OPTIONAL MATCH (u)-[pc:LIKES_CUISINE]->(c:Cuisine)
        OPTIONAL MATCH (u)-[:HAS_RESTRICTION]->(r:DietaryRestriction)
        OPTIONAL MATCH (u)-[:PURSUES_GOAL]->(g:DietaryGoal)
        OPTIONAL MATCH (u)-[i:INTERACTED_WITH]->(rest:Restaurant)

        RETURN u,
               collect(DISTINCT {food: f.name, level: pf.level, weight: pf.weight}) as foods,
               collect(DISTINCT {cuisine: c.name, level: pc.level, weight: pc.weight}) as cuisines,
               collect(DISTINCT {type: r.type, name: r.name}) as restrictions,
               collect(DISTINCT g.name) as goals,
               count(DISTINCT i) as total_interactions
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id)
                record = result.single()

                if not record:
                    return {}

                user_data = dict(record["u"])

                return {
                    "user": user_data,
                    "food_preferences": [f for f in record["foods"] if f["food"]],
                    "cuisine_preferences": [c for c in record["cuisines"] if c["cuisine"]],
                    "dietary_restrictions": record["restrictions"],
                    "dietary_goals": record["goals"],
                    "total_interactions": record["total_interactions"]
                }

        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}

    def get_recommended_restaurants(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get personalized restaurant recommendations using graph algorithms"""
        if not self.driver:
            return []

        query = """
        MATCH (u:User {user_id: $user_id})

        // Get user's preferred cuisines
        OPTIONAL MATCH (u)-[pc:LIKES_CUISINE]->(c:Cuisine)<-[:SERVES]-(r:Restaurant)
        WHERE NOT (u)-[:INTERACTED_WITH]->(r)
        WITH u, r, sum(pc.weight) as cuisine_score

        // Get restaurants similar users liked
        OPTIONAL MATCH (u)-[:INTERACTED_WITH]->(:Restaurant)-[:SERVES]->(c:Cuisine)
        <-[:SERVES]-(similar_r:Restaurant)
        WHERE NOT (u)-[:INTERACTED_WITH]->(similar_r)
        WITH u, COALESCE(r, similar_r) as restaurant,
             COALESCE(cuisine_score, 0) + count(similar_r) as score

        // Filter by dietary restrictions
        OPTIONAL MATCH (u)-[:HAS_RESTRICTION]->(restriction:DietaryRestriction)
        WHERE NOT (restaurant.name =~ '.*' + restriction.name + '.*')

        RETURN DISTINCT restaurant.restaurant_id as id,
               restaurant.name as name,
               restaurant.cuisine as cuisine,
               score
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, limit=limit)
                recommendations = [
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "cuisine": record["cuisine"],
                        "score": record["score"]
                    }
                    for record in result
                    if record["name"]
                ]
                return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []

    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get analytics and insights about user behavior"""
        if not self.driver:
            return {}

        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[i:INTERACTED_WITH]->(r:Restaurant)
        OPTIONAL MATCH (u)-[s:SEARCHED]->(sq:SearchQuery)
        OPTIONAL MATCH (r)-[:SERVES]->(c:Cuisine)

        WITH u,
             count(DISTINCT i) as total_interactions,
             count(DISTINCT s) as total_searches,
             collect(DISTINCT c.name) as top_cuisines,
             collect(DISTINCT i.type) as interaction_types

        RETURN {
            total_interactions: total_interactions,
            total_searches: total_searches,
            favorite_cuisines: top_cuisines[0..5],
            interaction_types: interaction_types,
            account_age_days: duration.between(u.created_at, datetime()).days
        } as insights
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id)
                record = result.single()
                return record["insights"] if record else {}

        except Exception as e:
            logger.error(f"Error getting insights: {str(e)}")
            return {}


    def analyze_preference_trends(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze user preference trends over time"""
        if not self.driver:
            return {}

        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[p:PREFERS|LIKES_CUISINE]->(item)
        OPTIONAL MATCH (u)-[:HAS_HISTORY]->(ph:PreferenceHistory)
        WHERE ph.item = item.name AND ph.timestamp >= datetime() - duration({days: $days})
        
        WITH u, p, ph, item
        ORDER BY ph.timestamp DESC
        
        WITH u, 
             collect({
                 item: item.name,
                 type: type(p),
                 old_level: ph.old_level,
                 new_level: ph.new_level,
                 timestamp: ph.timestamp
             }) as changes,
             collect(DISTINCT {
                 item: item.name,
                 type: type(p),
                 current_level: p.level,
                 weight: p.weight,
                 created_at: p.created_at,
                 updated_at: p.updated_at
             }) as current_preferences
        
        RETURN {
            user_id: u.user_id,
            preference_changes: changes,
            current_preferences: current_preferences,
            total_changes: size(changes),
            analysis_period_days: $days
        } as trends
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, days=days)
                record = result.single()
                return record["trends"] if record else {}

        except Exception as e:
            logger.error(f"Error analyzing preference trends: {str(e)}")
            return {}

    def get_preference_evolution(
        self,
        user_id: str,
        item_name: str,
        preference_type: str = "food"  # "food" or "cuisine"
    ) -> List[Dict[str, Any]]:
        """Get evolution of a specific preference over time"""
        if not self.driver:
            return []

        rel_type = "PREFERS" if preference_type == "food" else "LIKES_CUISINE"
        node_type = "Food" if preference_type == "food" else "Cuisine"

        query = f"""
        MATCH (u:User {{user_id: $user_id}})-[p:{rel_type}]->(item:{node_type} {{name: $item_name}})
        OPTIONAL MATCH (u)-[:HAS_HISTORY]->(ph:PreferenceHistory)
        WHERE ph.item = $item_name
        
        WITH p, ph, item
        ORDER BY COALESCE(ph.timestamp, p.created_at) ASC
        
        RETURN collect({{
            timestamp: COALESCE(ph.timestamp, p.created_at),
            level: COALESCE(ph.new_level, p.level),
            weight: COALESCE(ph.new_weight, p.weight),
            is_change: ph IS NOT NULL
        }}) as evolution
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, item_name=item_name)
                record = result.single()
                return record["evolution"] if record else []

        except Exception as e:
            logger.error(f"Error getting preference evolution: {str(e)}")
            return []


    def get_collaborative_filtering_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendations using collaborative filtering"""
        if not self.driver:
            return []

        query = """
        MATCH (u:User {user_id: $user_id})
        
        // Find similar users (users who liked similar cuisines/foods)
        MATCH (u)-[:LIKES_CUISINE|PREFERS]->(item)<-[:LIKES_CUISINE|PREFERS]-(similar_user:User)
        WHERE similar_user <> u
        
        // Get restaurants that similar users liked but current user hasn't interacted with
        MATCH (similar_user)-[i:INTERACTED_WITH]->(r:Restaurant)
        WHERE NOT (u)-[:INTERACTED_WITH]->(r)
        AND i.rating >= 4.0
        
        // Calculate similarity score
        WITH u, r, count(DISTINCT similar_user) as similar_users_count,
             avg(i.rating) as avg_rating,
             count(i) as interaction_count
        
        // Filter by user's dietary restrictions
        OPTIONAL MATCH (u)-[:HAS_RESTRICTION]->(restriction:DietaryRestriction)
        WHERE NOT (r.name =~ '.*' + restriction.name + '.*')
        
        // Calculate final score
        WITH r, similar_users_count, avg_rating, interaction_count,
             (similar_users_count * 0.4 + avg_rating * 0.4 + interaction_count * 0.2) as score
        
        RETURN DISTINCT r.restaurant_id as id,
               r.name as name,
               r.cuisine as cuisine,
               score,
               avg_rating,
               similar_users_count
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, limit=limit)
                recommendations = [
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "cuisine": record["cuisine"],
                        "score": record["score"],
                        "avg_rating": record["avg_rating"],
                        "similar_users_count": record["similar_users_count"],
                        "algorithm": "collaborative_filtering"
                    }
                    for record in result
                    if record["name"]
                ]
                return recommendations

        except Exception as e:
            logger.error(f"Error getting collaborative filtering recommendations: {str(e)}")
            return []

    def get_content_based_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on content similarity"""
        if not self.driver:
            return []

        query = """
        MATCH (u:User {user_id: $user_id})

        // Collect the user's loved/liked cuisine NAMES into a list (not nodes).
        OPTIONAL MATCH (u)-[pc:LIKES_CUISINE]->(fc:Cuisine)
        WHERE pc.level IN ['love', 'like']
        WITH u, collect(DISTINCT {name: fc.name, weight: coalesce(pc.weight, 3)}) AS fav_cuisines
        WITH u, fav_cuisines, [c IN fav_cuisines | c.name] AS fav_cuisine_names

        // Restaurants serving any favourite cuisine that the user hasn't interacted with.
        MATCH (r:Restaurant)-[:SERVES]->(c:Cuisine)
        WHERE c.name IN fav_cuisine_names AND NOT (u)-[:INTERACTED_WITH]->(r)

        // Score by the matched cuisine's weight; drop anything matching a restriction name.
        OPTIONAL MATCH (u)-[:HAS_RESTRICTION]->(restriction:DietaryRestriction)
        WITH r, c, fav_cuisines, restriction
        WHERE restriction IS NULL
           OR NOT toLower(coalesce(r.name, '')) CONTAINS toLower(coalesce(restriction.name, ''))
        WITH r,
             reduce(s = 0, fcw IN fav_cuisines | CASE WHEN fcw.name = c.name THEN s + fcw.weight ELSE s END) AS cuisine_score

        RETURN DISTINCT r.restaurant_id AS id,
               r.name AS name,
               r.cuisine AS cuisine,
               sum(cuisine_score) AS score,
               sum(cuisine_score) AS total_cuisine_score,
               0 AS food_match_score
        ORDER BY score DESC
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, limit=limit)
                recommendations = [
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "cuisine": record["cuisine"],
                        "score": record["score"],
                        "cuisine_score": record["total_cuisine_score"],
                        "food_score": record["food_match_score"],
                        "algorithm": "content_based"
                    }
                    for record in result
                    if record["name"]
                ]
                return recommendations

        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {str(e)}")
            return []

    def get_hybrid_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        collaborative_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get hybrid recommendations combining collaborative and content-based filtering"""
        if not self.driver:
            return []

        collaborative = self.get_collaborative_filtering_recommendations(user_id, limit * 2)
        content_based = self.get_content_based_recommendations(user_id, limit * 2)

        combined = {}
        for rec in collaborative:
            restaurant_id = rec["id"]
            if restaurant_id not in combined:
                combined[restaurant_id] = {
                    "id": rec["id"],
                    "name": rec["name"],
                    "cuisine": rec["cuisine"],
                    "collaborative_score": rec["score"],
                    "content_score": 0,
                    "hybrid_score": 0
                }
            combined[restaurant_id]["collaborative_score"] = rec["score"]

        for rec in content_based:
            restaurant_id = rec["id"]
            if restaurant_id not in combined:
                combined[restaurant_id] = {
                    "id": rec["id"],
                    "name": rec["name"],
                    "cuisine": rec["cuisine"],
                    "collaborative_score": 0,
                    "content_score": rec["score"],
                    "hybrid_score": 0
                }
            combined[restaurant_id]["content_score"] = rec["score"]

        max_collab = max([r["collaborative_score"] for r in combined.values() if r["collaborative_score"] > 0], default=1)
        max_content = max([r["content_score"] for r in combined.values() if r["content_score"] > 0], default=1)

        for restaurant_id in combined:
            norm_collab = combined[restaurant_id]["collaborative_score"] / max_collab if max_collab > 0 else 0
            norm_content = combined[restaurant_id]["content_score"] / max_content if max_content > 0 else 0
            combined[restaurant_id]["hybrid_score"] = (
                norm_collab * collaborative_weight +
                norm_content * (1 - collaborative_weight)
            )

        recommendations = sorted(
            combined.values(),
            key=lambda x: x["hybrid_score"],
            reverse=True
        )[:limit]

        for rec in recommendations:
            rec["algorithm"] = "hybrid"

        return recommendations

    def get_similar_users(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find users with similar preferences"""
        if not self.driver:
            return []

        query = """
        MATCH (u:User {user_id: $user_id})
        
        // Find users with overlapping preferences
        MATCH (u)-[:LIKES_CUISINE|PREFERS]->(item)<-[:LIKES_CUISINE|PREFERS]-(similar:User)
        WHERE similar <> u
        
        // Calculate similarity score
        WITH similar, count(DISTINCT item) as common_items,
             collect(DISTINCT item.name)[0..5] as common_preferences
        
        // Get interaction overlap
        OPTIONAL MATCH (u)-[:INTERACTED_WITH]->(r:Restaurant)<-[:INTERACTED_WITH]-(similar)
        WITH similar, common_items, common_preferences, count(DISTINCT r) as common_interactions
        
        // Calculate final similarity score
        WITH similar, common_items, common_preferences, common_interactions,
             (common_items * 0.7 + common_interactions * 0.3) as similarity_score
        
        RETURN similar.user_id as user_id,
               similar.name as name,
               similarity_score,
               common_items,
               common_interactions,
               common_preferences
        ORDER BY similarity_score DESC
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, user_id=user_id, limit=limit)
                similar_users = [
                    {
                        "user_id": record["user_id"],
                        "name": record["name"],
                        "similarity_score": record["similarity_score"],
                        "common_items": record["common_items"],
                        "common_interactions": record["common_interactions"],
                        "common_preferences": record["common_preferences"]
                    }
                    for record in result
                ]
                return similar_users

        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []


    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")


knowledge_graph_service = KnowledgeGraphService()
