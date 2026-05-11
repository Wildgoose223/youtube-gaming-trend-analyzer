import os
import json
from datetime import datetime

import psycopg2
from dotenv import load_dotenv


# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()


# =========================
# CONFIG
# =========================
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

if not DB_CONFIG["password"]:
    raise ValueError("Missing DB_PASSWORD in .env file")


# =========================
# FETCH DASHBOARD DATA
# =========================
def fetch_dashboard_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT run_time
        FROM trending_games
        ORDER BY run_time DESC
        LIMIT 2;
    """)

    runs = cursor.fetchall()

    if not runs:
        cursor.close()
        conn.close()
        return []

    current_run = runs[0][0]
    previous_run = runs[1][0] if len(runs) > 1 else None

    cursor.execute("""
        SELECT
            current.game_name,
            current.mentions,
            current.total_videos,
            current.percentage,
            COALESCE(previous.mentions, 0) AS previous_mentions,
            current.mentions - COALESCE(previous.mentions, 0) AS change,
            current.rawg_name,
            current.released,
            current.rating,
            current.metacritic,
            current.platforms,
            current.genres,
            current.background_image
        FROM trending_games current
        LEFT JOIN trending_games previous
            ON current.game_name = previous.game_name
            AND previous.run_time = %s
        WHERE current.run_time = %s
        ORDER BY current.mentions DESC
        LIMIT 10;
    """, (previous_run, current_run))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    dashboard_data = []

    for row in rows:
        (
            game_name,
            mentions,
            total_videos,
            percentage,
            previous_mentions,
            change,
            rawg_name,
            released,
            rating,
            metacritic,
            platforms,
            genres,
            background_image
        ) = row

        if change > 0:
            trend_label = "Trending Up"
        elif change < 0:
            trend_label = "Declining"
        else:
            trend_label = "Stable"

        dashboard_data.append({
            "game_name": game_name,
            "display_name": rawg_name or game_name,
            "mentions": mentions,
            "total_videos": total_videos,
            "percentage": percentage,
            "previous_mentions": previous_mentions,
            "change": change,
            "trend_label": trend_label,
            "released": str(released) if released else "Unknown",
            "rating": rating if rating is not None else "N/A",
            "metacritic": metacritic if metacritic is not None else "N/A",
            "platforms": platforms or "Unknown",
            "genres": genres or "Unknown",
            "background_image": background_image or ""
        })

    return dashboard_data


# =========================
# GENERATE HTML
# =========================
def generate_dashboard():
    data = fetch_dashboard_data()

    chart_labels = [item["display_name"] for item in data]
    chart_values = [item["mentions"] for item in data]

    cards_html = ""

    for rank, item in enumerate(data, start=1):
        image_html = ""

        if item["background_image"]:
            image_html = f"""
            <img class="game-image" src="{item["background_image"]}" alt="{item["display_name"]}">
            """

        cards_html += f"""
        <div class="game-card">
            {image_html}

            <div class="game-content">
                <div class="rank">#{rank}</div>

                <h2>{item["display_name"]}</h2>

                <p class="subtitle">
                    Matched as: <strong>{item["game_name"]}</strong>
                </p>

                <div class="stats">
                    <div>
                        <span class="stat-value">{item["mentions"]}</span>
                        <span class="stat-label">Mentions</span>
                    </div>

                    <div>
                        <span class="stat-value">{item["percentage"]}%</span>
                        <span class="stat-label">Share</span>
                    </div>

                    <div>
                        <span class="stat-value">{item["change"]}</span>
                        <span class="stat-label">Change</span>
                    </div>
                </div>

                <p class="trend {item["trend_label"].replace(" ", "-").lower()}">
                    {item["trend_label"]}
                </p>

                <div class="metadata">
                    <p><strong>Platforms:</strong> {item["platforms"]}</p>
                    <p><strong>Genres:</strong> {item["genres"]}</p>
                    <p><strong>Released:</strong> {item["released"]}</p>
                    <p><strong>RAWG Rating:</strong> {item["rating"]}</p>
                    <p><strong>Metacritic:</strong> {item["metacritic"]}</p>
                </div>
            </div>
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Project2026 Gaming Trend Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
        }}

        header {{
            padding: 32px;
            text-align: center;
            background: #111827;
            border-bottom: 1px solid #334155;
        }}

        header h1 {{
            margin: 0;
            font-size: 36px;
        }}

        header p {{
            color: #94a3b8;
            margin-top: 8px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px;
        }}

        .chart-section {{
            background: #111827;
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 32px;
            border: 1px solid #334155;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));
            gap: 24px;
        }}

        .game-card {{
            background: #111827;
            border: 1px solid #334155;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
        }}

        .game-image {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
        }}

        .game-content {{
            padding: 20px;
        }}

        .rank {{
            color: #38bdf8;
            font-weight: bold;
            font-size: 18px;
        }}

        h2 {{
            margin: 8px 0;
            font-size: 24px;
        }}

        .subtitle {{
            color: #94a3b8;
            font-size: 14px;
        }}

        .stats {{
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
            gap: 12px;
        }}

        .stats div {{
            background: #1e293b;
            padding: 12px;
            border-radius: 12px;
            text-align: center;
            flex: 1;
        }}

        .stat-value {{
            display: block;
            font-size: 22px;
            font-weight: bold;
        }}

        .stat-label {{
            display: block;
            color: #94a3b8;
            font-size: 12px;
            margin-top: 4px;
        }}

        .trend {{
            display: inline-block;
            padding: 8px 12px;
            border-radius: 999px;
            font-weight: bold;
            font-size: 13px;
        }}

        .trending-up {{
            background: #064e3b;
            color: #6ee7b7;
        }}

        .declining {{
            background: #7f1d1d;
            color: #fecaca;
        }}

        .stable {{
            background: #334155;
            color: #cbd5e1;
        }}

        .metadata {{
            margin-top: 18px;
            font-size: 14px;
            color: #cbd5e1;
            line-height: 1.5;
        }}

        .metadata p {{
            margin: 8px 0;
        }}

        footer {{
            text-align: center;
            color: #64748b;
            padding: 24px;
            font-size: 13px;
        }}
    </style>
</head>

<body>
    <header>
        <h1>Project2026 Gaming Trend Dashboard</h1>
        <p>Top 10 trending games from YouTube Gaming, enriched with RAWG metadata</p>
        <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </header>

    <div class="container">
        <section class="chart-section">
            <canvas id="trendChart"></canvas>
        </section>

        <section class="grid">
            {cards_html}
        </section>
    </div>

    <footer>
        Project2026 | YouTube Data API + PostgreSQL + RAWG
    </footer>

    <script>
        const labels = {json.dumps(chart_labels)};
        const values = {json.dumps(chart_values)};

        const ctx = document.getElementById('trendChart');

        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Mentions in Top YouTube Gaming Videos',
                    data: values,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#e5e7eb'
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{
                            color: '#e5e7eb'
                        }},
                        grid: {{
                            color: '#334155'
                        }}
                    }},
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            color: '#e5e7eb',
                            precision: 0
                        }},
                        grid: {{
                            color: '#334155'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open("dashboard.html", "w", encoding="utf-8") as file:
        file.write(html)

    print("Dashboard updated successfully: dashboard.html")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    generate_dashboard()