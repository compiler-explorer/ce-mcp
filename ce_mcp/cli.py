"""CLI entry point for Compiler Explorer MCP."""

import logging
from pathlib import Path

import click

from .config import Config
from .server import create_server


@click.command()
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=False, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging (more verbose than --verbose)",
)
def main(config_path: Path, verbose: bool, debug: bool) -> None:
    """Run the Compiler Explorer MCP server."""
    # Set up logging
    if debug:
        log_level = logging.DEBUG
        # Enable more detailed logging for debug mode
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        )
        # Enable debug logging for aiohttp and asyncio
        logging.getLogger("aiohttp").setLevel(logging.DEBUG)
        logging.getLogger("asyncio").setLevel(logging.DEBUG)
        logging.getLogger("ce_mcp").setLevel(logging.DEBUG)
    elif verbose:
        log_level = logging.DEBUG
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    logger = logging.getLogger(__name__)

    # Load configuration
    if config_path:
        logger.info(f"Loading configuration from {config_path}")
        server_config = Config.load_from_file(config_path)
    else:
        server_config = Config.load_from_file()

    # Create and run server
    server = create_server(server_config)

    logger.info("Starting Compiler Explorer MCP server...")

    # Run the server
    server.run()


if __name__ == "__main__":
    main()
