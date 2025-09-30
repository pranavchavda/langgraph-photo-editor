#!/bin/bash

# Test Google Product Studio v1alpha API for image upscaling

echo "🎨 Testing Google Product Studio v1alpha API"
echo "============================================"

ACCOUNT_ID="7893408"
TOKEN=$(gcloud auth print-access-token 2>/dev/null)
IMAGE_PATH="/home/pranav/langgraph-photo-editor/enhanced_enhanced_nurri-cropped (4).jpg"

# Encode image
echo "📸 Encoding image..."
IMAGE_BASE64=$(base64 -w 0 "$IMAGE_PATH")

echo "🏪 Account ID: $ACCOUNT_ID"
echo "🔑 Token obtained: $([ -n "$TOKEN" ] && echo "Yes" || echo "No")"
echo ""

# Try Product Studio v1alpha endpoints
echo "Testing Product Studio v1alpha endpoints:"
echo ""

# Pattern 1: Direct v1alpha endpoint
echo "1. merchantapi.googleapis.com/productstudio/v1alpha pattern:"
ENDPOINT="https://merchantapi.googleapis.com/productstudio/v1alpha/accounts/$ACCOUNT_ID:upscaleProductImage"
echo "   Testing: $ENDPOINT"

# Create request with proper format
cat > /tmp/productstudio_request.json <<EOF
{
  "name": "accounts/$ACCOUNT_ID",
  "inputImage": {
    "imageBytes": "$IMAGE_BASE64"
  }
}
EOF

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/productstudio_request.json \
  "$ENDPOINT" \
  -o /tmp/productstudio_response.json \
  -w "   Status: %{http_code}\n" \
  2>/dev/null

if [ -f /tmp/productstudio_response.json ]; then
    echo "   Response preview:"
    cat /tmp/productstudio_response.json | python3 -m json.tool 2>/dev/null | head -20 || cat /tmp/productstudio_response.json | head -5
fi
echo ""

# Pattern 2: Under merchant API with productstudio path
echo "2. merchantapi.googleapis.com/v1alpha/accounts pattern:"
ENDPOINT="https://merchantapi.googleapis.com/v1alpha/accounts/$ACCOUNT_ID/productstudio:upscaleImage"
echo "   Testing: $ENDPOINT"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/productstudio_request.json \
  "$ENDPOINT" \
  -o /tmp/productstudio_response2.json \
  -w "   Status: %{http_code}\n" \
  2>/dev/null

if [ -f /tmp/productstudio_response2.json ]; then
    echo "   Response preview:"
    cat /tmp/productstudio_response2.json | python3 -m json.tool 2>/dev/null | head -20 || cat /tmp/productstudio_response2.json | head -5
fi
echo ""

# Pattern 3: Shopping merchant productstudio pattern
echo "3. shoppingmerchant.googleapis.com/productstudio/v1alpha pattern:"
ENDPOINT="https://shoppingmerchant.googleapis.com/productstudio/v1alpha/accounts/$ACCOUNT_ID:upscaleProductImage"
echo "   Testing: $ENDPOINT"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/productstudio_request.json \
  "$ENDPOINT" \
  -o /tmp/productstudio_response3.json \
  -w "   Status: %{http_code}\n" \
  2>/dev/null

if [ -f /tmp/productstudio_response3.json ]; then
    echo "   Response preview:"
    cat /tmp/productstudio_response3.json | python3 -m json.tool 2>/dev/null | head -20 || cat /tmp/productstudio_response3.json | head -5
fi

echo ""
echo "💡 Product Studio v1alpha indicates this is an alpha/preview feature"
echo "   It might require special access or allowlisting"