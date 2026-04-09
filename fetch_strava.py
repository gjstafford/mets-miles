"""
fetch_strava.py
---------------
Run by GitHub Actions every 6 hours.
Reads STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN from env,
exchanges them for a fresh access token, pulls all Run activities since
Opening Day 2026, and writes strava-data.json to the repo root.
"""

import os, json, urllib.request, urllib.parse
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────
CLIENT_ID      = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET  = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN  = os.environ["STRAVA_REFRESH_TOKEN"]

# 2026 Opening Day (UTC midnight)
SEASON_START_EPOCH = int(datetime(2026, 3, 26, tzinfo=timezone.utc).timestamp())

# ── HTTP helpers ──────────────────────────────────────────────────────
def http_post(url: str, data: dict) -> dict:
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def http_get(url: str, token: str) -> list | dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# ── Refresh access token ──────────────────────────────────────────────
print("Refreshing Strava access token…")
token_resp = http_post("https://www.strava.com/oauth/token", {
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type":    "refresh_token",
    "refresh_token": REFRESH_TOKEN,
})
access_token = token_resp["access_token"]
print(f"  Got access token (expires in {token_resp.get('expires_in', '?')}s)")

# ── Fetch all activities since Opening Day ────────────────────────────
print("Fetching Strava activities since 2026-03-26…")
all_activities = []
page = 1

while True:
    url = (
        f"https://www.strava.com/api/v3/athlete/activities"
        f"?after={SEASON_START_EPOCH}&per_page=100&page={page}"
    )
    batch = http_get(url, access_token)
    if not isinstance(batch, list) or not batch:
        break
    all_activities.extend(batch)
    print(f"  Page {page}: {len(batch)} activities")
    if len(batch) < 100:
        break
    page += 1

# ── Filter to running activities only ────────────────────────────────
runs = [
    a for a in all_activities
    if a.get("sport_type") == "Run" or a.get("type") == "Run"
]
print(f"  {len(runs)} running activities found (of {len(all_activities)} total)")

# ── Convert and sort ──────────────────────────────────────────────────
activities = []
for a in runs:
    miles = round(a["distance"] / 1609.344, 2)   # metres → miles
    activities.append({
        "date":  a["start_date_local"][:10],       # YYYY-MM-DD local time
        "miles": miles,
        "name":  a.get("name", ""),
    })

activities.sort(key=lambda x: x["date"])
total_miles = round(sum(a["miles"] for a in activities), 2)

# ── Write output ──────────────────────────────────────────────────────
output = {
    "total_miles": total_miles,
    "activities":  activities,
    "last_updated": datetime.now(timezone.utc).isoformat(),
}

with open("strava-data.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\n✓ strava-data.json written — {len(activities)} runs, {total_miles} total miles")
