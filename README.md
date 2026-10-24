Here is a complete, professional, and tailored README.md based directly on your
code in logic.py and app.py.

The Madhav Matrix (StreetSignal) 🚦🏛️

An intelligent civic issue tracking and deduplication web platform. Built with
Flask, SQLAlchemy, and Scikit-Learn, this application automatically triages
citizen complaints to the appropriate city department using keyword matching and
clusters similar reports into unified tickets using TF-IDF Vectorization and
Cosine Similarity.

📌 Features

  - Automated Department Routing (logic.suggest_department)
    Scans incoming complaints and matches them against department-specific
    keywords:

      - 🚰 Water Department: leak, water, pipe, flood, burst, sewage, drain
      - 🚗 Roads & Transport: pothole, hole, road, street, pavement, sidewalk,
        traffic light, signal
      - 🗑️ Sanitation: trash, garbage, waste, dump, litter, recycling, smell
      - 🌳 Parks & Recreation: park, tree, grass, playground, bench, garden
      - ⚡ Electricity/Power: power, electric, wire, outage, blackout,
        transformer, spark
      - 🏢 General Services: Fallback for general or unclassified reports

  - Smart Ticket Deduplication & Clustering (logic.group_complaints)

      - Employs TF-IDF vectorization to represent complaints in numerical space.
      - Computes Cosine Similarity between the new report and all existing
        issues in the database.
      - If similarity reaches or exceeds the threshold (0.30), the issue is
        linked to the existing ticket's group_id.
      - Aggregates multiple reports into a single card with report counts
        (count) and raw messages (reports).

  - Persistent Storage
    Backed by SQLite via Flask-SQLAlchemy, tracking ticket IDs, complaint text,
    timestamps, department tags, and cluster IDs.

🏗️ How It Works

[ Citizen Submits Issue via Form ]
                │
                ▼
        POST /submit (app.py)
                │
        ┌───────┴────────────────────────┐
        ▼                                ▼
[ logic.suggest_department ]    [ logic.group_complaints ]
  (Keyword Matching)              (TF-IDF + Cosine Similarity)
        │                                │
        ▼                                ▼
Assigns Department Tag         Matches Existing Group ID
        │                                │
        └───────┬────────────────────────┘
                ▼
  [ Save to SQLite Database ]
                │
                ▼
   GET / (Dashboard View)
Aggregates reports by group_id -> Renders ticket cards with report counts

🛠️ Tech Stack & Requirements

  - Language: Python 3.8+
  - Web Framework: Flask
  - ORM / Database: Flask-SQLAlchemy / SQLite
  - Machine Learning / NLP: scikit-learn (TfidfVectorizer, cosine_similarity)

🚀 Getting Started

1. Clone the Repository

git clone https://github.com/Hardikagg2008/The_Madhav_Matrix.git
cd The_Madhav_Matrix

2. Set Up a Virtual Environment (Recommended)

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

3. Install Dependencies

pip install Flask Flask-SQLAlchemy scikit-learn

💻 Running the Application

1. Run the Web Application

python3 app.py

The server will start locally in debug mode on port 5001: 👉 Open your browser
at: http://127.0.0.1:5001

2. Run the Logic Test Suite (CLI)

You can test the department suggestion and NLP grouping functions directly in
the terminal:

python3 logic.py

📁 Project Structure

The_Madhav_Matrix/
│
├── app.py                  # Flask web server, database models, and route controllers
├── logic.py                # NLP logic (TF-IDF vectorizer, cosine similarity, department routing)
├── instance/
│   └── streetsignal.db     # SQLite database (auto-generated at runtime)
├── templates/
│   └── index.html          # Frontend template displaying grouped ticket cards
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation

🗄️ Database Schema (Complaint)

| Column       | Type          | Description                                                         |
| :----------- | :------------ | :------------------------------------------------------------------ |
| `id`         | `Integer`     | Primary key                                                         |
| `text`       | `String(500)` | The complaint text submitted by the user                            |
| `created_at` | `DateTime`    | UTC timestamp of when the report was created                        |
| `group_id`   | `Integer`     | ID linking similar complaints into a single cluster                 |
| `department` | `String(100)` | Assigned department (e.g., *Water Department*, *Roads & Transport*) |

⚙️ Configuration & Tuning

You can adjust the clustering sensitivity directly inside logic.py:

# In logic.py -> group_complaints()
THRESHOLD = 0.3  # Default balanced threshold

# 0.5+ : Stricter matching (only groups near-identical phrasing)
# 0.2- : Looser matching (groups loosely related reports)

🤝 Contributing

1.  Fork the Project
2.  Create your Feature Branch (git checkout -b feature/NewFeature)
3.  Commit your Changes (git commit -m 'Add some NewFeature')
4.  Push to the Branch (git push origin feature/NewFeature)
5.  Open a Pull Request

👤 Author

Hardik

  - GitHub: @Hardikagg2008
  - Repository: Hardikagg2008/The_Madhav_Matrix
