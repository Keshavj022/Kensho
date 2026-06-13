"""User profiles backed by the user_profiles table and bridged to Neo4j on write."""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from ..db.database import SessionLocal, session_scope
from ..db.models import UserProfileRow
from ..models.schemas import (
    DietaryInfo,
    DietaryRestriction,
    DietaryType,
    FoodPreference,
    RestrictionType,
    User,
    UserPreferences,
    UserProfile,
)


def _row_to_user(row: UserProfileRow) -> User:
    try:
        dtype = DietaryType(row.dietary_type)
    except Exception:
        dtype = DietaryType.NON_VEGETARIAN
    restrictions = []
    for r in row.dietary_restrictions or []:
        try:
            restrictions.append(DietaryRestriction(type=RestrictionType(r["type"]), value=r["value"]))
        except Exception:
            continue
    foods = {k: FoodPreference(**v) for k, v in (row.food_preferences or {}).items()}
    cuisines = {k: FoodPreference(**v) for k, v in (row.cuisine_preferences or {}).items()}
    return User(
        profile=UserProfile(name=row.name, age=row.age, location=row.location, dob=row.dob, gender=row.gender),
        dietary=DietaryInfo(type=dtype, restrictions=restrictions, goals=list(row.dietary_goals or [])),
        preferences=UserPreferences(foods=foods, cuisines=cuisines),
    )


def _age_from_dob(dob: Optional[str]) -> Optional[int]:
    if not dob:
        return None
    try:
        from datetime import date

        y, m, d = (int(x) for x in dob[:10].split("-"))
        today = date.today()
        return today.year - y - ((today.month, today.day) < (m, d))
    except Exception:
        return None


def _bridge_to_graph(user_id: str, user: User) -> None:
    try:
        from .knowledge_graph_service import knowledge_graph_service

        if not getattr(knowledge_graph_service, "driver", None):
            return
        knowledge_graph_service.create_user(
            user_id=user_id,
            name=user.profile.name,
            age=user.profile.age,
            location=user.profile.location,
            dietary_type=user.dietary.type.value if user.dietary.type else None,
        )
        for r in user.dietary.restrictions:
            knowledge_graph_service.add_dietary_restriction(user_id, r.type.value, r.value)
        for goal in user.dietary.goals:
            knowledge_graph_service.add_dietary_goal(user_id, goal)
        for name, pref in user.preferences.foods.items():
            knowledge_graph_service.add_food_preference(user_id, name, pref.preference, pref.weight)
        for name, pref in user.preferences.cuisines.items():
            knowledge_graph_service.add_cuisine_preference(user_id, name, pref.preference, pref.weight)
    except Exception as e:
        logger.warning(f"Neo4j bridge failed for {user_id}: {e}")


