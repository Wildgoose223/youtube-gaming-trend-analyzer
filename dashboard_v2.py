import os
import psycopg2
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "YouTube_Data")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def get_summary(conn, days):
    query = """
        SELECT
            COUNT(DISTINCT LOWER(game_name)) AS games_tracked,
            COALESCE(SUM(mentions), 0) AS total_mentions,
            COUNT(DISTINCT run_timestamp) AS total_runs
        FROM trending_games
        WHERE run_timestamp >= NOW() - INTERVAL %s;
    """
    return pd.read_sql(query, conn, params=(f"{days} days",))


def get_top_games(conn, days=7, limit=10):
    query = """
        SELECT
            LOWER(game_name) AS game_name,
            SUM(mentions) AS total_mentions,
            ROUND(AVG(percentage), 2) AS avg_percentage,
            COUNT(*) AS runs_count
        FROM trending_games
        WHERE run_timestamp >= NOW() - INTERVAL %s
        GROUP BY LOWER(game_name)
        ORDER BY total_mentions DESC
        LIMIT %s;
    """
    return pd.read_sql(query, conn, params=(f"{days} days", limit))


def get_latest_change(conn):
    query = """
        WITH latest_runs AS (
            SELECT DISTINCT run_timestamp
            FROM trending_games
            ORDER BY run_timestamp DESC
            LIMIT 2
        ),
        ranked_runs AS (
            SELECT
                run_timestamp,
                ROW_NUMBER() OVER (ORDER BY run_timestamp DESC) AS run_rank
            FROM latest_runs
        ),
        current_run AS (
            SELECT LOWER(t.game_name) AS game_name, SUM(t.mentions) AS mentions
            FROM trending_games t
            JOIN ranked_runs r ON t.run_timestamp = r.run_timestamp
            WHERE r.run_rank = 1
            GROUP BY LOWER(t.game_name)
        ),
        previous_run AS (
            SELECT LOWER(t.game_name) AS game_name, SUM(t.mentions) AS mentions
            FROM trending_games t
            JOIN ranked_runs r ON t.run_timestamp = r.run_timestamp
            WHERE r.run_rank = 2
            GROUP BY LOWER(t.game_name)
        )
        SELECT
            c.game_name,
            c.mentions AS current_mentions,
            COALESCE(p.mentions, 0) AS previous_mentions,
            c.mentions - COALESCE(p.mentions, 0) AS change
        FROM current_run c
        LEFT JOIN previous_run p ON c.game_name = p.game_name;
    """
    return pd.read_sql(query, conn)


def get_line_data(conn, days=7, limit=5):
    top_games = get_top_games(conn, days, limit)
    games = tuple(top_games["game_name"].tolist())

    if len(games) == 0:
        return pd.DataFrame()

    query = """
        SELECT
            DATE(run_timestamp) AS trend_date,
            LOWER(game_name) AS game_name,
            SUM(mentions) AS mentions
        FROM trending_games
        WHERE run_timestamp >= NOW() - INTERVAL %s
          AND LOWER(game_name) IN %s
        GROUP BY DATE(run_timestamp), LOWER(game_name)
        ORDER BY trend_date;
    """
    return pd.read_sql(query, conn, params=(f"{days} days", games))


def trend_label(change):
    if change > 0:
        return "Trending Up", "up"
    elif change < 0:
        return "Declining", "down"
    return "Stable", "stable"


