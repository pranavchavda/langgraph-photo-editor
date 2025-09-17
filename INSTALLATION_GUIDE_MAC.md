# Installation Guide for LangGraph Photo Editor on Mac (Intel)

## Prerequisites
Before starting, make sure you have:
- A Mac with macOS 10.15 (Catalina) or later
- About 2GB of free disk space
- Your API keys ready (we'll add them during setup)

## Step 1: Install Homebrew (if not already installed)
Homebrew is a package manager that makes installing software easy on Mac.

1. Open Terminal (find it in Applications > Utilities > Terminal)
2. Copy and paste this entire command and press Enter:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
3. Follow any prompts that appear (you may need to enter your Mac password)
4. When done, test it worked by typing:
```bash
brew --version
```
You should see a version number like "Homebrew 4.x.x"

## Step 2: Install Python and Git
1. In Terminal, run these commands one at a time:
```bash
brew install python@3.11
brew install git
brew install imagemagick
```
2. Verify Python is installed:
```bash
python3 --version
```
You should see "Python 3.11.x"

## Step 3: Clone the Repository
1. Choose where to put the app. Run this to create a Projects folder:
```bash
mkdir -p ~/Projects
cd ~/Projects
```

2. Download the photo editor code:
```bash
git clone https://github.com/pranavchavda/langgraph-photo-editor.git
cd langgraph-photo-editor
```

## Step 4: Create a Virtual Environment
This keeps the photo editor's files separate from other Python programs.

1. Create the virtual environment:
```bash
python3 -m venv venv
```

2. Activate it:
```bash
source venv/bin/activate
```
You'll see `(venv)` appear at the start of your Terminal line.

## Step 5: Install Required Packages
1. Install all the photo editor dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
This will take 2-5 minutes to download everything.

2. Verify Streamlit installed correctly:
```bash
pip show streamlit
```
You should see version information. If not, install it directly:
```bash
pip install streamlit
```

## Step 6: Set Up Your API Keys
You need API keys for the AI services. Here's how to add them:

1. Create a file for your keys:
```bash
nano .env
```

2. Add your API keys (replace the placeholder text with your actual keys):
```
ANTHROPIC_API_KEY=your_claude_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
REMOVE_BG_API_KEY=your_removebg_api_key_here
```

3. Save the file:
   - Press `Control + O` (that's the letter O, not zero)
   - Press `Enter` to confirm
   - Press `Control + X` to exit

## Step 7: Test the Installation
1. Run a quick test to make sure everything works:
```bash
python photo_editor.py test
```
You should see "Configuration test passed!" if everything is set up correctly.

## Step 8: Run the Streamlit Web App
1. Start the web interface:
```bash
streamlit run streamlit_app.py
```

2. Your default web browser should open automatically to `http://localhost:8501`
   - If it doesn't open, manually type that address into your browser

3. You'll see the photo editor interface where you can:
   - Upload single images or multiple images
   - Enter processing instructions
   - Download the enhanced results

## Daily Usage (After Installation)
Each time you want to use the photo editor:

1. Open Terminal
2. Navigate to the project:
```bash
cd ~/Projects/langgraph-photo-editor
```
3. Activate the virtual environment:
```bash
source venv/bin/activate
```
4. Start the app:
```bash
streamlit run streamlit_app.py
```
5. Use the web interface in your browser

## Stopping the App
- To stop the app: Press `Control + C` in the Terminal
- To deactivate the virtual environment: Type `deactivate`

## Troubleshooting Common Issues

### "Command not found" errors
- Make sure you're in the right directory: `cd ~/Projects/langgraph-photo-editor`
- Make sure the virtual environment is activated (you should see `(venv)` in Terminal)

### "streamlit: command not found" error
If you get this error when running `streamlit run streamlit_app.py`:
1. Make sure your virtual environment is activated (you should see `(venv)`)
2. Reinstall streamlit directly:
```bash
pip install streamlit
```
3. If that doesn't work, try running it with Python:
```bash
python -m streamlit run streamlit_app.py
```

### "API key not found" errors
- Check your .env file has the correct keys: `cat .env`
- Make sure there are no spaces around the = sign in the .env file

### Browser doesn't open automatically
- Manually go to: `http://localhost:8501` in Safari or Chrome

### Port already in use error
- Another Streamlit app might be running. Try:
```bash
streamlit run streamlit_app.py --server.port 8502
```
Then go to `http://localhost:8502` instead

## Getting Your API Keys

### Claude (Anthropic) API Key:
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Go to API Keys section
4. Create a new key

### Gemini API Key:
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"

### Remove.bg API Key (Optional):
1. Go to https://www.remove.bg/users/sign_up
2. Create an account
3. Go to API section
4. Get your API key

## Need Help?
If you run into issues:
1. Take a screenshot of the error message
2. Note which step you're on
3. Contact support with these details

---
Remember: You only need to do Steps 1-6 once. After that, just use the "Daily Usage" section each time you want to edit photos!