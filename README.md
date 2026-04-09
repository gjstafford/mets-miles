# ⚾ Mets Miles Challenge Dashboard

A live dashboard tracking a season-long challenge: **run one mile for every run scored by the New York Mets in 2025**.

- **MLB data** — pulled live from the public MLB Stats API on every page load, no API key needed
- **Strava data** — pulled every 6 hours via GitHub Actions and committed as `strava-data.json`
- **Hosted for free** on GitHub Pages

---

## Part 1 — GitHub Pages Setup

### 1. Create the repository

1. Go to [github.com](https://github.com) and sign in (create a free account if needed)
2. Click **New repository**
3. Name it whatever you like — e.g. `mets-miles`
4. Set it to **Public** (required for free GitHub Pages)
5. Click **Create repository**

### 2. Upload the project files

Option A — **GitHub web UI** (easiest)

1. On the new repo page, click **Add file → Upload files**
2. Drag and drop the following files and folders:
   - `index.html`
   - `strava-data.json`
   - `fetch_strava.py`
   - `.github/` folder (with `workflows/update-strava.yml` inside)
3. Click **Commit changes**

Option B — **Git CLI**

```bash
cd mets-miles
git init
git remote add origin https://github.com/YOUR_USERNAME/mets-miles.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 3. Enable GitHub Pages

1. In your repo, click **Settings → Pages** (in the left sidebar)
2. Under **Source**, select **Deploy from a branch**
3. Choose branch: **main**, folder: **/ (root)**
4. Click **Save**
5. After ~60 seconds, your site will be live at:
   `https://YOUR_USERNAME.github.io/mets-miles/`

---

## Part 2 — Strava API Setup

Strava requires OAuth to read an athlete's private activity data. These steps let GitHub Actions automatically refresh the data every 6 hours.

> **Note:** The friend being tracked (athlete ID 124790296) must complete this setup using **their own** Strava account.

### Step 1 — Create a Strava API Application

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Fill in:
   - **Application Name**: Mets Miles Challenge (or anything)
   - **Category**: Other
   - **Website**: your GitHub Pages URL (e.g. `https://yourusername.github.io/mets-miles`)
   - **Authorization Callback Domain**: `localhost`
3. Click **Create** and note down:
   - `Client ID`
   - `Client Secret`

### Step 2 — Get a Refresh Token

You need to authorize the app once to receive a refresh token. Open this URL in your browser (replace `YOUR_CLIENT_ID`):

```
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all
```

1. Log in with your Strava account and click **Authorize**
2. You'll be redirected to a URL like:
   ```
   http://localhost/?state=&code=SOME_LONG_CODE&scope=...
   ```
3. Copy the `code` value from the URL

Now exchange it for a refresh token using this `curl` command in your terminal:

```bash
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=YOUR_CODE_FROM_ABOVE \
  -d grant_type=authorization_code
```

The response JSON contains a `"refresh_token"` field — copy it.

### Step 3 — Add Secrets to GitHub

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret** and add each of these:

| Secret name             | Value                            |
|-------------------------|----------------------------------|
| `STRAVA_CLIENT_ID`      | Your numeric Client ID           |
| `STRAVA_CLIENT_SECRET`  | Your Client Secret string        |
| `STRAVA_REFRESH_TOKEN`  | The refresh token from Step 2    |

### Step 4 — Trigger the first data pull

1. In your repo, go to **Actions → Update Strava Data**
2. Click **Run workflow → Run workflow**
3. After it completes (~30 seconds), `strava-data.json` will be committed with real data
4. Reload your GitHub Pages site — the miles should now appear

Going forward, the workflow runs automatically every 6 hours.

---

## Customisation

| What to change | Where |
|---|---|
| Historical average runs (default: 690) | `HIST_AVG` constant near top of `<script>` in `index.html` |
| Season start / end dates | `SEASON_START` / `SEASON_END` in `index.html` |
| Auto-update frequency | `cron` line in `.github/workflows/update-strava.yml` |
| Filter activity type (e.g. include trails) | `fetch_strava.py` line with `sport_type == "Run"` |

---

## How it works

```
GitHub Actions (every 6 hrs)
  └─ fetch_strava.py
       └─ Strava API → strava-data.json (committed to repo)

Browser (on page load)
  ├─ MLB Stats API (live) → game-by-game scores → cumulative runs
  └─ strava-data.json (static, from last GH Actions run) → cumulative miles
```

The chart shows cumulative season totals for both, plus a dashed pace line representing the historical average of ~690 Mets runs/season (10-year average, 2014–2024, excluding the 2020 shortened season).
