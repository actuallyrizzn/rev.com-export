# User Guide

This guide covers how to use Rev Exporter to export your Rev.com workspace.

## Overview

Rev Exporter provides a simple command-line interface to:
- Export all completed orders from your Rev.com account
- Download media files (audio/video)
- Download transcripts and captions
- Organize exports in a structured directory format
- Resume interrupted exports (idempotent operations)

## Commands

### `test-connection`

Test your API credentials and connection to Rev.com.

```bash
rev-exporter test-connection
```

**Output:**
- `[OK] Connection test successful!` - Credentials are valid
- `[ERROR] Connection test failed` - Check your API keys

**When to use:**
- After first installation
- When troubleshooting authentication issues
- To verify API access

### `sync`

Export all completed orders from your Rev.com account.

#### Basic Usage

```bash
rev-exporter sync
```

This will:
- Fetch all orders from your account
- Filter to only completed orders
- Download all media files and transcripts
- Save everything to `./exports` directory (default)

#### Options

**`--output-dir PATH`**
- Specify the output directory for exported files
- Default: `./exports`
- Example: `rev-exporter sync --output-dir ~/rev-backup`

**`--since DATE`**
- Only export orders placed after this date
- Format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
- Example: `rev-exporter sync --since 2024-01-01`
- Useful for incremental backups or exporting recent orders only

**`--include-media / --no-include-media`**
- Control whether media files are downloaded
- Default: `--include-media` (media files are included)
- Example: `rev-exporter sync --no-include-media` (transcripts only)

**`--include-transcripts / --no-include-transcripts`**
- Control whether transcripts and captions are downloaded
- Default: `--include-transcripts` (transcripts are included)
- Example: `rev-exporter sync --no-include-transcripts` (media only)

**`--dry-run`**
- Preview what would be downloaded without actually downloading
- Shows which orders and attachments would be processed
- Useful for:
  - Estimating download size
  - Verifying filters work correctly
  - Testing configuration

**`--debug`**
- Enable debug logging
- Shows detailed information about API requests and processing
- Useful for troubleshooting

#### Examples

**Export only transcripts from 2024:**
```bash
rev-exporter sync --since 2024-01-01 --no-include-media
```

**Preview what would be downloaded:**
```bash
rev-exporter sync --dry-run
```

**Export to a specific directory with debug logging:**
```bash
rev-exporter sync --output-dir ~/rev-archive --debug
```

**Export only media files:**
```bash
rev-exporter sync --no-include-transcripts
```

## Output Structure

Exported files are organized in a structured directory format:

```
exports/
  <order_number>/
    attachments.json          # Order metadata (JSON)
    media/
      <attachment_id>_<sanitized_name>.<ext>
    transcripts/
      <attachment_id>_<sanitized_name>.<ext>
    other/
      <attachment_id>_<sanitized_name>.<ext>
```

### Directory Structure Details

**Order Directories**
- Each order gets its own directory named with the order number
- Example: `TC0243028600/`, `TC0507300957/`

**`attachments.json`**
- Contains complete order metadata
- Includes order number, status, date, and list of all attachments
- Useful for programmatic access to order information

**`media/` Directory**
- Contains all audio and video files
- Original media uploaded to Rev.com
- Formats: `.mp3`, `.mp4`, `.m4a`, `.wav`, etc.

**`transcripts/` Directory**
- Contains transcripts and captions
- Formats: `.json`, `.txt`, `.docx`, `.srt`, etc.
- Transcripts are preferred in JSON format when available

**`other/` Directory**
- Contains any attachments that don't fit into media or transcript categories
- May include documents, notes, or other file types

### File Naming

Files are named using the pattern: `<attachment_id>_<sanitized_name>.<ext>`

- `attachment_id`: Unique identifier from Rev.com
- `sanitized_name`: Original filename with unsafe characters removed
- `ext`: File extension based on format and type

Example: `Xcw8Hk1FqQgAAAAAAgAAAA_audio2484736686.m4a.m4a`

## Idempotency

Rev Exporter is designed to be **idempotent**—you can run it multiple times safely without creating duplicates.

### How It Works

- The tool maintains an index file (`.rev-exporter-index.json`) in the output directory
- This index tracks which attachments have already been downloaded
- Before downloading, the tool checks if an attachment is already in the index
- Already-downloaded attachments are skipped

### Benefits

- **Safe to re-run**: If an export is interrupted, you can simply run it again
- **Incremental updates**: Run periodically to download only new orders
- **No duplicates**: The same attachment won't be downloaded twice

### Resetting the Index

If you need to re-download everything (e.g., after deleting files), you can:

1. Delete the index file: `rm exports/.rev-exporter-index.json`
2. Or delete the entire exports directory and start fresh

## Progress and Status

During a sync operation, you'll see:

```
Fetching orders...
   Found 150 total orders
   120 completed orders

Processing order TC0243028600 (1/120)
   [OK] Downloaded: audio2484736686.m4a
   [SKIP] Skipping transcript.docx (already downloaded)
   [OK] Downloaded: transcript.json

Processing order TC0507300957 (2/120)
   ...
```

### Status Messages

- `[OK]` - Successfully downloaded
- `[SKIP]` - Already downloaded, skipped
- `[ERROR]` - Download failed (see error message)
- `[WOULD DOWNLOAD]` - Shown in dry-run mode

### Final Summary

After completion, a summary is displayed:

```
============================================================
SYNC SUMMARY
============================================================
Orders scanned:        120
Attachments downloaded: 245
Failures:               2
Time elapsed:           0:15:32
============================================================
```

## Best Practices

### Regular Backups

Run exports periodically to keep your local archive up to date:

```bash
# Weekly backup
rev-exporter sync --output-dir ~/rev-backup
```

### Incremental Exports

Use `--since` to export only recent orders:

```bash
# Export orders from the last month
rev-exporter sync --since 2024-11-01
```

### Dry Run First

Always do a dry run before large exports:

```bash
rev-exporter sync --dry-run
```

### Monitor Disk Space

Large archives can consume significant disk space:
- Media files are typically the largest
- Use `--no-include-media` if you only need transcripts
- Monitor your output directory size

### Error Handling

If you encounter errors:
- Check the error messages in the output
- Use `--debug` for more detailed information
- Failed downloads are logged but don't stop the entire process
- Re-run the sync to retry failed downloads

## Advanced Usage

### Automation

You can automate exports using cron (Linux/Mac) or Task Scheduler (Windows):

**Linux/Mac cron example:**
```bash
# Run weekly on Sundays at 2 AM
0 2 * * 0 cd /path/to/rev.com-export && source venv/bin/activate && rev-exporter sync --output-dir ~/rev-backup
```

**Windows Task Scheduler:**
- Create a task that runs your sync command
- Set it to run on a schedule

### Scripting

You can also create wrapper scripts for common operations:

```bash
#!/bin/bash
# backup-rev.sh
export REV_CLIENT_API_KEY="your_key"
export REV_USER_API_KEY="your_key"
rev-exporter sync --output-dir ~/rev-backup --since $(date -d '1 week ago' +%Y-%m-%d)
```

## Troubleshooting

See the [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

## Next Steps

- Review the [API Reference](api-reference.md) for programmatic usage
- Check the [Project Plan](project-plan.md) for development details
- Read the [PRD](PRD.md) for product requirements

