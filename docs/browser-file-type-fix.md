# Browser File Type Detection Fix - Handoff Document

## Problem Statement

The browser component is incorrectly detecting and displaying file types. Users are seeing:
- SRT files when they expect DOCX files
- JSON files when they expect transcripts
- Files not loading correctly in the viewer

## Root Cause

Files in the export directory have **double extensions** due to how Rev.com API returns data and how files are saved:

**CRITICAL FINDING (Verified):**
- **NO actual `.docx` files exist** - only `.docx.json` files
- **NO actual `.srt` files exist** - only `.srt.srt` files  
- The `.docx.json` files contain JSON transcript data (speakers, timestamps, text elements)
- The `.srt.srt` files are actual SRT caption files (just with double extension)

1. **`.docx.json` files**: These are JSON transcript data, NOT actual DOCX files
   - Example: `UyYuAaMoaAgAAAAABQAAAA_What is a Central Bank Digital Currency.docx.json`
   - Contains JSON transcript data with speakers, timestamps, etc.
   - Should be displayed as formatted JSON, not converted as DOCX

2. **`.srt.srt` files**: These are actual SRT caption files with double extension
   - Example: `lHPhMjkA2AUAAAAABQAAAA_Why Colored Coins didn't work.srt.srt`
   - Should be displayed as plain text (SRT format)

3. **Actual `.docx` files**: May or may not exist - need to check if they're actually DOCX format

## Current Code Issues

### 1. File Scanner (`rev_exporter/browser/file_scanner.py`)

**Current Logic:**
- `_get_real_extension()` tries to detect the "real" extension by stripping double extensions
- `_is_viewable()` marks `.docx.json` files as viewable (correct) but doesn't distinguish between JSON data and actual DOCX

**Problem:**
- The extension detection is working, but the file viewer doesn't know the file is actually JSON content

### 2. File Viewer Template (`rev_exporter/browser/templates.py`)

**Current Logic:**
```python
is_docx = name_lower.endswith('.docx') and not name_lower.endswith('.docx.json')
is_json = name_lower.endswith('.json')
```

**Problem:**
- This correctly identifies `.docx.json` as JSON, BUT
- The file path resolution is wrong - files are in `files/` subdirectory but paths are relative to export root
- The JavaScript tries to load files but path might be incorrect

### 3. File Path Resolution

**Issue:**
- File viewer pages are in `files/file_<hash>.html`
- Files are in `TC0019801683/transcripts/file.docx.json`
- Path needs to be `../TC0019801683/transcripts/file.docx.json` from the viewer page
- Current code uses `file_path_relative = f"../{file_path}"` but this might not work correctly

## What Needs to Be Fixed

### Step 1: Verify Actual File Types on Disk ✅ COMPLETED

**VERIFIED FINDINGS:**
- Only `.docx.json` files exist (no actual `.docx` files)
- `.docx.json` files contain JSON transcript data with structure: `{"speakers": [...], "monologues": [...]}`
- Only `.srt.srt` files exist (no plain `.srt` files)
- Files are correctly saved in order directories

**Original test commands (for reference):**
```powershell
# Check a specific order
Get-ChildItem tmp\rev-export\TC0019801683\transcripts\ | Select-Object Name, Length

# Check if .docx files exist (without .json)
Get-ChildItem tmp\rev-export\TC0019801683\transcripts\*.docx -ErrorAction SilentlyContinue

# Check what .docx.json files contain
Get-Content tmp\rev-export\TC0019801683\transcripts\*.docx.json | Select-Object -First 10
```

**Expected Findings:**
- `.docx.json` files exist and contain JSON transcript data
- Actual `.docx` files (without `.json`) may or may not exist
- Need to determine: Are there BOTH `.docx` and `.docx.json` files, or ONLY `.docx.json`?

### Step 2: Fix File Type Detection ✅ USE OPTION A

**CONFIRMED: Only `.docx.json` files exist (no actual DOCX)**

