import argparse

import csv
import os
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Union, Iterator

from matplotlib import pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter

FIRST, LAST = 0, -1

# Command line options
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--maxrank", dest="maxrank", default=10, help="Max rank to include")
parser.add_argument("-src", "--source", dest="source", default="waffle.csv", help="Source CSV file")
parser.add_argument("-f", "--fig", dest="fig", default="", help="Figure filename")
parser.add_argument("-s", "--figsize", dest="figsize", default=20, help="Figure size")
parser.add_argument("-t", "--textboxes", dest="textboxes", action="store_true", help="Do textboxes?")
parser.add_argument("-nl", "--no-legend", dest="no_legend", action="store_true", help="Skip legend?")
parser.add_argument("-ng", "--no-grid", dest="no_grid", action="store_true", help="Skip grid?")
args = parser.parse_args()

# Filtering
MAX_RANK = int(args.maxrank)

# Output
FIG_NAME = args.fig
FIG_LOCATION = os.path.join(os.path.dirname(__file__), FIG_NAME)
FIG_SIZE = (int(args.figsize), int(args.figsize))

# Data source
WAFFLE_CSV = os.path.join(os.path.dirname(__file__), "waffle.csv")
COL_UID = 0
COL_WAFFLES = 1
COL_TIME = 2
COL_USERNAME = 3
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Plot settings
DO_GRID = not args.no_grid
GRID_LINESTYLE = "-."

DO_LEGEND = not args.no_legend
LEGEND_MAX_ROWS = 12

DO_TEXTBOXES = bool(args.textboxes)
TEXTBOX_SIZE = 9
TEXTBOX_COLOR = "white"
TEXTBOX_EDGE_COLOR = "black"
TEXTBOX_ALPHA = 0.5

LINESTYLE_PRIMARY_THRESHOLD = 25
LINESTYLE_SECONDARY_THRESHOLD = 50
LINESTYLE_FIRST_QUARTER = ":"
LINESTYLE_SECOND_QUARTER = "-."
LINESTYLE_THIRD_QUARTER = "--"
LINESTYLE_FOURTH_QUARTER = "-"
LINEWIDTH = 2

COLOR_MAP = 'gist_ncar'
XAXIS_DATE_FORMAT = "%b '%y"
XAXIS_TICK_MONTHS = (1, 7)

# Type hints
RowList = List[Dict[str, str]]
DatetimeList = List[datetime]
CountLookup = Dict[str, int]
IndexLookup = Dict[str, int]
History = List[int]
HistoryLookup = Dict[str, History]
Number = Union[int, float, bool]


def read_csv() -> RowList:
    """Read the csv file and return its list-of-dicts representation."""
    return list(csv.reader(open(WAFFLE_CSV)))


def get_top_users(rows: RowList) -> CountLookup:
    """Take the input from reading the csv file. The return value is a dict
    where each key is a username. Each value is the total number of waffles
    eaten by that person. Only users who have at one point been in the top
    MAX_RANK waffle eaters are included."""
    users = defaultdict(int)
    prev_day = None
    top_users = {}

    for row in rows:
        # Add waffles
        users[row[COL_USERNAME]] += int(row[COL_WAFFLES])

        # Check date
        consumption_time = datetime.strptime(row[COL_TIME], TIME_FORMAT)

        # If it is a new day, set the new top users
        if consumption_time.day != prev_day:
            top_users.update({
                key: users[key]
                for key in sorted(users, key=users.get, reverse=True)[:MAX_RANK]
            })
        prev_day = consumption_time.day

    return top_users


def parse_waffle_rows(rows: RowList) -> (DatetimeList, HistoryLookup):
    """Take the input from reading the csv file. The first return value is a
    list of datetimes at which point waffles were consumed. The second return
    value is a dict where each key is a username. Each value in the second
    return value is a list of waffle counts for each point in time in the date-
    time list (the first return value)."""
    top_users = get_top_users(rows)
    user_counts = { key: 0 for key in top_users }

    consumption_times: DatetimeList = []
    history_lookup: HistoryLookup = defaultdict(list)
    prev_day = None

    for row in (row for row in rows if row[COL_USERNAME] in top_users):
        # Add waffles
        user_counts[row[COL_USERNAME]] += int(row[COL_WAFFLES])

        # Check dates
        consumption_time = datetime.strptime(row[COL_TIME], TIME_FORMAT)

        # If it is a new day, add line data
        if consumption_time.day != prev_day:
            for user, count in user_counts.items():
                history_lookup[user].append(count)
            consumption_times.append(consumption_time)
        prev_day = consumption_time.day

    return consumption_times, history_lookup


