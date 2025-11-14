"""
Command-line interface for Rev Exporter.
"""

import sys
import click
from pathlib import Path
from datetime import datetime
from typing import Optional

from rev_exporter.config import Config
from rev_exporter.logging_config import setup_logging
from rev_exporter.client import RevAPIClient
from rev_exporter.orders import OrderManager
from rev_exporter.attachments import AttachmentManager, AttachmentType
from rev_exporter.storage import StorageManager
from rev_exporter.models import Order, Attachment
from rev_exporter.browser import generate_browser

logger = None


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
@click.pass_context
def main(ctx: click.Context, debug: bool) -> None:
    """Rev Exporter - Export media and transcripts from Rev.com"""
    global logger
    setup_logging(debug=debug)
    import logging

    logger = logging.getLogger(__name__)
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@main.command()
@click.pass_context
def test_connection(ctx: click.Context) -> None:
    """Test the connection to Rev.com API"""
    try:
        config = Config()
        if not config.is_configured():
            click.echo("[ERROR] API credentials not configured", err=True)
            click.echo(
                "Set REV_API_KEY (or REV_CLIENT_API_KEY and REV_USER_API_KEY) environment variables",
                err=True,
            )
            sys.exit(1)

        client = RevAPIClient(config=config)
        if client.test_connection():
            click.echo("[OK] Connection test successful!")
            sys.exit(0)
        else:
            click.echo("[ERROR] Connection test failed", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    default="./exports",
    help="Output directory for exported files (default: ./exports)",
)
@click.option(
    "--since",
    type=click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]),
    help="Only export orders placed after this date (ISO format: YYYY-MM-DD)",
)
@click.option(
    "--include-media/--no-include-media",
    default=True,
    help="Include media files in export (default: True)",
)
@click.option(
    "--include-transcripts/--no-include-transcripts",
    default=True,
    help="Include transcripts in export (default: True)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading",
)
@click.pass_context
def sync(
    ctx: click.Context,
    output_dir: str,
    since: Optional[datetime],
    include_media: bool,
    include_transcripts: bool,
    dry_run: bool,
) -> None:
    """Sync all completed orders from Rev.com"""
    start_time = datetime.now()

    try:
        # Initialize components
        config = Config()
        if not config.is_configured():
            click.echo("[ERROR] API credentials not configured", err=True)
            sys.exit(1)

        client = RevAPIClient(config=config)
        order_manager = OrderManager(client)
        attachment_manager = AttachmentManager(client)
        storage = StorageManager(Path(output_dir))

        if dry_run:
            click.echo("[DRY RUN] No files will be downloaded\n")

        # Get all orders
        click.echo("Fetching orders...")
        all_orders = order_manager.get_all_orders(since=since)
        click.echo(f"   Found {len(all_orders)} total orders")

        # Filter completed orders
        completed_orders = order_manager.filter_completed_orders(all_orders)
        click.echo(f"   {len(completed_orders)} completed orders\n")

        if not completed_orders:
            click.echo("[OK] No completed orders to export")
            return

        # Process orders
        orders_scanned = 0
        attachments_downloaded = 0
        failures = []

        for i, order in enumerate(completed_orders, 1):
            click.echo(f"Processing order {order.order_number} ({i}/{len(completed_orders)})")

            try:
                # Get full order details with attachments
                full_order = order_manager.get_order_details(order.order_number)
                orders_scanned += 1

                # Save order metadata
                if not dry_run:
                    storage.save_order_metadata(full_order)

                # Process attachments
                for attachment in full_order.attachments:
                    try:
                        # Check if already downloaded
                        if storage.is_downloaded(attachment.id):
                            # Sanitize filename for console output (handle Unicode)
                            safe_name = attachment.name.encode('ascii', 'replace').decode('ascii')
                            click.echo(f"   [SKIP] Skipping {safe_name} (already downloaded)")
                            continue

                        # Classify attachment
                        att_type = attachment_manager.classify_attachment(attachment)

                        # Check if we should download this type
                        if att_type == AttachmentType.MEDIA and not include_media:
                            continue
                        if att_type in [AttachmentType.TRANSCRIPT, AttachmentType.CAPTION]:
                            if not include_transcripts:
                                continue

                        # Get preferred format
                        preferred_format = attachment_manager.get_preferred_format(
                            att_type, attachment
                        )

                        if dry_run:
                            click.echo(
                                f"   [WOULD DOWNLOAD] {attachment.name} "
                                f"({att_type.value}, format: {preferred_format or 'default'})"
                            )
                            attachments_downloaded += 1
                        else:
                            # Get full attachment metadata
                            full_attachment = attachment_manager.get_attachment_metadata(
                                attachment.id
                            )

                            # Download content
                            content = attachment_manager.download_attachment_content(
                                attachment.id, format=preferred_format
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
                                file_ext,
                            )

                            # Mark as downloaded
                            storage.mark_downloaded(attachment.id)
                            attachments_downloaded += 1
                            # Sanitize filename for console output (handle Unicode)
                            safe_name = attachment.name.encode('ascii', 'replace').decode('ascii')
                            click.echo(f"   [OK] Downloaded: {safe_name}")

                    except Exception as e:
                        error_msg = f"Failed to download {attachment.name}: {e}"
                        logger.error(error_msg)
                        failures.append(error_msg)
                        # Sanitize error message for console output (handle Unicode)
                        safe_error = str(error_msg).encode('ascii', 'replace').decode('ascii')
                        click.echo(f"   [ERROR] {safe_error}")

            except Exception as e:
                error_msg = f"Failed to process order {order.order_number}: {e}"
                logger.error(error_msg)
                failures.append(error_msg)
                # Sanitize error message for console output (handle Unicode)
                safe_error = str(error_msg).encode('ascii', 'replace').decode('ascii')
                click.echo(f"   [ERROR] {safe_error}")

        # Print summary
        elapsed = datetime.now() - start_time
        click.echo("\n" + "=" * 60)
        click.echo("SYNC SUMMARY")
        click.echo("=" * 60)
        click.echo(f"Orders scanned:        {orders_scanned}")
        click.echo(f"Attachments downloaded: {attachments_downloaded}")
        click.echo(f"Failures:               {len(failures)}")
        click.echo(f"Time elapsed:           {elapsed}")
        click.echo("=" * 60)

        if failures:
            click.echo("\n[WARNING] Failures:")
            for failure in failures[:10]:  # Show first 10 failures
                # Sanitize failure message for console output (handle Unicode)
                safe_failure = str(failure).encode('ascii', 'replace').decode('ascii')
                click.echo(f"   - {safe_failure}")
            if len(failures) > 10:
                click.echo(f"   ... and {len(failures) - 10} more")

        if dry_run:
            click.echo("\n[INFO] This was a dry run. Use without --dry-run to actually download files.")

    except KeyboardInterrupt:
        click.echo("\n\n[WARNING] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n[ERROR] Fatal error: {e}", err=True)
        logger.exception("Fatal error in sync command")
        sys.exit(1)


@main.command()
@click.option(
    "--export-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default="./exports",
    help="Export directory to browse (default: ./exports)",
)
@click.option(
    "--no-open",
    is_flag=True,
    help="Don't open browser automatically after generation",
)
@click.pass_context
def browse(ctx: click.Context, export_dir: Path, no_open: bool) -> None:
    """Generate and open HTML browser for exported orders."""
    setup_logging(ctx.obj.get("debug", False))

    try:
        click.echo(f"Generating browser for: {export_dir}")
        generate_browser(export_dir, open_browser=not no_open)
        click.echo(f"\n[OK] Browser generated successfully!")
        click.echo(f"Open {export_dir / 'index.html'} in your browser to view.")
    except Exception as e:
        click.echo(f"\n[ERROR] Failed to generate browser: {e}", err=True)
        if ctx.obj.get("debug", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

