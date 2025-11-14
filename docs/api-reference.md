# API Reference

This document provides detailed information about Rev Exporter's programmatic API for developers who want to use it as a library.

## Overview

Rev Exporter can be used both as a CLI tool and as a Python library. This reference covers the library API.

## Core Modules

### `rev_exporter.config.Config`

Configuration management for API credentials.

```python
from rev_exporter.config import Config

# Initialize with default loading (ENV vars > config file > key.md)
config = Config()

# Or specify a custom config file
config = Config(config_file=Path("custom-config.json"))

# Check if configured
if config.is_configured():
    print("API credentials loaded")

# Get auth header for API requests
auth_header = config.get_auth_header()  # Returns "Rev CLIENT:USER"
```

**Methods:**

- `is_configured() -> bool`: Check if API credentials are configured
- `get_auth_header() -> str`: Get Authorization header value
- `to_dict() -> Dict[str, Any]`: Get configuration as dictionary (without sensitive data)

### `rev_exporter.client.RevAPIClient`

Low-level API client for Rev.com API.

```python
from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.config import Config

config = Config()
client = RevAPIClient(config=config)

# Test connection
if client.test_connection():
    print("Connected successfully")

# Make GET request
try:
    response = client.get("/orders", params={"page": 0, "results_per_page": 10})
    print(response)
except RevAPIError as e:
    print(f"API error: {e}")

# Make POST request
try:
    response = client.post("/endpoint", json_data={"key": "value"})
except RevAPIError as e:
    print(f"API error: {e}")

# Download binary content
content = client.get("/attachments/123/content", stream=True)
```

**Initialization:**

```python
RevAPIClient(
    config: Optional[Config] = None,
    max_retries: int = 3,
    retry_backoff_factor: float = 1.0
)
```

**Methods:**

- `test_connection() -> bool`: Test API connection
- `get(endpoint, params=None, headers=None, stream=False) -> Union[Dict, bytes]`: GET request
- `post(endpoint, params=None, headers=None, json_data=None) -> Dict`: POST request

**Exceptions:**

- `RevAPIError`: Base exception for API errors

### `rev_exporter.models.Order`

Data model for Rev.com orders.

```python
from rev_exporter.models import Order

# Create from API response
order_data = {
    "order_number": "TC0243028600",
    "status": "Complete",
    "placed_on": "2024-01-15T10:30:00Z",
    "attachments": [...]
}
order = Order.from_api_response(order_data)

# Access properties
print(order.order_number)  # "TC0243028600"
print(order.status)        # "Complete"
print(order.placed_on)     # datetime object
print(order.attachments)   # List of Attachment objects

# Check if completed
if order.is_completed():
    print("Order is completed")
```

**Properties:**

- `order_number: str`: Order identifier
- `status: str`: Order status
- `placed_on: Optional[datetime]`: Order date
- `attachments: List[Attachment]`: List of attachments
- `metadata: Optional[Dict]`: Raw API response data

**Methods:**

- `from_api_response(data: Dict) -> Order`: Create Order from API response
- `is_completed() -> bool`: Check if order is completed

### `rev_exporter.models.Attachment`

Data model for Rev.com attachments.

```python
from rev_exporter.models import Attachment

# Create from API response
attachment_data = {
    "id": "Xcw8Hk1FqQgAAAAAAgAAAA",
    "name": "audio2484736686.m4a",
    "type": "media",
    "download_uri": "https://..."
}
attachment = Attachment.from_api_response(attachment_data)

# Access properties
print(attachment.id)           # "Xcw8Hk1FqQgAAAAAAgAAAA"
print(attachment.name)         # "audio2484736686.m4a"
print(attachment.type)         # "media"
print(attachment.download_uri) # URL or None
```

**Properties:**

- `id: str`: Attachment identifier
- `name: str`: Attachment name
- `type: str`: Attachment type
- `download_uri: Optional[str]`: Download URI (if available)
- `metadata: Optional[Dict]`: Raw API response data

**Methods:**

- `from_api_response(data: Dict) -> Attachment`: Create Attachment from API response