**Required Fix:**
- Treat ALL `.docx.json` files as JSON transcript data
- **DO NOT** try to convert them with mammoth.js (they're not DOCX files)
- Display as formatted JSON
- The current code incorrectly tries to load them as DOCX

**For `.srt.srt` files:**
- These are actual SRT caption files
- Display as plain text (SRT format)
- Current code should handle this, but verify

### Step 3: Fix File Path Resolution

The file viewer is in `files/file_<hash>.html` and needs to load files from order directories.

**Current path structure:**
```
export_dir/
  index.html
  order_<hash>.html
  files/
    file_<hash>.html  ← File viewer pages are here
  TC0019801683/
    transcripts/
      file.docx.json  ← Actual files are here
```

**Path from file viewer to file:**
- From: `files/file_abc123.html`
- To: `TC0019801683/transcripts/file.docx.json`
- Correct relative path: `../TC0019801683/transcripts/file.docx.json`

**Check current implementation:**
```python
# In generate_file_viewer()
file_path = file_info['path']  # e.g., "TC0019801683/transcripts/file.docx.json"
file_path_relative = f"../{file_path}"  # Should be "../TC0019801683/transcripts/file.docx.json"
```

This should work, but verify:
1. Are paths using forward slashes? (Windows uses backslashes)
2. Is the path correctly escaped in JavaScript?
3. Does fetch() work with file:// protocol?

### Step 4: Fix JavaScript File Loading

**Current issues:**
1. File path encoding in JavaScript string
2. Fetch API with file:// protocol (may have CORS issues)
3. Error handling when files don't exist

**Test in browser console:**
```javascript
// Test if file path is correct
const filePath = "../TC0019801683/transcripts/file.docx.json";
fetch(filePath).then(r => r.text()).then(console.log).catch(console.error);
```

## Recommended Fix Approach

### 0. Key Insight

**The problem is in the file viewer template's JavaScript logic:**

Current code:
```javascript
const isDocx = name_lower.endswith('.docx') && !name_lower.endswith('.docx.json')
```

This evaluates to:
- `"file.docx.json".endswith('.docx')` → `true` (because it ends with `.docx.json`)
- `!"file.docx.json".endswith('.docx.json')` → `false`
- Result: `true && false` = `false` ✅ (correctly identifies as NOT DOCX)

BUT the issue is that the file viewer is still trying to load `.docx.json` files as DOCX in some cases, OR the path resolution is failing.

### 1. Update File Scanner

```python
def _is_viewable(self, file_path: Path) -> bool:
    """Check if file can be viewed in browser."""
    name_lower = file_path.name.lower()
    
    # Files ending in .json are JSON transcript data (viewable)
    if name_lower.endswith('.json'):
        # Check if it's a double extension (e.g., .docx.json, .srt.json)
        # These are JSON transcript data, not metadata files
        if any(name_lower.endswith(ext + '.json') for ext in ['.docx', '.srt', '.txt', '.mp4', '.m4a', '.mp3']):
            return True
        # Plain .json files in root are metadata, not viewable
        return False
    
    # Check for actual content files
    ext = self._get_real_extension(file_path)
    viewable_extensions = {".docx", ".txt", ".srt"}
    return ext in viewable_extensions
```

### 2. Update File Viewer Template ⚠️ PRIMARY FIX NEEDED HERE

**Key changes needed:**

1. **Fix file type detection logic:**
```python
# Check actual file extension (handles double extensions)
name_lower = file_name.lower()

# CRITICAL: Check for JSON transcript files FIRST (before checking for DOCX)
# .docx.json, .srt.json, .txt.json files are JSON transcript data
is_json_transcript = any(
    name_lower.endswith(ext + '.json') 
    for ext in ['.docx', '.srt', '.txt', '.mp4', '.m4a', '.mp3']
)

# Actual DOCX files (must NOT end in .json)
is_docx = name_lower.endswith('.docx') and not is_json_transcript

# SRT files (including .srt.srt double extension, but NOT .srt.json)
is_srt = (name_lower.endswith('.srt') or name_lower.endswith('.srt.srt')) and not is_json_transcript

# TXT files (but NOT .txt.json)
is_txt = name_lower.endswith('.txt') and not is_json_transcript

# Plain JSON files (not double extension)
is_json = name_lower.endswith('.json') and not is_json_transcript
```

**IMPORTANT:** The order matters! Check for JSON transcript files FIRST, then check for actual content files.

2. **Fix path resolution:**
```python
# Ensure forward slashes for web compatibility
file_path_normalized = file_path.replace('\\', '/')
file_path_relative = f"../{file_path_normalized}"
```

3. **Update JavaScript loading logic:**
```javascript
async function loadFile() {
    const contentDiv = document.getElementById('file-content');
    
    try {
        // CRITICAL: Check JSON transcript files FIRST
        if (isJson) {
            // Load and format JSON transcript data
            const response = await fetch(filePath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const json = await response.json();
            contentDiv.innerHTML = `<pre>${escapeHtml(JSON.stringify(json, null, 2))}</pre>`;
            return; // Exit early - don't try DOCX conversion
        }
        
        // Only try DOCX conversion if it's actually a DOCX file
        if (isDocx) {
            // ... mammoth.js conversion ...
        } else if (isTxt || isSrt) {
            // ... text file loading ...
        }
    } catch (error) {
        // ... error handling ...
    }
}
```

**Key fix:** Check `isJson` FIRST and return early. Don't let JSON files fall through to DOCX conversion.

### 3. Test Cases

Create test cases to verify:

1. **`.docx.json` file** → Should display as formatted JSON
2. **`.srt.srt` file** → Should display as plain text
3. **`.txt` file** → Should display as plain text
4. **Actual `.docx` file** (if exists) → Should convert with mammoth.js
5. **File path resolution** → Should load from correct relative path

## Debugging Steps

1. **Check what files actually exist:**
   ```powershell
   Get-ChildItem tmp\rev-export\TC0019801683\transcripts\ | Format-Table Name, Length
   ```

2. **Check file content:**
   ```powershell
   # Check if .docx.json is actually JSON
   Get-Content tmp\rev-export\TC0019801683\transcripts\*.docx.json | ConvertFrom-Json | Select-Object -First 1
   ```

3. **Test in browser:**
   - Open `tmp/rev-export/index.html`
   - Click on an order
   - Click "View" on a file
   - Open browser console (F12)
   - Check for fetch errors
   - Verify file path in network tab

4. **Check generated HTML:**
   - Open a file viewer page source
   - Check the `filePath` variable in JavaScript
   - Verify it's correctly escaped

## Expected Behavior After Fix

1. **`.docx.json` files** → Display as formatted JSON transcript data (NOT try DOCX conversion)
2. **`.srt.srt` files** → Display as SRT caption text
3. **`.txt` files** → Display as plain text
4. **Actual `.docx` files** (if any exist in future) → Convert to HTML and display
5. **All file paths** → Load correctly from relative paths (use forward slashes, proper encoding)
6. **Error handling** → Show clear error messages if files can't be loaded

## Quick Fix Checklist

- [ ] Update `generate_file_viewer()` in `templates.py` to check for JSON transcript files FIRST
- [ ] Ensure `isJson` is checked before `isDocx` in JavaScript
- [ ] Fix path normalization (use forward slashes: `file_path.replace('\\', '/')`)
- [ ] Test with a `.docx.json` file - should show JSON, not try DOCX conversion
- [ ] Test with a `.srt.srt` file - should show SRT text
- [ ] Verify file paths load correctly in browser console
- [ ] Regenerate browser and test in actual browser

## Files to Modify

1. `rev_exporter/browser/file_scanner.py` - File type detection
2. `rev_exporter/browser/templates.py` - File viewer generation
3. Test with: `rev-exporter browse --export-dir tmp/rev-export --no-open`

## Additional Notes

- The file:// protocol may have CORS restrictions in some browsers
- Consider using a local HTTP server for testing if file:// doesn't work
- Path separators: Windows uses `\`, web uses `/` - normalize to `/`
- File names may contain special characters - ensure proper URL encoding

