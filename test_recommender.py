from recommender import recommend_destinations

destinations = [
    {
        "name": "Tirupati",
        "category": "Temples",
        "description": "Famous temple and pilgrimage destination"
    },
    {
        "name": "Goa",
        "category": "Beach",
        "description": "Beautiful beaches and coastal tourism"
    },
    {
        "name": "Manali",
        "category": "Mountains",
        "description": "Mountains, snow and adventure"
    }
]

try:
    result = recommend_destinations(
        destinations,
        interest="temples"
    )

    print("\nAI RECOMMENDATION TEST SUCCESSFUL")

    for place in result:
        print(
            place["name"],
            "| AI Score:", place["ai_score"],
            "| Reason:", place["recommendation_reason"]
        )

except Exception as error:
    print("\nERROR FOUND:")
    print(type(error).__name__, error)