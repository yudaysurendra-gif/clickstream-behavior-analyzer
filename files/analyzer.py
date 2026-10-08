"""Clickstream Behavior Analyzer.

Usage:  python analyzer.py [path/to/clickstream.csv]
Input CSV columns: user_id, timestamp, page, device
"""
import sys
from pathlib import Path

import pandas as pd

SESSION_TIMEOUT = pd.Timedelta(minutes=30)
FUNNEL = ["home", "product", "cart", "checkout", "purchase"]
OUT_DIR = Path("output")


def load(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)


def sessionize(df):
    """New session when a user is inactive for more than SESSION_TIMEOUT."""
    gap = df.groupby("user_id")["timestamp"].diff()
    is_new = gap.isna() | (gap > SESSION_TIMEOUT)
    df["session_num"] = is_new.groupby(df["user_id"]).cumsum()
    df["session_id"] = df["user_id"] + "-" + df["session_num"].astype(str)
    return df


def session_summary(df):
    s = df.groupby("session_id").agg(
        user_id=("user_id", "first"), device=("device", "first"),
        start=("timestamp", "min"), end=("timestamp", "max"),
        pages=("page", "count"), entry=("page", "first"), exit=("page", "last"),
    )
    s["duration_s"] = (s["end"] - s["start"]).dt.total_seconds()
    s["bounce"] = s["pages"] == 1
    return s


def funnel(df):
    """Share of sessions reaching each funnel step (and all earlier steps)."""
    visited = df.groupby("session_id")["page"].agg(set)
    rows, remaining = [], visited
    for step in FUNNEL:
        remaining = remaining[remaining.apply(lambda p, s=step: s in p)]
        rows.append((step, len(remaining)))
    out = pd.DataFrame(rows, columns=["step", "sessions"])
    out["pct_of_first"] = (out["sessions"] / out["sessions"].iloc[0] * 100).round(1)
    out["step_conversion_pct"] = (out["sessions"] / out["sessions"].shift(1) * 100).round(1)
    return out


def top_transitions(df, n=10):
    d = df.copy()
    d["next_page"] = d.groupby("session_id")["page"].shift(-1)
    d = d.dropna(subset=["next_page"])
    return (d.groupby(["page", "next_page"]).size()
             .sort_values(ascending=False).head(n).rename("count").reset_index())


def build_report(df, sessions):
    lines = ["=== CLICKSTREAM BEHAVIOR REPORT ===",
             f"Events:            {len(df):,}",
             f"Unique users:      {df['user_id'].nunique():,}",
             f"Sessions:          {len(sessions):,}",
             f"Avg pages/session: {sessions['pages'].mean():.2f}",
             f"Avg duration (s):  {sessions['duration_s'].mean():.1f}",
             f"Bounce rate:       {sessions['bounce'].mean() * 100:.1f}%",
             "", "-- Top pages (views) --", df["page"].value_counts().to_string(),
             "", "-- Top entry pages --", sessions["entry"].value_counts().head(5).to_string(),
             "", "-- Top exit pages --", sessions["exit"].value_counts().head(5).to_string(),
             "", "-- Device share (sessions, %) --",
             (sessions["device"].value_counts(normalize=True) * 100).round(1).to_string(),
             "", "-- Conversion funnel --", funnel(df).to_string(index=False),
             "", "-- Top page transitions --", top_transitions(df).to_string(index=False)]
    return "\n".join(lines)


def make_charts(df, sessions):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping charts.")
        return
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    df["page"].value_counts().plot.bar(ax=ax[0, 0], title="Page views")
    f = funnel(df)
    ax[0, 1].barh(f["step"][::-1], f["sessions"][::-1], color="seagreen")
    ax[0, 1].set_title("Conversion funnel (sessions)")
    df.groupby(df["timestamp"].dt.hour).size().plot(ax=ax[1, 0], marker="o", title="Traffic by hour")
    sessions["device"].value_counts().plot.pie(ax=ax[1, 1], autopct="%1.0f%%", title="Device share")
    ax[1, 1].set_ylabel("")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "dashboard.png", dpi=120)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/clickstream.csv"
    if not Path(path).exists():
        sys.exit(f"{path} not found. Run `python generate_data.py` first.")
    OUT_DIR.mkdir(exist_ok=True)
    df = sessionize(load(path))
    sessions = session_summary(df)
    report = build_report(df, sessions)
    print(report)
    (OUT_DIR / "report.txt").write_text(report)
    sessions.to_csv(OUT_DIR / "sessions.csv")
    make_charts(df, sessions)
    print(f"\nSaved results to {OUT_DIR}/")


if __name__ == "__main__":
    main()
