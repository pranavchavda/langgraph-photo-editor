#!/bin/bash

# Try different Google Shopping/Merchant API endpoints

echo "🔍 Testing different Google Merchant/Shopping API endpoints"
echo "==========================================================="

MERCHANT_ID="7893408"
TOKEN=$(gcloud auth print-access-token 2>/dev/null)

echo "Testing various endpoints:"
echo ""

# Test 1: Content API for Shopping v2.1
echo "1. Content API for Shopping v2.1:"
curl -s -o /dev/null -w "   %{http_code} - " \
  -H "Authorization: Bearer $TOKEN" \
  "https://shoppingcontent.googleapis.com/content/v2.1/accounts/$MERCHANT_ID"
echo "https://shoppingcontent.googleapis.com/content/v2.1/"
echo ""

# Test 2: Merchant API (beta)
echo "2. Merchant API (newer):"
curl -s -o /dev/null -w "   %{http_code} - " \
  -H "Authorization: Bearer $TOKEN" \
  "https://merchantapi.googleapis.com/accounts/v1beta/accounts/$MERCHANT_ID"
echo "https://merchantapi.googleapis.com/accounts/v1beta/"
echo ""

# Test 3: Check if account exists
echo "3. Check merchant account access:"
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://shoppingcontent.googleapis.com/content/v2.1/$MERCHANT_ID/accounts/$MERCHANT_ID" \
  -w "\n   HTTP Status: %{http_code}\n" | head -5
echo ""

echo "💡 Notes:"
echo "- 200/204 = Endpoint exists and you have access"
echo "- 401 = Authentication issue"
echo "- 403 = Permission denied (API not enabled or no access)"
echo "- 404 = Endpoint doesn't exist"
echo ""
echo "The Product Studio AI upscaling might be:"
echo "- Part of a private/beta API"
echo "- Available through the Merchant Center UI only"
echo "- Part of Google Ads API instead"