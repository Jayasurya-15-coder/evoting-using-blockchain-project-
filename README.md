# 🔐 Secure E-Voting System Using Blockchain Technology

> **CSE Mini Project | Academic Year 2024**  
> A custom blockchain-based digital voting platform built with Python Flask, SQLite, and SHA-256 hashing.

---

## 📋 Project Overview

This system implements a tamper-proof electronic voting application where every vote is stored as a cryptographic block in a custom blockchain. Voter identities are hashed for privacy, and the chain can be verified at any time to detect tampering.

---

## 🗂️ Project Structure

```
evoting/
├── app.py              # Flask routes, session management, business logic
├── blockchain.py       # Custom blockchain & Block class (SHA-256)
├── database.py         # SQLite initialization, helpers, sample data
├── requirements.txt    # Python dependencies
├── evoting.db          # SQLite database (auto-created on first run)
│
├── templates/
│   ├── base.html           # Shared layout with navbar & flash messages
│   ├── home.html           # Landing page
│   ├── admin_login.html    # Admin login form
│   ├── voter_login.html    # Voter login form
│   ├── admin_dashboard.html# Admin control panel
│   ├── candidates.html     # Add/view candidates
│   ├── voters.html         # Voter registry
│   ├── voting.html         # Ballot page
│   ├── confirmation.html   # Post-vote confirmation with block hash
│   ├── results.html        # Chart.js bar chart + vote counts
│   └── blockchain.html     # Block explorer with hash search
│
└── static/
    ├── css/style.css   # Dark tech UI with violet accent
    └── js/main.js      # Animations, counter effects, toast helpers
```

---

## ⚙️ Setup & Run Instructions

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### 2. Install Dependencies
```bash
cd evoting
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000**

---

## 🔑 Default Credentials

### Admin
| Username | Password  |
|----------|-----------|
| admin    | admin123  |

### Sample Voters (10 pre-loaded)
| Voter ID | Password |
|----------|----------|
| V001     | pass001  |
| V002     | pass002  |
| V003     | pass003  |
| ...      | ...      |
| V010     | pass010  |

### Sample Candidates (4 pre-loaded)
- Amit Shah
- Neha Gupta
- Rohan Das
- Sunita Rao

---

## 🧱 Blockchain Implementation

Each vote creates a new block containing:

| Field          | Description                                         |
|----------------|-----------------------------------------------------|
| `block_index`  | Sequential position in the chain                    |
| `timestamp`    | Date and time of vote                               |
| `voter_id_hash`| SHA-256 hash of voter ID (privacy preserved)        |
| `candidate_id` | ID of the candidate voted for                       |
| `previous_hash`| Hash of the preceding block (creates the chain)     |
| `current_hash` | SHA-256 hash of all above fields combined           |

**Chain Validation** checks:
1. Each block's current hash matches a fresh recompute of its data
2. Each block's previous_hash matches the prior block's current_hash

---

## 🗃️ Database Tables

| Table               | Purpose                                      |
|---------------------|----------------------------------------------|
| `voters`            | Voter ID, name, hashed password, voted flag  |
| `candidates`        | Candidate ID and name                        |
| `votes`             | Vote records (candidate + timestamp only)    |
| `blockchain`        | Persisted blockchain blocks                  |
| `election_settings` | Election active/inactive state               |
| `admins`            | Admin credentials                            |

---

## 🛡️ Security Features

- **Password hashing** — All passwords stored as SHA-256 hashes
- **One-vote enforcement** — DB flag + server-side check before recording
- **Voter ID hashing** — Original IDs never stored in the blockchain
- **Session management** — Flask sessions with secret key
- **Input validation** — Server-side validation on all form inputs
- **Blockchain integrity** — Hash linkage detects any data tampering

---

## 🎯 Key Features

- ✅ Admin can start/end election
- ✅ Admin can add/remove candidates
- ✅ Voters can cast one vote each
- ✅ Blockchain explorer with all blocks
- ✅ Hash search in blockchain
- ✅ Chain validity verification (REST API + UI)
- ✅ Live results with Chart.js bar chart
- ✅ Winner declaration
- ✅ JSON export of results
- ✅ Block hash copy & confirmation page
- ✅ Voter search by name/ID
- ✅ Election statistics dashboard
- ✅ Responsive mobile-friendly design

---

## 📚 Technologies Used

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | HTML5, CSS3, Bootstrap 5.3, Chart.js |
| Backend    | Python 3, Flask 3.0               |
| Database   | SQLite (via Python sqlite3)        |
| Blockchain | Custom SHA-256 implementation      |
| Icons      | Bootstrap Icons 1.11              |

---

## 🚀 How to Demo (Evaluator Guide)

1. Start app → visit `http://127.0.0.1:5000`
2. Login as **admin** → Start Election
3. Open incognito or another browser → Login as **V001 / pass001**
4. Cast a vote → see the block hash confirmation
5. Try voting again → blocked ("already voted")
6. Back in admin → View Blockchain → Verify Chain
7. View Results → see bar chart and winner

---

*Developed as a CSE Mini Project — 2026git branch -M main
*
"# blockchian-project"  "# blockchian-project" 
"# blockchian-project" 
"# blockchian-project" 
