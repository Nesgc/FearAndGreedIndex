# crypto_fear_greed.py
import json, re, time, requests
from datetime import datetime
from collections import Counter
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.graph_objects as go

nltk.download('vader_lexicon', quiet=True)
vader = SentimentIntensityAnalyzer()

REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/new.json?limit=50"
NITTER_URL = "https://nitter.net/search?f=tweets&q=bitcoin&since_time="  # simple timestamp cache-buster

def reddit_score() -> float:
    hdrs = {"User-Agent": "Mozilla/5.0"}
    data = requests.get(REDDIT_URL, headers=hdrs, timeout=10).json()
    titles = [p["data"]["title"] for p in data["data"]["children"]]
    scores = [vader.polarity_scores(t)["compound"] for t in titles]
    return (sum(scores) / len(scores) + 1) * 50   # → 0-100

def twitter_score() -> float:
    html = requests.get(NITTER_URL + str(int(time.time())), timeout=10).text
    emo = re.findall(r'[^\w\s,]', html)  # crude: grab all emoji-like chars
    counts = Counter(emo)
    GREED_EMOJI = {"🔥", "🚀", "💎", "🙌"}
    FEAR_EMOJI  = {"💀", "🥶", "😭"}
    greed = sum(counts[e] for e in GREED_EMOJI)
    fear  = sum(counts[e] for e in FEAR_EMOJI)
    if greed + fear == 0:
        return 50.0
    return 100 * greed / (greed + fear)

def blended_index() -> int:
    r, t = reddit_score(), twitter_score()
    return round((r + t) / 2)

def draw_gauge(value: int) -> None:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "black"},
            "steps": [
                {"range": [0, 25],  "color": "#ea3943"},
                {"range": [25, 50], "color": "#f4ae3f"},
                {"range": [50, 75], "color": "#9dd56d"},
                {"range": [75, 100],"color": "#15c15d"},
            ],
        }))
    fig.update_layout(title=f"Crypto Fear & Greed — {datetime.now():%H:%M UTC}")
    fig.show()

if __name__ == "__main__":
    while True:
        idx = blended_index()
        print(f"{datetime.now():%H:%M:%S}  Index = {idx}")
        draw_gauge(idx)
        time.sleep(60)     # refresh every minute
