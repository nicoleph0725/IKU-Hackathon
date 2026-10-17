# ☕ StudySpot

A web app to help students find study cafes.

- **backend/**: Flask (Python)
- **frontend/**: Vite + Tailwind CSS + Google Maps (vanilla JavaScript)

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv            # Windows: python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env, then add your MAP_KEY
flask run                        # http://localhost:5000
```

Activate the venv in every new terminal before running backend commands.

### Frontend

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

> **Mac:** if requests to the backend return 403, turn off System Settings → AirPlay Receiver (it uses port 5000).
