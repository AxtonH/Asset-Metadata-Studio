# Cost Reduction Options Analysis

## Current Setup
- **Model:** GPT-5-mini (or GPT-5-image-mini)
- **Pricing:** $0.25/M input tokens, $2.00/M output tokens
- **Usage:** ~500 assets/day
- **Current optimizations:** Reduced image size, lower reasoning effort, reduced max tokens

---

## Option 1: Different OpenAI Models

### GPT-4o-mini (Cheaper Alternative)
- **Input:** $0.15/M tokens (40% cheaper than GPT-5-mini)
- **Output:** $0.60/M tokens (70% cheaper than GPT-5-mini)
- **Vision:** ✅ Full vision support
- **Quality:** Slightly lower than GPT-5-mini but still excellent
- **Savings:** ~50-60% cost reduction
- **Trade-off:** May need slightly more tokens or retries

### GPT-4 Turbo (Older but Proven)
- **Input:** $10/M tokens (more expensive)
- **Output:** $30/M tokens (much more expensive)
- **Vision:** ✅ Full vision support
- **Verdict:** ❌ Not cost-effective

### GPT-3.5 Turbo (Text Only)
- **Input:** $0.50/M tokens
- **Output:** $1.50/M tokens
- **Vision:** ❌ No vision support
- **Verdict:** ❌ Cannot use for image analysis

---

## Option 2: Non-OpenAI Models

### Google Gemini 2.0 Flash-Lite (BEST VALUE)
- **Input:** $0.07/M tokens (72% cheaper than GPT-5-mini!)
- **Output:** $0.30/M tokens (85% cheaper than GPT-5-mini!)
- **Vision:** ✅ Excellent vision support
- **Context:** 1M tokens
- **Quality:** Very good for structured tasks
- **Savings:** ~75-80% cost reduction potential
- **API:** Google Vertex AI or Google AI Studio
- **Trade-off:** Different API structure, may need code changes

### Google Gemini 2.5 Flash-Lite
- **Input:** $0.10/M tokens (60% cheaper)
- **Output:** $0.40/M tokens (80% cheaper)
- **Vision:** ✅ Excellent vision support
- **Quality:** Slightly better than 2.0 Flash-Lite
- **Savings:** ~70% cost reduction

### Google Gemini 1.5 Flash
- **Input:** $0.075/M tokens
- **Output:** $0.30/M tokens
- **Vision:** ✅ Excellent vision support
- **Savings:** ~75% cost reduction

### Claude Sonnet 4.5 (Anthropic)
- **Input:** $3.00/M tokens (12x MORE expensive!)
- **Output:** $15.00/M tokens (7.5x MORE expensive!)
- **Vision:** ✅ Full vision support
- **Verdict:** ❌ Much more expensive, not suitable

### Claude Haiku 3.5 (Anthropic)
- **Input:** $0.25/M tokens (same as GPT-5-mini)
- **Output:** $1.25/M tokens (37% cheaper)
- **Vision:** ✅ Full vision support
- **Savings:** ~20-30% cost reduction
- **Trade-off:** Different API, may need code changes

---

## Option 3: Third-Party Aggregators

### OpenRouter
- **Benefit:** Access to multiple models through one API
- **Fee:** 5.5% markup (or free tier with 1M requests/month)
- **Models:** Can switch between OpenAI, Google, Anthropic easily
- **Savings:** Can use cheapest available model
- **Trade-off:** Additional layer, but minimal code changes needed

### laozhang.ai / Kie.ai
- **Gemini 2.5 Flash:** $0.025/image (49% discount vs official)
- **Benefit:** Pre-configured, OpenAI-compatible endpoints
- **Savings:** Significant if pricing is per-image
- **Trade-off:** Third-party dependency

---

## Option 4: Additional Optimization Strategies

### A. Image Preprocessing
- **Further reduce image size:** 512px instead of 768px
- **Savings:** Additional 30-40% on input tokens
- **Trade-off:** May affect quality for complex images

### B. Caching/Deduplication
- **Hash-based caching:** Cache results for identical images
- **Savings:** 100% for duplicates (common in templates)
- **Implementation:** Add image hash checking before API call
- **Trade-off:** Requires storage/database

### C. Batch Processing
- **Group similar assets:** Process multiple images in one API call
- **Savings:** Shared context tokens, reduced overhead
- **Trade-off:** More complex error handling

### D. Adaptive Quality
- **Simple assets:** Use lower quality/smaller images
- **Complex assets:** Use higher quality
- **Savings:** 20-30% average reduction
- **Trade-off:** Requires asset classification logic

