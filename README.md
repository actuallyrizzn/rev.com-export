# Rev Exporter

A command-line tool for exporting media files and transcripts from Rev.com accounts.

## Features

- ✅ Export all completed orders from your Rev.com account
- ✅ Download media files and transcripts
- ✅ Idempotent downloads (safe to re-run, no duplicates)
- ✅ Pagination support for accounts with thousands of orders
- ✅ Filter by date, include/exclude media or transcripts
- ✅ Dry-run mode to preview what will be downloaded

## Installation

### Prerequisites

- Python 3.8 or higher
- Rev.com API credentials (Client API Key and User API Key)

### Setup

1. Clone this repository:
```bash
git clone https://github.com/actuallyrizzn/rev.com-export.git
cd rev.com-export
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Configuration

### Environment Variables (Recommended)

Set the following environment variables:

```bash
export REV_CLIENT_API_KEY="your_client_api_key"
export REV_USER_API_KEY="your_user_api_key"
```

### Config File (Alternative)

Create a `config.json` file in the current directory or `~/.rev-exporter/config.json`:

```json
{
  "client_api_key": "your_client_api_key",
  "user_api_key": "your_user_api_key"
}
```

**Note:** Environment variables take precedence over config files.

## Usage

### Test Connection

Test your API credentials:

```bash
rev-exporter test-connection
```

### Sync Orders

Export all completed orders:

```bash
rev-exporter sync
```

### Options

```bash
rev-exporter sync --help
```

Available options:

- `--output-dir PATH`: Output directory (default: `./exports`)
- `--since DATE`: Only export orders placed after this date (format: YYYY-MM-DD)
- `--include-media / --no-include-media`: Include media files (default: True)
- `--include-transcripts / --no-include-transcripts`: Include transcripts (default: True)
- `--dry-run`: Show what would be downloaded without actually downloading
- `--debug`: Enable debug logging

### Examples

Export only transcripts from orders placed after 2024-01-01:

```bash
rev-exporter sync --since 2024-01-01 --no-include-media
```

Preview what would be downloaded:

```bash
rev-exporter sync --dry-run
```

## Output Structure

Exported files are organized as follows:

```
exports/
  <order_number>/
    attachments.json          # Order metadata
    media/
      <attachment_id>_<name>.<ext>
    transcripts/
      <attachment_id>_<name>.<ext>
    other/
      <attachment_id>_<name>.<ext>
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black rev_exporter/

# Lint
flake8 rev_exporter/

# Type checking
mypy rev_exporter/
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
