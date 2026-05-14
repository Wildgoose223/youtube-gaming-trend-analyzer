@echo off
cd /d C:\Users\Samob\OneDrive\Desktop\Project2026

echo Running Project2026 update...

python youtube_trend_analyzer.py
python dashboard_generator.py

git add index.html dashboard_generator.py
git commit -m "Auto update dashboard"

git push

echo Project2026 update complete.