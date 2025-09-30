# Streamlit Cloud Deployment Guide

## Quick Deploy Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add rembg support and model selection"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select your repository: `pranavchavda/langgraph-photo-editor`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Click "Deploy!"

3. **Configure Secrets (Optional)**
   In Streamlit Cloud settings, add secrets:
   ```toml
   ANTHROPIC_API_KEY = "your-key-here"
   GEMINI_API_KEY = "your-key-here"
   REMOVE_BG_API_KEY = "your-key-here"  # Optional
   ```

## What Works on Streamlit Cloud

✅ **Full Support:**
- rembg background removal (all 17+ models)
- ImageMagick optimization
- Lens corrections
- Gemini AI editing
- Claude analysis & QC
- Batch processing
- File upload/download
- WebP/PNG output

✅ **Background Removal Options:**
- **rembg (FREE)**: Works perfectly, no API needed
  - First run downloads models (~170MB-1GB)
  - Models cached in cloud instance
  - All 17 models available
  - Alpha matting supported
- **remove.bg API**: Works with API key
- **Auto mode**: Smart selection

## Important Notes

### Model Downloads
- rembg models download on first use
- Cached in `/home/appuser/.u2net/` on cloud
- Models persist during app session
- May re-download after instance restart

### Performance
- First image with new model: 30-60s (download time)
- Subsequent images: 5-15s
- Batch processing: Works well with 2-3 concurrent

### Memory Limits
- Streamlit Cloud has 1GB RAM limit
- Large models (birefnet-massive) may cause issues
- Recommended models for cloud:
  - `bria-rmbg` (good balance)
  - `u2netp` (lightweight)
  - `silueta` (smaller)

### File Size Limits
- Max upload: 200MB per file
- Batch processing: Keep under 10 images
- Output: WebP format saves space

## Testing Checklist

After deployment, test:

1. [ ] Single image with rembg
2. [ ] Try different rembg models
3. [ ] Batch processing with 3-5 images
4. [ ] Background removal toggle
5. [ ] ImageMagick optimizations
6. [ ] Download processed images
7. [ ] API key persistence (localStorage)

## Troubleshooting

**If rembg fails:**
- Check Streamlit logs for errors
- Try a smaller model (u2netp)
- Restart the app instance

**If ImageMagick fails:**
- It should work (packages.txt handles it)
- Falls back to Gemini if unavailable

**Memory issues:**
- Use smaller models
- Process fewer images in batch
- Reduce concurrent processing

## URL After Deployment

Your app will be available at:
```
https://[your-app-name].streamlit.app
```

Share this URL with users - no installation needed!