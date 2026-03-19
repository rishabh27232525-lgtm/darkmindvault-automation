# 🎬 YouTube Automation — Cloud Setup Guide
**Works on ANY laptop (even 4GB RAM) — GitHub does all the work**
**6 Languages · 1 Video/Day · $0 Cost Forever**

---

## 🏗️ Architecture

```
YOUR LAPTOP (4GB RAM)          GITHUB CLOUD (7GB RAM, Free)
─────────────────────          ─────────────────────────────
Run auth_setup.py (once) ───►  Runs pipeline.py EVERY DAY
Close laptop forever     ◄───  Uploads to all 6 language channels
```

**Your laptop only needed ONCE for the YouTube login. After that, it can stay off.**

---

## 📋 What You Need (All Free)

| Tool | Purpose | Link |
|------|---------|------|
| GitHub Account | Runs the automation for free | github.com |
| Groq API Key | AI script writing (Llama 3.3 70B) | console.groq.com |
| Pexels API Key | Free HD stock footage | pexels.com/api |
| YouTube API | Upload videos automatically | console.cloud.google.com |

---

## 🚀 Setup Steps

### STEP 1 — Install Python on your laptop (needed once)
Download from python.org → Check "Add Python to PATH"
```bash
python --version   # Should show 3.11+
```

### STEP 2 — Install packages on your laptop (needed once)
```bash
pip install google-api-python-client google-auth-oauthlib
```

### STEP 3 — Get Groq API Key (2 minutes)
1. Go to **console.groq.com**
2. Sign up free
3. Go to "API Keys" → "Create API Key"
4. Copy the key (starts with `gsk_...`)

### STEP 4 — Get Pexels API Key (2 minutes)
1. Go to **pexels.com/api**
2. Sign up free
3. Your API key is shown on the dashboard

### STEP 5 — Set Up YouTube API (5 minutes)
1. Go to **console.cloud.google.com**
2. Create new project → Enable "YouTube Data API v3"
3. Credentials → Create OAuth 2.0 Client ID → Desktop App
4. Download JSON → rename to `client_secrets.json`
5. Place in same folder as the scripts

### STEP 6 — Connect Your YouTube Channel (One Time Only)
```bash
python src/auth_setup.py
```
- Browser opens → Log in → Click Allow
- Two files created: `YOUTUBE_CREDS_B64.txt` and `YOUTUBE_TOKEN_B64.txt`

### STEP 7 — Create GitHub Repository
1. Go to **github.com** → New Repository
2. Name: `youtube-automation` (or anything)
3. Set to **Private** (important — keeps your API keys safe)
4. Upload all the project files

### STEP 8 — Add GitHub Secrets (30 seconds each)
Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|------------|-------|
| `GROQ_API_KEY` | Your Groq key (gsk_...) |
| `PEXELS_API_KEY` | Your Pexels API key |
| `YOUTUBE_CREDS_B64` | Copy entire content of YOUTUBE_CREDS_B64.txt |
| `YOUTUBE_TOKEN_B64` | Copy entire content of YOUTUBE_TOKEN_B64.txt |

### STEP 9 — Push code to GitHub
```bash
git init
git add .
git commit -m "Initial setup"
git remote add origin https://github.com/YOUR_USERNAME/youtube-automation.git
git push -u origin main
```

### STEP 10 — Enable GitHub Actions
1. Go to your repo → **Actions** tab
2. Click "I understand my workflows, go ahead and enable them"
3. Done! The pipeline runs daily at 1 PM UTC automatically.

---

## 🧪 Test Before Going Live

Go to GitHub → Actions → "YouTube Automation" → "Run workflow" → Set test_mode = true

This creates videos WITHOUT uploading, so you can check output first.

---

## 📅 Upload Schedule

| Language | Upload Time | Target Audience |
|---------|------------|-----------------|
| 🇺🇸 English | 3:00 PM UTC | USA prime time |
| 🇪🇸 Spanish | 4:00 PM UTC | Latin America |
| 🇮🇳 Hindi | 6:30 PM IST | India evening |
| 🇧🇷 Portuguese | 3:00 PM BRT | Brazil peak |
| 🇸🇦 Arabic | 8:00 PM GST | Gulf/MENA |
| 🇫🇷 French | 5:00 PM CET | Europe peak |

---

## 💰 Revenue Potential

With 6 language channels posting daily:

| Timeline | Videos Total | Monthly Revenue |
|---------|-------------|----------------|
| Month 3 | 90 videos | Applying for monetization |
| Month 6 | 180 videos | $500–1500/month (EN only) |
| Month 9 | 270 videos | $2000–5000/month (all langs) |
| Month 12 | 360 videos | $5000–15000/month |

**6 channels × higher CPM = exponential growth**

---

## 🔄 Token Refresh (Every ~6 Months)

YouTube tokens expire. When uploads fail, re-run on your laptop:
```bash
python src/auth_setup.py
```
Then update `YOUTUBE_TOKEN_B64` in GitHub Secrets.

---

## ❓ Troubleshooting

**Pipeline fails on Groq step**
→ Check GROQ_API_KEY secret is correct. Groq free tier: 30 req/min, 14,400/day

**Videos created but not uploaded**
→ Token expired. Re-run auth_setup.py and update GitHub secret

**No footage in video**
→ Check PEXELS_API_KEY secret. System will use gradient background as fallback

**GitHub Actions not running**
→ Go to Actions tab → check if workflows are enabled

---

*System: Groq AI + edge-tts + MoviePy + Pexels + YouTube API v3*
*Cloud: GitHub Actions (free, 2000 min/month)*
*Cost: $0.00 forever*
