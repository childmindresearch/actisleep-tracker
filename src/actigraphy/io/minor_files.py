"""Functions for reading and writing minor files to a format accepted by GGIR."""
import csv
import datetime
from os import path
from typing import Any

from actigraphy.core import utils as core_utils
from actigraphy.io import data_import
from actigraphy.io import utils as io_utils


def read_sleeplog(filepath: str) -> tuple[list[str], list[str]]:
    """Reads sleep log data from a CSV file.

    Args:
        filepath: The path to the CSV file containing the sleep log data.

    Returns:
        list[str]: A list of the sleep times.
        list[str]: A list of the wake times.
    """
    sleep_hours = io_utils.read_one_line_from_csv_file(filepath, 1)[1:]

    if len(sleep_hours) == 0:
        msg = "The sleep log file is empty."
        raise ValueError(msg)
    if len(sleep_hours) % 2 != 0:
        msg = "The sleep log file has an odd number of entries."
        raise ValueError(msg)

    wake = [sleep_hours[index] for index in range(len(sleep_hours)) if index % 2 == 1]
    sleep = [sleep_hours[index] for index in range(len(sleep_hours)) if index % 2 != 1]

    return sleep, wake


def modify_sleeplog(
    file_manager: dict[str, str],
    day: int,
    sleep: float,
    wake: float,
) -> None:
    """Writes sleep and wake times to the sleeplog file for a given day.

    Args:
        file_manager: A dictionary containing file paths for various files.
        day: The day for which to write the sleep and wake times.
        sleep: The sleep time for the given day, represented as a decimal point.
        wake: The wake time for the given day, represented as a decimal point.
    """
    with open(file_manager["sleeplog_file"]) as file_buffer:
        reader = csv.reader(file_buffer)
        sleeplog: list[list[str]] = list(reader)

    dates = data_import.get_dates(file_manager)
    sleeplog[1][0] = file_manager["identifier"]

    timezone = data_import.get_timezone(file_manager)
    sleep_time = core_utils.point2time(sleep, dates[day], timezone)
    wake_time = core_utils.point2time(wake, dates[day], timezone)

    sleeplog[1][(day * 2) + 1] = str(sleep_time)
    sleeplog[1][(day * 2) + 2] = str(wake_time)

    with open(file_manager["sleeplog_file"], "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerows(sleeplog)


def write_sleeplog(dates: list[datetime.datetime], filepath: str) -> None:
    """Save the given hour vector to a CSV file.

    Args:
        dates: A list of dates to write to the CSV file.
        filepath: The path to the output file.

    Notes:
        The last day is discarded as each frontend "day" displays two days.

    """
    dates_no_end = dates[:-2]
    data_line = ["identifier"]
    data_line.extend([str(date) for date in dates_no_end])
    data_line = [data if data else "NA" for data in data_line]

    sleep_times = io_utils.flatten(
        [
            [f"onset_N{day + 1}", f"wakeup_N{day + 1}"]
            for day in range(len(dates_no_end) // 2)
        ],
    )
    header = ["ID", *sleep_times]

    with open(filepath, "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(header)
        writer.writerow(data_line)


def write_log_file(name: str, filepath: str, identifier: str) -> None:
    """Writes a log file with the given name, filepath, and identifier.

    Args:
        name: The name of the user.
        filepath: The path to the file where the log will be written.
        identifier: The identifier for the log file.

    """
    filename = "sleeplog_" + identifier + ".csv"

    log_info = [
        name,
        identifier,
        datetime.date.today(),
        filename,
    ]

    if not path.exists(filepath):
        with open(filepath, "w") as file_buffer:
            writer = csv.writer(file_buffer)
            writer.writerow(["Username", "Participant", "Date", "Filename"])

    with open(filepath, "a") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(log_info)


def write_log_analysis_completed(
    is_completed: bool,  # noqa: FBT001
    identifier: str,
    filepath: str,
) -> None:
    """Writes a CSV file indicating that the sleep log analysis has been completed.

    Args:
        is_completed: Whether the analysis has been completed.
        identifier: The identifier of the participant.
        filepath: The path to the CSV file to write the log information to.
    """
    completion_word = "Yes" if is_completed else "No"
    log_info = [
        identifier,
        completion_word,
        datetime.datetime.now(),
    ]

    header = [
        "Participant",
        "Is the sleep log analysis completed?",
        "Last modified",
    ]
    with open(filepath, "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(header)
        writer.writerow(log_info)


def write_vector(filepath: str, vector: list[Any]) -> None:
    """Write a list of values to a CSV file.

    Args:
        filepath: The path to the CSV file.
        vector: The list of values to write to the CSV file.

    """
    with open(filepath, "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(vector)


def read_vector(filepath: str, up_to_column: int | None = None) -> list[Any]:
    """Reads a vector of data from a CSV file.

    Args:
        filepath: The path to the CSV file.
        up_to_column: The index of the last column to read. If not specified,
            reads all columns.

    Returns:
        list[Any]: A list of values read from the CSV file.
    """
    data = io_utils.read_one_line_from_csv_file(filepath, 0)
    if up_to_column is not None:
        return data[:up_to_column]
    return data


def initialize_files(
    file_manager: dict[str, str],
    evaluator_name: str,
) -> None:
    """Initializes the files required for actigraphy analysis.

    Args:
        file_manager: A dictionary containing file paths for various files.
        evaluator_name: The name of the evaluator.

    """
    if not path.exists(file_manager["sleeplog_file"]):
        dates = data_import.get_dates(file_manager)
        timezone = data_import.get_timezone(file_manager)
        date_vector = [
            [core_utils.point2time(None, date, timezone)] * 2 for date in dates
        ]
        date_vector_flat = io_utils.flatten(date_vector)
        write_sleeplog(date_vector_flat, file_manager["sleeplog_file"])

    daycount = data_import.get_daycount(file_manager["base_dir"])
    vector_files = [
        "review_night_file",
        "multiple_sleeplog_file",
        "data_cleaning_file",
        "missing_sleep_file",
    ]
    for vector_file in vector_files:
        filepath = file_manager[vector_file]
        if not path.exists(filepath):
            write_vector(filepath, [0] * daycount)

    write_log_file(evaluator_name, file_manager["log_file"], file_manager["identifier"])
