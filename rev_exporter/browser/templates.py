"""
HTML template generation for the browser.
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from rev_exporter.browser.styles import get_css


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def escape_js_string(text: str) -> str:
    """Escape string for use in JavaScript."""
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_date(date_str: Any) -> str:
    """Format date string for display."""
    if not date_str:
        return "Unknown"
    try:
        if isinstance(date_str, str):
            # Try parsing ISO format
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return str(date_str)


def generate_index(orders: List[Dict[str, Any]], export_dir: str) -> str:
    """Generate index.html with order list."""
    orders_json = json.dumps(orders, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rev.com Export Browser</title>
    {get_css()}
</head>
<body>
    <div class="container">
        <header>
            <h1>📁 Rev.com Export Browser</h1>
            <p class="subtitle">Browse your exported orders and files</p>
            <div class="search-box">
                <input type="text" id="search-input" placeholder="🔍 Search orders by number, status, or date...">
            </div>
        </header>

        <div class="orders-table">
            <table id="orders-table">
                <thead>
                    <tr>
                        <th class="sortable" data-sort="order_number">Order Number</th>
                        <th class="sortable" data-sort="status">Status</th>
                        <th class="sortable" data-sort="placed_on">Date</th>
                        <th>Media Files</th>
                        <th>Transcripts</th>
                        <th>Other Files</th>
                    </tr>
                </thead>
                <tbody id="orders-tbody">
                </tbody>
            </table>
        </div>

        <div id="no-results" class="no-results hidden">No orders found matching your search.</div>
    </div>

    <script>
        const orders = {orders_json};
        let currentSort = {{ field: null, direction: 'asc' }};

        function renderOrders(filteredOrders) {{
            const tbody = document.getElementById('orders-tbody');
            const noResults = document.getElementById('no-results');
            const table = document.getElementById('orders-table');

            if (filteredOrders.length === 0) {{
                table.classList.add('hidden');
                noResults.classList.remove('hidden');
                return;
            }}

            table.classList.remove('hidden');
            noResults.classList.add('hidden');

            tbody.innerHTML = filteredOrders.map(order => {{
                const date = formatDate(order.placed_on);
                return `
                    <tr>
                        <td><a href="order_${{order.file_hash}}.html" class="order-link">${{escapeHtml(order.order_number)}}</a></td>
                        <td><span class="status-badge status-${{order.status.toLowerCase()}}">${{escapeHtml(order.status)}}</span></td>
                        <td>${{escapeHtml(date)}}</td>
                        <td class="file-count">${{order.media_files.length}}</td>
                        <td class="file-count">${{order.transcript_files.length}}</td>
                        <td class="file-count">${{order.other_files.length}}</td>
                    </tr>
                `;
            }}).join('');
        }}

        function formatDate(dateStr) {{
            if (!dateStr) return 'Unknown';
            try {{
                const date = new Date(dateStr);
                return date.toISOString().split('T')[0];
            }} catch {{
                return dateStr;
            }}
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function filterOrders() {{
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const filtered = orders.filter(order => {{
                return order.order_number.toLowerCase().includes(searchTerm) ||
                       order.status.toLowerCase().includes(searchTerm) ||
                       (order.placed_on && order.placed_on.toLowerCase().includes(searchTerm));
            }});
            renderOrders(filtered);
        }}

        function sortOrders(field) {{
            if (currentSort.field === field) {{
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            }} else {{
                currentSort.field = field;
                currentSort.direction = 'asc';
            }}

            // Update header classes
            document.querySelectorAll('th.sortable').forEach(th => {{
                th.classList.remove('sort-asc', 'sort-desc');
                if (th.dataset.sort === field) {{
                    th.classList.add(`sort-${{currentSort.direction}}`);
                }}
            }});

            // Sort orders
            const sorted = [...orders].sort((a, b) => {{
                let aVal = a[field] || '';
                let bVal = b[field] || '';
                
                if (field === 'placed_on') {{
                    aVal = aVal ? new Date(aVal).getTime() : 0;
                    bVal = bVal ? new Date(bVal).getTime() : 0;
                }} else {{
                    aVal = String(aVal).toLowerCase();
                    bVal = String(bVal).toLowerCase();
                }}

                if (currentSort.direction === 'asc') {{
                    return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
                }} else {{
                    return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
                }}
            }});

            renderOrders(sorted);
        }}

        // Initialize
        renderOrders(orders);

        // Search functionality
        document.getElementById('search-input').addEventListener('input', filterOrders);

        // Sort functionality
        document.querySelectorAll('th.sortable').forEach(th => {{
            th.addEventListener('click', () => sortOrders(th.dataset.sort));
        }});
    </script>
</body>
</html>"""

    return html


