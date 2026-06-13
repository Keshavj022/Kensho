"""
Curated airport dataset + nearest-airport lookup (no external API).

Used to default the traveller's origin airport from their saved location, and to
tell the assistant which airport "home" is. India-focused + key international hubs.
"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any, Optional

AIRPORTS: list[dict[str, Any]] = [
    {"iata": "DEL", "city": "Delhi", "name": "Indira Gandhi Intl", "lat": 28.5562, "lng": 77.1000},
    {"iata": "BOM", "city": "Mumbai", "name": "Chhatrapati Shivaji Intl", "lat": 19.0896, "lng": 72.8656},
    {"iata": "CCU", "city": "Kolkata", "name": "Netaji Subhas Chandra Bose Intl", "lat": 22.6547, "lng": 88.4467},
    {"iata": "BLR", "city": "Bengaluru", "name": "Kempegowda Intl", "lat": 13.1986, "lng": 77.7066},
    {"iata": "MAA", "city": "Chennai", "name": "Chennai Intl", "lat": 12.9941, "lng": 80.1709},
    {"iata": "HYD", "city": "Hyderabad", "name": "Rajiv Gandhi Intl", "lat": 17.2403, "lng": 78.4294},
    {"iata": "COK", "city": "Kochi", "name": "Cochin Intl", "lat": 10.1520, "lng": 76.4019},
    {"iata": "AMD", "city": "Ahmedabad", "name": "Sardar Vallabhbhai Patel Intl", "lat": 23.0772, "lng": 72.6347},
    {"iata": "PNQ", "city": "Pune", "name": "Pune Airport", "lat": 18.5793, "lng": 73.9089},
    {"iata": "GOI", "city": "Goa", "name": "Dabolim (Goa)", "lat": 15.3808, "lng": 73.8314},
    {"iata": "JAI", "city": "Jaipur", "name": "Jaipur Intl", "lat": 26.8242, "lng": 75.8122},
    {"iata": "LKO", "city": "Lucknow", "name": "Chaudhary Charan Singh Intl", "lat": 26.7606, "lng": 80.8893},
    {"iata": "PAT", "city": "Patna", "name": "Jay Prakash Narayan", "lat": 25.5913, "lng": 85.0880},
    {"iata": "BBI", "city": "Bhubaneswar", "name": "Biju Patnaik Intl", "lat": 20.2444, "lng": 85.8178},
    {"iata": "GAU", "city": "Guwahati", "name": "Lokpriya Gopinath Bordoloi Intl", "lat": 26.1061, "lng": 91.5859},
    {"iata": "TRV", "city": "Thiruvananthapuram", "name": "Trivandrum Intl", "lat": 8.4821, "lng": 76.9200},
    {"iata": "IXC", "city": "Chandigarh", "name": "Chandigarh Intl", "lat": 30.6735, "lng": 76.7885},
    {"iata": "NAG", "city": "Nagpur", "name": "Dr. Babasaheb Ambedkar Intl", "lat": 21.0922, "lng": 79.0472},
    {"iata": "IXB", "city": "Siliguri", "name": "Bagdogra", "lat": 26.6812, "lng": 88.3286},
    {"iata": "VNS", "city": "Varanasi", "name": "Lal Bahadur Shastri Intl", "lat": 25.4524, "lng": 82.8593},
    {"iata": "IXR", "city": "Ranchi", "name": "Birsa Munda", "lat": 23.3143, "lng": 85.3217},
    {"iata": "RPR", "city": "Raipur", "name": "Swami Vivekananda", "lat": 21.1804, "lng": 81.7388},
    {"iata": "IDR", "city": "Indore", "name": "Devi Ahilyabai Holkar", "lat": 22.7218, "lng": 75.8011},
    {"iata": "ATQ", "city": "Amritsar", "name": "Sri Guru Ram Dass Jee Intl", "lat": 31.7096, "lng": 74.7973},
    {"iata": "SXR", "city": "Srinagar", "name": "Srinagar Intl", "lat": 33.9871, "lng": 74.7742},
    {"iata": "CJB", "city": "Coimbatore", "name": "Coimbatore Intl", "lat": 11.0301, "lng": 77.0434},
    {"iata": "VTZ", "city": "Visakhapatnam", "name": "Visakhapatnam", "lat": 17.7211, "lng": 83.2245},
    {"iata": "BDQ", "city": "Vadodara", "name": "Vadodara", "lat": 22.3362, "lng": 73.2263},
    {"iata": "IXM", "city": "Madurai", "name": "Madurai", "lat": 9.8345, "lng": 78.0934},
    {"iata": "GAY", "city": "Gaya", "name": "Gaya Intl", "lat": 24.7443, "lng": 84.9512},
    {"iata": "DXB", "city": "Dubai", "name": "Dubai Intl", "lat": 25.2528, "lng": 55.3644},
    {"iata": "SIN", "city": "Singapore", "name": "Changi", "lat": 1.3592, "lng": 103.9894},
    {"iata": "BKK", "city": "Bangkok", "name": "Suvarnabhumi", "lat": 13.6900, "lng": 100.7501},
    {"iata": "KUL", "city": "Kuala Lumpur", "name": "KLIA", "lat": 2.7456, "lng": 101.7099},
    {"iata": "DOH", "city": "Doha", "name": "Hamad Intl", "lat": 25.2731, "lng": 51.5650},
    {"iata": "CMB", "city": "Colombo", "name": "Bandaranaike Intl", "lat": 7.1808, "lng": 79.8841},
    {"iata": "KTM", "city": "Kathmandu", "name": "Tribhuvan Intl", "lat": 27.6966, "lng": 85.3591},
    {"iata": "LHR", "city": "London", "name": "Heathrow", "lat": 51.4700, "lng": -0.4543},
    {"iata": "JFK", "city": "New York", "name": "John F. Kennedy Intl", "lat": 40.6413, "lng": -73.7781},
]


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    d = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(d))


def nearest_airport(lat: float, lng: float) -> dict[str, Any]:
    best = min(AIRPORTS, key=lambda a: _haversine(lat, lng, a["lat"], a["lng"]))
    return {**best, "distance_km": round(_haversine(lat, lng, best["lat"], best["lng"]), 1)}


def airport_for_city(name: Optional[str]) -> Optional[dict[str, Any]]:
    if not name:
        return None
    n = name.lower()
    for a in AIRPORTS:
        if a["city"].lower() in n or a["iata"].lower() == n.strip():
            return {**a, "distance_km": None}
    return None


def home_airport(lat: Optional[float] = None, lng: Optional[float] = None, location: Optional[str] = None) -> Optional[dict[str, Any]]:
    if lat is not None and lng is not None:
        return nearest_airport(lat, lng)
    return airport_for_city(location)
