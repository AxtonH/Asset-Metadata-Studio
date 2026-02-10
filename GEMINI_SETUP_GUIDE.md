# Google Gemini 2.0 Flash-Lite Setup Guide

## Option 1: Google AI Studio (Easiest - Recommended for Testing)

### Step 1: Get Your API Key

1. **Go to Google AI Studio:**
   - Visit: https://aistudio.google.com/
   - Sign in with your Google account

2. **Create API Key:**
   - Click "Get API Key" button (top right)
   - Click "Create API Key" 
   - Choose to create in a new project or existing project
   - Copy your API key (starts with `AIza...`)
   - ⚠️ **Important:** Save it immediately - you won't be able to see it again!

3. **Set Usage Limits (Optional but Recommended):**
   - Go to: https://aistudio.google.com/app/apikey
   - Click on your API key
   - Set daily/monthly quotas to prevent unexpected charges
   - Enable billing alerts

### Step 2: Enable Billing (Required for Production)

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Enable Billing:**
   - Go to "Billing" → "Link a billing account"
   - Add a payment method (credit card)
   - Note: Free tier includes $300 credit for new accounts

3. **Enable Required APIs:**
   - Go to "APIs & Services" → "Library"
   - Search for "Generative Language API"
   - Click "Enable"

### Step 3: Test Your API Key

You can test the API key using curl or Python:

```bash
# Test with curl
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Hello, what can you do?"
      }]
    }]
  }'
```

Or with Python:
```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Hello!")
print(response.text)
```

---

## Option 2: Google Vertex AI (Better for Production)

### Step 1: Set Up Google Cloud Project

1. **Create/Select Project:**
   - Go to: https://console.cloud.google.com/
   - Create new project or select existing
   - Note your Project ID

2. **Enable Billing:**
   - Go to "Billing" → "Link a billing account"
   - Add payment method

3. **Enable APIs:**
   - Go to "APIs & Services" → "Library"
   - Enable "Vertex AI API"
   - Enable "Generative Language API"

### Step 2: Create Service Account

1. **Create Service Account:**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it (e.g., "gemini-api-user")
   - Grant role: "Vertex AI User"

2. **Create Key:**
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the JSON file
   - ⚠️ **Keep this file secure!**

### Step 3: Set Environment Variable

Set the path to your service account JSON:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

---

## Pricing & Limits

### Google AI Studio (Free Tier)
- **Free quota:** 15 requests/minute, 1,500 requests/day
- **After free tier:** Pay-as-you-go pricing
- **Best for:** Testing and low-volume usage

### Vertex AI (Production)
- **No free tier** (but $300 credit for new accounts)
- **Better rate limits:** Higher quotas available
- **Better for:** Production workloads

### Gemini 2.0 Flash-Lite Pricing
- **Input:** $0.07 per 1M tokens
- **Output:** $0.30 per 1M tokens
- **Much cheaper than GPT-5-mini!**

---

## Security Best Practices

1. **Never commit API keys to git:**
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Restrict API Key:**
   - In Google AI Studio, restrict key to specific APIs
   - Set IP restrictions if possible
   - Set usage quotas

3. **Rotate keys regularly:**
   - Create new keys periodically
   - Revoke old keys

4. **Monitor usage:**
   - Set up billing alerts
   - Check usage dashboard regularly

---

## Next Steps After Getting API Key

1. **Add to your `.env` file:**
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Code changes needed:**
   - Install `google-generativeai` package
   - Update `openai_client.py` to use Gemini API
   - Adapt response extraction logic
   - Update model configuration

3. **Test with sample images:**
   - Verify quality matches expectations
   - Check response format
   - Ensure metadata extraction works

---

## Troubleshooting

### "API key not valid"
- Check if API key is copied correctly
- Verify Generative Language API is enabled
- Check if billing is enabled (required for production)

### "Quota exceeded"
- Check your usage limits in Google AI Studio
- Increase quotas if needed
- Consider switching to Vertex AI for higher limits

### "Permission denied"
- Verify API is enabled in your project
- Check service account permissions (if using Vertex AI)
- Ensure billing account is linked

---

## Resources

- **Google AI Studio:** https://aistudio.google.com/
- **Gemini API Docs:** https://ai.google.dev/docs
- **Pricing:** https://ai.google.dev/pricing
- **Python SDK:** https://github.com/google/generative-ai-python
