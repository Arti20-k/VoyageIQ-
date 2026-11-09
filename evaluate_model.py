
from recommender import recommend_destinations


# Sample destinations for testing VoyageIQ
test_destinations = [
    {
        "name": "Tirupati",
        "state": "Andhra Pradesh",
        "district": "Tirupati",
        "interest": "temples",
        "description": "Famous pilgrimage and spiritual destination",
        "places": ["Tirumala Temple", "Sri Venkateswara Temple"],
        "cost": 1500
    },
    {
        "name": "Madurai",
        "state": "Tamil Nadu",
        "district": "Madurai",
        "interest": "temples",
        "description": "Historic temple city with cultural heritage",
        "places": ["Meenakshi Temple"],
        "cost": 1800
    },
    {
        "name": "Ayodhya",
        "state": "Uttar Pradesh",
        "district": "Ayodhya",
        "interest": "temples",
        "description": "Religious and spiritual pilgrimage destination",
        "places": ["Ram Mandir"],
        "cost": 2000
    },
    {
        "name": "Coorg",
        "state": "Karnataka",
        "district": "Kodagu",
        "interest": "nature",
        "description": "Green forests, waterfalls and beautiful scenery",
        "places": ["Abbey Falls", "Raja's Seat"],
        "cost": 2500
    },
    {
        "name": "Manali",
        "state": "Himachal Pradesh",
        "district": "Kullu",
        "interest": "mountains",
        "description": "Beautiful mountains, valleys and snow-covered peaks",
        "places": ["Solang Valley", "Rohtang Pass"],
        "cost": 3500
    },
    {
        "name": "Ooty",
        "state": "Tamil Nadu",
        "district": "Nilgiris",
        "interest": "nature",
        "description": "Hill station with gardens, lakes and greenery",
        "places": ["Ooty Lake", "Botanical Garden"],
        "cost": 2200
    },
    {
        "name": "Goa",
        "state": "Goa",
        "district": "North Goa",
        "interest": "beach",
        "description": "Popular coastal destination with beautiful beaches",
        "places": ["Baga Beach", "Calangute Beach"],
        "cost": 3000
    },
    {
        "name": "Mumbai",
        "state": "Maharashtra",
        "district": "Mumbai",
        "interest": "beach",
        "description": "Coastal city with sea views and beaches",
        "places": ["Juhu Beach", "Marine Drive"],
        "cost": 3200
    },
    {
        "name": "Jaipur",
        "state": "Rajasthan",
        "district": "Jaipur",
        "interest": "culture",
        "description": "Historical city famous for forts and palaces",
        "places": ["Hawa Mahal", "Amber Fort"],
        "cost": 2800
    },
    {
        "name": "Mysuru",
        "state": "Karnataka",
        "district": "Mysuru",
        "interest": "culture",
        "description": "Cultural city known for its palace and heritage",
        "places": ["Mysore Palace", "Chamundi Hills"],
        "cost": 2000
    }
]


# Sample relevant destinations for each interest.
# These labels are manually created for this demonstration.
relevant_destinations = {
    "temples": ["Tirupati", "Madurai", "Ayodhya"],
    "nature": ["Coorg", "Ooty"],
    "mountains": ["Manali"],
    "beach": ["Goa", "Mumbai"],
    "culture": ["Jaipur", "Mysuru"]
}


def evaluate_recommendations(k=3):

    total_precision = 0
    total_recall = 0
    total_f1 = 0

    print("\n===================================")
    print("       VOYAGEIQ MODEL EVALUATION")
    print("===================================")

    for interest, relevant in relevant_destinations.items():

        recommendations = recommend_destinations(
            test_destinations,
            interest=interest,
            origin="India",
            budget=0,
            days=3
        )

        top_k = recommendations[:k]

        recommended_names = [
            place["name"] for place in top_k
        ]

        relevant_found = [
            name for name in recommended_names
            if name in relevant
        ]

        hits = len(relevant_found)

        precision = hits / k
        recall = hits / len(relevant)

        if precision + recall > 0:
            f1 = (
                2 * precision * recall
                / (precision + recall)
            )
        else:
            f1 = 0

        total_precision += precision
        total_recall += recall
        total_f1 += f1

        print(f"\nInterest: {interest.title()}")
        print("Recommended:", recommended_names)
        print("Relevant found:", relevant_found)
        print(f"Precision@{k}: {precision * 100:.2f}%")
        print(f"Recall@{k}: {recall * 100:.2f}%")
        print(f"F1-score: {f1 * 100:.2f}%")

    count = len(relevant_destinations)

    print("\n===================================")
    print("          AVERAGE RESULTS")
    print("===================================")

    print(
        f"Average Precision: "
        f"{(total_precision / count) * 100:.2f}%"
    )

    print(
        f"Average Recall: "
        f"{(total_recall / count) * 100:.2f}%"
    )

    print(
        f"Average F1-score: "
        f"{(total_f1 / count) * 100:.2f}%"
    )

    print("\nEvaluation completed successfully!")


if __name__ == "__main__":
    evaluate_recommendations(k=3)
