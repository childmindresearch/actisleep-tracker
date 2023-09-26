"""Contains the app settings."""
import functools
import logging

import pydantic


class Settings(pydantic.BaseModel):
    """Represents the app settings."""

    APP_NAME: str = pydantic.Field(
        "Actigraphy", description="The name of the app.", env="ACTIGRAPHY_APP_NAME"
    )
    LOGGER_NAME: str = pydantic.Field(
        "Actigraphy",
        description="The name of the logger.",
        env="ACTIGRAPHY_LOGGER_NAME",
    )


@functools.lru_cache()
def get_settings() -> Settings:
    """Cached function to get the app settings.

    Returns:
        The app settings.
    """
    return Settings()


def initialize_logger(logging_level: int = logging.INFO) -> None:
    """Initializes the logger."""
    settings = get_settings()
    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.setLevel(logging_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
