# TaxiWatch - API Keys Setup Guide

## 🔑 Required API Keys for Full E2E Implementation

To have a **fully functional end-to-end application**, you need to configure these API keys:

---

## 1. **OpenAI API Key** (REQUIRED for AI features)

### What it's used for:
- ✅ Chat assistant (`/chat` page)
- ✅ Incident detection via Vision API
- ✅ Driver behavior analysis
- ✅ Natural language incident summaries

### How to get it:
1. Go to: https://platform.openai.com/account/api-keys
2. Sign up or login with your account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. **Keep it secret** - don't share or commit to git

### Where to put it:
```bash
# File: backend/.env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Cost:
- **Chat (GPT-4o-mini):** ~$0.15 per 1M tokens
- **Vision (GPT-4o-mini):** ~$0.01 per image (small images)
- Free tier: $5 credit (usually sufficient for testing)

### Test without it:
- ❌ Chat will fail
- ❌ Video analysis will fail
- ✅ Everything else still works

### Fallback:
- Chat returns keyword-based responses
- Vision analysis returns mock results

---

## 2. **Mapbox API Token** (REQUIRED for maps)

### What it's used for:
- ✅ Dashboard live map
- ✅ Live Map page (`/map`)
- ✅ Vehicle detail map
- ✅ GPS tracking visualization

### How to get it:
1. Go to: https://account.mapbox.com/auth/signup/
2. Sign up with email
3. Verify email
4. Go to: https://account.mapbox.com/tokens/
5. Click "Create a token"
6. Name it "TaxiWatch" (or any name)
7. Enable "Public scopes" 
8. Click "Create token"
9. Copy the token (starts with `pk.`)

### Where to put it:
```bash
# File: ui/.env.local
NEXT_PUBLIC_MAPBOX_TOKEN=pk-your-actual-token-here
```

### Cost:
- **Free tier:** 50,000 static requests/month
- **Free tier:** 25,000 vector tiles requests/month
- Perfect for testing and development
- No credit card required

### Test without it:
- ❌ Maps won't display
- ❌ Map pages show blank
- ✅ Everything else works

### Fallback:
- Map component fails gracefully
- API still works normally

---

## 3. **Optional: AWS Credentials** (for production S3 storage)

### What they're used for:
- Video frame storage (S3)
- Camera footage backup
- Static file hosting

### How to get them:
1. Create AWS account: https://aws.amazon.com/
2. Go to: https://console.aws.amazon.com/iam/
3. Create new user with S3 permissions
4. Generate access key ID and secret
5. Note down both values

### Where to put it (optional):
```bash
# File: backend/.env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
S3_BUCKET_FRAMES=taxiwatch-frames
S3_BUCKET_VIDEOS=taxiwatch-videos
```

### Cost:
- S3: ~$0.023 per GB stored
- Free tier: 1GB storage free (first year)

### Test without it:
- ✅ System still fully functional
- ⚠️ Videos stored locally instead of S3
- ✅ All features work for development

### Fallback:
- Local filesystem storage (`/media` folder)
- Works perfectly for testing

---

## 📋 Complete Setup Checklist

### Minimum for Testing (2 keys needed):
```
[ ] OpenAI API key configured in backend/.env
[ ] Mapbox token configured in ui/.env.local
```

### Full Production Setup (optional 3rd key):
```
[ ] OpenAI API key configured
[ ] Mapbox token configured
[ ] AWS credentials configured (optional, for S3)
```

---

## 🚀 Quick Setup Steps

### Step 1: Get OpenAI Key
```bash
# Go to https://platform.openai.com/account/api-keys
# Copy your key, then:
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env
```

### Step 2: Get Mapbox Token
```bash
# Go to https://account.mapbox.com/tokens/
# Copy your token, then:
echo "NEXT_PUBLIC_MAPBOX_TOKEN=pk-your-token-here" >> ui/.env.local
```

### Step 3: Verify Setup
```bash
# Backend
grep OPENAI_API_KEY backend/.env

