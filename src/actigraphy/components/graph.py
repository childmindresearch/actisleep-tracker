"""Defines the graph component of the Actigraphy app.

The graph component contains a graph and range slider for use in the Actigraphy
app. The graph displays the sensor angle and arm movement data for a given day.
The range slider is used to select a sleep window for the given day.
"""
import datetime
import logging

import dash
from dash import dcc, html

from actigraphy.core import callback_manager, config, utils
from actigraphy.io import data_import, minor_files
from actigraphy.plotting import sensor_plots

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
TIME_FORMATTING = "%A - %d %B %Y %H:%M"

logger = logging.getLogger(LOGGER_NAME)

manager = callback_manager.CallbackManager()


def graph() -> html.Div:
    """Builds the graph component of the Actigraphy app.

    Returns:
    html.Div: A Dash HTML div containing a graph and range slider components.
    """
    return html.Div(
        children=[
            dcc.Graph(id="graph"),
            html.Div(
                children=[
                    html.B(id="sleep-onset"),
                    html.B(id="sleep-offset"),
                    html.B(id="sleep-duration"),
                ],
                style={"margin-left": "80px", "margin-right": "55px"},
            ),
            html.Div(
                children=[
                    dcc.RangeSlider(
                        min=0,
                        max=36 * 60,  # 36 hours in minutes
                        step=1,
                        marks={
                            hour * 60: f"{(hour + 12) % 24:02d}:00"
                            for hour in range(0, 37, 2)
                        },
                        id="my-range-slider",
                        updatemode="mouseup",
                    ),
                    html.Pre(id="annotations-slider"),
                ],
                # html.Pre(id="annotations-nap"),
                style={"margin-left": "55px", "margin-right": "55px"},
            ),
        ],
    )


@callback_manager.global_manager.callback(
    dash.Output("graph", "figure"),
    dash.Input("day_slider", "value"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def create_graph(day: int, drag_value: list[int], file_manager: dict[str, str]) -> dict:
    """Creates a graph for a given day using data from the file manager.

    Args:
        day: The day for which to create the graph (0-indexed).
        drag_value: The drag value for the slider.
        file_manager: The file manager containing the data.

    Returns:
        dict: The figure object representing the graph.
    """
    logger.debug("Entering create graph callback")

    dates = data_import.get_dates(file_manager)
    n_points_per_day = data_import.get_n_points_per_day(file_manager)

    day_1_sensor_angles, day_1_arm_movement, day_1_non_wear = data_import.create_graph(
        file_manager, day
    )
    if day < len(dates):
        (
            day_2_sensor_angles,
            day_2_arm_movement,
            day_2_non_wear,
        ) = data_import.create_graph(file_manager, day + 1)
    else:
        day_2_sensor_angles = [0] * n_points_per_day
        day_2_arm_movement = [-210] * n_points_per_day
        day_2_non_wear = [0] * n_points_per_day

    sensor_angle = day_1_sensor_angles[n_points_per_day // 2 :] + day_2_sensor_angles
    arm_movement = day_1_arm_movement[n_points_per_day // 2 :] + day_2_arm_movement
    nonwear = day_1_non_wear[n_points_per_day // 2 :] + day_2_non_wear

    title_day = f"Day {day+1}: {dates[day].strftime('%A - %d %B %Y')}"  # Frontend uses 1-indexed days.
    day_timestamps = [dates[day]] * (n_points_per_day // 2) + (
        [dates[day] + datetime.timedelta(days=1)]
    ) * n_points_per_day

    timestamp = [
        " ".join(
            [
                day_timestamps[point].strftime("%d/%b/%Y"),
                utils.point2time_timestamp(point, n_points_per_day, offset=12),
            ]
        )
        for point in range(len(day_timestamps))
    ]

    nonwear_changes = []
    for index in range(1, len(nonwear)):
        if nonwear[index] != nonwear[index - 1]:
            nonwear_changes += [index]
    if nonwear[0]:
        nonwear_changes.insert(0, 0)
    if len(nonwear_changes) % 2 != 0:
        nonwear_changes.append(len(timestamp) - 1)

    figure = sensor_plots.build_sensor_plot(
        timestamp, sensor_angle, arm_movement, title_day
    )

    rectangle_timepoints = utils.slider_values_to_graph_values(
        drag_value, n_points_per_day
    )

    if rectangle_timepoints[0] != rectangle_timepoints[1]:
        sensor_plots.add_rectangle(figure, rectangle_timepoints, "red", "sleep window")
    for index in range(0, len(nonwear_changes), 2):
        sensor_plots.add_rectangle(
            figure,
            [nonwear_changes[index], nonwear_changes[index + 1]],
            "green",
            "non-wear",
        )
    return figure


@callback_manager.global_manager.callback(
    dash.Output("sleep-onset", "children", allow_duplicate=True),
    dash.Output("sleep-offset", "children", allow_duplicate=True),
    dash.Output("sleep-duration", "children", allow_duplicate=True),
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("file_manager", "data"),
    prevent_initial_call=True,
)
def refresh_range_slider(
    day: int, file_manager: dict[str, str]
) -> tuple[str, str, str, list[int]]:
    """Reads the sleep logs for the given day from the file manager and returns
    the sleep onset, sleep offset, and sleep duration as strings.

    Args:
        day: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.

    Returns:
        tuple[str, str, str]: A tuple of strings containing the sleep onset,
            sleep offset, and sleep duration.
    """
    logger.debug("Entering refresh range slider callback")
    dates = data_import.get_dates(file_manager)

    sleep_onset, wake_up = minor_files.read_sleeplog(file_manager["sleeplog_file"])
    sleep_time = datetime.datetime.fromisoformat(sleep_onset[day])
    wake_time = datetime.datetime.fromisoformat(wake_up[day])

    sleep_point = utils.time2point(sleep_time, dates[day])
    wake_point = utils.time2point(wake_time, dates[day])

    return (
        f"Sleep onset: {sleep_time.strftime(TIME_FORMATTING)}\n",
        f"Sleep offset: {wake_time.strftime(TIME_FORMATTING)}\n",
        f"Sleep duration: {utils.datetime_delta_as_hh_mm(wake_time - sleep_time)}\n",
        [sleep_point, wake_point],
    )


@callback_manager.global_manager.callback(
    dash.Output("annotations-save", "children"),
    dash.Output("sleep-onset", "children", allow_duplicate=True),
    dash.Output("sleep-offset", "children", allow_duplicate=True),
    dash.Output("sleep-duration", "children", allow_duplicate=True),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
    prevent_initial_call=True,
)
def adjust_range_slider(drag_value: list[int], file_manager: dict[str, str], day: int):
    """Adjusts the text labels fora  given day and writes the sleep log to a file.

    Args:
        drag_value: The drag values of the range slider.
        file_manager: The file manager containing the sleep log.
        day: The day for which to adjust the range slider.

    Returns:
        Tuple[str, str, str, str]: A tuple containing the sleep onset, sleep offset, and sleep duration.
    """
    logger.debug("Entering write info callback")
    dates = data_import.get_dates(file_manager)
    minor_files.write_sleeplog(file_manager, day, drag_value[0], drag_value[1])

    sleep_time = utils.point2time(drag_value[0], dates[day])
    wake_time = utils.point2time(drag_value[1], dates[day])

    return (
        "",
        f"Sleep onset: {sleep_time.strftime(TIME_FORMATTING)}\n",
        f"Sleep offset: {wake_time.strftime(TIME_FORMATTING)}\n",
        f"Sleep duration: {utils.datetime_delta_as_hh_mm(wake_time - sleep_time)}\n",
    )
