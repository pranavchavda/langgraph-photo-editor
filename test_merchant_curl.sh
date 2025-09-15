#!/bin/bash

# Test Google Merchant API upscaling with curl

echo "🏪 Testing Google Merchant API Product Studio Upscaling"
echo "======================================================="

# Configuration
MERCHANT_ID="7893408"
IMAGE_PATH="/home/pranav/langgraph-photo-editor/enhanced_enhanced_nurri-cropped (4).jpg"

# Check if image exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ Image not found: $IMAGE_PATH"
    exit 1
fi

echo "📸 Using image: $(basename "$IMAGE_PATH")"
echo "🏪 Merchant ID: $MERCHANT_ID"

# Get token
echo -e "\n🔑 Getting auth token..."
TOKEN=$(gcloud auth print-access-token 2>/dev/null)
if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get auth token"
    exit 1
fi
echo "✅ Got token"

# Encode image to base64
echo "📦 Encoding image..."
IMAGE_BASE64=$(base64 -w 0 "$IMAGE_PATH")
echo "   Encoded size: ${#IMAGE_BASE64} chars"

# Create request JSON
cat > /tmp/merchant_request.json <<EOF
{
  "image": {
    "rawImageBytes": "$IMAGE_BASE64"
  },
  "upscaleFactor": "2x"
}
EOF

echo -e "\n📤 Sending request to Merchant API..."
echo "   Endpoint: https://merchantapi.googleapis.com/v1/accounts/$MERCHANT_ID/productImages:upscale"

# Make the request
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/merchant_request.json \
  "https://merchantapi.googleapis.com/v1/accounts/$MERCHANT_ID/productImages:upscale" \
  -o /tmp/merchant_response.json \
  -w "\nHTTP Status: %{http_code}\n" \
  2>/dev/null

# Check response
echo -e "\n📨 Response:"
if [ -f /tmp/merchant_response.json ]; then
    # Pretty print if jq is available
    if command -v jq &> /dev/null; then
        cat /tmp/merchant_response.json | jq '.' | head -50
    else
        cat /tmp/merchant_response.json | python3 -m json.tool | head -50
    fi
else
    echo "❌ No response file created"
fi

echo -e "\n💡 If you get a 403 or 404 error, the Merchant API might need:"
echo "   - Different authentication (OAuth instead of service account)"
echo "   - API to be enabled in Google Cloud Console"
echo "   - Different endpoint or request format"
echo "   - Merchant Center API access permissions"