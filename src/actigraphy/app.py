"""Main app setup for the Actigraphy app."""

import logging

import dash
import dash_bootstrap_components
from dash import dcc, html

from actigraphy.components import app_license, file_selection
from actigraphy.core import callback_manager, cli, config

settings = config.get_settings()
APP_NAME = settings.APP_NAME
LOGGER_NAME = settings.LOGGER_NAME


def create_app() -> dash.Dash:
    """Creates a new instance of the Actigraphy app.

    Returns:
        A new instance of the Actigraphy app.
    """
    args = cli.parse_args()
    config.initialize_logger(logging_level=args.verbosity)
    logger = logging.getLogger(LOGGER_NAME)

    logger.info("Starting Actigraphy app")
    app = dash.Dash(
        APP_NAME,
        external_stylesheets=[dash_bootstrap_components.themes.BOOTSTRAP],
    )
    app.title = APP_NAME

    logger.info("Attaching callbacks to app")
    callback_manager.initialize_components()
    callback_manager.global_manager.attach_to_app(app)

    logger.info("Creating app layout")
    subject_directories = cli.get_subject_folders(args)
    app.layout = html.Div(
        (
            dcc.Store(id="file_manager", storage_type="session"),
            dcc.Store(id="check-done", storage_type="session"),
            file_selection.file_selection(subject_directories),
            html.Pre(id="annotations-data"),
            app_license.app_license(),
        ),
    )
    return app


def run_app() -> None:
    """Entrypoint for the application."""
    app = create_app()
    app.run_server(debug=False, port=8051)
