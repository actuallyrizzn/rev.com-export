# Project Plan — Rev Exporter Tool

**Based on:** PRD.md  
**Project Name:** rev-exporter  
**Type:** CLI tool + importable client library

---

## Overview

This project plan breaks down the Rev Exporter tool development into logical phases, each building upon the previous phase to deliver a complete, production-ready tool for exporting Rev.com media and transcripts.

---

## Phase 0: Project Setup & Foundation

**Goal:** Establish project structure, dependencies, and development environment.

**Duration:** 1-2 days

### Tasks

1. **Project Structure**
   - Set up Python project structure (package layout)
   - Create `rev_exporter/` package directory
   - Create `tests/` directory
   - Set up `setup.py` or `pyproject.toml` for packaging

2. **Dependencies**
   - Choose HTTP client library (requests or httpx)
   - Add CLI framework (click, argparse, or typer)
   - Add logging library (standard library or structlog)
   - Create `requirements.txt` or `pyproject.toml` with dependencies
   - Set up development dependencies (pytest, black, mypy, etc.)

3. **Configuration Management**
   - Design config file format (JSON/YAML/TOML)
   - Create config loader module
   - Implement environment variable support
   - Priority: ENV vars > config file

4. **Logging Infrastructure**
   - Set up structured logging (INFO/WARN/ERROR levels)
   - Implement log formatters
   - Ensure API keys are never logged

5. **Development Environment**
   - Set up Python virtual environment
   - Create `.gitignore` (already done)
   - Add development scripts/helpers

### Deliverables

- Project structure in place
- Dependencies defined and installable
- Basic logging system working
- Config loading mechanism ready

### Dependencies

- None (foundation phase)

---

## Phase 1: Core API Client & Authentication

**Goal:** Build the foundational API client with authentication and basic request handling.

**Duration:** 2-3 days

### Tasks

1. **API Client Base**
   - Create `RevAPIClient` class
   - Implement base URL configuration (`https://www.rev.com/api/v1`)
   - Add request/response handling
   - Implement error handling for HTTP errors

2. **Authentication**
   - Implement `Authorization: Rev CLIENT_API_KEY:USER_API_KEY` header
   - Load credentials from ENV vars (`REV_CLIENT_API_KEY`, `REV_USER_API_KEY`)
   - Fallback to config file if ENV vars not present
   - Validate credential format

3. **Connection Testing**
   - Implement `test_connection()` method
   - Make minimal `GET /api/v1/orders?page=0&results_per_page=1` request
   - Return success/failure with error details
   - Handle authentication errors gracefully

4. **Retry Logic Foundation**
   - Add retry mechanism for network errors
   - Implement exponential backoff
   - Configurable retry attempts

5. **Response Parsing**
   - Handle JSON responses
   - Handle binary/file responses
   - Error response parsing

### Deliverables

- Working `RevAPIClient` class
- Authentication working correctly
- `test_connection()` method functional
- Basic error handling in place

### Dependencies

- Phase 0 complete

### Testing

- Unit tests for auth header generation
- Integration test for connection validation
- Test error handling scenarios

---

## Phase 2: Order Enumeration & Retrieval

**Goal:** Implement order listing with pagination and order detail retrieval.

**Duration:** 3-4 days

### Tasks

1. **Order Listing**
   - Implement `list_orders(page, results_per_page)` method
   - Parse response: `total_count`, `results_per_page`, `page`, `orders[]`
   - Extract: `order_number`, `status`, `placed_on` from each order

2. **Pagination Logic**
   - Implement `get_all_orders()` method
   - Loop until `orders` array is empty
   - Handle edge cases (empty results, single page, etc.)
   - Progress logging for large result sets

3. **Order Detail Retrieval**
   - Implement `get_order_details(order_number)` method
   - Parse full order metadata
   - Extract `attachments[]` array
   - Capture all documented order fields

4. **Order Filtering**
   - Research official status values from Rev API docs
   - Implement `filter_completed_orders(orders)` method
   - Add filtering logic based on documented status values
   - Support `--since <ISO_DATE>` filtering (store for Phase 4)

5. **Data Models**
   - Create `Order` dataclass/model
   - Create `Attachment` dataclass/model (preliminary)
   - Type hints for all API responses

### Deliverables

- Complete order enumeration with pagination
- Order detail retrieval working
- Completed order filtering functional
- Data models defined

### Dependencies

- Phase 1 complete

### Testing

- Test pagination with mock responses
- Test order filtering logic
- Test edge cases (no orders, single order, etc.)
- Integration test with real API (if credentials available)

