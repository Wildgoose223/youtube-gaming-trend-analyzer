# Project2026 – Gaming Trend Analyzer

Project2026 is a Python-based analytics project that tracks trending gaming content on YouTube and transforms it into a live gaming trend dashboard.

The system:
- Pulls trending gaming videos from YouTube
- Detects which games are currently trending
- Enriches game data using the RAWG API
- Stores historical trend data in PostgreSQL
- Generates a dashboard showing game momentum, metadata, and analytics

This project combines:
- ETL pipelines
- API integration
- PostgreSQL
- dashboard generation
- historical trend analysis

---

# Dashboard Features

- Top 10 trending games
- Trend movement tracking
- Platform detection
- Genre metadata
- RAWG ratings
- Metacritic scores
- Historical trend snapshots
- Interactive charts
- Game artwork/background images

---

## Live Dashboard

View the live dashboard here:

https://wildgoose223.github.io/youtube-gaming-trend-analyzer/

# Example Analytics Output

```text
Top 10 Trending Games Right Now:

Roblox — 4 videos (16.00%)
Trend: Stable
Platforms: PC, PlayStation 5, Xbox, iOS, Android
Genres: Adventure, Action, Multiplayer

Rust — 2 videos (8.00%)
Trend: Stable
Platforms: PC, Xbox One, PlayStation 4
Genres: Survival, Shooter, Indie
Metacritic: 66
```

---

# Example Architecture

```text
YouTube API
    ↓
Video Title Collection
    ↓
Custom Alias Matching Engine
    ↓
RAWG Metadata Enrichment
    ↓
PostgreSQL Storage
    ↓
Dashboard Generator
    ↓
HTML Analytics Dashboard
```

---

# Tech Stack

## Languages
- Python
- SQL
- HTML/CSS

## APIs
- YouTube Data API v3
- RAWG Video Game Database API

## Database
- PostgreSQL

## Libraries
- psycopg2
- requests
- google-api-python-client
- python-dotenv

## Visualization
- Chart.js

---

# Current Features

## Trend Collection
- Pulls trending gaming videos from YouTube
- Detects games using alias matching
- Tracks mentions and trend percentages

## Metadata Enrichment
- RAWG API integration
- Platform detection
- Genre lookup
- Ratings and Metacritic scores
- Game artwork support

## Historical Analytics
- Stores historical trend snapshots
- Compares previous runs
- Detects trend movement over time

## Dashboard System
- Generates a responsive HTML dashboard
- Displays Top 10 trending games
- Includes interactive chart visualizations
- Displays metadata cards for each game

---

# Folder Structure

```text
Project2026/
│
├── dashboard_generator.py
├── youtube_trends_to_db.py
├── dashboard.html
├── build_game_library_from_rawg.py
├── sync_game_library.py
├── game_library.py
├── run_log.txt
├── .env
├── .gitignore
├── Images/
│
└── README.md
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/Wildgoose223/youtube-gaming-trend-analyzer.git
cd youtube-gaming-trend-analyzer
```

---

## 2. Install Dependencies

```bash
pip install psycopg2 requests python-dotenv google-api-python-client
```

---

## 3. Create PostgreSQL Database

Create a PostgreSQL database:

```sql
CREATE DATABASE YouTube_Data;
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
YOUTUBE_API_KEY=your_youtube_api_key
RAWG_API_KEY=your_rawg_api_key
DB_HOST=localhost
DB_NAME=YouTube_Data
DB_USER=postgres
DB_PASSWORD=your_password
```

---

# Database Tables

This project uses PostgreSQL tables for:

- games
- game_aliases
- trending_games
- unknown_terms

The `trending_games` table stores:
- trend snapshots
- game metadata
- trend percentages
- historical movement data

---

# Running The Project

## Pull Trending Data

```bash
python youtube_trends_to_db.py
```

---

## Generate Dashboard

```bash
python dashboard_generator.py
```

---

## Open Dashboard

Open:

```text
dashboard.html
```

in your browser.

---

# Future Improvements

- Platform-specific trend filtering
- Indie vs AAA classification
- Historical sparkline trend charts
- Momentum scoring
- Daily trend summaries
- Azure deployment
- Live hosted dashboard
- AI-assisted trend analysis
- Twitch integration
- Steam integration
- Sentiment analysis from comments

---

# Security

This project uses `.env` environment variable handling to securely manage:
- API keys
- database credentials
- configuration settings

Secrets are excluded from Git tracking using `.gitignore`.

---

# Why This Project Matters

Project2026 demonstrates:
- ETL pipeline development
- API integration
- database design
- metadata enrichment
- dashboard generation
- historical trend analytics
- secure configuration handling
- real-world debugging and system integration

This project was built as part of a transition into data analytics, cloud technologies, and systems-oriented engineering work.

---

# Author

Samuel O'Brien

GitHub:
https://github.com/Wildgoose223
