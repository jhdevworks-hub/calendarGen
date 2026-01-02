import svgwrite
from svgwrite.shapes import Polyline
from svgwrite.text import Text
import logging
import sys


class YearData:
    def __init__(self, year):
        self.month_names = [
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
        self.month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if year % 4 == 0:
            self.month_days[1] = 29
        match year:
            case 2025:
                self.year_day_start_index = 2
            case 2026:
                self.year_day_start_index = 3
            case 2027:
                self.year_day_start_index = 4
            case _:
                raise NotImplementedError
        self.month_starting_day_indexes = [self.year_day_start_index]
        for i in range(1, 12):
            self.month_starting_day_indexes.append(
                (self.month_starting_day_indexes[i - 1] + self.month_days[i - 1]) % 7
            )
        # TODO: Add holidays for other years, these are for 2026.
        self.holidays = {
            0: [1],
            1: [],
            2: [],
            3: [3, 4, 5],
            4: [1, 21],
            5: [21, 29],
            6: [16],
            7: [15],
            8: [18, 19],
            9: [12, 31],
            10: [1],
            11: [8, 25],
        }


class MonthData:
    def __init__(self, year_data, index):
        self.n_days = year_data.month_days[index]
        self.start_index = year_data.month_starting_day_indexes[index]
        self.holidays = year_data.holidays[index]


def mm_to_px(length_in_mm):
    return round(3.543307 * length_in_mm)


def create_month_grid(
    grid_anchor,
    current_month,
    previous_month,
    next_month,
):
    """
    Create the grid for a full month, plus the previous/next months' days if they fit.

    :param grid_anchor: Anchor position in the drawing, in px.
    """
    # Parameters
    day_spacing = mm_to_px(1)
    day_size = (mm_to_px(50), mm_to_px(39))
    line_color = (0, 100, 0)
    line_thickness = 1
    font_color = (0, 0, 0)
    font_size = 32
    text_offset = (mm_to_px(1), mm_to_px(1))

    days_in_month = current_month.n_days
    month_day_start_index = current_month.start_index
    days_in_previous_month = previous_month.n_days

    logging.info(
        "Input parameters:\n"
        f"days_in_month: {days_in_month}\n"
        f"month_day_start: {month_day_start_index}\n"
        f"days_in_previous_month: {days_in_previous_month}"
    )

    grid_group = svgwrite.container.Group(class_="calendar_grid")

    def make_day_cell(
        group,
        grid_index,
        day_number,
        day_size,
        day_spacing,
        text_offset,
        off_month,
        holiday,
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
        group, grid_index, day_number, day_size, day_spacing, text_offset, holiday
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
    for day_number in range(fitting_days_in_month):
        make_day_cell(
            grid_group,
            day_number + month_day_start_index,
            day_number + 1,
            day_size,
            day_spacing,
            text_offset,
            False,
            True if day_number in current_month.holidays else False,
        )

    # Add previous month days
    if month_day_start_index != 0:
        for day_index, day_number in enumerate(
            range(
                days_in_previous_month - month_day_start_index + 1,
                days_in_previous_month + 1,
            )
        ):
            make_day_cell(
                grid_group,
                day_index,
                day_number,
                day_size,
                day_spacing,
                text_offset,
                True,
                True if day_number in previous_month.holidays else False,
            )

    if full_month_fits:
        last_day_index = month_day_start_index + (days_in_month - 1)
        days_in_next_month = 7 - ((last_day_index + 1) % 7)
        # Add next month days
        if days_in_next_month != 7:
            for next_month_day_index, next_day_number in enumerate(
                range(1, days_in_next_month + 1), last_day_index + 1
            ):
                make_day_cell(
                    grid_group,
                    next_month_day_index,
                    next_day_number,
                    day_size,
                    day_spacing,
                    text_offset,
                    True,
                    True if day_number in next_month.holidays else False,
                )
    else:
        # Add missing month days with a diagonal line.
        for index, extra_day_number in enumerate(
            range(fitting_days_in_month + 1, days_in_month + 1), 28
        ):
            make_extra_day_halfcell(
                grid_group,
                index,
                extra_day_number,
                day_size,
                day_spacing,
                text_offset,
                True if extra_day_number in current_month.holidays else False,
            )
    return grid_group


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
    )

    # Parameters
    grid_anchor = (mm_to_px(20), mm_to_px(66))
    month_label_anchor = (mm_to_px(20), mm_to_px(40))
    label_color = svgwrite.rgb(0, 0, 0, "rgb")
    label_size = 48

    # Load stylesheet
    css_path = "calendar.css"
    with open(css_path, "r") as file:
        stylesheet = file.read()

    # Prepare year data before loop
    year_2025 = YearData(2025)
    year_2026 = YearData(2026)
    year_2027 = YearData(2027)
    for month_index in range(12):
        dwg = svgwrite.Drawing(
            f"test_month_{month_index}.svg", size=("380mm", "265mm"), profile="full"
        )
        dwg.embed_font(
            name="Creato Display", filename="fonts/CreatoDisplay-Regular.otf"
        )
        dwg.embed_stylesheet(stylesheet)
        dwg.add(
            dwg.rect(
                insert=(0, 0), size=("100%", "100%"), rx=None, ry=None, fill="#efeeea"
            )
        )

        logging.info(f"Creating grid for month {month_index}")

        previous_month_data = (
            MonthData(year_2026, month_index - 1)
            if month_index != 0
            else MonthData(year_2025, 11)
        )
        current_month_data = MonthData(year_2026, month_index)
        next_month_data = (
            MonthData(year_2026, month_index + 1)
            if month_index != 11
            else MonthData(year_2027, 0)
        )

        grid_group = create_month_grid(
            grid_anchor, current_month_data, previous_month_data, next_month_data
        )

        month_label = Text(
            year_2026.month_names[month_index],
            x=[month_label_anchor[0]],
            y=[month_label_anchor[1]],
            stroke=label_color,
            fill=label_color,
            font_size=label_size,
            dominant_baseline="alphabetic",
            class_="calendar_label",
        )
        dwg.add(grid_group)
        dwg.add(month_label)
        dwg.save()

    logging.info("Done.")
