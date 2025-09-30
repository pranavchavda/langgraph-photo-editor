# 📸 DOUG'S PHOTO EDITOR - SIMPLE GUIDE

## 🚀 ONE-TIME SETUP (5 minutes)

### Step 1: Download and Run Setup
```bash
curl -O https://raw.githubusercontent.com/pranavchavda/langgraph-photo-editor/main/doug_docker_setup.sh
chmod +x doug_docker_setup.sh
./doug_docker_setup.sh
```

That's it! The script will:
- Install Docker if needed
- Build everything
- Start the web interface
- Open your browser

### Step 2: Use the Web Interface

1. **Browser opens to:** `http://localhost:8501`
2. **Enter your API keys** in the sidebar (saved in browser)
3. **Upload photos** and click Process
4. **Download results**

## 🔑 API Keys (Get these once)

You need 2 API keys (the web app will guide you):

1. **Claude API Key**: https://console.anthropic.com/settings/keys
2. **Gemini API Key**: https://makersuite.google.com/app/apikey

## 💡 Daily Use

After setup, just run:
```bash
./doug_web.sh
```

Then open browser to: `http://localhost:8501`

## 🛑 Stop Everything

When done for the day:
```bash
./doug_stop.sh
```

## 🎯 That's ALL You Need!

- No Python installation
- No dependency management
- No command line editing
- API keys saved in your browser
- Everything runs in Docker

## 📱 Works Everywhere

- Mac ✅
- Windows ✅
- Linux ✅
- iPad/Tablet (via browser) ✅

## 🆘 Troubleshooting

**Docker not starting?**
- Mac: Open Docker Desktop app first
- Linux: Run `sudo systemctl start docker`

**Port 8501 already in use?**
- Stop other Streamlit apps
- Or edit `docker-compose.yml` to use port 8502

**Can't see web interface?**
- Check Docker is running: `docker ps`
- Try: `http://127.0.0.1:8501`

## 🚀 Advanced (Optional)

**Batch process folder of images:**
```bash
# Put images in ./input folder
./doug_batch.sh
# Results appear in ./output folder
```

**Process single image from command line:**
```bash
./doug_single.sh photo.jpg "make it more vibrant"
```

---

**Remember:** The web interface at `http://localhost:8501` does EVERYTHING you need!