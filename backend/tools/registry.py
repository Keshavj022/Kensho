"""
Tool registry — which tools each specialist agent gets (and ONLY those).

Kept as functions (not module-level lists) so menu_tools (added in the menu
pipeline milestone) can be picked up once it exists, without import-order issues.
"""
from __future__ import annotations

from . import kg_tools, places_tools, rag_tools, search_tools, serpapi_tools, trip_tools


def restaurant_tools() -> list:
    tools = [
        places_tools.search_restaurants,
        places_tools.get_restaurant_details,
        rag_tools.search_dishes,
        rag_tools.get_restaurant_context,
        kg_tools.get_user_preferences,
        kg_tools.recommend_restaurants,
        kg_tools.track_interaction,
        search_tools.web_search,
    ]
    try:  # menu pipeline tool (added in M5); optional so M4 works without it
        from . import menu_tools

        tools.insert(2, menu_tools.get_menu)
    except Exception:
        pass
    return tools


def travel_tools() -> list:
    return [
        serpapi_tools.search_flights,
        serpapi_tools.resolve_flight_booking_options,
        serpapi_tools.search_hotels,
        trip_tools.plan_trip,
        search_tools.web_search,
    ]


def shopping_tools() -> list:
    return [
        serpapi_tools.search_products,
        search_tools.web_search,
    ]