def build_trend_summary(top_games, changes, days):
    if top_games.empty:
        return "Not enough data has been collected yet to summarize trends."

    top_game = top_games.iloc[0]["game_name"].title()
    top_mentions = int(top_games.iloc[0]["total_mentions"])

    if days == 1:
        period = "today"
    elif days == 7:
        period = "the last 7 days"
    elif days == 30:
        period = "the last 30 days"
    else:
        period = f"the last {days} days"

    summary = f"In {period}, {top_game} is leading overall with {top_mentions} total mentions. "

    if changes.empty:
        summary += "There is not enough previous-run data yet to compare movement."
        return summary

    biggest_up = changes.sort_values("change", ascending=False).iloc[0]
    biggest_down = changes.sort_values("change", ascending=True).iloc[0]

    up_game = biggest_up["game_name"].title()
    up_change = int(biggest_up["change"])

    down_game = biggest_down["game_name"].title()
    down_change = int(biggest_down["change"])

    if up_change > 0:
        summary += f"{up_game} has trended up the most since the previous run, gaining {up_change} mentions. "
    else:
        summary += "No major upward movement was detected since the previous run. "

    if down_change < 0:
        summary += f"{down_game} has cooled off the most, dropping {abs(down_change)} mentions."
    else:
        summary += "No major decline was detected since the previous run."

    return summary