### E. Prompt Optimization (If Allowed)
- **Shorter prompts:** Reduce from ~2800 to ~1500 chars
- **Savings:** ~30% on input tokens
- **Trade-off:** You mentioned keeping original prompt

### F. Output Token Optimization
- **Reduce max_output_tokens further:** 2000 instead of 3000
- **Savings:** Prevents over-allocation
- **Trade-off:** Risk of truncation (but responses are typically ~300 tokens)

---

## Cost Comparison (Estimated Monthly for 500 assets/day = 15,000 assets/month)

### Assumptions:
- Average: 1400 input tokens, 2300 output tokens per asset
- Total: 21M input tokens, 34.5M output tokens/month

### Cost Estimates:

| Model | Input Cost | Output Cost | Total/Month | Savings vs GPT-5-mini |
|-------|-----------|-------------|-------------|----------------------|
| **GPT-5-mini** (current) | $5.25 | $69.00 | **$74.25** | Baseline |
| GPT-4o-mini | $3.15 | $20.70 | **$23.85** | 68% savings |
| **Gemini 2.0 Flash-Lite** | $1.47 | $10.35 | **$11.82** | **84% savings** ⭐ |
| Gemini 2.5 Flash-Lite | $2.10 | $13.80 | **$15.90** | 79% savings |
| Claude Haiku 3.5 | $5.25 | $43.13 | **$48.38** | 35% savings |

### With Additional Optimizations (512px images, caching 20% duplicates):
- **Gemini 2.0 Flash-Lite:** ~$8-9/month (88% savings!)
- **GPT-4o-mini:** ~$18-19/month (75% savings)

---

## Recommendations (Ranked by Savings Potential)

### 🥇 Best Option: Google Gemini 2.0 Flash-Lite
- **Savings:** 84% cost reduction
- **Quality:** Excellent for structured metadata generation
- **Effort:** Moderate code changes needed
- **Risk:** Low (Google is reliable)
- **Monthly cost:** ~$12 vs $74 (saves $62/month, $744/year)

### 🥈 Second Best: GPT-4o-mini
- **Savings:** 68% cost reduction
- **Quality:** Very good, similar to GPT-5-mini
- **Effort:** Minimal code changes (same API)
- **Risk:** Very low
- **Monthly cost:** ~$24 vs $74 (saves $50/month, $600/year)

### 🥉 Third Best: Add Caching + Further Image Optimization
- **Savings:** 40-50% additional reduction on current setup
- **Quality:** No change
- **Effort:** Moderate (add caching layer)
- **Risk:** Very low
- **Monthly cost:** ~$37-45 vs $74 (saves $29-37/month)

### Combination Approach:
- **Switch to Gemini 2.0 Flash-Lite** + **Add caching** + **512px images**
- **Potential savings:** 90%+ cost reduction
- **Monthly cost:** ~$6-8 vs $74
- **Annual savings:** ~$800/year

---

## Implementation Considerations

### For Gemini Migration:
1. **API Changes:** Different SDK (google-generativeai vs openai)
2. **Response Format:** Different structure, need to adapt extraction
3. **Image Format:** Base64 or URL (similar to OpenAI)
4. **Prompt:** Can use same prompt
5. **Error Handling:** Similar patterns

### For Caching:
1. **Storage:** Need database (SQLite, PostgreSQL, or Redis)
2. **Hashing:** Use image hash (MD5/SHA256) as key
3. **TTL:** Optional expiration for cache
4. **Code Changes:** Add cache check before API call

### For Further Image Optimization:
1. **Config Change:** Update IMAGE_MAX_SIDE to 512
2. **Testing:** Verify quality on complex images
3. **Fallback:** Keep higher quality for edge cases

---

## Next Steps

1. **Test Gemini 2.0 Flash-Lite** with a few sample images to verify quality
2. **Implement caching** for immediate savings on current setup
3. **Consider hybrid approach:** Use Gemini for bulk, GPT-5-mini for complex cases
4. **Monitor quality:** Ensure metadata quality doesn't degrade

---

## Questions to Consider

1. **Quality tolerance:** How much quality reduction is acceptable?
2. **Migration effort:** How quickly do you need to implement changes?
3. **Vendor lock-in:** Prefer multi-vendor (OpenRouter) or single vendor?
4. **Duplicate rate:** What % of your 500 assets/day are duplicates/similar?
5. **Complexity:** Are your assets mostly simple or complex?
