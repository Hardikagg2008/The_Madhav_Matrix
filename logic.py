from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEPARTMENT_MAP = {
    "Water Department": ["leak", "water", "pipe", "flood", "burst", "sewage", "drain"],
    "Roads & Transport": ["pothole", "hole", "road", "street", "pavement", "sidewalk", "traffic light", "signal"],
    "Sanitation": ["trash", "garbage", "waste", "dump", "litter", "recycling", "smell"],
    "Parks & Recreation": ["park", "tree", "grass", "playground", "bench", "garden"],
    "Electricity/Power": ["power", "electric", "wire", "outage", "blackout", "transformer", "spark"],
}

def suggest_department(text):
    """
    Analyzes the complaint text and suggests a city department 
    based on keyword matching.
    """
    text = text.lower()
    for department, keywords in DEPARTMENT_MAP.items():
        if any(keyword in text for keyword in keywords):
            return department
    
    return "General Services"  # Fallback if no keywords match

def group_complaints(new_complaint, existing_complaints):
    """
    Checks if a new complaint is similar to any existing complaints using TF-IDF.
    
    Args:
        new_complaint (str): The text of the new report.
        existing_complaints (list): A list of strings of current open issues.
        
    Returns:
        str or None: The text of the matching complaint if similarity > threshold, else None.
    """
    if not existing_complaints:
        return None

    # Create a corpus: [New Complaint, Existing 1, Existing 2, ...]
    corpus = [new_complaint] + existing_complaints
    
    # Convert text to TF-IDF vectors (turns words into numbers)
    vectorizer = TfidfVectorizer().fit_transform(corpus)
    vectors = vectorizer.toarray()
    
    # Calculate Cosine Similarity between the new one (index 0) and the rest
    similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]
    
    # Find the best match
    max_idx = similarities.argmax()
    max_score = similarities[max_idx]
    
    # THRESHOLD: 0.3 is a good balance. 
    # Higher (0.5) = stricter matching. Lower (0.2) = looser matching.
    THRESHOLD = 0.3 
    
    if max_score >= THRESHOLD:
        return existing_complaints[max_idx]
    
    return None

# ==========================================
# TEST BLOCK: This only runs if you run 'python3 logic.py' directly
# ==========================================
if __name__ == "__main__":
    print("--- Testing Department Suggestion ---")
    test_text = "There is a massive water leak on Main St"
    print(f"Text: {test_text} -> Dept: {suggest_department(test_text)}") 

    print("\n--- Testing Grouping ---")
    existing = [
        "Huge hole in the road on 5th Ave",
        "Trash hasn't been picked up in two days",
        "Street light is flickering on Oak St"
    ]
    new_issue = "Pothole on 5th Avenue"
    
    match = group_complaints(new_issue, existing)
    if match:
        print(f"MATCH FOUND: '{new_issue}' groups with '{match}'")
    else:
        print("NO MATCH: Creating a new ticket.")