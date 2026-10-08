# Clickstream Behavior Analyzer

Sessionizes raw click events and reports user behavior: bounce rate, session length,
top/entry/exit pages, device share, conversion funnel, and common page transitions.

## Run
    pip install -r requirements.txt
    python generate_data.py     # creates data/clickstream.csv (synthetic)
    python analyzer.py          # or: python analyzer.py your_file.csv

CSV columns required: `user_id, timestamp, page, device`.
Outputs go to `output/` (report.txt, sessions.csv, dashboard.png).
