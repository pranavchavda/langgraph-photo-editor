#!/bin/bash

echo "🎨 Testing Google Product Studio v1alpha - Generate Background API"
echo "=================================================================="

ACCOUNT_ID="7893408"
TOKEN=$(gcloud auth application-default print-access-token 2>/dev/null)

echo "🏪 Account ID: $ACCOUNT_ID"
echo "🔑 Token obtained: $([ -n "$TOKEN" ] && echo "Yes" || echo "No")"
echo ""

# Product Studio v1alpha endpoint for background generation
ENDPOINT="https://merchantapi.googleapis.com/productstudio/v1alpha/accounts/$ACCOUNT_ID/generatedImages:generateProductImageBackground"

echo "📍 Endpoint: $ENDPOINT"
echo ""

# Create request JSON with your pitcher rinser image
cat > /tmp/productstudio_bg_request.json <<'EOF'
{
   "input_image": {
      "image_uri": "https://cdn.shopify.com/s/files/1/1201/3604/files/PR-2-Inset-Mirror.jpg?v=1700544407&width=2600&crop=center"
   },
   "config": {
      "product_description": "a premium espresso machine pitcher rinser",
      "background_description": "sitting on a marble countertop in a modern coffee shop with warm lighting, professional product photography, clean and minimal aesthetic, high resolution"
   }
}
EOF

echo "📤 Request payload:"
cat /tmp/productstudio_bg_request.json | python3 -m json.tool
echo ""

echo "🚀 Sending request to Product Studio API..."
echo ""

# Make the API call
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "x-goog-user-project: atomic-airship-228716" \
  -d @/tmp/productstudio_bg_request.json \
  "$ENDPOINT" \
  -o /tmp/productstudio_bg_response.json \
  -w "HTTP Status: %{http_code}\n" \
  2>/dev/null

echo ""
echo "📨 Response:"
if [ -f /tmp/productstudio_bg_response.json ]; then
    # Check if response is JSON
    if python3 -c "import json; json.load(open('/tmp/productstudio_bg_response.json'))" 2>/dev/null; then
        cat /tmp/productstudio_bg_response.json | python3 -m json.tool | head -100
        
        # If successful, try to extract the generated image
        python3 <<'PYTHON'
import json
import base64

try:
    with open('/tmp/productstudio_bg_response.json', 'r') as f:
        response = json.load(f)
    
    # Check for generated image in response
    if 'generatedImage' in response:
        print("\n✅ Found generated image in response!")
        
        # Check for different possible fields
        if 'imageUri' in response['generatedImage']:
            print(f"   Image URI: {response['generatedImage']['imageUri']}")
        elif 'imageBytes' in response['generatedImage']:
            print("   Found image bytes, saving to file...")
            image_data = base64.b64decode(response['generatedImage']['imageBytes'])
            with open('/tmp/productstudio_generated.jpg', 'wb') as f:
                f.write(image_data)
            print("   Saved to: /tmp/productstudio_generated.jpg")
    elif 'error' in response:
        print(f"\n❌ API Error: {response['error'].get('message', 'Unknown error')}")
    else:
        print("\n⚠️ Unexpected response structure")
        
except Exception as e:
    print(f"\n⚠️ Could not parse response: {e}")
PYTHON
    else:
        # Not JSON, probably HTML error page
        echo "Response is not JSON (likely an error page):"
        cat /tmp/productstudio_bg_response.json | head -10
    fi
else
    echo "❌ No response file created"
fi

echo ""
echo "💡 If you get a 403/404 error:"
echo "   - The API might require special access or allowlisting"
echo "   - Check if your project is linked to Merchant Center"
echo "   - The endpoint might not be publicly available yet (v1alpha)"