def get_limiting_waffles(history_lookup: HistoryLookup) -> (IndexLookup, IndexLookup):
    """Returns a tuple of two dicts with the first and last relevant index in
    the history_lookup for each user. In each dict, the key is a username and
    the value is the first (or last) relevant index for that user."""
    first_waffle: IndexLookup = {}
    last_waffle: IndexLookup = {}

    for username, history in history_lookup.items():
        # Run backwards and find the last time the wafflecount changed
        last_index = len(history)
        next_wafflecount = history[LAST]
        for wafflecount in reversed(history):
            last_index -= 1
            if wafflecount != next_wafflecount:
                break
            next_wafflecount = wafflecount
        last_waffle[username] = min(last_index + 1, len(history))

        # Run forwards and find the first time the wafflecount changed
        first_index = 0
        prev_wafflecount = history[FIRST]
        for wafflecount in history:
            if wafflecount != prev_wafflecount:
                break
            first_index += 1
        first_waffle[username] = max(first_index - 1, 0)

    return first_waffle, last_waffle


def get_color_cycle(num_users: int) -> Iterator[List[Tuple[float]]]:
    """Generates colors in a way that is compatible with set_prop_cycle.

    It will cycle through colors multiple times if there are many users (since
    the linestyles will also change)
    """
    color_map = plt.get_cmap(COLOR_MAP)
    for index in range(num_users):
        yield color_map(
            1.
            * index
            * (2 if num_users > LINESTYLE_PRIMARY_THRESHOLD else 1)
            * (2 if num_users > LINESTYLE_SECONDARY_THRESHOLD else 1)
            / num_users
            % 1
        )


def get_linestyle_cycle(num_users: int) -> Iterator[str]:
    """Generates linestyles in a way that is compatible with set_prop_cycle.

    It will yield more varied linestyles if there are many users.
    """
    for index in range(num_users):
        if index < num_users // 4 and num_users > LINESTYLE_SECONDARY_THRESHOLD:
            yield LINESTYLE_FIRST_QUARTER
        elif index < num_users // 2 and num_users > LINESTYLE_PRIMARY_THRESHOLD:
            yield LINESTYLE_SECOND_QUARTER
        elif index < 3 * num_users // 4 and num_users > LINESTYLE_SECONDARY_THRESHOLD:
            yield LINESTYLE_THIRD_QUARTER
        else:
            yield LINESTYLE_FOURTH_QUARTER


def do_plot(consumption_times: DatetimeList, history_lookup: HistoryLookup):
    """Make a plot with the data"""
    # Figure out when people started and stopped eating waffles
    first_waffle, last_waffle = get_limiting_waffles(history_lookup)

    # Set up the figure
    fig = plt.figure(figsize=FIG_SIZE)
    ax = fig.add_subplot(111)

    # Set up colors and linestyles in a way that makes sense depending on the
    # number of users
    num_users = len(history_lookup)
    ax.set_prop_cycle(
        linestyle=get_linestyle_cycle(num_users),
        color=get_color_cycle(num_users),
    )

    # Plot every history
    for index, (username, history) in enumerate(history_lookup.items()):
        # Plot line
        history_slice = slice(first_waffle[username], last_waffle[username])
        ax.plot(
            consumption_times[history_slice],
            history[history_slice],
            label=username,
            linewidth=LINEWIDTH,
        )

        if DO_TEXTBOXES:
            # Add text box at the end of the line
            txt = ax.text(
                consumption_times[last_waffle[username]-1],
                history[last_waffle[username]-1],
                f"{username}={history_lookup[username][LAST]}",
                fontsize=TEXTBOX_SIZE,
                backgroundcolor=TEXTBOX_COLOR
            )

            # Stylize the text box
            txt.set_bbox({
                "facecolor": TEXTBOX_COLOR,
                "alpha": TEXTBOX_ALPHA,
                "edgecolor": TEXTBOX_EDGE_COLOR,
            })

    # Set up x axis to show dates
    ax.xaxis.set_major_locator(MonthLocator(XAXIS_TICK_MONTHS, bymonthday=1))
    ax.xaxis.set_major_formatter(DateFormatter(XAXIS_DATE_FORMAT))

    # Move y axis to the right
    ax.yaxis.tick_right()

    # Zoom in on the data
    ax.set_ylim(0, max([history[LAST] for history in history_lookup.values()]))
    ax.set_xlim(consumption_times[FIRST], consumption_times[LAST])

    # Add grid
    if DO_GRID:
        ax.grid(linestyle=GRID_LINESTYLE)

    # Add legend
    if DO_LEGEND:
        ax.legend(ncol=num_users // LEGEND_MAX_ROWS, handleheight=1)

    # Save or display figure
    if FIG_NAME:
        plt.savefig(FIG_LOCATION)
    else:
        plt.show()


def do_it():
    """Read data, parse it and make a plot"""
    do_plot(*parse_waffle_rows(read_csv()))


if __name__ == "__main__":
    do_it()
