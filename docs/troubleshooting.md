# Troubleshooting Guide

This guide helps you resolve common issues when using Rev Exporter.

## Authentication Issues

### "API credentials not configured"

**Symptoms:**
- Error message: `[ERROR] API credentials not configured`
- Connection test fails

**Solutions:**

1. **Check environment variables:**
   ```bash
   # Windows PowerShell
   echo $env:REV_CLIENT_API_KEY
   echo $env:REV_USER_API_KEY
   
   # Linux/Mac
   echo $REV_CLIENT_API_KEY
   echo $REV_USER_API_KEY
   ```

2. **Verify config file exists and is valid:**
   - Check `./config.json` or `~/.rev-exporter/config.json`
   - Ensure it's valid JSON
   - Check file permissions (should be readable)

3. **Set environment variables:**
   ```bash
   # Windows PowerShell
   $env:REV_CLIENT_API_KEY="your_key"
   $env:REV_USER_API_KEY="your_key"
   
   # Linux/Mac
   export REV_CLIENT_API_KEY="your_key"
   export REV_USER_API_KEY="your_key"
   ```

### "Connection test failed"

**Symptoms:**
- `test-connection` command returns `[ERROR] Connection test failed`
- API requests fail with authentication errors

**Solutions:**

1. **Verify API keys are correct:**
   - Double-check the keys in your Rev.com account settings
   - Ensure there are no extra spaces or newlines
   - Try regenerating the keys in Rev.com

2. **Check key format:**
   - Client API Key and User API Key should be separate
   - Or use single API key format if supported by your account

3. **Test with curl:**
   ```bash
   curl -H "Authorization: Rev CLIENT_KEY:USER_KEY" \
        https://api.rev.com/api/v1/orders?page=0&results_per_page=1
   ```

4. **Check network connectivity:**
   - Ensure you can reach `api.rev.com`
   - Check firewall/proxy settings
   - Try from a different network

## Download Issues

### Files Not Downloading

**Symptoms:**
- Sync runs but no files are created
- Attachments are skipped unexpectedly

**Solutions:**

1. **Check output directory permissions:**
   ```bash
   # Linux/Mac
   ls -ld exports/
   # Should show write permissions
   
   # Try creating a test file
   touch exports/test.txt
   ```

2. **Verify disk space:**
   ```bash
   # Linux/Mac
   df -h .
   
   # Windows
   # Check in File Explorer properties
   ```

3. **Check dry-run mode:**
   - Ensure you're not using `--dry-run` flag
   - Dry-run mode doesn't actually download files

4. **Review logs:**
   - Use `--debug` flag for detailed information
   - Look for error messages in the output

### Partial Downloads

**Symptoms:**
- Some files download, others don't
- Errors appear for specific attachments

**Solutions:**

1. **Check error messages:**
   - Review the failure summary at the end of sync
   - Use `--debug` for more details

2. **Retry failed downloads:**
   - Re-run the sync command
   - Idempotency ensures already-downloaded files are skipped
   - Only failed downloads will be retried

3. **Check attachment availability:**
   - Some attachments may no longer be available on Rev.com
   - Old orders may have expired attachments
   - Verify in Rev.com web interface

### Duplicate Files

**Symptoms:**
- Same file downloaded multiple times
- Index file not working correctly

**Solutions:**

1. **Check index file:**
   ```bash
   cat exports/.rev-exporter-index.json
   ```
   - Should contain a list of downloaded attachment IDs
   - If corrupted, delete it and re-run (will re-download everything)

2. **Verify idempotency:**
   - Run sync twice in a row
   - Second run should skip all files
   - If not, there may be an issue with the index

3. **Reset index if needed:**
   ```bash
   rm exports/.rev-exporter-index.json
   # Re-run sync (will re-download everything)
   ```

## Performance Issues

### Slow Downloads

**Symptoms:**
- Sync takes a very long time
- Downloads seem to hang

**Solutions:**

1. **Check network speed:**
   - Test your internet connection
   - Large media files take time to download

2. **Use date filtering:**
   - Export in smaller batches using `--since`
   - Example: `rev-exporter sync --since 2024-01-01`

3. **Exclude media if not needed:**
   - Media files are typically the largest
   - Use `--no-include-media` for transcripts only

