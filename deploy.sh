#!/bin/bash
# Deployment script for Linode

echo "🚀 Deploying LangGraph Photo Editor to Linode..."

# Configuration
REMOTE_USER="root"  # Change to your user
REMOTE_HOST="your-linode-ip"  # Change to your Linode IP
APP_DIR="/opt/photo-editor"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Creating directory structure on server...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $APP_DIR"

echo -e "${BLUE}Step 2: Copying files to server...${NC}"
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='.git' \
    --exclude='electron' --exclude='node_modules' \
    ./ $REMOTE_USER@$REMOTE_HOST:$APP_DIR/

echo -e "${BLUE}Step 3: Setting up Python environment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd /opt/photo-editor
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install streamlit
EOF

echo -e "${BLUE}Step 4: Creating systemd service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cat > /etc/systemd/system/photo-editor.service << 'SERVICE'
[Unit]
Description=LangGraph Photo Editor Streamlit App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/photo-editor
Environment="PATH=/opt/photo-editor/venv/bin"
Environment="PYTHONPATH=/opt/photo-editor"
ExecStart=/opt/photo-editor/venv/bin/streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE
EOF

echo -e "${BLUE}Step 5: Starting service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
systemctl daemon-reload
systemctl enable photo-editor
systemctl restart photo-editor
systemctl status photo-editor
EOF

echo -e "${BLUE}Step 6: Setting up nginx...${NC}"
scp nginx.conf $REMOTE_USER@$REMOTE_HOST:/etc/nginx/sites-available/photo-editor
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
ln -sf /etc/nginx/sites-available/photo-editor /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
EOF

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "Access your app at: ${GREEN}http://$REMOTE_HOST:8501${NC}"
echo -e "Or configure your domain to point to: ${GREEN}$REMOTE_HOST${NC}"