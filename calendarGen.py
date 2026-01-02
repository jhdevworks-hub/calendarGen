import svgwrite
from svgwrite import px
from svgwrite.shapes import Polyline
from svgwrite.text import Text
import logging
import sys


def create_month_grid(
    grid_anchor, days_in_month, month_day_start_index, days_in_previous_month
):
    """
    Create the grid for a full month, plus the previous/next months' days if they fit.

    :param grid_anchor: Anchor position in the drawing, in px.
    :param days_in_month: Amount of days in the current month.
    :param month_day_start_index: Index for the first day of the month. 0 for Monday, 6 for Sunday.
    :param days_in_previous_month: Amount of days in the previous month.
    """
    # Parameters
    day_spacing = 10
    day_size = (180, 143)
    line_color = (0, 100, 0)
    line_thickness = 3
    font_color = (0, 0, 0)
    font_size = 32
    text_offset = (5, 5)

    logging.info(
        "Input parameters:\n"
        f"days_in_month: {days_in_month}\n"
        f"month_day_start: {month_day_start_index}\n"
        f"days_in_previous_month: {days_in_previous_month}"
    )

    grid_group = svgwrite.container.Group()

    def make_day_cell(
        group, grid_index, day_number, day_size, day_spacing, text_offset, off_month
    ):
        """
        Make a cell for a single day.

        :param group: Group container for the day cell.
        :param grid_index: Index of the day to add. From 0 to 34.
        :param day_number: Number for the day.
        :param day_size: Size of the day cell, in px.
        :param day_spacing: Spacing between cells, in px.
        :param off_month: Whether the cell is out of the main month, i.e is a day from previous or next month.
        """
        current_row = grid_index // 7
        current_col = grid_index % 7

        x_stride = day_size[0] + day_spacing
        y_stride = day_size[1] + day_spacing

        cell_left = current_col * x_stride + grid_anchor[0]
        cell_right = (current_col + 1) * x_stride + grid_anchor[0]
        cell_top = current_row * y_stride + grid_anchor[1]
        cell_bottom = (current_row + 1) * y_stride + grid_anchor[1]

        start_point = (cell_left + day_spacing, cell_bottom)
        corner_point = (cell_right, cell_bottom)
        end_point = (cell_right, cell_top + day_spacing)

        opacity = 1.0 if not off_month else 0.6
        line_full_color = svgwrite.rgb(*line_color, "rgb")

        line = Polyline(
            [start_point, corner_point, end_point],
            stroke=line_full_color,
            stroke_width=line_thickness,
            stroke_opacity=opacity,
            fill="none",
            opacity=opacity,
        )

        font_full_color = svgwrite.rgb(*font_color, "rgb")

        number = Text(
            str(day_number),
            x=[cell_left + text_offset[0]],
            y=[cell_top + text_offset[1]],
            stroke=font_full_color,
            stroke_opacity=opacity,
            fill=font_full_color,
            fill_opacity=opacity,
            font_size=font_size,
            dominant_baseline="hanging",
        )
        group.add(line)
        group.add(number)

    def make_extra_day_halfcell(
        group, grid_index, day_number, day_size, day_spacing, text_offset
    ):
        """
        Make a half-day inside another day cell. Used for days that don't fit in the 5 week rows.

        :param group: Group container for the half-day objects.
        :param grid_index: Index of the day to add. From 0 to 34.
        :param day_number: Number for the day.
        :param day_size: Size of the day cell, in px.
        :param day_spacing: Spacing between cells, in px.
        """
        current_row = grid_index // 7
        current_col = grid_index % 7

        x_stride = day_size[0] + day_spacing
        y_stride = day_size[1] + day_spacing

        cell_left = current_col * x_stride + grid_anchor[0]
        cell_right = (current_col + 1) * x_stride + grid_anchor[0]
        cell_top = current_row * y_stride + grid_anchor[1]
        cell_bottom = (current_row + 1) * y_stride + grid_anchor[1]

        diagonal_spacing = 10
        start_point = (
            cell_left + day_spacing + diagonal_spacing,
            cell_bottom - diagonal_spacing,
        )
        end_point = (
            cell_right - diagonal_spacing,
            cell_top + day_spacing + diagonal_spacing,
        )

        line_full_color = svgwrite.rgb(*line_color, "rgb")

        line = Polyline(
            [start_point, end_point],
            stroke=line_full_color,
            stroke_width=line_thickness,
            fill="none",
        )

        font_full_color = svgwrite.rgb(*font_color, "rgb")

        number = Text(
            str(day_number),
            x=[cell_right - text_offset[0]],
            y=[cell_bottom - text_offset[1]],
            stroke=font_full_color,
            fill=font_full_color,
            font_size=font_size,
            dominant_baseline="alphabetic",
            text_anchor="end",
        )
        group.add(line)
        group.add(number)

    # Check if all month days fit in the 5 week rows.
    last_day_index = month_day_start_index + days_in_month
    full_month_fits = last_day_index < 36

    fitting_days_in_month = None
    if full_month_fits:
        fitting_days_in_month = days_in_month
    else:
        fitting_days_in_month = 35 - month_day_start_index
        logging.info(
            f"Month did not fit, making cells until day {fitting_days_in_month}"
        )

    # Add month days
    for day in range(fitting_days_in_month):
        make_day_cell(
            grid_group,
            day + month_day_start_index,
            day + 1,
            day_size,
            day_spacing,
            text_offset,
            False,
        )

    # Add previous month days
    if month_day_start_index != 0:
        day_index = 0
        for prev_day in range(
            days_in_previous_month - month_day_start_index, days_in_previous_month
        ):
            make_day_cell(
                grid_group,
                day_index,
                prev_day + 1,
                day_size,
                day_spacing,
                text_offset,
                True,
            )
            day_index += 1

    if full_month_fits:
        last_day_index = month_day_start_index + (days_in_month - 1)
        days_in_next_month = 7 - ((last_day_index + 1) % 7)
        # Add next month days
        if days_in_next_month != 7:
            next_month_day_index = last_day_index + 1
            for next_day in range(1, days_in_next_month + 1):
                make_day_cell(
                    grid_group,
                    next_month_day_index,
                    next_day,
                    day_size,
                    day_spacing,
                    text_offset,
                    True,
                )
                next_month_day_index += 1
    else:
        # Add missing month days with a diagonal line.
        index = 28
        for extra_day in range(fitting_days_in_month + 1, days_in_month + 1):
            make_extra_day_halfcell(
                grid_group, index, extra_day, day_size, day_spacing, text_offset
            )
            index += 1
    return grid_group


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
    )
    grid_anchor = (30, 150)
    month_label_anchor = (30, 140)
    label_color = svgwrite.rgb(0, 0, 0, "rgb")
    label_size = 72

    month_names = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    year_day_start = 3  # 2026 starts on Thursday
    month_starting_day = year_day_start
    for month_index in range(12):
        dwg = svgwrite.Drawing(
            f"test_month_{month_index}.svg", size=("380mm", "265mm"), profile="full"
        )
        dwg.add(
            dwg.rect(
                insert=(0, 0), size=("100%", "100%"), rx=None, ry=None, fill="#efeeea"
            )
        )

        logging.info(f"Creating grid for month {month_index}")

        grid_group = create_month_grid(
            grid_anchor,
            month_days[month_index],
            month_starting_day,
            month_days[month_index - 1] if (month_index != 0) else 31,
        )

        month_label = Text(
            month_names[month_index],
            x=[month_label_anchor[0]],
            y=[month_label_anchor[1]],
            stroke=label_color,
            fill=label_color,
            font_size=label_size,
            dominant_baseline="alphabetic",
        )
        dwg.add(grid_group)
        dwg.add(month_label)
        month_starting_day = (month_starting_day + month_days[month_index]) % 7
        dwg.save()

    logging.info("Done.")
