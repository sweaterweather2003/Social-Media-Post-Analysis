import matplotlib.pyplot as plt
from db import get_all_posts
import pandas as pd

def load_dataframe() -> pd.DataFrame:
    posts = get_all_posts()
    df = pd.DataFrame(posts)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["total_engagement"] = df["likes_count"] + df["comments_count"]
    return df

def print_summary(df: pd.DataFrame):
    if df.empty:
        print("No data available yet.")
        return
    print("\n--- Engagement Summary ---")
    print(f"Total posts analyzed: {len(df)}")
    print(f"Average likes: {df['likes_count'].mean():.1f}")
    print(f"Average comments: {df['comments_count'].mean():.1f}")
    print(f"Average total engagement: {df['total_engagement'].mean():.1f}")

def plot_engagement_trend(df: pd.DataFrame, output_path: str = "engagement_trend.png"):
    if df.empty:
        return
    df_sorted = df.sort_values("timestamp")
    plt.figure(figsize=(10, 5))
    plt.plot(df_sorted["timestamp"], df_sorted["likes_count"], marker="o", label="Likes")
    plt.plot(df_sorted["timestamp"], df_sorted["comments_count"], marker="o", label="Comments")
    plt.xlabel("Post Date")
    plt.ylabel("Count")
    plt.title("Engagement Trend Over Time")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Chart saved to {output_path}")

def plot_top_posts_bar(df: pd.DataFrame, output_path: str = "top_posts.png", top_n: int = 10):
    if df.empty:
        return
    top_posts = df.sort_values("total_engagement", ascending=False).head(top_n)
    plt.figure(figsize=(10, 6))
    plt.barh(top_posts["shortcode"].astype(str), top_posts["total_engagement"])
    plt.xlabel("Total Engagement")
    plt.ylabel("Post")
    plt.title(f"Top {top_n} Posts by Engagement")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Chart saved to {output_path}")

def run_full_analysis():
    df = load_dataframe()
    print_summary(df)
    plot_engagement_trend(df)
    plot_top_posts_bar(df)