---

## Phase 3: Attachment Processing & Download

**Goal:** Implement attachment metadata retrieval and content downloading.

**Duration:** 4-5 days

### Tasks

1. **Attachment Metadata**
   - Implement `get_attachment_metadata(attachment_id)` method
   - Parse attachment details from `GET /api/v1/attachments/{id}`
   - Extract `type`, `name`, and other documented fields
   - Update `Attachment` model with full metadata

2. **File Type Classification**
   - Implement attachment classification logic
   - Categorize as: media, transcript, caption, other
   - Use only documented fields (`type`, `name`)
   - Handle edge cases and unknown types

3. **Content Download**
   - Implement `download_attachment_content(attachment_id, format=None)` method
   - Support `GET /api/v1/attachments/{id}/content`
   - Support format extensions: `.json`, `.txt`, `.docx`, `.srt`
   - Handle Accept headers for format selection
   - Download raw media files (mp3/mp4/etc.)

4. **Format Selection**
   - Implement format preference logic
   - Transcripts: prefer JSON or TXT (user-configurable)
   - Captions: prefer SRT
   - Media: use server default
   - Fallback to server default if preferred format unavailable

5. **File Storage**
   - Implement directory structure creation
   - Structure: `<output_root>/<order_number>/media|transcripts|other/`
   - Generate safe filenames: `<attachment_id>_<name>.<ext>`
   - Save `attachments.json` with order metadata per order

6. **Idempotency**
   - Create local index of downloaded attachment IDs
   - Store index in JSON file (e.g., `.rev-exporter-index.json`)
   - Check index before downloading
   - Update index after successful download
   - Handle partial downloads (cleanup on failure)

### Deliverables

- Attachment metadata retrieval working
- Content download functional for all formats
- File storage with proper directory structure
- Idempotent downloads (no duplicates)

### Dependencies

- Phase 2 complete

### Testing

