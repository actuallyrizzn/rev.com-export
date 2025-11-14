"""
CSS styles for the browser.
"""


def get_css() -> str:
    """Return CSS styles for the browser."""
    return """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h1 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #2c3e50;
        }

        .subtitle {
            color: #666;
            font-size: 1em;
        }

        .search-box {
            margin-top: 20px;
        }

        .search-box input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s;
        }

        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }

        .orders-table {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: #34495e;
            color: white;
        }

        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }

        th:hover {
            background: #2c3e50;
        }

        th.sortable::after {
            content: ' ↕';
            opacity: 0.5;
        }

        th.sort-asc::after {
            content: ' ↑';
            opacity: 1;
        }

        th.sort-desc::after {
            content: ' ↓';
            opacity: 1;
        }

        tbody tr {
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        tbody tr:last-child {
            border-bottom: none;
        }

        td {
            padding: 15px;
        }

        .order-link {
            color: #3498db;
            text-decoration: none;
            font-weight: 600;
        }

        .order-link:hover {
            text-decoration: underline;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .status-complete {
            background: #d4edda;
            color: #155724;
        }

        .file-count {
            color: #666;
            font-size: 0.9em;
        }

        .order-detail {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .order-header {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }

        .order-header h2 {
            font-size: 1.8em;
            margin-bottom: 10px;
            color: #2c3e50;
        }

        .order-meta {
            color: #666;
            font-size: 0.95em;
        }

        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #3498db;
            text-decoration: none;
            font-weight: 600;
        }

        .back-link:hover {
            text-decoration: underline;
        }

        .file-section {
            margin-bottom: 30px;
        }

        .file-section-title {
            font-size: 1.3em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #2c3e50;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }

        .file-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }

        .file-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border: 2px solid transparent;
            transition: all 0.2s;
        }

        .file-item:hover {
            border-color: #3498db;
            background: #f0f7ff;
        }

        .file-name {
            font-weight: 600;
            margin-bottom: 8px;
            word-break: break-word;
        }

        .file-meta {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 10px;
        }

        .file-actions {
            display: flex;
            gap: 10px;
        }

        .file-link {
            color: #3498db;
            text-decoration: none;
            font-size: 0.9em;
        }

        .file-link:hover {
            text-decoration: underline;
        }

        .file-viewer {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .file-content {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .file-content pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.6;
        }

        .file-content .docx-content {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.8;
        }

        .transcript-content {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.8;
        }

        .monologue {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }

        .monologue:last-child {
            border-bottom: none;
        }

        .monologue-header {
            margin-bottom: 10px;
            color: #2c3e50;
            font-size: 1.1em;
        }

        .monologue-header strong {
            color: #3498db;
        }

        .timestamp {
            color: #666;
            font-size: 0.85em;
            font-weight: normal;
            margin-left: 10px;
        }

        .monologue-text {
            color: #333;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #666;
            font-size: 1.1em;
        }

        .hidden {
            display: none !important;
        }
    </style>"""

