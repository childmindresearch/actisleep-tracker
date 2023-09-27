""" Main app setup for the Actigraphy app """
import logging

import dash
import dash_bootstrap_components
from dash import dcc, html

from actigraphy.components import app_license, file_selection
from actigraphy.core import callback_manager, cli, config

settings = config.get_settings()
APP_NAME = settings.APP_NAME
LOGGER_NAME = settings.LOGGER_NAME

config.initialize_logger(logging_level=logging.DEBUG)
logger = logging.getLogger(LOGGER_NAME)


def create_app() -> dash.Dash:
    """
    Creates a new instance of the Actigraphy app.

    Returns:
        A new instance of the Actigraphy app.
    """
    logger.info("Starting Actigraphy app")
    app = dash.Dash(
        APP_NAME, external_stylesheets=[dash_bootstrap_components.themes.BOOTSTRAP]
    )
    app.title = APP_NAME

    logger.debug("Attaching callbacks to app")
    callback_manager.initialize_components()
    callback_manager.global_manager.attach_to_app(app)

    logger.debug("Parsing command line arguments")
    args = cli.parse_args()
    subject_directories = cli.get_subject_folders(args)

    logger.debug("Creating app layout")
    header = html.Img(
        src="/assets/CMI_Logo_title.png", style={"height": "60%", "width": "60%"}
    )
    app.layout = html.Div(
        (
            dcc.Store(id="file_manager", storage_type="session"),
            dcc.Store(id="check-done", storage_type="session"),
            dcc.Store(id="annotations-save", storage_type="session"),
            header,
            file_selection.file_selection(subject_directories),
            html.Pre(id="annotations-data"),
            app_license.app_license(),
        ),
    )
    return app