def build_dashboard(days=7):
    conn = get_connection()

    summary = get_summary(conn, days)
    top_games = get_top_games(conn, days, 10)
    weekly_games = get_top_games(conn, 7, 10)
    monthly_games = get_top_games(conn, 30, 10)
    changes = get_latest_change(conn)
    line_data = get_line_data(conn, days, 5)

    conn.close()

    change_map = {
        row["game_name"]: row["change"]
        for _, row in changes.iterrows()
    }

    trend_summary = build_trend_summary(top_games, changes, days)

    if not line_data.empty:
        line_fig = px.line(
            line_data,
            x="trend_date",
            y="mentions",
            color="game_name",
            markers=True,
            title="Compact Trend Movement - Top 5"
        )
        line_fig.update_layout(
            height=300,
            template="plotly_dark",
            margin=dict(l=30, r=30, t=55, b=30),
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            legend_title_text=""
        )
        line_html = line_fig.to_html(full_html=False, include_plotlyjs="cdn")
    else:
        line_html = "<p>Not enough trend history yet. Let this run for a few days.</p>"

    bar_fig = px.bar(
        top_games,
        x="game_name",
        y="total_mentions",
        text="total_mentions",
        title=f"Top 10 Games - Last {days} Days"
    )
    bar_fig.update_layout(
        height=320,
        template="plotly_dark",
        margin=dict(l=30, r=30, t=55, b=40),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827"
    )
    bar_html = bar_fig.to_html(full_html=False, include_plotlyjs=False)

    cards = ""

    for index, row in top_games.head(10).iterrows():
        game = row["game_name"]
        change = int(change_map.get(game, 0))
        status, status_class = trend_label(change)

        cards += f"""
        <div class="game-card">
            <div class="rank">#{index + 1}</div>
            <h3>{game.title()}</h3>
            <p class="desc">Detected from YouTube Gaming titles, tags, RAWG titles, and manual aliases.</p>

            <div class="stats">
                <div><strong>{int(row['total_mentions'])}</strong><span>Mentions</span></div>
                <div><strong>{row['avg_percentage']}%</strong><span>Avg Share</span></div>
                <div><strong>{change:+}</strong><span>Vs Last Run</span></div>
            </div>

            <div class="status {status_class}">{status}</div>

            <p class="context">
                {game.title()} appeared {int(row['total_mentions'])} times in the selected range.
                Average visibility was {row['avg_percentage']}% across {int(row['runs_count'])} stored result rows.
            </p>
        </div>
        """

    s = summary.iloc[0]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project2026 Dashboard V2</title>
        <style>
            body {{
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.18) 0%, transparent 28%),
                    radial-gradient(circle at top right, rgba(99, 102, 241, 0.14) 0%, transparent 30%),
                    linear-gradient(135deg, #020617 0%, #0f172a 48%, #111827 100%);
                color: #e5e7eb;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 24px;
            }}

            h1 {{
                color: #38bdf8;
                margin-bottom: 4px;
            }}

            h2 {{
                margin-top: 0;
            }}

            .subtitle {{
                color: #94a3b8;
                margin-bottom: 22px;
            }}

            .buttons a {{
                display: inline-block;
                background: #1e293b;
                color: white;
                padding: 10px 16px;
                margin-right: 8px;
                border-radius: 8px;
                text-decoration: none;
                border: 1px solid #334155;
            }}

            .summary {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 14px;
                margin-top: 20px;
            }}

            .summary-card, .panel, .game-card {{
                background: rgba(15, 23, 42, 0.92);
                border: 1px solid #334155;
                border-radius: 16px;
                box-shadow: 0 12px 30px rgba(0,0,0,0.28);
            }}

            .summary-card {{
                padding: 18px;
                text-align: center;
            }}

            .summary-card strong {{
                display: block;
                font-size: 30px;
                color: #38bdf8;
            }}

            .summary-card span {{
                color: #94a3b8;
                font-size: 13px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-top: 20px;
            }}

            .game-card {{
                padding: 18px;
            }}

            .rank {{
                color: #38bdf8;
                font-weight: bold;
            }}

            .game-card h3 {{
                margin: 6px 0;
                font-size: 22px;
            }}

            .desc, .context {{
                color: #94a3b8;
                font-size: 13px;
                line-height: 1.45;
            }}

            .trend-summary {{
                font-size: 17px;
                line-height: 1.6;
                color: #dbeafe;
                background: rgba(2, 6, 23, 0.45);
                border-left: 4px solid #38bdf8;
                padding: 14px;
                border-radius: 10px;
            }}

            .stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin: 14px 0;
            }}

            .stats div {{
                background: #020617;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 10px;
                text-align: center;
            }}

            .stats strong {{
                display: block;
                color: white;
            }}

            .stats span {{
                font-size: 11px;
                color: #94a3b8;
            }}

            .status {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 8px;
            }}

            .up {{ background: rgba(34,197,94,.15); color: #4ade80; }}
            .down {{ background: rgba(239,68,68,.15); color: #f87171; }}
            .stable {{ background: rgba(234,179,8,.15); color: #facc15; }}

            .panel {{
                padding: 18px;
                margin-top: 22px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}

            th, td {{
                border-bottom: 1px solid #334155;
                padding: 10px;
                text-align: left;
            }}

            th {{
                color: #38bdf8;
            }}
        </style>
    </head>
    <body>
        <h1>Project2026 Gaming Trend Dashboard V2</h1>
        <div class="subtitle">YouTube Gaming trend intelligence using titles, tags, RAWG titles, and manual aliases.</div>

        <div class="buttons">
            <a href="dashboard_today.html">Today</a>
            <a href="dashboard_week.html">7 Days</a>
            <a href="dashboard_month.html">30 Days</a>
        </div>

        <div class="summary">
            <div class="summary-card"><strong>{int(s['games_tracked'])}</strong><span>Games Tracked</span></div>
            <div class="summary-card"><strong>{int(s['total_mentions'])}</strong><span>Total Mentions</span></div>
            <div class="summary-card"><strong>{int(s['total_runs'])}</strong><span>Stored Runs</span></div>
        </div>

        <div class="panel">
            <h2>Trend Summary</h2>
            <div class="trend-summary">{trend_summary}</div>
        </div>

        <div class="grid">
            {cards}
        </div>

        <div class="panel">
            <h2>Small Trend Graph</h2>
            {line_html}
        </div>

        <div class="panel">
            <h2>Top 10 Bar Chart</h2>
            {bar_html}
        </div>

        <div class="panel">
            <h2>Weekly Top 10</h2>
            {weekly_games.to_html(index=False)}
        </div>

        <div class="panel">
            <h2>Monthly Top 10</h2>
            {monthly_games.to_html(index=False)}
        </div>
    </body>
    </html>
    """

    filename = {
        1: "dashboard_today.html",
        7: "dashboard_week.html",
        30: "dashboard_month.html"
    }.get(days, "dashboard_custom.html")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Created {filename}")


if __name__ == "__main__":
    build_dashboard(1)
    build_dashboard(7)
    build_dashboard(30)
    print("Dashboard V2 rebuilt with trend summaries.")