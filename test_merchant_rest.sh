#!/bin/bash

# Test Google Merchant API REST endpoint for image upscaling
# Based on the pattern from the documentation

echo "🔍 Testing Merchant API REST endpoints for image upscaling"
echo "=========================================================="

ACCOUNT_ID="7893408"
TOKEN=$(gcloud auth print-access-token 2>/dev/null)
IMAGE_PATH="/home/pranav/langgraph-photo-editor/enhanced_enhanced_nurri-cropped (4).jpg"

# Encode image
IMAGE_BASE64=$(base64 -w 0 "$IMAGE_PATH" 2>/dev/null | head -c 10000)  # Truncate for testing

echo "🏪 Account ID: $ACCOUNT_ID"
echo "🔑 Token obtained: $([ -n "$TOKEN" ] && echo "Yes" || echo "No")"
echo ""

# Try different possible endpoint patterns
echo "Testing possible REST endpoints:"
echo ""

# Pattern 1: Based on typical Google API patterns
echo "1. merchantapi.googleapis.com/v1beta pattern:"
ENDPOINT="https://merchantapi.googleapis.com/v1beta/accounts/$ACCOUNT_ID:upscaleProductImage"
echo "   Testing: $ENDPOINT"
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputImage":{"imageBytes":"'$IMAGE_BASE64'"}}' \
  "$ENDPOINT" \
  -w "   Status: %{http_code}\n" \
  -o /tmp/test1.json 2>/dev/null
[ -f /tmp/test1.json ] && echo "   Response: $(cat /tmp/test1.json | head -c 200)"
echo ""

# Pattern 2: Under images path
echo "2. merchantapi.googleapis.com/v1beta/accounts/images pattern:"
ENDPOINT="https://merchantapi.googleapis.com/v1beta/accounts/$ACCOUNT_ID/images:upscale"
echo "   Testing: $ENDPOINT"
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputImage":{"imageBytes":"'$IMAGE_BASE64'"}}' \
  "$ENDPOINT" \
  -w "   Status: %{http_code}\n" \
  -o /tmp/test2.json 2>/dev/null
[ -f /tmp/test2.json ] && echo "   Response: $(cat /tmp/test2.json | head -c 200)"
echo ""

# Pattern 3: Shopping Content API pattern
echo "3. shoppingcontent.googleapis.com pattern:"
ENDPOINT="https://shoppingcontent.googleapis.com/content/v2.1/$ACCOUNT_ID/productimages:upscale"
echo "   Testing: $ENDPOINT"
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputImage":{"imageBytes":"'$IMAGE_BASE64'"}}' \
  "$ENDPOINT" \
  -w "   Status: %{http_code}\n" \
  -o /tmp/test3.json 2>/dev/null
[ -f /tmp/test3.json ] && echo "   Response: $(cat /tmp/test3.json | head -c 200)"
echo ""

echo "💡 If all return 404, the feature might:"
echo "   - Only be available via client libraries"
echo "   - Be in private preview"
echo "   - Require special API access"