### `rev_exporter.orders.OrderManager`

High-level interface for order enumeration and retrieval.

```python
from rev_exporter.client import RevAPIClient
from rev_exporter.orders import OrderManager
from rev_exporter.config import Config
from datetime import datetime

config = Config()
client = RevAPIClient(config=config)
order_manager = OrderManager(client)

# List orders for a specific page
response = order_manager.list_orders(page=0, results_per_page=50)
print(f"Total orders: {response['total_count']}")
print(f"Orders on page: {len(response['orders'])}")

# Get all orders
all_orders = order_manager.get_all_orders()
print(f"Retrieved {len(all_orders)} orders")

# Get all orders since a date
since = datetime(2024, 1, 1)
recent_orders = order_manager.get_all_orders(since=since)

# Get order details
order = order_manager.get_order_details("TC0243028600")
print(f"Order has {len(order.attachments)} attachments")

# Filter completed orders
completed = order_manager.filter_completed_orders(all_orders)
print(f"{len(completed)} completed orders")
```

**Methods:**

- `list_orders(page=0, results_per_page=50) -> Dict`: List orders for a page
- `get_all_orders(results_per_page=50, since=None) -> List[Order]`: Get all orders with pagination
- `get_order_details(order_number: str) -> Order`: Get full order details
- `filter_completed_orders(orders: List[Order]) -> List[Order]`: Filter to completed orders

### `rev_exporter.attachments.AttachmentManager`

High-level interface for attachment processing and downloads.

```python
from rev_exporter.client import RevAPIClient
from rev_exporter.attachments import AttachmentManager, AttachmentType
from rev_exporter.config import Config

config = Config()
client = RevAPIClient(config=config)
attachment_manager = AttachmentManager(client)

# Get attachment metadata
attachment = attachment_manager.get_attachment_metadata("Xcw8Hk1FqQgAAAAAAgAAAA")

# Classify attachment type
att_type = attachment_manager.classify_attachment(attachment)
print(att_type)  # AttachmentType.MEDIA, TRANSCRIPT, CAPTION, or OTHER

# Get preferred format
preferred_format = attachment_manager.get_preferred_format(att_type, attachment)
print(preferred_format)  # "json", "srt", or None

# Download content
content = attachment_manager.download_attachment_content(
    attachment.id,
    format=preferred_format
)

# Get file extension
file_ext = attachment_manager.get_file_extension(
    attachment, att_type, preferred_format
)
print(file_ext)  # ".json", ".m4a", etc.

# Sanitize filename
safe_name = AttachmentManager.sanitize_filename("unsafe<>name.txt")
print(safe_name)  # "unsafe__name.txt"
```

**Methods:**

- `get_attachment_metadata(attachment_id: str) -> Attachment`: Get full attachment metadata
- `classify_attachment(attachment: Attachment) -> AttachmentType`: Classify attachment type
- `download_attachment_content(attachment_id, format=None, preferred_formats=None) -> bytes`: Download content
- `get_preferred_format(attachment_type, attachment) -> Optional[str]`: Get preferred format
- `get_file_extension(attachment, attachment_type, format) -> str`: Determine file extension
- `sanitize_filename(filename: str) -> str`: Sanitize filename (static method)

**Enums:**

- `AttachmentType.MEDIA`: Media files (audio/video)
- `AttachmentType.TRANSCRIPT`: Transcripts
- `AttachmentType.CAPTION`: Captions/subtitles
- `AttachmentType.OTHER`: Other file types

### `rev_exporter.storage.StorageManager`

File storage and idempotency management.

```python
from rev_exporter.storage import StorageManager
from rev_exporter.attachments import AttachmentType
from pathlib import Path

# Initialize storage manager
output_dir = Path("./exports")
storage = StorageManager(output_dir)

# Check if attachment is already downloaded
if storage.is_downloaded("Xcw8Hk1FqQgAAAAAAgAAAA"):
    print("Already downloaded")

# Get order directory
order_dir = storage.get_order_dir("TC0243028600")

# Create directory structure
dirs = storage.create_order_structure("TC0243028600")
# Returns: {"root": Path, "media": Path, "transcripts": Path, "other": Path}

# Save attachment
file_path = storage.save_attachment(
    order_number="TC0243028600",
    attachment=attachment,
    attachment_type=AttachmentType.MEDIA,
    content=b"file content...",
    file_extension=".m4a"
)

# Mark as downloaded
storage.mark_downloaded("Xcw8Hk1FqQgAAAAAAgAAAA")

# Save order metadata
metadata_path = storage.save_order_metadata(order)
```

