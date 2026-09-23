import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Path to our example dataset
DATA_PATH = Path(__file__).parent / "data" / "examples.json"


# Load the examples from JSON
with open(DATA_PATH, "r", encoding="utf-8") as file:
    EXAMPLES = json.load(file)


# Get only the requirement text from each example
requirements = [example["requirement"] for example in EXAMPLES]


# Convert the requirements into TF-IDF vectors
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(requirements)


def find_similar(requirement: str, k: int = 3) -> list[dict]:
    """
    Find the k most similar examples for the given requirement.
    """

    # Convert the new requirement into a TF-IDF vector
    query_vector = vectorizer.transform([requirement])

    # Compare the query with all stored examples
    scores = cosine_similarity(query_vector, tfidf_matrix)[0]

    # Get the indexes of the k highest similarity scores
    top_k_indices = scores.argsort()[-k:][::-1]

    # Return the corresponding examples
    return [EXAMPLES[index] for index in top_k_indices]
if __name__ == "__main__":
    test_requirement = "verify if an email address is valid"

    results = find_similar(test_requirement, k=3)

    print("User requirement:")
    print(test_requirement)

    print("\nMost similar examples:")

    for result in results:
        print("-", result["requirement"])