4. **Check API rate limits:**
   - Rev.com may have rate limits
   - Tool includes automatic retries with backoff
   - Very large accounts may take hours

### Memory Issues

**Symptoms:**
- Process uses too much memory
- System becomes slow during sync

**Solutions:**

1. **Process in smaller batches:**
   - Use `--since` to limit date range
   - Run multiple smaller syncs

2. **Check for memory leaks:**
   - Monitor memory usage
   - Restart the process if memory grows too large

3. **Stream large files:**
   - The tool should stream large downloads
   - If issues persist, report as a bug

## File Organization Issues

### Incorrect File Types

**Symptoms:**
- Files saved in wrong directories (media vs transcripts)
- File extensions incorrect

**Solutions:**

1. **Check attachment classification:**
   - Use `--debug` to see classification logic
   - Some edge cases may be misclassified

2. **Manual reorganization:**
   - Files can be moved manually if needed
   - Directory structure is just for organization

3. **Report classification issues:**
   - If you find systematic misclassification, report it
   - Include examples of misclassified attachments

### Missing Metadata Files

**Symptoms:**
- `attachments.json` not created for some orders
- Order metadata incomplete

**Solutions:**

1. **Check for errors during sync:**
   - Review error messages
   - Metadata is saved before attachments are processed

2. **Re-run sync:**
   - Idempotency ensures metadata is saved even if attachments fail
   - Re-run to complete missing metadata

## API Issues

### Rate Limiting

**Symptoms:**
- Requests fail with 429 status codes
- "Too many requests" errors

**Solutions:**

1. **Automatic retries:**
   - Tool includes automatic retry with exponential backoff
   - Should handle temporary rate limits

2. **Reduce request rate:**
   - Process smaller batches
   - Add delays between requests (may require code changes)

3. **Contact Rev.com:**
   - If rate limits are too restrictive
   - May need to request higher limits

### API Changes

**Symptoms:**
- Previously working commands now fail
- Unexpected API responses

**Solutions:**

1. **Check Rev.com API status:**
   - Visit Rev.com API documentation
   - Check for API changes or deprecations

2. **Update the tool:**
   - Pull latest changes from repository
   - May include API compatibility fixes

3. **Report issues:**
   - If API has changed, report as a bug
   - Include API response details (with sensitive data removed)

## Platform-Specific Issues

### Windows Issues

**Path Length Limitations:**
- Windows has 260 character path limit
- Very long filenames may cause issues
- Solution: Use shorter output directory paths

**PowerShell Execution Policy:**
- If scripts won't run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Linux/Mac Issues

**Permission Denied:**
- Ensure virtual environment is activated
- Check file permissions on config files
- Use `chmod` to fix permissions if needed

**Python Version:**
- Ensure Python 3.8+ is installed
- Use `python3` instead of `python` if needed

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check existing issues:**
   - Search GitHub issues for similar problems
   - Check if it's a known issue

2. **Gather information:**
   - Run with `--debug` flag
   - Note the exact error messages
   - Include Python version and OS

3. **Create a new issue:**
   - Provide clear description of the problem
   - Include steps to reproduce
   - Attach relevant logs (with sensitive data removed)

4. **Check documentation:**
   - Review [User Guide](user-guide.md)
   - Check [API Reference](api-reference.md)
   - Read [Installation Guide](installation.md)

## Common Error Messages

### "Failed to parse JSON response"
- API returned unexpected format
- May indicate API changes or errors
- Check with `--debug` for raw response

### "Request failed: Connection timeout"
- Network connectivity issue
- Check internet connection
- Verify firewall/proxy settings

### "Invalid JSON response"
- API returned non-JSON data
- May be an error page or redirect
- Check API status

### "File not found" or "Permission denied"
- Output directory issues
- Check directory permissions
- Verify disk space

## Prevention Tips

1. **Regular backups:**
   - Run exports regularly to avoid large one-time exports
   - Use `--since` for incremental backups

2. **Test first:**
   - Always use `--dry-run` before large exports
   - Verify configuration with `test-connection`

3. **Monitor progress:**
   - Watch for errors during sync
   - Check disk space before starting

4. **Keep updated:**
   - Pull latest changes regularly
   - Check for bug fixes and improvements

