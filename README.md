# Rev Exporter

A command-line tool for exporting your complete Rev.com workspace archive, including all media files and transcripts.

## About This Project

Before AI transcription services became ubiquitous, [Rev.com](http://rev.com) was the go-to platform for professional transcription services. Many of us built up substantial archives of transcriptions over the years—interviews, podcasts, meetings, and more. As the industry shifted toward AI-driven solutions, those archives remained locked in Rev's platform.

This tool was born out of that need: a simple, reliable way to export your entire Rev.com workspace. Whether you're migrating to a new platform, creating local backups, or analyzing your historical transcription data, Rev Exporter helps you take ownership of your archive.

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/actuallyrizzn/rev.com-export.git
   cd rev.com-export
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

### Configuration

Set your Rev.com API credentials as environment variables:

```bash
# Windows (PowerShell)
$env:REV_CLIENT_API_KEY="your_client_api_key"
$env:REV_USER_API_KEY="your_user_api_key"

# Linux/Mac
export REV_CLIENT_API_KEY="your_client_api_key"
export REV_USER_API_KEY="your_user_api_key"
```

Alternatively, create a `config.json` file in your home directory (`~/.rev-exporter/config.json`) or the current directory:

```json
{
  "client_api_key": "your_client_api_key",
  "user_api_key": "your_user_api_key"
}
```

### Basic Usage

1. **Test your connection:**
   ```bash
   rev-exporter test-connection
   ```

2. **Export all completed orders:**
   ```bash
   rev-exporter sync
   ```

3. **Preview what will be downloaded (dry run):**
   ```bash
   rev-exporter sync --dry-run
   ```

## Features

- ✅ Export all completed orders from your Rev.com account
- ✅ Download media files and transcripts
- ✅ Idempotent downloads (safe to re-run, no duplicates)
- ✅ Pagination support for accounts with thousands of orders
- ✅ Filter by date, include/exclude media or transcripts
- ✅ Dry-run mode to preview what will be downloaded

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

## Documentation

For detailed documentation, including:
- Complete installation guide
- Configuration options
- Advanced usage examples
- API reference
- Troubleshooting

See the [documentation in the `docs/` folder](docs/).

## License

- **Code**: Licensed under the [GNU Affero General Public License v3](LICENSE) (AGPLv3)
- **Documentation**: Licensed under [Creative Commons Attribution-ShareAlike 4.0](LICENSE-CC-BY-SA) (CC-BY-SA)

## Contributing

Contributions welcome! Please open an issue or pull request.