class UserService:
    def get_user(self, user_id: str = "default") -> Optional[User]:
        with SessionLocal() as db:
            row = db.get(UserProfileRow, user_id)
            return _row_to_user(row) if row else None

    def create_user(self, user_id: str, user: User) -> User:
        """Upsert the profile row AND bridge to Neo4j (shared user_id)."""
        with session_scope() as db:
            row = db.get(UserProfileRow, user_id)
            if row is None:
                row = UserProfileRow(user_id=user_id)
                db.add(row)
            row.name = user.profile.name
            row.age = user.profile.age
            row.location = user.profile.location
            row.dietary_type = user.dietary.type.value if user.dietary.type else "non-vegetarian"
            row.dietary_restrictions = [{"type": r.type.value, "value": r.value} for r in user.dietary.restrictions]
            row.dietary_goals = list(user.dietary.goals)
            row.food_preferences = {k: v.model_dump() for k, v in user.preferences.foods.items()}
            row.cuisine_preferences = {k: v.model_dump() for k, v in user.preferences.cuisines.items()}
        _bridge_to_graph(user_id, user)
        logger.info(f"Profile saved + bridged to graph: {user_id}")
        return user

    def update_user(self, user_id: str, updates: dict[str, Any]) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return self.create_user(user_id, user)

    def learn_preference(
        self, user_id: str, preference_type: str, item_name: str, preference_level: str, weight: int = 3
    ) -> bool:
        with session_scope() as db:
            row = db.get(UserProfileRow, user_id)
            if not row:
                return False
            entry = {"preference": preference_level, "weight": weight}
            if preference_type == "food":
                prefs = dict(row.food_preferences or {})
                prefs[item_name] = entry
                row.food_preferences = prefs
            elif preference_type == "cuisine":
                prefs = dict(row.cuisine_preferences or {})
                prefs[item_name] = entry
                row.cuisine_preferences = prefs
            else:
                return False
        try:
            from .knowledge_graph_service import knowledge_graph_service

            if getattr(knowledge_graph_service, "driver", None):
                if preference_type == "food":
                    knowledge_graph_service.add_food_preference(user_id, item_name, preference_level, weight)
                else:
                    knowledge_graph_service.add_cuisine_preference(user_id, item_name, preference_level, weight)
        except Exception as e:
            logger.warning(f"learn_preference graph bridge failed: {e}")
        return True

    def get_personalized_preferences(self, user_id: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        user = self.get_user(user_id)
        if user:
            out["profile"] = user.model_dump()
        try:
            from .knowledge_graph_service import knowledge_graph_service

            if getattr(knowledge_graph_service, "driver", None):
                out["graph"] = knowledge_graph_service.get_user_preferences(user_id)
        except Exception:
            pass
        return out

    def get_user_context(self, user_id: str = "default") -> str:
        user = self.get_user(user_id)
        if not user:
            return ""
        context = (
            f"User Profile:\n- Name: {user.profile.name}\n"
            f"- Location: {user.profile.location}\n- Dietary Type: {user.dietary.type.value}\n"
        )
        if user.dietary.restrictions:
            context += "- Restrictions: " + ", ".join(f"{r.type.value}: {r.value}" for r in user.dietary.restrictions) + "\n"
        if user.dietary.goals:
            context += "- Goals: " + ", ".join(user.dietary.goals) + "\n"
        liked = [f for f, p in user.preferences.foods.items() if p.preference in ("love", "like")]
        if liked:
            context += "- Favorite Foods: " + ", ".join(liked[:5]) + "\n"
        return context

    def save_profile(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist the full onboarding profile and bridge it to Neo4j."""
        with session_scope() as db:
            row = db.get(UserProfileRow, user_id)
            if row is None:
                row = UserProfileRow(user_id=user_id)
                db.add(row)
            if payload.get("name"):
                row.name = payload["name"]
            row.dob = payload.get("dob")
            row.gender = payload.get("gender")
            row.age = payload.get("age") or _age_from_dob(payload.get("dob")) or row.age
            row.location = payload.get("location") or row.location or ""
            row.lat = payload.get("lat") if payload.get("lat") is not None else row.lat
            row.lng = payload.get("lng") if payload.get("lng") is not None else row.lng
            row.dietary_type = payload.get("dietary_type") or "non-vegetarian"
            row.spice_tolerance = payload.get("spice_tolerance")
            row.dietary_restrictions = [{"type": "allergy", "value": a} for a in payload.get("allergies", []) if a]
            row.dietary_goals = [g for g in payload.get("goals", []) if g]
            foods: dict[str, Any] = {}
            for f in payload.get("likes", []):
                if f:
                    foods[f] = {"preference": "like", "weight": 4}
            for f in payload.get("dislikes", []):
                if f:
                    foods[f] = {"preference": "dislike", "weight": 2}
            row.food_preferences = foods
            row.cuisine_preferences = {c: {"preference": "like", "weight": 4} for c in payload.get("cuisines", []) if c}
            row.onboarded = True
        user = self.get_user(user_id)
        if user:
            _bridge_to_graph(user_id, user)
        logger.info(f"Saved onboarding profile for {user_id}")
        return self.get_profile_dict(user_id)

    def get_profile_dict(self, user_id: str) -> dict[str, Any]:
        with SessionLocal() as db:
            row = db.get(UserProfileRow, user_id)
            if not row:
                return {"user_id": user_id, "onboarded": False}
            likes, dislikes = [], []
            for name, v in (row.food_preferences or {}).items():
                (likes if v.get("preference") in ("like", "love") else dislikes).append(name)
            return {
                "user_id": user_id,
                "name": row.name,
                "dob": row.dob,
                "gender": row.gender,
                "age": row.age,
                "location": row.location,
                "lat": row.lat,
                "lng": row.lng,
                "dietary_type": row.dietary_type,
                "spice_tolerance": row.spice_tolerance,
                "allergies": [r.get("value") for r in (row.dietary_restrictions or []) if r.get("type") == "allergy"],
                "goals": list(row.dietary_goals or []),
                "likes": likes,
                "dislikes": dislikes,
                "cuisines": list((row.cuisine_preferences or {}).keys()),
                "onboarded": bool(row.onboarded),
            }

    def taste_graph(self, user_id: str) -> dict[str, Any]:
        """A visualisable taste graph for the profile page.

        Derived from the saved profile (always available) and enriched with Neo4j
        insights when the graph is reachable. Returns radial nodes + edges centred
        on the diner — never raises.
        """
        p = self.get_profile_dict(user_id)
        center = {"id": "me", "label": p.get("name") or "You", "group": "user"}
        nodes: list[dict[str, Any]] = [center]
        edges: list[dict[str, Any]] = []

        def add(node_id: str, label: str, group: str, kind: str, weight: int = 3) -> None:
            if not label:
                return
            nodes.append({"id": node_id, "label": label, "group": group, "weight": weight})
            edges.append({"source": "me", "target": node_id, "kind": kind})

        if p.get("dietary_type"):
            add("diet", str(p["dietary_type"]).replace("-", " ").title(), "diet", "eats", 5)
        for i, c in enumerate(p.get("cuisines") or []):
            add(f"cuisine:{i}", c.title() if c.islower() else c, "cuisine", "loves_cuisine", 4)
        for i, f in enumerate((p.get("likes") or [])[:12]):
            add(f"food:{i}", f, "food", "likes", 4)
        for i, a in enumerate(p.get("allergies") or []):
            add(f"allergy:{i}", a, "allergy", "avoids", 5)
        for i, g in enumerate(p.get("goals") or []):
            add(f"goal:{i}", g, "goal", "pursues", 3)

        insights: dict[str, Any] = {}
        try:
            from .knowledge_graph_service import knowledge_graph_service

            if getattr(knowledge_graph_service, "driver", None):
                insights = knowledge_graph_service.get_user_insights(user_id) or {}
        except Exception:
            insights = {}

        return {
            "status": "ok",
            "onboarded": bool(p.get("onboarded")),
            "center": center,
            "nodes": nodes,
            "edges": edges,
            "insights": insights,
        }

    def profile_summary(self, user_id: str) -> str:
        """A SILENT personalization directive for the LLM.

        Tells the assistant to apply the diner's diet/allergies as hard filters and
        lean toward their tastes — without announcing it, restating the profile, or
        using the diner's name (so replies feel naturally tailored, not robotic). The
        diner's home city is only a fallback: an explicitly-named place always wins.
        """
        p = self.get_profile_dict(user_id)
        if not p.get("onboarded"):
            return ""

        diet = (p.get("dietary_type") or "non-vegetarian").strip()
        limits: list[str] = []
        if diet and diet != "non-vegetarian":
            limits.append(f"the diner is {diet} — only ever suggest {diet}-friendly food")
        if p.get("allergies"):
            limits.append("never suggest anything containing " + ", ".join(p["allergies"]) + " (allergy — exclude if unsure)")

        leanings: list[str] = []
        if p.get("likes"):
            leanings.append("enjoys " + ", ".join(p["likes"][:8]))
        if p.get("dislikes"):
            leanings.append("would rather avoid " + ", ".join(p["dislikes"]))
        if p.get("cuisines"):
            leanings.append("favourite cuisines: " + ", ".join(p["cuisines"]))
        if p.get("goals"):
            leanings.append("health goals: " + ", ".join(p["goals"]))
        if p.get("spice_tolerance"):
            leanings.append(f"spice tolerance: {p['spice_tolerance']}")

        loc = p.get("location")
        loc_line = ""
        if loc:
            loc_line = (
                f" If the user names a city, area, or place, search exactly there. "
                f"Only when they give no location, assume they're near {loc}."
            )
        airport_line = ""
        try:
            from .airports import home_airport

            ap = home_airport(p.get("lat"), p.get("lng"), loc)
            if ap:
                airport_line = f" For flights, default the origin to {ap['iata']} ({ap['city']}) only when the user doesn't name one."
        except Exception:
            pass

        body: list[str] = []
        if limits:
            body.append("Hard limits: " + "; ".join(limits) + ".")
        if leanings:
            body.append("Leanings (use to rank and suggest, don't force): " + "; ".join(leanings) + ".")
        if not body and not loc_line and not airport_line:
            return ""
        return (
            "[Personalize SILENTLY: apply the diner's tastes to what you suggest, but do NOT "
            "announce that you're personalizing, do NOT restate this profile, and do NOT use "
            "the diner's name.] " + " ".join(body) + loc_line + airport_line
        ).strip()


user_service = UserService()