def generate_order_detail(order: Dict[str, Any], export_dir: str) -> str:
    """Generate order detail page."""
    order_json = json.dumps(order, indent=2)

    def file_section(title: str, files: List[Dict[str, Any]], icon: str) -> str:
        if not files:
            return ""
        return f"""
            <div class="file-section">
                <div class="file-section-title">{icon} {title} ({len(files)})</div>
                <div class="file-list">
                    {''.join([
                        f"""
                        <div class="file-item">
                            <div class="file-name">{escape_html(f['name'])}</div>
                            <div class="file-meta">
                                {f['size']:,} bytes • {f['extension']}
                            </div>
                            <div class="file-actions">
                                <a href="files/file_{f['file_hash']}.html" class="file-link">📄 View</a>
                                <a href="{escape_html(f['path'])}" class="file-link" download>📥 Download</a>
                            </div>
                        </div>
                        """
                        for f in files
                    ])}
                </div>
            </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order {escape_html(order['order_number'])} - Rev.com Export Browser</title>
    {get_css()}
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Orders</a>

        <div class="order-detail">
            <div class="order-header">
                <h2>{escape_html(order['order_number'])}</h2>
                <div class="order-meta">
                    Status: <span class="status-badge status-{order['status'].lower()}">{escape_html(order['status'])}</span>
                    • Date: {escape_html(format_date(order['placed_on']))}
                </div>
            </div>

            {file_section('Media Files', order['media_files'], '🎬')}
            {file_section('Transcripts & Captions', order['transcript_files'], '📄')}
            {file_section('Other Files', order['other_files'], '📦')}
        </div>
    </div>
</body>
</html>"""

    return html


def generate_file_viewer(file_info: Dict[str, Any], order_hash: str, export_dir: str) -> str:
    """Generate file viewer page."""
    file_path = file_info['path']
    file_name = file_info['name']
    file_ext = file_info['extension']
    
    # Since this page is in files/ subdirectory, we need to go up one level for the file path
    # Path is already normalized with forward slashes from scanner
    file_path_relative = f"../{file_path}"
    
    # Check actual file extension (handles double extensions)
    # CRITICAL: Check for JSON transcript files FIRST (before checking for DOCX)
    # .docx.json, .srt.json, .txt.json files are JSON transcript data, not actual DOCX/SRT/TXT
    name_lower = file_name.lower()
    
    # Check if it's a JSON transcript file (double extension like .docx.json, .srt.json)
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
    
    # JSON files (either JSON transcript files or plain JSON)
    is_json = name_lower.endswith('.json')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(file_name)} - Rev.com Export Browser</title>
    {get_css()}
    {'''
    <script src="https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js"></script>
    ''' if is_docx else ''}
