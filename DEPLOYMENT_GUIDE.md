# AI Photo Editor - Easy Web Access Guide for Doug

## Quick Access Link
Once deployed, you'll access the app at: **https://[your-app-name].streamlit.app**

## How to Use the Web App

### Step 1: Open the App
Simply click the link above or paste it into your browser (Chrome, Safari, Firefox - any modern browser works!)

### Step 2: Upload Your Photo
1. Click the "Browse files" button in the Upload section
2. Select your product photo from your computer
3. The photo will appear on screen once uploaded

### Step 3: Edit Your Photo
1. The app comes with default instructions already filled in
2. You can change the instructions to describe what you want:
   - "Make the colors more vibrant"
   - "Remove the background and enhance the product"
   - "Make it look more professional for my website"
3. Click the green "🚀 Process Image" button

### Step 4: Download Your Enhanced Photo
1. Wait about 30-60 seconds for the AI to work its magic
2. Your enhanced photo will appear on the right side
3. Click "⬇️ Download Enhanced Image" to save it to your computer

## First Time Setup - API Keys
You'll need to enter your API keys once (they'll be saved in your browser):

1. Look for the "Settings" sidebar on the left
2. Enter your API keys:
   - **Anthropic API Key**: Required for image analysis
   - **Gemini API Key**: Required for AI editing
   - **Remove.bg Key**: Optional for background removal
3. The keys will be saved locally in your browser for next time

### Getting Your API Keys:
- **Anthropic (Claude)**: Visit [console.anthropic.com](https://console.anthropic.com)
- **Google Gemini**: Visit [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey) 
- **Remove.bg**: Visit [remove.bg/api](https://remove.bg/api)

**Security Note**: Your API keys stay in your browser and are never sent to any server.

## Tips for Best Results
- Upload clear, well-lit product photos
- JPG, PNG, and WebP formats all work
- Files up to 100MB are supported
- Be specific in your instructions for better results

## Need Different Edits?
Simply upload the same photo again with different instructions!

## Support
If you have any issues, just let Pranav know and he can help troubleshoot.

---

# Deployment Instructions (For Pranav)

## Option 1: Deploy to Streamlit Cloud (Recommended for Doug)

### Prerequisites
- GitHub repository (already set up)
- Streamlit Cloud account (free at share.streamlit.io)

### Steps

1. **Push latest changes to GitHub:**
```bash
git add .
git commit -m "Add Streamlit web interface for Doug"
git push origin main
```

2. **Connect to Streamlit Cloud:**
- Go to https://share.streamlit.io
- Sign in with GitHub
- Click "New app"
- Select repository: `pranavchavda/langgraph-photo-editor`
- Main file path: `streamlit_app.py`
- Click "Deploy"

3. **Configure Secrets (Optional):**
If you want to pre-configure API keys for all users (not recommended for public apps), you can add them in Streamlit Cloud dashboard under App Settings > Secrets:
```toml
ANTHROPIC_API_KEY = "your-actual-anthropic-key"
GEMINI_API_KEY = "your-actual-gemini-key"
REMOVE_BG_API_KEY = "your-actual-removebg-key"
```

**Note**: For Doug's use case, it's better to let him enter his own API keys which will be stored locally in his browser.

4. **Share the Link:**
- Streamlit will provide a URL like: `https://langgraph-photo-editor.streamlit.app`
- Share this with Doug - it works on any device with a browser!

## Option 2: Deploy to Your Linode Server

### Steps

1. **Update deployment script with your server details:**
Edit `deploy.sh` and set:
- `REMOTE_HOST="your-linode-ip"`
- `server_name` in nginx.conf

2. **Run deployment:**
```bash
chmod +x deploy.sh
./deploy.sh
```

3. **Set up environment on server:**
SSH into your server and create `/opt/photo-editor/.env`:
```bash
ANTHROPIC_API_KEY=your-key
GEMINI_API_KEY=your-key
REMOVE_BG_API_KEY=your-key
```

4. **Optional: Set up domain and SSL:**
```bash
# Install certbot if not already installed
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d photo-editor.yourdomain.com
```

5. **Access the app:**
- Without domain: `http://your-linode-ip:8501`
- With domain: `https://photo-editor.yourdomain.com`

## Monitoring and Maintenance

### Check app status (Linode deployment):
```bash
sudo systemctl status photo-editor
sudo journalctl -u photo-editor -f  # View logs
```

### Update the app:
```bash
# For Streamlit Cloud: Just push to GitHub
git push origin main

# For Linode: Run deployment script again
./deploy.sh
```

## Troubleshooting

### If Doug can't access the app:
1. Check if the Streamlit Cloud app is running (green status in dashboard)
2. Make sure he's entered his API keys in the sidebar
3. Try refreshing the page or using a different browser
4. API keys are saved per browser - if using a different browser, re-enter them

### If image processing fails:
1. Check API key validity
2. Verify you have credits/quota for the APIs
3. Try with a smaller image first

### API Key Management:
- Keep keys secure - never commit them to git
- Streamlit Cloud secrets are encrypted and safe
- Consider setting usage limits on your API accounts

## Cost Considerations
- **Streamlit Cloud Community**: Free tier includes 1 app, perfect for Doug
- **API Costs**: 
  - Anthropic: Pay per token used
  - Gemini: Free tier available (check limits)
  - Remove.bg: Optional, has free tier

## Quick Test
After deployment, test with a sample image to ensure everything works before sharing with Doug.