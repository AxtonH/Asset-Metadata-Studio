# API Requests Analysis

## Current Behavior

### Per File Analysis:

**Image Files (PNG, JPG, SVG, GIF):**
- **1 API request per file**
- Each image file = 1 task = 1 API call

**PPT/PPTX Files:**
- **1 API request per slide**
- Example: A PPT file with 10 slides = 10 API requests
- Example: A PPT file with 50 slides = 50 API requests

### Processing Flow:

1. **File Upload** → File saved
2. **File Processing:**
   - **PPT files**: Converted to images (1 image per slide) → Each slide becomes a task
   - **Image files**: Prepared/optimized → Becomes 1 task
3. **API Calls**: Each task triggers 1 API request to Gemini
4. **Parallel Processing**: Up to `MAX_CONCURRENCY` (default: 8) requests run simultaneously

## Current Statistics

For **500 assets/day**:
- If all are single images: **500 API requests/day**
- If mix of PPTs and images: **Could be 1000-5000+ API requests/day** depending on:
  - Number of PPT files
  - Average slides per PPT
  - Number of image files

## Cost Impact

Each API request includes:
- **Input tokens**: Prompt (~1400 tokens) + Image tokens (varies by size)
- **Output tokens**: ~300 tokens average

With Gemini 2.5 Flash-Lite:
- Input: $0.10/M tokens
- Output: $0.40/M tokens

**Per request cost estimate:**
- Input: ~1400 tokens × $0.10/M = $0.00014
- Image: ~500-1000 tokens (depends on size) × $0.10/M = $0.00005-0.0001
- Output: ~300 tokens × $0.40/M = $0.00012
- **Total per request: ~$0.0003-0.0004**

**Daily cost (500 requests):** ~$0.15-0.20/day
**Monthly cost:** ~$4.50-6.00/month

## Optimization Opportunities

### 1. Batch Multiple Images in One Request
- **Current**: 1 image per API call
- **Potential**: Send multiple images in one API call
- **Savings**: Reduce API overhead, shared prompt tokens
- **Trade-off**: More complex response parsing

### 2. Caching/Deduplication
- **Current**: Every image analyzed, even duplicates
- **Potential**: Hash-based caching for identical images
- **Savings**: 100% for duplicates (common in templates)
- **Implementation**: Add image hash checking before API call

### 3. Reduce Image Size Further
- **Current**: 768px max side
- **Potential**: 512px or even 384px
- **Savings**: 30-50% reduction in image tokens
- **Trade-off**: May affect quality for complex images

### 4. Smart Prompt Caching
- **Current**: Same prompt sent with every request
- **Potential**: Use prompt caching if API supports it
- **Savings**: Reduced input token costs
- **Note**: Check if Gemini supports prompt caching

## Recommendations

1. **Add caching** - Biggest impact if you have duplicate/similar images
2. **Monitor actual usage** - Track requests/day to see real numbers
3. **Consider batch API** - If Gemini supports batch processing
4. **Further image optimization** - Test 512px to see if quality is acceptable