</head>
<body>
    <div class="container">
        <a href="order_{order_hash}.html" class="back-link">← Back to Order</a>
        <a href="index.html" class="back-link" style="margin-left: 20px;">← All Orders</a>

        <div class="file-viewer">
            <div class="order-header">
                <h2>{escape_html(file_name)}</h2>
                <div class="order-meta">
                    {file_info['size']:,} bytes • {file_ext}
                </div>
            </div>

            <div class="file-actions" style="margin-bottom: 20px;">
                <a href="{escape_html(file_path_relative)}" class="file-link" download>📥 Download File</a>
            </div>

            <div class="file-content" id="file-content">
                <div class="loading">Loading file content...</div>
            </div>
        </div>
    </div>

    <script>
        const filePath = "{escape_js_string(file_path_relative)}";
        const isDocx = {str(is_docx).lower()};
        const isTxt = {str(is_txt).lower()};
        const isSrt = {str(is_srt).lower()};
        const isJson = {str(is_json).lower()};

        async function loadFile() {{
            const contentDiv = document.getElementById('file-content');

            try {{
                // Encode the file path to handle special characters (like #, spaces, etc.)
                const encodedPath = encodeURI(filePath);
                
                // CRITICAL: Check JSON transcript files FIRST (before DOCX conversion)
                // .docx.json, .srt.json files are JSON transcript data, not actual DOCX/SRT files
                if (isJson) {{
                    // Load and format JSON transcript data
                    const response = await fetch(encodedPath);
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    const json = await response.json();
                    
                    // Check if this is a Rev.com transcript JSON structure
                    if (json.speakers && json.monologues) {{
                        // Format as readable transcript
                        let transcriptHtml = '<div class="transcript-content">';
                        
                        // Build speaker map for quick lookup
                        const speakerMap = {{}};
                        if (json.speakers) {{
                            json.speakers.forEach((speaker, idx) => {{
                                speakerMap[idx] = speaker.name || `Speaker ${{idx + 1}}`;
                            }});
                        }}
                        
                        // Process each monologue
                        json.monologues.forEach((monologue) => {{
                            const speakerName = monologue.speaker_name || speakerMap[monologue.speaker] || 'Unknown Speaker';
                            // Get timestamp from first element if available
                            const firstElement = monologue.elements && monologue.elements.length > 0 ? monologue.elements[0] : null;
                            const timestamp = firstElement?.timestamp || '';
                            
                            transcriptHtml += `<div class="monologue">`;
                            
                            // Speaker header with timestamp
                            if (timestamp) {{
                                transcriptHtml += `<div class="monologue-header"><strong>${{escapeHtml(speakerName)}}</strong> <span class="timestamp">[${{escapeHtml(timestamp)}}]</span></div>`;
                            }} else {{
                                transcriptHtml += `<div class="monologue-header"><strong>${{escapeHtml(speakerName)}}</strong></div>`;
                            }}
                            
                            // Build text from elements
                            let monologueText = '';
                            if (monologue.elements) {{
                                monologue.elements.forEach((element) => {{
                                    if (element.type === 'text' && element.value) {{
                                        monologueText += element.value;
                                    }}
                                }});
                            }}
                            
                            // Display the text
                            transcriptHtml += `<div class="monologue-text">${{escapeHtml(monologueText)}}</div>`;
                            transcriptHtml += `</div>`;
                        }});
                        
                        transcriptHtml += '</div>';
                        contentDiv.innerHTML = transcriptHtml;
                    }} else {{
                        // Not a transcript JSON, show as formatted JSON
                        contentDiv.innerHTML = `<pre>${{escapeHtml(JSON.stringify(json, null, 2))}}</pre>`;
                    }}
                    return; // Exit early - don't try DOCX conversion
                }}
                
                // Only try DOCX conversion if it's actually a DOCX file (not .docx.json)
                if (isDocx) {{
                    // Load DOCX using mammoth.js
                    if (typeof mammoth === 'undefined') {{
                        contentDiv.innerHTML = '<p style="color: red;">Error: mammoth.js library not loaded. Please check your internet connection.</p>';
                        return;
                    }}

                    const response = await fetch(encodedPath);
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    const arrayBuffer = await response.arrayBuffer();
                    
                    const result = await mammoth.convertToHtml({{ arrayBuffer: arrayBuffer }});
                    contentDiv.innerHTML = `<div class="docx-content">${{result.value}}</div>`;
                    
                    if (result.messages.length > 0) {{
                        console.warn('DOCX conversion warnings:', result.messages);
                    }}
                }} else if (isTxt || isSrt) {{
                    // Load text file (TXT or SRT)
                    const response = await fetch(encodedPath);
                    if (!response.ok) {{
                        throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                    }}
                    const text = await response.text();
                    contentDiv.innerHTML = `<pre>${{escapeHtml(text)}}</pre>`;
                }} else {{
                    contentDiv.innerHTML = '<p>This file type cannot be previewed. Please download the file to view it.</p>';
                }}
            }} catch (error) {{
                contentDiv.innerHTML = `<p style="color: red;">Error loading file: ${{escapeHtml(error.message)}}</p>`;
                console.error('Error loading file:', error);
            }}
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // Load file when page loads
        loadFile();
    </script>
</body>
</html>"""

    return html

