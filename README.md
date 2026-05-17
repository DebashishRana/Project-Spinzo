<div align="center">
<img width="1232" height="627" alt="SPINZO Banner" src="https://github.com/user-attachments/assets/2fb0beda-22b4-4d82-8c5f-8cbe2091d05c" />
# SPINZO
 
**Autonomous Agentic Cricket Intelligence System**
 
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)](#)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](#)
[![Bayesian Logic](https://img.shields.io/badge/Bayesian_Inference-FF6F00?style=for-the-badge&logoColor=white)](#)
[![Live Demo](https://img.shields.io/badge/Live_Demo-project--spinzo.onrender.com-brightgreen?style=for-the-badge)](https://project-spinzo.onrender.com)
 
> An AI reasoning engine that identifies any IPL player from a **161-player dataset** through adaptive yes/no questioning — converging on the correct player in an average of **5.3 questions**.
 
**Case Paper:** [project-spinzo.onrender.com](https://project-spinzo.onrender.com)
 
</div>
---



 
## Table of Contents
 
- [Overview](#overview)
- [How It Works](#how-it-works)
- [Core Features](#core-features)
- [System Architecture](#system-architecture)
- [AI Character Engine — Orbit](#ai-character-engine--orbit)
- [Audio & Visual System](#audio--visual-system)
- [API Reference](#api-reference)
- [Dataset](#dataset)
- [SPINZO vs Traditional Akinators](#spinzo-vs-traditional-akinators)
- [Enterprise Applications](#enterprise-applications)
- [Getting Started](#getting-started)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Hackathon Context](#hackathon-context)
---


<img width="1710" height="951" alt="Screenshot 2026-05-17 182321" src="https://github.com/user-attachments/assets/71b589a1-72fe-490a-85ca-057df366ecb3" />

<img width="1536" height="1024" alt="WhatsApp Image 2026-05-17 at 6 27 13 PM" src="https://github.com/user-attachments/assets/92f8b4a8-4bff-4a2c-a70a-37be2f57a03a" />
<img width="1288" height="1221" alt="WhatsApp Image 2026-05-17 at 6 25 48 PM" src="https://github.com/user-attachments/assets/952a0e39-e3cb-45b0-a401-4217c056ff1b" />


## Overview
 
Traditional guessing games rely on hardcoded question trees — they break under ambiguity, fail silently on contradictions, and hide all reasoning. SPINZO is fundamentally different.
 
**What SPINZO actually is:**
- An **entropy-driven diagnostic engine** — selects every question by calculating which one mathematically eliminates the most candidates
- A **live Bayesian reasoner** — updates probability distributions across all 161 players simultaneously with every answer
- A **contradiction-aware system** — detects logical conflicts, flags them visually, and recalibrates without crashing
- A **transparent AI** — all reasoning is displayed in real time via a Cognitive Dashboard
> The game framing is intentional — it makes AI behavior legible and engaging. The underlying architecture is a general-purpose probabilistic reasoner with direct applications in medical triage, IT diagnostics, and e-commerce recommendation.
 
---
 
## How It Works
 
```
┌─────────────────────────────────────────────────────────────────┐
│                     GAME SESSION FLOW                           │
├──────────────┬──────────────────┬──────────────────┬───────────┤
│  1. INIT     │  2. QUESTION     │  3. CONVERGE     │ 4. RESULT │
│              │     LOOP         │                  │           │
│ User clicks  │ User answers     │ Confidence > 90% │  Correct? │
│ Play →       │ Yes/No/Sometimes │ OR 10 questions  │           │
│              │ ↓                │ reached →        │  ✓ Victory│
│ POST /init   │ POST /answer     │ Final Guess      │  ✗ Failure│
│ ↓            │ ↓                │ Screen           │           │
│ UUID session │ Gemini re-ranks  │                  │ Reset →   │
│ created      │ all 161 players  │ Player name,     │ Home      │
│ ↓            │ ↓                │ team, confidence │           │
│ First        │ Confidence bar   │ & reasoning      │           │
│ question     │ updates          │ revealed         │           │
└──────────────┴──────────────────┴──────────────────┴───────────┘
```
 
### Step-by-Step Breakdown
 
**1. Session Initialization**
- User clicks Play → frontend calls `POST /api/game/init`
- Backend creates a UUID session and initializes empty answer history
- Gemini 2.5 Flash is invoked with the full 161-player dataset
- Returns: first question, confidence score, reaction string, thinking message — all as structured JSON
**2. Question Loop**
- Each answer (Yes / No / Sometimes) triggers `POST /api/game/answer`
- Full conversation history is passed back to Gemini every turn
- Gemini selects the next highest-entropy question and returns an updated confidence score
- Frontend updates: confidence bar, mascot image, AI character state
**3. Convergence & Final Guess**
- Triggered when: confidence exceeds **90%** OR question limit (**10**) is reached
- Gemini returns `"action": "guess"` with a structured prediction object:
  - Player name, team, emoji, confidence score, plain-language reasoning
- Player images are resolved via a **3-tier priority**:
  1. Real image URL from the API
  2. Initials avatar via `ui-avatars.com`
  3. Player emoji as final fallback
**4. Result & Reset**
- **Correct guess** → success screen + crowd wave animation + `celebrating` character state
- **Incorrect guess** → failure screen + `shocked` character state
- Either path resets session state and returns to the home screen
---
 
## Core Features
 
### Bayesian Probability Engine
 
```
Every player starts with equal prior probability
         ↓
User answers a question
         ↓
Bayes' theorem applied across ALL 161 players
         ↓
Players re-ranked by updated probability mass
         ↓
Confidence score drives:
  ├── Confidence bar color (blue → cyan → green → gold)
  ├── AI character emotional state
  └── Energy meter gradient
```
 
- Every player begins with equal prior probability
- Each answer applies Bayes' theorem across all 161 players simultaneously
- Confidence score reflects the probability mass concentrated on the top candidate
---
 
### Entropy-Based Question Selection
 
```
Before each question:
         ↓
Calculate Shannon entropy for every possible yes/no question
         ↓
Select the question that MINIMIZES expected remaining entropy
(worst-case — regardless of how user answers)
         ↓
Result: Narrows the field most efficiently
         ↓
Average convergence: 5.3 questions (vs. 8–10 for scripted trees)
```
 
---
 
### Contradiction Detection — The Akinator Trap
 
```
User answers "Yes" to fast bowling
         ↓
User later confirms spin bowling
         ↓
Contradiction Agent detects logical conflict
         ↓
Flagged visually in the UI
         ↓
Confidence recalibrated using weighted decay
(not ignored, not a crash)
```
 
- Full answer history is passed to Gemini on every single turn
- Conflict detection is embedded directly in the system prompt
- System never crashes or silently ignores inconsistencies
---
 
### Cognitive Dashboard
 
Live panel displayed alongside every question — showing:
 
| Panel Element | What It Shows |
|---|---|
| **Top candidate players** | Probability percentages updating after each answer |
| **Question rationale** | Plain English explanation (e.g. "Asking about captaincy to eliminate 68 non-captains") |
| **Confidence trajectory** | Animated progress bar with color-coded thresholds |
 
---
 
### Dynamic Persona via Gemini NLP
 
- `reaction` and `thinkingMsg` strings are **generated by Gemini** per call — not pulled from a static pool
- Tone adapts continuously to Bayesian state:
  - Flat probability distribution → genuine uncertainty in language
  - One player crosses 80% → language shifts to near-certainty
- **10 distinct character states** — each with unique SVG expressions, glow colors, and particle effects
---
 
### Post-Game Intelligence Report
 
After the game ends, SPINZO generates a reasoning trace identifying:
 
- **The Pivot Question** — the exact answer that caused one player's probability to spike decisively
- **Plain-English explanation** — e.g. *"When you confirmed left-arm spinner, Jadeja's probability moved from 12% to 89%."*
---
 
## System Architecture
 
<div align="center">
<img width="1080" alt="SPINZO System Architecture" src="https://github.com/user-attachments/assets/be8ff574-481e-4687-9914-404e875ee776"/>
</div>
### Multi-Agent AI System
 
Four specialized reasoning agents interact through shared session state managed by FastAPI:
 
| Agent | Responsibility | Implementation |
|---|---|---|
| **Strategist Agent** | Selects the next highest-entropy question | Gemini prompt layer — evaluates candidate questions against current probability state |
| **Probability Agent** | Maintains and updates Bayesian confidence array per answer | Backend session state; confidence score returned in every API response |
| **Contradiction Agent** | Detects logical conflicts across the full answer history | Full history passed to Gemini every turn; conflict detection embedded in system prompt |
| **Explainability Agent** | Translates probability state into human-readable rationale | Gemini `reaction` and `thinkingMsg` fields; rendered live on the frontend |
 
---
 
### Session Management
 
Each session (keyed by UUID, stored in-memory) contains:
 
- Full ordered answer history as `[{ question, answer }]` pairs
- Current question text and question number
- Session status: `active` or `finished`
- Final prediction object (once the game concludes)
> The entire history is passed to Gemini on every turn — giving the model full context and contradiction-detection capability without additional state management logic.
 
---
 
### Frontend State Machine
 
```
┌──────────┐    Play     ┌──────────┐   Answer   ┌───────────┐
│   HOME   │ ─────────► │ GAMEPLAY │ ──────────► │ FINALGUESS│
└──────────┘             └──────────┘             └───────────┘
                                                       │
                                    ┌──────────────────┤
                                    │                  │
                              ✓ Correct           ✗ Incorrect
                                    │                  │
                             ┌──────▼──┐        ┌──────▼──┐
                             │ SUCCESS │        │ FAILURE │
                             └─────────┘        └─────────┘
                                    │                  │
                                    └──── Reset ───────┘
                                               │
                                          ┌────▼─────┐
                                          │   HOME   │
                                          └──────────┘
```
 
**UX guards during API calls:**
- Answer buttons disabled (`pointerEvents: none`, `opacity: 0.3`) to prevent double-submission
- Loading overlay with rotating thinking indicator shown while the API call is in-flight
- Screen transitions handled by `showPage()` with CSS slide-up entry animations
---
 
## AI Character Engine — Orbit
 
Orbit is a fully programmatic SVG entity with **10 distinct emotional states**. Every state transition directly modifies:
 
- SVG path attributes (brow curvature, eye radius, mouth arc)
- Glow colors and energy bar gradients
- Ambient particle count and color
**State transitions are triggered by:**
- Confidence score returned by the API
- User's answer (Yes, No, Sometimes)
- Game lifecycle events (start, guess, correct, incorrect)
### State Definitions
 
| State | Eye Color | Status Text | Trigger Condition |
|---|---|---|---|
| `idle` | `#00e5ff` | ORBIT ONLINE | Game start, waiting for input |
| `thinking` | `#b57bee` | SCANNING DATA | API call in progress |
| `focused` | `#40c8ff` | ANALYZING | Answer received, next question loading |
| `confident` | `#00e5ff` | NARROWING DOWN | Confidence 50–75% |
| `surprised` | `#ffaa00` | RECALCULATING | Unexpected answer pattern |
| `unsure` | `#cccc00` | AMBIGUOUS DATA | Flat probability distribution |
| `confused` | `#ff6666` | RECONFIGURING | Contradiction detected |
| `smug` | `#00ff78` | I KNOW THIS | Confidence > 75% |
| `guessing` | `#ffd700` | MIND READ! | Final guess triggered |
| `celebrating` | `#00ff78` | VICTORY! | Correct guess confirmed |
| `shocked` | `#ff4444` | IMPOSSIBLE... | Wrong guess confirmed |
 
**Speech bubble behavior:**
- Lines selected randomly from curated arrays per state
- Displayed for **2.8 seconds** before fading
- Particle count scales with state intensity: 2 orbs at idle → 8 at celebrating
---
 
## Audio & Visual System
 
### Sound Engine — Web Audio API
 
> All game audio is synthesized in real time. There are no pre-recorded sound effect files — every sound is constructed programmatically from oscillators, gain envelopes, and filters.
 
| Event | Synthesis Method |
|---|---|
| Game start (bat hit) | Short noise burst with exponential decay |
| Thinking | Low-frequency sine wave pulse |
| Answer Yes | Two ascending sine tones (440Hz → 550Hz) with 60ms offset |
| Answer No | Two descending sawtooth tones (330Hz → 260Hz) through lowpass filter |
| Reveal | Multi-oscillator chord with decay tail |
| Victory | Ascending four-note sine sequence |
| Failure | Descending four-note sawtooth sequence through lowpass filter |
| UI click | Short 880Hz sine blip, 60ms duration |
 
**Background music:**
- IPL 2025 theme BGM plays on loop
- Custom player widget: track name, status, animated equalizer bars, volume slider
- First interaction (click or touchend) triggers auto-play (browser autoplay compliance)
- Fade in/out handled by interval-based volume stepping
- All SFX globally toggle-able via top-right button
---
 
### Visual Effects
 
Stadium atmosphere built from layered CSS animations:
 
| Effect | Implementation | Details |
|---|---|---|
| Stars | 40 randomized `div` elements | Variable size (0.5–2.5px), random position and animation duration |
| Ambient particles | 8 floating orbs | Random IPL palette colors (cyan, gold, blue, purple, white); 8–20s float cycle |
| Floodlights | 4 radial gradient elements | Positioned at corners; slow pulse with staggered 1.5s delays |
| Lasers | CSS-animated diagonal beams | Sweep across background layer |
| Crowd wave | Full-width overlay | Activates on correct guess; 2.1-second sweep animation |
| Screen flash | Full-viewport radial gradient | Body scales to 1.02x for physical impact feel |
| Pointer parallax | `pointermove` + `requestAnimationFrame` | Home screen tracks mouse via `--pointer-x` / `--pointer-y` CSS variables |
| Button ripple | Dynamically injected `span.ripple-fx` | Positioned at cursor intersection; expands and fades over 560ms |
| Confidence bar | CSS gradient with JS width update | Color shifts: deep blue → cyan → green → gold |
 
**Performance optimizations (via `optimize.py`):**
- Stars reduced from 130 → **40**
- Particles reduced from 22 → **8**
- `will-change: transform, opacity` on all animated elements
- Result: stable **60fps** on mid-range devices
---
 
## API Reference
 
All requests and responses use JSON. Swagger UI available at `http://localhost:8000/docs` when running locally.
 
---
 
### `POST /api/game/init`
 
Starts a new game session. No request body required.
 
**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "Is your player a batsman?",
  "question_number": 1,
  "confidence": 10,
  "reaction": "The oracle awakens...",
  "thinkingMsg": "Consulting IPL archives..."
}
```
 
---
 
### `POST /api/game/answer`
 
Submits an answer to the current question. Returns either the next question or a final prediction.
 
**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Yes"
}
```
 
**Response — next question:**
```json
{
  "action": "ask",
  "question": "Has your player played for Mumbai Indians?",
  "question_number": 2,
  "confidence": 35,
  "reaction": "Interesting...",
  "thinkingMsg": "Narrowing the field..."
}
```
 
**Response — final guess:**
```json
{
  "action": "guess",
  "confidence": 94,
  "reaction": "I have seen enough!",
  "thinkingMsg": "The Oracle has spoken...",
  "prediction": {
    "player_name": "MS Dhoni",
    "player_team": "Chennai Super Kings",
    "player_emoji": "🚁",
    "confidence": 94,
    "guess_reason": "Your player is a wicketkeeper for CSK known for finishing matches under pressure."
  }
}
```
 
---
 
### Additional Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/game/{session_id}/state` | Full session state: history, current question, status |
| `GET` | `/api/game/{session_id}/history` | Ordered list of all `{ question, answer }` pairs |
| `GET` | `/api/game/{session_id}/prediction` | Final prediction object (or `null` if still active) |
 
---
 
### Error Handling
 
- `404` — `session_id` not found in active session store
- `500` — `GEMINI_API_KEY` environment variable missing
- **Frontend behavior on error:** displays connection error in question area, transitions Orbit to `confused` state
---
 
## Dataset
 
161-player elite IPL dataset covering both active and retired players across all IPL franchises (including legacy teams). Loaded once at backend startup from `players.json` and held in memory for the lifetime of the process.
 
### Standard Fields
 
| Field | Type | Description |
|---|---|---|
| `name` | string | Full player name |
| `team` | string | Current or last IPL franchise |
| `role` | string | Batsman, Bowler, Wicketkeeper, All-Rounder |
| `status` | string | Active or Retired |
| `emoji` | string | Visual shorthand used on guess screen |
| `hints` | string[3] | Three human-readable descriptors used as Gemini NLP context |
 
### Semantic Dimensions (for inference)
 
| Dimension | Description | High Examples |
|---|---|---|
| **Aggression** | Emotional intensity and playing style | Virat Kohli, Andre Russell |
| **Leadership** | Captaincy history and on-field presence | MS Dhoni, Pat Cummins |
| **Clutch Ability** | Performance under pressure | Jasprit Bumrah, Hardik Pandya |
| **Crowd Aura** | Fan perception and cultural impact | Rinku Singh, AB de Villiers |
 
> Players exist in a **semantic vector space** — enabling inference on characteristics that raw statistics alone cannot express.
 
---
 
## SPINZO vs Traditional Akinators
 
| Capability | Standard Akinator | SPINZO |
|---|---|---|
| Question selection | Pre-written static tree | Entropy-optimized per turn by Gemini |
| Ambiguous answers | Binary failure | Probabilistic degradation (Sometimes = partial update) |
| Contradictions | Silent failure or full derailment | Detection, UI flagging, recalibration |
| Reasoning visibility | Hidden black box | Live Cognitive Dashboard |
| AI persona | Fixed neutral chatbot | 10-state dynamic SVG character |
| End state | Shows name | Post-Game Intelligence Report with Pivot Question |
| Dataset depth | Shallow attributes | 161-player semantic vector space |
| Average questions to converge | 8–12 | **5.3** |
| Retired player support | Often excluded | Yes — all 161 players |
 
---
 
## Enterprise Applications
 
The three core components — **entropy-based question selection**, **Bayesian state management**, and **contradiction resolution** — are domain-agnostic. Only the JSON dataset changes per domain.
 
```
SPINZO Core Engine
        │
        ├── 🏏 IPL Cricket (current)
        │       └── 161-player semantic dataset
        │
        ├── 🏥 Medical Triage
        │       └── Symptom-condition mapping dataset
        │       └── Narrows diagnoses with fewest questions
        │       └── Flags contradictory symptom reports
        │
        ├── 💻 IT Helpdesk Automation
        │       └── Error types and root causes dataset
        │       └── Diagnoses server/app/network issues
        │       └── No scripted question tree required
        │
        └── 🛒 E-Commerce Product Discovery
                └── SKU and product attributes dataset
                └── Converges on personalized recommendation
                └── 4–6 natural language questions
```
 
---
 
## Getting Started
 
### Prerequisites
 
- Python 3.11+
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Node.js (for serving the frontend with `npx serve`)
---
 
### Installation
 
**1. Clone the repository**
```bash
git clone https://github.com/your-username/spinzo.git
cd spinzo
```
 
**2. Configure environment**
 
Create a `.env` file in the `backend/` directory:
```
GEMINI_API_KEY=your_google_gemini_api_key_here
```
 
> The key is read at startup via `os.environ.get("GEMINI_API_KEY")`. If missing, the backend logs a warning and all game requests return a 500 error.
 
**3. Start the backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
- API available at: `http://localhost:8000`
- Swagger UI at: `http://localhost:8000/docs`
**4. Start the frontend**
```bash
cd frontend
npx serve .
```
- Update the `BACKEND_URL` constant at the top of `script.js` if your backend runs on a different host or port (defaults to `http://localhost:8000`)
**5. Verify the setup**
- Click Play — if the AI character loads and a question appears, setup is complete
- Red connection error in the question area → backend not reachable or API key missing
---
 
## Tech Stack
 
| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Vanilla HTML, CSS, JavaScript | Multi-screen SPA with no framework dependency |
| Styling | Custom CSS (1,475 lines) | Full animation system, theming, responsive layout |
| Audio | Web Audio API | Real-time procedural sound synthesis (no audio files for SFX) |
| Backend | Python 3.11+, FastAPI, Uvicorn | REST API, session management, Gemini integration |
| AI / NLP | Google Gemini 2.5 Flash | Question generation, confidence scoring, persona generation |
| Inference | Bayesian Probability Engine | Per-answer player probability updates |
| Question Selection | Shannon Entropy Optimization | Maximum information gain per question |
| Dataset | 161-player IPL Semantic Dataset | Player attributes and semantic dimensions |
| Avatars | ui-avatars.com | Initials-based player avatar generation |
| Deployment | Render | Backend and static frontend hosting |
| Asset Optimization | `optimize.py` (Python) | Base64 CSS extraction, particle count reduction |
 
**Python dependencies (`requirements.txt`):**
```
fastapi
uvicorn
google-genai
pydantic
```
 
---
 
## Project Structure
 
```
spinzo/
├── backend/
│   ├── main.py              # FastAPI app — sessions, Gemini integration, all endpoints
│   ├── players.json         # 161-player IPL semantic dataset
│   ├── requirements.txt     # Python dependencies
│   └── optimize.py          # Asset optimization — CSS base64 extraction, particle tuning
│
├── frontend/
│   ├── index.html           # Full SPA — markup for all five screens + how-to-play modal
│   ├── script.js            # Game state machine, API calls, CharEngine, SFX, visual effects
│   ├── style.css            # Complete animation and theme system
│   └── assets/
│       ├── audio/
│       │   └── bgm.mp3      # IPL 2025 theme — background music loop
│       └── images/
│           ├── logo.png     # SPINZO wordmark
│           └── stadium-bg.jpg  # Stadium background
│
└── README.md
```
 
**Key file sizes:**
 
| File | Lines | Contents |
|---|---|---|
| `script.js` | 1,025 | Game state machine, API integration, CharEngine, SFX, all visual effects |
| `style.css` | 1,475 | Stars, particles, lasers, floodlights, crowd wave, screen flash, ripple, all screen layouts |
| `index.html` | 389 | Five screens (home, gameplay, finalguess, success, failure) + how-to-play modal |
 
---
 
## Hackathon Context
 
SPINZO was built for the **Google Developer Groups (GDG) Hackathon**.
 
**The core contribution — Visible Machine Cognition:**
 
```
Traditional AI Systems          SPINZO
─────────────────────          ──────────────────────────────────
Questions → [Black Box]        Questions → [Transparent Reasoner]
              ↓                              ↓
            Answer             Live probability updates
                               Contradiction flagging
                               Entropy-based question choice
                               Plain-English rationale
                               Pivot question identified
                                             ↓
                               Answer + Full Reasoning Trace
```
 
- The cricket game is the **interface**
- The entropy-driven diagnostic engine is the **actual contribution**
- Traditional Akinator systems show you questions and an answer — SPINZO shows you the math, explains each decision, catches your mistakes, and tells you exactly **when and why** it figured you out
---
 
<div align="center">
Built with Google Gemini &nbsp;|&nbsp; [project-spinzo.onrender.com](https://project-spinzo.onrender.com)
 
</div>
