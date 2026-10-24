# 🚨 The Madhav Matrix — StreetSignal

> **Hackathon Project** | AI-Powered Civic Complaint Intelligence Platform

---

## 📌 Topic

**Smart City Complaint Aggregation, Routing, and Citizen-to-Municipal Action Platform**

Transforming how citizens report city problems — grouping duplicate complaints intelligently with TF-IDF, routing them to the right department automatically, enforcing a **72-Hour Municipal Resolution SLA**, and connecting citizens directly to municipal authorities.

---

## 📖 Description

**StreetSignal** (built on *The Madhav Matrix*) is a complete dual-portal civic tech platform:

1. **Citizen Portal (`/citizen`)**:
   - Citizens register and log in to report civic problems in their neighborhoods.
   - Requires verified **Photo Evidence** and **GPS Geolocation**.
   - Supports **18+ languages** (with automatic English translation) and **Voice Input (Mic)**.
   - Citizens can track the live status of their submitted complaints (In Progress, Critical, or Resolved).

2. **Municipal Authority Portal (`/admin`)**:
   - Municipal staff access department-specific queues (Water, Roads, Sanitation, Parks, Electricity, General Services).
   - Full audit logs of citizen reports, timestamps, photos, and exact map locations.
   - Municipal officers mark tickets as **Resolved** (recording verified completion timestamps) or Reopen them.

3. **🚨 72-Hour Auto-Escalation Engine**:
   - Any complaint not resolved within **72 hours** is automatically escalated to **CRITICAL priority**.
   - Flagged with `⚠️ OVERDUE (>72h) - RESOLVE FIRST` and moved to the top of the municipal action queue so authorities resolve it immediately.

No duplicate noise. No lost reports. No language barriers. Guaranteed civic accountability.

---

## ✨ Features

| Feature | Description |
|---|---|
| 👥 Dual-Portal Access | Separate portals: Citizen (`/citizen`) for reporting and Municipal Admin (`/admin`) for resolution |
| 🚨 72h SLA Auto-Escalation | Problems unsolved under 72h auto-escalate to Critical & sort to the top of the queue |
| 🤖 AI Duplicate Grouping | TF-IDF vectorization + Cosine Similarity groups duplicate citizen reports |
| 📸 Mandatory Photo Proof | Drag-and-drop or upload photo with perceptual hashing (`pHash`) to prevent duplicate spam |
| 📍 Mandatory GPS Location | Captures coordinates and reverse-geocodes to street address via OpenStreetMap |
| 🌐 18 Languages | Multi-language dropdown with real-time translation to English before AI processing |
| 🎤 Voice Input (Mic) | Web Speech API allows citizens to speak their complaint in any language |
| 🏛️ Auto Department Routing | Keyword NLP routes to Water, Roads, Sanitation, Parks, Electricity |
| ✅ Municipal Resolution | Authorized officers mark issues resolved with live status sync back to the citizen |
| 🔒 Submit Lockout | Submit button locked until both photo and location are provided |

---

## 🧠 How The AI Works

```
Citizen submits complaint (Text / Mic + Photo + GPS)
        │
        ▼
  [Translate to English]   ← deep-translator (Google Translate API)
        │
        ▼
  [Check Duplicate Photo]  ← perceptual hash (pHash) hamming distance
        │
        ▼
  [Check Duplicate Text]   ← TF-IDF similarity ≥ 0.65 (alerts user if already registered)
        │
        ▼
  [TF-IDF Grouping]        ← score ≥ 0.30 links report to existing municipal ticket
        │
        ▼
  [Department Routing]     ← routes to Water, Roads, Sanitation, Parks, Electricity
        │
        ▼
  Saved to Database (Linked to Citizen Profile)
        │
        ▼
  [72-Hour SLA Monitor]    ← Unresolved after 72h? Auto-escalates to CRITICAL to resolve first!
        │
        ▼
  Municipal Officer marks RESOLVED → Citizen sees live green resolution badge!
```

---

## 🔑 Demo & Test Credentials

| Role | Portal URL | Credentials |
|---|---|---|
| **Municipal Admin** | `http://127.0.0.1:5002/admin` | **Email**: `admin@streetsignal.com`<br/>**Password**: `admin123` |
| **Citizen** | `http://127.0.0.1:5002/citizen` | Register any new account at `/register` |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask, Flask-SQLAlchemy |
| **Authentication** | Werkzeug Security (salted password hashing), Session-based RBAC |
| **Database** | SQLite (`streetsignal.db`) |
| **AI / NLP** | scikit-learn (TF-IDF Vectorizer, Cosine Similarity) |
| **Image Verification** | Pillow, ImageHash (perceptual pHash) |
| **Translation** | deep-translator (Google Translate) |
| **Geocoding** | OpenStreetMap Nominatim API (free, no key required) |
| **Voice Input** | Web Speech API (browser-native speech-to-text) |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JavaScript |

---

## 🚀 Getting Started

### 1. Set up virtual environment & install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5002
```

---

## 🌐 Supported Languages

English · Hindi · Tamil · Telugu · Bengali · Marathi · Gujarati · Punjabi · Urdu · Spanish · French · Arabic · German · Chinese · Japanese · Russian · Portuguese · Korean

---

## 🏆 Built For

**Hackathon** — Smart Cities, Civic Tech & AI Governance Track

*The Madhav Matrix team — building technology that makes cities listen and act.*
