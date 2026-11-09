
import re
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------
# 1. INTEREST KEYWORDS
# ---------------------------------

INTEREST_KEYWORDS = {
    "temples": [
        "temple", "temples", "pilgrimage", "religious",
        "spiritual", "worship", "shrine", "heritage"
    ],
    "nature": [
        "nature", "forest", "greenery", "waterfall",
        "wildlife", "garden", "lake", "river"
    ],
    "beach": [
        "beach", "sea", "ocean", "coast", "island",
        "shore", "water sports"
    ],
    "mountains": [
        "mountain", "hill", "hills", "valley",
        "trekking", "snow", "adventure"
    ],
    "culture": [
        "culture", "history", "historical", "heritage",
        "museum", "palace", "monument", "architecture"
    ]
}

INTEREST_LABELS = {
    "temples": "Temples and religious places",
    "nature": "Nature and greenery",
    "beach": "Beaches and coastal destinations",
    "mountains": "Mountains and hill stations",
    "culture": "Culture, history and heritage",
    "all": "Travel and tourism destinations"
}


# ---------------------------------
# 2. NORMALISE INTEREST
# ---------------------------------

def normalise_interest(interest):

    if not interest:
        return "all"

    interest = str(interest).lower().strip()

    aliases = {
        "temple": "temples",
        "religious": "temples",
        "spiritual": "temples",
        "mountain": "mountains",
        "hills": "mountains",
        "hill station": "mountains",
        "beaches": "beach",
        "historical": "culture",
        "heritage": "culture",
        "all interests": "all"
    }

    interest = aliases.get(interest, interest)

    if interest not in INTEREST_KEYWORDS and interest != "all":
        return "all"

    return interest


# ---------------------------------
# 3. BUILD DESTINATION TEXT
# ---------------------------------

def build_destination_text(destination):

    if isinstance(destination, dict):

        fields = [
            "name",
            "destination",
            "city",
            "state",
            "category",
            "type",
            "description",
            "about",
            "interests",
            "attractions",
            "places",
            "best_for",
            "tags"
        ]

        text_parts = []

        for field in fields:

            value = destination.get(field, "")

            if value:
                if isinstance(value, (list, tuple, set)):
                    text_parts.extend(str(item) for item in value)
                else:
                    text_parts.append(str(value))

        return " ".join(text_parts)

    return str(destination)


# ---------------------------------
# 4. CHECK KEYWORD MATCHING
# ---------------------------------

def calculate_keyword_score(text, interest):

    if interest == "all":
        return 0

    keywords = INTEREST_KEYWORDS.get(interest, [])

    if not keywords:
        return 0

    text = text.lower()

    matched = 0

    for keyword in keywords:

        if keyword.lower() in text:
            matched += 1

    return (matched / len(keywords)) * 100


# ---------------------------------
# 5. CHECK CATEGORY MATCHING
# ---------------------------------

def calculate_category_score(text, interest):

    if interest == "all":
        return 0

    keywords = INTEREST_KEYWORDS.get(interest, [])

    text = text.lower()

    for keyword in keywords:

        if keyword.lower() in text:
            return 100

    return 0


# ---------------------------------
# 6. MAIN AI RECOMMENDATION MODEL
# ---------------------------------

def recommend_destinations(
    destinations,
    interest="all",
    origin="India",
    budget=0,
    days=3
):

    if not destinations:
        return []

    interest = normalise_interest(interest)

    # Create a safe copy of destination dictionaries
    destination_list = []

    for destination in destinations:

        if isinstance(destination, dict):
            destination_list.append(destination.copy())
        else:
            destination_list.append(destination)

    # Build destination descriptions
    destination_texts = [
        build_destination_text(destination)
        for destination in destination_list
    ]

    # Create search query
    if interest == "all":

        query_text = "travel tourism popular destinations India"

    else:

        keywords = INTEREST_KEYWORDS[interest]

        query_text = (
            INTEREST_LABELS[interest]
            + " "
            + " ".join(keywords)
        )

    # Combine query and destination descriptions
    all_texts = [query_text] + destination_texts

    # TF-IDF vectorisation
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000
    )

    try:

        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Convert to a normal NumPy array.
        # This avoids unsupported np.matrix inputs.
        tfidf_array = np.asarray(
            tfidf_matrix.toarray(),
            dtype=np.float64
        )

        query_vector = tfidf_array[0:1]

        destination_vectors = tfidf_array[1:]

        # Cosine similarity
        similarity_matrix = cosine_similarity(
            query_vector,
            destination_vectors
        )

        positive_scores = np.asarray(
            similarity_matrix,
            dtype=np.float64
        ).ravel()

    except ValueError:

        positive_scores = np.zeros(len(destination_list))

    recommendations = []

    # ---------------------------------
    # 7. CALCULATE RECOMMENDATION SCORES
    # ---------------------------------

    for index, destination in enumerate(destination_list):

        text = destination_texts[index]

        similarity_score = float(
            positive_scores[index] * 100
        )

        category_score = calculate_category_score(
            text,
            interest
        )

        keyword_score = calculate_keyword_score(
            text,
            interest
        )

        if interest == "all":

            final_score = similarity_score

        else:

            final_score = (
                similarity_score * 0.60
                + category_score * 0.30
                + keyword_score * 0.10
            )

        final_score = round(
            min(max(final_score, 0), 100),
            2
        )

        # Recommendation explanation
        if interest == "all":

            reason = "Recommended using AI text similarity."

        elif category_score > 0:

            reason = (
                "Matches your interest in "
                + INTEREST_LABELS[interest]
                + "."
            )

        else:

            reason = (
                "Recommended based on text similarity "
                "with your selected interest."
            )

        # Add AI information
        if isinstance(destination, dict):

            destination["ai_score"] = final_score

            destination["recommendation_reason"] = reason

            destination["similarity_score"] = round(
                similarity_score,
                2
            )

            destination["category_score"] = round(
                category_score,
                2
            )

            destination["keyword_score"] = round(
                keyword_score,
                2
            )

        recommendations.append(destination)

    # ---------------------------------
    # 8. SORT BY AI SCORE
    # ---------------------------------

    recommendations.sort(
        key=lambda item: (
            item.get("ai_score", 0)
            if isinstance(item, dict)
            else 0
        ),
        reverse=True
    )

    return recommendations
