# Browser Component Plan

## Overview
A Python-based static HTML generator for viewing and browsing exported Rev.com orders and files. Generates flat HTML files that can be opened directly in a browser.

## Requirements

### Core Features
1. **List View** - Display all orders in a clean, sortable table/list (not cards)
2. **Complete Data** - Show all orders and files, ensure nothing is missing
3. **File Browsing** - Actually read and display file contents embedded in HTML
4. **DOCX Support** - Read and display DOCX transcript files in the browser
5. **Order Details** - Individual HTML pages for each order
6. **File Viewers** - Individual HTML pages for viewing file contents
7. **Search/Filter** - Client-side JavaScript search/filter functionality

### Technical Stack
- **Static Site Generator**: Python script that generates HTML files
- **DOCX Reader**: JavaScript library (mammoth.js or docx-preview) to convert DOCX in browser
- **File Reading**: JavaScript FileReader/Fetch API for reading files
- **UI**: Clean, modern HTML/CSS/JS with list-based layout, all self-contained

## Architecture

### Components

1. **`rev_exporter/browser/`** - New package for browser generation
   - `generator.py` - Main generator that orchestrates everything
   - `file_scanner.py` - Scan export directory and build complete index
   - `templates.py` - HTML template generation functions
   - `styles.py` - CSS generation

2. **CLI Integration**
   - Add `rev-exporter browse` command
   - Takes `--export-dir` parameter (defaults to `./exports`)
   - Generates static HTML files in export directory
   - Opens index.html in default browser

### Data Flow

1. **Scan**: Scan export directory, build complete index of all orders and files
2. **Generate Index**: Create `index.html` with list of all orders
3. **Generate Order Pages**: Create `order_<order_number>.html` for each order
4. **Generate File Viewers**: Create `file_<hash>.html` for each viewable file
5. **Include JS Libraries**: Bundle mammoth.js (or similar) for DOCX conversion
6. **Client-Side Rendering**: JavaScript loads and converts DOCX files on demand

### File Structure (Generated)

```
export_dir/
  index.html                    # Main order list
  order_TC0634956651.html      # Order detail page
  order_TC0602955340.html
  ...
  files/
    file_abc123.html            # File viewer pages
    file_def456.html
    ...
  [existing export structure]
```

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] Create `rev_exporter/browser/` package structure
- [ ] Create file scanner to index export directory completely
- [ ] Research and choose JavaScript DOCX library (mammoth.js recommended)

### Phase 2: HTML Generation
- [ ] Create index.html generator (order list table)
- [ ] Create order detail page generator
- [ ] Create file viewer page generator
- [ ] Include JavaScript DOCX library (CDN or bundled)
- [ ] Generate CSS styles

### Phase 3: UI & Navigation
- [ ] Design clean list-based UI
- [ ] Add client-side search/filter JavaScript
- [ ] Add sorting functionality
- [ ] Create navigation between pages
- [ ] Implement DOCX file loading and conversion in JavaScript
- [ ] Style file content display
- [ ] Handle TXT files (simple fetch and display)

### Phase 4: CLI Integration
- [ ] Add `browse` command to CLI
- [ ] Handle export directory parameter
- [ ] Generate all HTML files
- [ ] Open index.html in browser

### Phase 5: Polish
- [ ] Ensure all files are indexed and linked
- [ ] Improve file content formatting
- [ ] Add metadata display
- [ ] Test with real export data
- [ ] Handle edge cases (missing files, etc.)

## File Structure (Source)

```
rev_exporter/
  browser/
    __init__.py
    generator.py          # Main generator
    file_scanner.py        # Directory scanning
    templates.py           # HTML template functions
    styles.py             # CSS generation
```

## JavaScript Libraries

- **mammoth.js** - Converts DOCX to HTML (via CDN: https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js)
- Or bundle a local copy if needed for offline use

## Generated HTML Pages

- `index.html` - Order list (table view with sortable columns)
- `order_<order_number>.html` - Order detail with all files
- `files/file_<hash>.html` - Individual file viewer pages

## Dependencies to Add

- None! (JavaScript libraries loaded via CDN or bundled)

## Usage

```bash
# Generate browser
rev-exporter browse --export-dir tmp/rev-export

# Generates HTML files and opens index.html in browser
# All files are static and can be opened directly
```