# Frontend
grep NEXT_PUBLIC_MAPBOX_TOKEN ui/.env.local
```

### Step 4: Restart Services
```bash
docker-compose restart backend
cd ui && npm run dev
```

---

## 🧪 What Works Without API Keys

### Without OpenAI Key:
- ✅ Login/registration
- ✅ Vehicle management
- ✅ GPS tracking
- ✅ Device management
- ✅ FAQ viewing
- ✅ User management
- ❌ Chat with AI
- ❌ Incident detection via Vision API

### Without Mapbox Token:
- ✅ All API endpoints
- ✅ Chat
- ✅ Vehicle CRUD
- ✅ Device management
- ✅ GPS data retrieval
- ❌ Map visualization
- ❌ Live map page
- ❌ Dashboard map

### With Both Keys:
- ✅ **EVERYTHING** works perfectly!

---

## 🔒 Security Best Practices

### Do's:
```bash
✅ Keep API keys in .env file
✅ Never commit .env to git
✅ Add .env to .gitignore (already done)
✅ Use restricted API keys for production
✅ Rotate keys regularly
✅ Monitor API usage and billing
```

### Don'ts:
```bash
❌ Don't hardcode keys in source code
❌ Don't share keys in chat/email
❌ Don't use production keys for testing
❌ Don't commit .env file to git
❌ Don't expose keys in frontend (use backend proxy)
```

### Check if keys are exposed:
```bash
# Make sure .env is not tracked
git status | grep ".env"

# If it shows .env, remove it:
git rm --cached backend/.env ui/.env.local
```

---

## 💰 Estimated Monthly Costs (with free tiers)

| Service | Free Tier | Paid |
|---------|-----------|------|
| **OpenAI** | $5 credits | $0.15 per 1M tokens |
| **Mapbox** | 50K requests/month | Pay-as-you-go |
| **AWS S3** | 1GB storage | ~$0.023/GB |
| **Total** | **Free** | **~$10-50/month** |

---

## 🧪 Testing Each Feature

### Test Chat (requires OpenAI key):
```bash
# Go to http://localhost:3000/chat
# Type: "How many vehicles are in the fleet?"
# Should get AI response, not error
```

### Test Map (requires Mapbox token):
```bash
# Go to http://localhost:3000/map
# Should see interactive Mapbox map with vehicles
# Not a blank/grey area
```

### Test Video Analysis (requires OpenAI key):
```bash
# Go to /admin and upload image
# Should analyze for incidents
# Not return error
```

---

## 🆘 Troubleshooting

### "OpenAI API key is not valid"
```
Solution:
1. Check you copied the full key (should start with sk-)
2. Key must be from current account, not expired
3. Key must have API usage enabled
4. Restart backend: docker-compose restart backend
```

### "Mapbox token is invalid"
```
Solution:
1. Check you copied the full token (should start with pk.)
2. Token must have public scopes enabled
3. Token should not be expired
4. Restart frontend: cd ui && npm run dev
```

### "Can't see API key" (terminal):
```bash
# View backend key (hidden)
cat backend/.env | grep OPENAI

# View frontend key (public, that's okay)
cat ui/.env.local | grep MAPBOX
```

### "Getting rate limited"
```
Solution:
1. Check your API usage: https://platform.openai.com/usage
2. May have hit free tier limit
3. Consider upgrading to paid tier
4. Add rate limiting in backend (future optimization)
```

---

## ✅ Verification Commands

```bash
# Check both keys are set and non-empty
echo "=== BACKEND ==="
grep OPENAI_API_KEY backend/.env | grep -v "your-"

echo "=== FRONTEND ==="
grep NEXT_PUBLIC_MAPBOX_TOKEN ui/.env.local | grep -v "pk.your"

# Test OpenAI key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $(grep OPENAI_API_KEY backend/.env | cut -d= -f2)"

# Test Mapbox token is valid
curl "https://api.mapbox.com/tokens/v2?access_token=$(grep NEXT_PUBLIC_MAPBOX_TOKEN ui/.env.local | cut -d= -f2)"
```

---

## 📚 Additional Resources

- **OpenAI Documentation:** https://platform.openai.com/docs
- **Mapbox Documentation:** https://docs.mapbox.com/
- **AWS Documentation:** https://docs.aws.amazon.com/s3/
- **TaxiWatch .env.testing:** Check `.env.testing` for full config reference

---

## 🎯 Next Steps

1. ✅ Get OpenAI API key (5 min)
2. ✅ Get Mapbox token (5 min)
3. ✅ Update .env files (2 min)
4. ✅ Restart services (1 min)
5. ✅ Test all features (10 min)
6. ✅ System fully functional! 🚀

---

## Summary

| Feature | API Key | Required | Cost |
|---------|---------|----------|------|
| Chat | OpenAI | ✅ Yes* | $5 free |
| Maps | Mapbox | ✅ Yes* | Free |
| Video Analysis | OpenAI | ✅ Yes* | $5 free |
| GPS Tracking | None | ❌ No | Free |
| Vehicle Mgmt | None | ❌ No | Free |
| Device Mgmt | None | ❌ No | Free |
| User Mgmt | None | ❌ No | Free |
| Admin Panel | None | ❌ No | Free |

*Can test without, will use fallbacks

---

**With both API keys configured, your TaxiWatch system is 100% feature-complete! 🚀**