**Methods:**

- `is_downloaded(attachment_id: str) -> bool`: Check if already downloaded
- `mark_downloaded(attachment_id: str) -> None`: Mark as downloaded
- `get_order_dir(order_number: str) -> Path`: Get order directory path
- `create_order_structure(order_number: str) -> Dict[str, Path]`: Create directory structure
- `save_attachment(order_number, attachment, attachment_type, content, file_extension) -> Path`: Save attachment
- `save_order_metadata(order: Order) -> Path`: Save order metadata JSON

## Complete Example

Here's a complete example of using the library API:

```python
from pathlib import Path
from rev_exporter.config import Config
from rev_exporter.client import RevAPIClient
from rev_exporter.orders import OrderManager
from rev_exporter.attachments import AttachmentManager, AttachmentType
from rev_exporter.storage import StorageManager

# Initialize components
config = Config()
if not config.is_configured():
    raise ValueError("API credentials not configured")

client = RevAPIClient(config=config)
order_manager = OrderManager(client)
attachment_manager = AttachmentManager(client)
storage = StorageManager(Path("./exports"))

# Get all completed orders
print("Fetching orders...")
all_orders = order_manager.get_all_orders()
completed_orders = order_manager.filter_completed_orders(all_orders)
print(f"Found {len(completed_orders)} completed orders")

# Process each order
for order in completed_orders:
    print(f"Processing order {order.order_number}")
    
    # Get full order details
    full_order = order_manager.get_order_details(order.order_number)
    
    # Save order metadata
    storage.save_order_metadata(full_order)
    
    # Process attachments
    for attachment in full_order.attachments:
        # Skip if already downloaded
        if storage.is_downloaded(attachment.id):
            print(f"  Skipping {attachment.name} (already downloaded)")
            continue
        
        # Classify and download
        att_type = attachment_manager.classify_attachment(attachment)
        preferred_format = attachment_manager.get_preferred_format(att_type, attachment)
        
        # Get full metadata
        full_attachment = attachment_manager.get_attachment_metadata(attachment.id)
        
        # Download content
        content = attachment_manager.download_attachment_content(
            attachment.id,
            format=preferred_format
        )
        
        # Determine file extension
        file_ext = attachment_manager.get_file_extension(
            full_attachment, att_type, preferred_format
        )
        
        # Save file
        file_path = storage.save_attachment(
            full_order.order_number,
            full_attachment,
            att_type,
            content,
            file_ext
        )
        
        # Mark as downloaded
        storage.mark_downloaded(attachment.id)
        print(f"  Downloaded: {attachment.name}")

print("Export complete!")
```

## Error Handling

All API methods may raise `RevAPIError` exceptions. Always wrap API calls in try-except blocks:

```python
from rev_exporter.client import RevAPIError

try:
    response = client.get("/orders")
except RevAPIError as e:
    print(f"API error: {e}")
    # Handle error appropriately
```

## Thread Safety

The library components are not thread-safe. If you need concurrent operations:
- Create separate client instances per thread
- Use separate storage managers per thread with different output directories
- Or implement your own synchronization

## Best Practices

1. **Always check configuration**: Verify `config.is_configured()` before using the client
2. **Handle errors gracefully**: Wrap API calls in try-except blocks
3. **Use idempotency**: Check `storage.is_downloaded()` before downloading
4. **Respect rate limits**: Add delays between requests if needed
5. **Log operations**: Use Python's logging module for debugging

## See Also

- [User Guide](user-guide.md) for CLI usage
- [Installation Guide](installation.md) for setup instructions
- [Troubleshooting Guide](troubleshooting.md) for common issues

