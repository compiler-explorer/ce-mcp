"""CLI entry point for Compiler Explorer MCP."""

import logging
from pathlib import Path

import click

from .server import create_server
from .config import Config


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
def main(config_path: Path, verbose: bool) -> None:
    """Run the Compiler Explorer MCP server."""
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
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
