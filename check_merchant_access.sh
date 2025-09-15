#!/bin/bash

echo "🔍 Checking Merchant Center API access and configuration"
echo "========================================================"

TOKEN=$(gcloud auth print-access-token 2>/dev/null)
ACCOUNT_ID="7893408"

echo "1. Check Content API v2.1 account access:"
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://shoppingcontent.googleapis.com/content/v2.1/accounts/$ACCOUNT_ID" \
  -w "\nHTTP Status: %{http_code}\n" | head -10

echo ""
echo "2. Check Merchant API v1beta account access:"
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://merchantapi.googleapis.com/accounts/v1beta/accounts/$ACCOUNT_ID" \
  -w "\nHTTP Status: %{http_code}\n" | head -10

echo ""
echo "3. List available methods (if accessible):"
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://merchantapi.googleapis.com/\$discovery/rest?version=v1beta" \
  -w "\nHTTP Status: %{http_code}\n" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'resources' in data:
        for resource in data.get('resources', {}).keys():
            print(f'   - {resource}')
except:
    pass
" 2>/dev/null

echo ""
echo "💡 Notes:"
echo "- You may need to link your Google Cloud project to Merchant Center"
echo "- Product Studio might require allowlisting for alpha access"
echo "- Check: https://merchants.google.com/mc/settings"