- Test attachment metadata retrieval
- Test all download formats
- Test file storage structure
- Test idempotency (re-run doesn't duplicate)
- Test error handling (missing attachments, network failures)

---

## Phase 4: CLI Interface & User Experience

**Goal:** Build the command-line interface with all required commands and flags.

**Duration:** 3-4 days

### Tasks

1. **CLI Framework Setup**
   - Set up CLI entry point (`rev-exporter` command)
   - Create command structure using chosen framework
   - Implement help text and usage information

2. **`test-connection` Command**
   - Implement `rev-exporter test-connection` command
   - Call `test_connection()` from API client
   - Display success/failure with clear messages
   - Exit with appropriate exit codes

3. **`sync` Command Core**
   - Implement `rev-exporter sync` command
   - Integrate order enumeration
   - Integrate order filtering (completed only)
   - Integrate attachment processing
   - Integrate download logic

4. **CLI Flags Implementation**
   - `--output-dir`: Set output directory (default: `./exports`)
   - `--since <ISO_DATE>`: Filter orders by date
   - `--include-media / --no-include-media`: Toggle media downloads
   - `--include-transcripts / --no-include-transcripts`: Toggle transcript downloads
   - `--dry-run`: Show what would be downloaded without downloading
   - `--debug`: Enable debug logging

5. **Progress Reporting**
   - Add progress indicators (spinner, progress bar)
   - Show current order being processed
   - Show download progress for large files
   - Real-time status updates

6. **Final Summary**
   - Display summary after sync completes:
     - Number of orders scanned
     - Number of attachments downloaded
     - Number of failures
     - Total time elapsed
   - Format summary clearly (table or structured output)

7. **Error Reporting**
   - Collect errors during sync
   - Display error summary at end
   - Log detailed errors to file (optional `--error-log` flag)

### Deliverables

- Fully functional CLI with both commands
- All flags implemented and tested
- User-friendly progress reporting
- Comprehensive summary output

### Dependencies

- Phase 3 complete

### Testing

- Test all CLI commands
- Test all flags and combinations
- Test error handling in CLI context
- Test dry-run mode
- User acceptance testing

---

## Phase 5: Reliability & Performance Enhancements

**Goal:** Add production-ready reliability features and performance optimizations.

**Duration:** 3-4 days

### Tasks

1. **Enhanced Retry Logic**
   - Implement exponential backoff with jitter
   - Different retry strategies for different error types
   - Configurable retry limits
   - Retry for transient errors only

2. **Concurrent Downloads**
   - Add optional concurrency for attachment downloads
   - Configurable thread/worker pool size
   - Thread-safe index updates
   - Progress reporting for concurrent operations

3. **Resume Capability**
   - Detect interrupted syncs
   - Resume from last successful download
   - Handle partial file cleanup
   - Update index correctly on resume

4. **Rate Limiting**
   - Implement rate limiting to respect API limits
   - Configurable requests per second
   - Queue management for rate-limited requests

5. **Error Recovery**
   - Graceful handling of missing attachments
   - Continue processing on individual failures
   - Detailed error logging per attachment
   - Retry failed downloads at end (optional)

6. **Memory Management**
   - Stream large file downloads (don't load into memory)
   - Efficient pagination (don't cache all orders)
   - Clean up resources properly

7. **Validation**
   - Validate API responses match expected schema
   - Handle unexpected response formats gracefully
   - Validate file downloads (size checks, integrity)

### Deliverables

- Robust error handling and retry logic
- Optional concurrent downloads
- Resume capability for interrupted syncs
- Production-ready reliability

### Dependencies

- Phase 4 complete

### Testing

- Test retry logic with simulated failures
- Test concurrent downloads
- Test resume functionality
- Test rate limiting
- Load testing with large accounts

---

## Phase 6: Testing & Documentation

**Goal:** Comprehensive testing, documentation, and final polish.

**Duration:** 2-3 days

### Tasks

1. **Unit Testing**
   - Achieve >80% code coverage
   - Test all core functions
   - Mock API responses for unit tests
   - Test edge cases and error conditions

2. **Integration Testing**
   - Test with real Rev API (if credentials available)
   - Test full sync workflow
   - Test with various account sizes
   - Test error scenarios

3. **Documentation**
   - Write comprehensive README.md:
     - Installation instructions
     - Configuration guide
     - Usage examples
     - Troubleshooting
   - Add inline code documentation (docstrings)
   - Create example config file
   - Document all CLI commands and flags

4. **Code Quality**
   - Run linters (black, flake8, mypy)
   - Fix all linting errors
   - Code review and refactoring
   - Ensure type hints throughout

5. **Packaging**
   - Finalize `setup.py` or `pyproject.toml`
   - Test installation from source
   - Create distribution packages (optional)
   - Test installation in clean environment

6. **Final Validation**
   - End-to-end test with real account
   - Verify all PRD requirements met
   - Performance validation
   - User acceptance testing

### Deliverables

- Comprehensive test suite
- Complete documentation
- Production-ready codebase
- Verified against PRD requirements

### Dependencies

- Phase 5 complete

---

## Phase Summary

| Phase | Focus | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 0 | Project Setup | 1-2 days | None |
| Phase 1 | API Client & Auth | 2-3 days | Phase 0 |
| Phase 2 | Order Enumeration | 3-4 days | Phase 1 |
| Phase 3 | Attachment Download | 4-5 days | Phase 2 |
| Phase 4 | CLI Interface | 3-4 days | Phase 3 |
| Phase 5 | Reliability & Performance | 3-4 days | Phase 4 |
| Phase 6 | Testing & Documentation | 2-3 days | Phase 5 |

**Total Estimated Duration:** 18-26 days (approximately 3.5-5 weeks)

---

## Risk Mitigation

### High-Risk Areas

1. **API Documentation Gaps**
   - Risk: Official docs may be incomplete
   - Mitigation: Test with real API early, document findings

2. **Large Account Performance**
   - Risk: Thousands of orders may cause performance issues
   - Mitigation: Implement pagination and concurrency early, test with large datasets

3. **Attachment Format Variations**
   - Risk: Unexpected attachment types or formats
   - Mitigation: Robust error handling, fallback mechanisms, extensible classification

4. **Rate Limiting**
   - Risk: API rate limits may slow down exports
   - Mitigation: Implement rate limiting early, make it configurable

### Dependencies on External Factors

- Rev.com API availability and stability
- API documentation accuracy
- Access to test credentials

---

## Success Criteria (from PRD)

- [ ] Running `rev-exporter sync` mirrors entire Rev account locally
- [ ] Works for thousands of orders with stable pagination
- [ ] Idempotent (safe to re-run, no duplicates)
- [ ] Simple configuration and clear logs
- [ ] All completed orders exported
- [ ] All media and transcript attachments downloaded
- [ ] Proper error handling and recovery

---

## Notes

- Each phase should be completed and tested before moving to the next
- Integration testing with real API should begin as early as Phase 1
- User feedback should be incorporated throughout development
- Consider creating a `CHANGELOG.md` to track progress

