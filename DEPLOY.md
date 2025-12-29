# Deploying RefactorIQ - Making It Accessible to Others

There are several ways to make your RefactorIQ application accessible to others. Choose the option that best fits your needs.

## Option 1: Quick Sharing with ngrok (Temporary - Easiest)

**Best for:** Quick demos, testing, or temporary sharing

### Steps:

1. **Install ngrok:**
   - Download from: https://ngrok.com/download
   - Or use: `choco install ngrok` (Windows with Chocolatey)
   - Or: `winget install ngrok`

2. **Start your Flask app:**
   ```bash
   python app.py
   ```
   Keep this running in one terminal.

3. **In a new terminal, start ngrok:**
   ```bash
   ngrok http 5000
   ```

4. **Copy the forwarding URL:**
   - ngrok will show something like: `https://abc123.ngrok.io`
   - This is your shareable link!
   - Share this URL with others

5. **Note:** 
   - Free ngrok URLs change each time you restart
   - For a permanent URL, sign up for a free ngrok account

---

## Option 2: Deploy to Render (Free - Permanent)

**Best for:** Permanent hosting with a free tier

### Steps:

1. **Create a Render account:**
   - Go to: https://render.com
   - Sign up with GitHub

2. **Create a new Web Service:**
   - Connect your GitHub repository
   - Or use Render's manual deploy

3. **Configure the service:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Environment:** Python 3

4. **Add environment variables (if needed):**
   - None required for basic setup

5. **Deploy:**
   - Render will give you a URL like: `https://refactoriq.onrender.com`
   - This is your permanent shareable link!

---

## Option 3: Deploy to Railway (Free Trial - Easy)

**Best for:** Easy deployment with good free tier

### Steps:

1. **Create a Railway account:**
   - Go to: https://railway.app
   - Sign up with GitHub

2. **Create a new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure:**
   - Railway auto-detects Python
   - Add `requirements.txt` if not already present
   - Start command: `python app.py`

4. **Get your URL:**
   - Railway provides a URL like: `https://refactoriq.up.railway.app`
   - Share this link!

---

## Option 4: Deploy to PythonAnywhere (Free - Beginner Friendly)

**Best for:** Python-specific hosting, very beginner-friendly

### Steps:

1. **Create account:**
   - Go to: https://www.pythonanywhere.com
   - Sign up for free account

2. **Upload your files:**
   - Use the Files tab to upload your project
   - Or use Git to clone your repository

3. **Configure Web App:**
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask
   - Set source code directory

4. **Update WSGI file:**
   - Edit the WSGI file to point to your app
   - Set: `from app import app`

5. **Reload:**
   - Click "Reload" button
   - Get your URL: `https://yourusername.pythonanywhere.com`

---

## Option 5: Deploy to Heroku (Free Tier Discontinued)

**Note:** Heroku no longer offers free tier, but paid options available.

---

## Quick Comparison

| Service | Free Tier | Ease of Use | Permanent URL | Best For |
|---------|-----------|-------------|----------------|----------|
| **ngrok** | ✅ Yes | ⭐⭐⭐⭐⭐ | ❌ No (changes) | Quick demos |
| **Render** | ✅ Yes | ⭐⭐⭐⭐ | ✅ Yes | Permanent hosting |
| **Railway** | ✅ Trial | ⭐⭐⭐⭐⭐ | ✅ Yes | Easy deployment |
| **PythonAnywhere** | ✅ Yes | ⭐⭐⭐ | ✅ Yes | Python-specific |

---

## Recommended: Start with ngrok for Quick Sharing

If you just need to share it quickly:

```bash
# Terminal 1: Start your app
python app.py

# Terminal 2: Start ngrok
ngrok http 5000
```

Then share the ngrok URL (e.g., `https://abc123.ngrok.io`) with others!

---

## Making Your App Production-Ready

Before deploying permanently, consider:

1. **Disable debug mode:**
   ```python
   # In app.py, change:
   app.run(debug=True, host='0.0.0.0', port=5000)
   # To:
   app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
   ```

2. **Add error handling** (already done)

3. **Set up environment variables** for sensitive data

4. **Add a Procfile** (for Heroku/Railway):
   ```
   web: python app.py
   ```

---

## Need Help?

- **ngrok docs:** https://ngrok.com/docs
- **Render docs:** https://render.com/docs
- **Railway docs:** https://docs.railway.app
- **PythonAnywhere docs:** https://help.pythonanywhere.com

