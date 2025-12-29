# Get Your Shareable Link with ngrok

## Quick Method (Recommended)

I've created a batch file for you. Just double-click:

**`start_ngrok.bat`**

This will:
1. Start your Flask server
2. Start ngrok
3. Show you the shareable link

---

## Manual Method

### Step 1: Start Flask Server
Open a terminal and run:
```bash
python app.py
```
Keep this terminal open.

### Step 2: Start ngrok
Open a **NEW** terminal and run:
```bash
ngrok http 5000
```

### Step 3: Get Your Link
You'll see output like this:
```
Forwarding   https://abc123xyz.ngrok.io -> http://localhost:5000
```

**That `https://abc123xyz.ngrok.io` is your shareable link!**

Copy it and share with anyone.

---

## Important Notes

- ✅ The link works as long as both Flask and ngrok are running
- ✅ Anyone with the link can access your app
- ⚠️ Free ngrok URLs change each time you restart
- 💡 For a permanent URL, sign up for free ngrok account at https://ngrok.com

---

## Troubleshooting

**If port 5000 is busy:**
- Close other applications using port 5000
- Or change the port in `app.py` and use that port with ngrok

**If ngrok doesn't start:**
- Make sure ngrok is installed: `ngrok version`
- Check if Flask is running on port 5000

