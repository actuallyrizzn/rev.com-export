"""
Test CLI main entry point.
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch


def test_cli_main_entry_point():
    """Test that CLI __main__ block is executed."""
    # To cover line 252, we need to execute the module with __name__ == "__main__"
    # We'll use importlib to load and execute it
    
    cli_path = Path(__file__).parent.parent / "rev_exporter" / "cli.py"
    
    # Read the file with UTF-8 encoding
    with open(cli_path, "r", encoding="utf-8") as f:
        cli_code = f.read()
    
    # Compile the code
    compiled = compile(cli_code, str(cli_path), "exec")
    
    # Create a namespace with __name__ set to "__main__" and import all needed modules
    namespace = {
        "__name__": "__main__",
        "__file__": str(cli_path),
        "__package__": "rev_exporter",
        "__builtins__": __builtins__,
    }
    
    # Import all the modules that cli.py needs
    import click
    import sys as sys_module
    from pathlib import Path as Path_module
    from datetime import datetime
    from typing import Optional
    
    namespace.update({
        "sys": sys_module,
        "click": click,
        "Path": Path_module,
        "datetime": datetime,
        "Optional": Optional,
    })
    
    # Import rev_exporter modules
    from rev_exporter import config, logging_config, client, orders, attachments, storage, models
    namespace.update({
        "Config": config.Config,
        "setup_logging": logging_config.setup_logging,
        "RevAPIClient": client.RevAPIClient,
        "OrderManager": orders.OrderManager,
        "AttachmentManager": attachments.AttachmentManager,
        "StorageManager": storage.StorageManager,
        "Order": models.Order,
        "Attachment": models.Attachment,
        "AttachmentType": attachments.AttachmentType,
    })
    
    # Mock sys.argv and sys.exit
    original_argv = sys.argv
    try:
        sys.argv = ["cli.py", "--help"]
        
        # Execute the compiled code - this will run the __main__ block
        try:
            exec(compiled, namespace)
        except SystemExit:
            pass  # Expected when --help is used
    finally:
        sys.argv = original_argv
