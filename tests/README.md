# Test Suite

This directory contains comprehensive tests for the Rev Exporter tool.

## Test Structure

- **Unit Tests** (`test_*.py`): Test individual modules and functions
- **Integration Tests** (`integration/`): Test with real API (requires credentials)
- **E2E Tests** (`e2e/`): Test full CLI workflow (requires credentials)

## Running Tests

### Run All Tests (Unit Only)

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=rev_exporter --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/`.

### Run Integration Tests

Integration tests require API credentials:

```bash
export REV_CLIENT_API_KEY="your_key"
export REV_USER_API_KEY="your_key"
pytest tests/integration/
```

### Run E2E Tests

E2E tests also require API credentials:

```bash
export REV_CLIENT_API_KEY="your_key"
export REV_USER_API_KEY="your_key"
pytest tests/e2e/
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

## Test Coverage

The test suite aims for 100% code coverage. Coverage reports are generated in:
- Terminal: `--cov-report=term-missing`
- HTML: `--cov-report=html` (view in `htmlcov/index.html`)
- XML: `--cov-report=xml` (for CI/CD)

## Test Files

- `test_config.py`: Configuration loading and management
- `test_client.py`: API client and request handling
- `test_models.py`: Data models (Order, Attachment)
- `test_orders.py`: Order enumeration and retrieval
- `test_attachments.py`: Attachment processing and classification
- `test_storage.py`: File storage and idempotency
- `test_cli.py`: Command-line interface
- `test_logging_config.py`: Logging configuration
- `integration/test_integration.py`: Integration tests with real API
- `e2e/test_e2e.py`: End-to-end workflow tests

## Fixtures

Common test fixtures are defined in `conftest.py`:
- `mock_config`: Mock configuration with API keys
- `mock_config_unconfigured`: Mock configuration without keys
- `sample_order_data`: Sample order data structure
- `sample_orders_list_response`: Sample paginated orders response
- `sample_attachment_data`: Sample attachment metadata
- `temp_output_dir`: Temporary directory for file operations
- `mock_api_client`: Mock API client instance
- `mock_requests_response`: Factory for mock HTTP responses

