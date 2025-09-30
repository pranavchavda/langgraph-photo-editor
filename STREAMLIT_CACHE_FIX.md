# Streamlit Cloud Cache Issue Fix

## Problem
After the merge, Streamlit Cloud shows this error:
```
libgdal32 : Depends: libodbc2 (>= 2.3.1) but it is not going to be installed
             Depends: libodbcinst2 (>= 2.3.1) but it is not going to be installed
E: Unmet dependencies. Try 'apt --fix-broken install' with no packages (or specify a solution).
```

## Root Cause
Streamlit Cloud has cached a broken apt state from a previous deployment where `libgdal32` was installed (possibly from `gmic` or `libmagickwand-dev` which were removed in commit 3bdc047).

## Solution: Force Clean Rebuild

### Option 1: Reboot App (Quickest)
1. Go to your [Streamlit Cloud dashboard](https://share.streamlit.io/)
2. Find your app: `langgraph-photo-editor`
3. Click the **⋮** (three dots menu)
4. Select **"Reboot app"**
5. This forces Streamlit to rebuild from scratch

### Option 2: Clear Cache
1. In the Streamlit Cloud dashboard
2. Click on your app
3. Click **"Manage app"** in the top right
4. Scroll down to **"Clear cache"**
5. Click **"Clear cache"** button
6. Streamlit will rebuild the environment

### Option 3: Trigger Fresh Deployment
Make a trivial change to force redeployment:
```bash
# Add a comment to packages.txt
echo "# Fresh deployment after merge" >> packages.txt
git add packages.txt
git commit -m "Force Streamlit rebuild"
git push origin main
```

### Option 4: Change Python Version (Nuclear Option)
Edit `.streamlit/config.toml`:
```toml
[server]
pythonVersion = "3.11"  # or "3.10" if currently 3.11
```
This forces a complete environment rebuild.

## Why This Happened
The merge brought in quality improvements from main, but Streamlit Cloud cached the old broken apt state. The `libgdal32` package (a GDAL geospatial library) is not needed for this project and should not be installed.

## Prevention
The `packages.txt` has been simplified to only include essential runtime dependencies:
- `imagemagick` - For image processing (required)

Previously problematic packages that caused ODBC dependency issues have been removed:
- ❌ `libmagickwand-dev` (development headers, not needed)
- ❌ `gmic` (pulled in GDAL, not essential)
