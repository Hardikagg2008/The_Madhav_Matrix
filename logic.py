import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------------------------------------------------------
# CONFIGURATION: Department Keyword Mapping
# -------------------------------------------------------------------------
DEPARTMENT_MAP = {
    "Water Department": ["leak", "water", "pipe", "flood", "burst", "sewage", "drain"],
    "Roads & Transport": ["pothole", "hole", "road", "street", "pavement", "sidewalk", "traffic light", "signal"],
    "Sanitation": ["trash", "garbage", "waste", "dump", "litter", "recycling", "smell"],
    "Parks & Recreation": ["park", "tree", "grass", "playground", "bench", "garden"],
    "Electricity/Power": ["power", "electric", "wire", "outage", "blackout", "transformer", "spark"],
}

def preprocess_text(text):
    """
    Cleans the input text: lowercase, removes punctuation and special characters.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text) # Removes punctuation (e.g., "Hole!!!" -> "hole")
    return text.strip()

def suggest_department(text):
    """
    Analyzes the complaint text and suggests a city department.
    """
    cleaned_text = preprocess_text(text)
    for department, keywords in DEPARTMENT_MAP.items():
        if any(keyword in cleaned_text for keyword in keywords):
            return department
    
    return "General Services"

def group_complaints(new_complaint_text, existing_complaints_list):
    """
    Args:
        new_complaint_text (str): The text of the new report.
        existing_complaints_list (list): A list of DICTIONARIES 
                                         (e.g., [{'id': 1, 'text': '...'}, ...])
        
    Returns:
        int or None: The ID of the matching complaint if similarity > threshold, else None.
    """
    if not existing_complaints_list:
        return None

    # 1. Preprocess the new complaint
    new_text = preprocess_text(new_complaint_text)
    
    # 2. Extract and preprocess all existing complaint texts
    existing_texts = [preprocess_text(item['text']) for item in existing_complaints_list]
    
    # Create a corpus
    corpus = [new_text] + existing_texts
    
    # 3. TF-IDF with stop_words='english' to ignore useless words (the, a, is, etc.)
    vectorizer = TfidfVectorizer(stop_words='english').fit_transform(corpus)
    vectors = vectorizer.toarray()
    
    # Calculate Cosine Similarity
    similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]
    
    max_idx = similarities.argmax()
    max_score = similarities[max_idx]
    
    THRESHOLD = 0.3 
    
    if max_score >= THRESHOLD:
        # RETURN THE ID, not the text. This is what the backend needs.
        return existing_complaints_list[max_idx]['id']
    
    return None

# ==========================================
# TEST BLOCK: Updated for IDs
# ==========================================
if __name__ == "__main__":
    print("--- Testing Department Suggestion ---")
    print(f"Result: {suggest_department('There is a massive WATER leak!!!')}") 

    print("\n--- Testing Grouping with IDs ---")
    # Mock data: This is exactly how the backend will send the data
    existing_data = [
        {"id": 101, "text": "Huge hole in the road on 5th Ave"},
        {"id": 102, "text": "Trash hasn't been picked up in two days"},
        {"id": 103, "text": "Street light is flickering on Oak St"}
    ]
    new_issue = "Pothole on 5th Avenue"
    
    match_id = group_complaints(new_issue, existing_data)
    if match_id:
        print(f"MATCH FOUND: New issue groups with Ticket ID: {match_id}")
    else:
        print("NO MATCH: Creating a new ticket.")