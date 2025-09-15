#!/bin/bash

# Test Google AI Upscaling API with a local image

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 Testing Google AI Upscaling API${NC}"
echo "=================================="

# Check if test image exists, create if not
TEST_IMAGE="/tmp/test_upscale.jpg"
if [ ! -f "$TEST_IMAGE" ]; then
    echo -e "${YELLOW}Creating test image (256x256)...${NC}"
    # Use ImageMagick to create a simple test image
    convert -size 256x256 gradient:blue-red "$TEST_IMAGE"
    echo -e "${GREEN}✅ Test image created at $TEST_IMAGE${NC}"
fi

# Get image size
SIZE=$(identify -format "%wx%h" "$TEST_IMAGE")
echo -e "📐 Test image size: ${GREEN}$SIZE${NC}"

# Encode image to base64
echo -e "${YELLOW}Encoding image to base64...${NC}"
IMAGE_BASE64=$(base64 -w 0 "$TEST_IMAGE")

# Get auth token
echo -e "${YELLOW}Getting auth token...${NC}"
TOKEN=$(gcloud auth print-access-token 2>/dev/null)
if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get auth token. Make sure gcloud is authenticated.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Got auth token${NC}"

# Set project ID (use default or from environment)
PROJECT_ID=${GCP_PROJECT_ID:-"atomic-airship-228716"}
echo -e "🔧 Using project: ${GREEN}$PROJECT_ID${NC}"

# Prepare the request JSON
REQUEST_JSON=$(cat <<EOF
{
  "instances": [
    {
      "image": {
        "bytesBase64Encoded": "$IMAGE_BASE64"
      }
    }
  ],
  "parameters": {
    "sampleCount": 1,
    "mode": "upscale",
    "upscaleConfig": {
      "upscaleFactor": "x2"
    }
  }
}
EOF
)

# Save request to file for debugging
echo "$REQUEST_JSON" > /tmp/upscale_request.json
echo -e "${YELLOW}Request saved to /tmp/upscale_request.json${NC}"

# API endpoint for Vertex AI image generation/upscaling
API_ENDPOINT="https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/us-central1/publishers/google/models/imagegeneration:predict"

echo -e "\n${YELLOW}📤 Sending request to Vertex AI...${NC}"
echo -e "Endpoint: $API_ENDPOINT"

# Make the API call
RESPONSE=$(curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON" \
  "$API_ENDPOINT" 2>/dev/null)

# Check if response is empty
if [ -z "$RESPONSE" ]; then
    echo -e "${RED}❌ Empty response from API${NC}"
    exit 1
fi

# Save response for debugging
echo "$RESPONSE" > /tmp/upscale_response.json
echo -e "${YELLOW}Response saved to /tmp/upscale_response.json${NC}"

# Check for error in response
if echo "$RESPONSE" | grep -q '"error"'; then
    echo -e "${RED}❌ API returned an error:${NC}"
    echo "$RESPONSE" | python3 -m json.tool
    exit 1
fi

# Extract the upscaled image from response
echo -e "\n${YELLOW}Extracting upscaled image...${NC}"

# Use Python to parse JSON and extract image
python3 <<PYTHON_SCRIPT
import json
import base64

try:
    with open('/tmp/upscale_response.json', 'r') as f:
        response = json.load(f)
    
    if 'predictions' in response and len(response['predictions']) > 0:
        prediction = response['predictions'][0]
        if 'bytesBase64Encoded' in prediction:
            image_data = base64.b64decode(prediction['bytesBase64Encoded'])
            output_path = '/tmp/test_upscaled.png'
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ Upscaled image saved to {output_path}")
        else:
            print("❌ No image data in prediction")
            print(json.dumps(prediction, indent=2))
    else:
        print("❌ No predictions in response")
        print(json.dumps(response, indent=2))
except Exception as e:
    print(f"❌ Error processing response: {e}")
PYTHON_SCRIPT

# Check if upscaled image was created
if [ -f "/tmp/test_upscaled.png" ]; then
    UPSCALED_SIZE=$(identify -format "%wx%h" "/tmp/test_upscaled.png")
    echo -e "\n${GREEN}🎉 SUCCESS!${NC}"
    echo -e "Original size: $SIZE"
    echo -e "Upscaled size: ${GREEN}$UPSCALED_SIZE${NC}"
    echo -e "Output saved to: /tmp/test_upscaled.png"
    
    # Open the image if possible
    if command -v xdg-open &> /dev/null; then
        echo -e "\n${YELLOW}Opening upscaled image...${NC}"
        xdg-open /tmp/test_upscaled.png
    fi
else
    echo -e "${RED}❌ Failed to create upscaled image${NC}"
    echo -e "Check /tmp/upscale_response.json for details"
fi