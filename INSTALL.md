# 🚀 Installation Guide for Doug

## Option 1: One-Line Installer (EASIEST!)

Just copy and paste this single command into your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/pranavchavda/langgraph-photo-editor/main/install_doug.sh | bash
```

That's it! The script will:
- Download everything to `~/DougPhotoEditor`
- Install Docker if needed
- Build the container
- Start the web interface

## Option 2: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/pranavchavda/langgraph-photo-editor.git
cd langgraph-photo-editor

# 2. Run the setup script
chmod +x doug_docker_setup.sh
./doug_docker_setup.sh

# 3. Start the web interface
./doug_web.sh
```

## Option 3: Download ZIP (No Git Required)

1. Download: https://github.com/pranavchavda/langgraph-photo-editor/archive/refs/heads/main.zip
2. Extract the ZIP file
3. Open Terminal in the extracted folder
4. Run: `./doug_docker_setup.sh`

## 📱 Daily Usage

After installation, just:
```bash
cd ~/DougPhotoEditor
./doug_web.sh
```

Then open browser to: **http://localhost:8501**

## 🔑 API Keys

You'll need:
1. **Claude API Key**: https://console.anthropic.com/settings/keys
2. **Gemini API Key**: https://makersuite.google.com/app/apikey

Enter them in the web interface - they'll be saved in your browser!

## 🛑 Stop Everything

```bash
cd ~/DougPhotoEditor
./doug_stop.sh
```

## 🆘 Troubleshooting

**"Permission denied" error:**
```bash
chmod +x doug_docker_setup.sh
chmod +x doug_web.sh
```

**Docker not starting on Mac:**
- Open Docker Desktop app manually first
- Then run `./doug_web.sh`

**Port 8501 in use:**
- Stop other Streamlit apps
- Or edit `docker-compose.doug.yml` → change `8501:8501` to `8502:8501`
- Then access at http://localhost:8502

---

**That's all!** The one-liner installer handles everything else automatically.