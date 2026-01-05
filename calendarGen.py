import svgwrite
from svgwrite.shapes import Polyline, Rect
from svgwrite.text import Text
import logging
import sys
import cssutils


class YearData:
    @staticmethod
    def month_names(index):
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
        return month_names[index]

    def __init__(self, year):
        self.year = year
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
        self.year = year_data.year
        self.index = index
        self.n_days = year_data.month_days[index]
        self.start_index = year_data.month_starting_day_indexes[index]
        self.holidays = year_data.holidays[index]


def mm_to_px(length_in_mm):
    return 3.78 * length_in_mm


def getPropertyFromCSS(css, inSelector, inProperty):
    css_object = cssutils.parseString(css)
    for rule in css_object:
        if rule.type == rule.STYLE_RULE:
            selectorList = rule.selectorList
            for selectorEntry in selectorList:
                if selectorEntry.selectorText == inSelector:
                    for propertyEntry in rule.style:
                        if propertyEntry.name == inProperty:
                            return propertyEntry.value


def create_single_minimonth(
    minimonth_size, month_label, current_month, prev_month, next_month
):
    miniday_size = (minimonth_size[0] / 7, minimonth_size[1] / 7)
    minimonth_group = svgwrite.container.Group()
    border_percentage = 0.3
    border_y_margin = border_percentage * miniday_size[1]

    # Make border
    border = Rect(
        insert=(0, 0),
        size=(minimonth_size[0], minimonth_size[1] + border_y_margin),
        class_="minicalendar_border",
    )
    minimonth_group.add(border)

    # Fill month label
    minilabel = Text(
        month_label,
        x=[0],
        y=[0],
        class_=("mini_calendar_label"),
    )
    minilabel.translate(0, -border_y_margin)
    minimonth_group.add(minilabel)

    minidays_group = svgwrite.container.Group(class_="minicalendar")
    minidays_group.translate(0, miniday_size[1])

    # Fill miniweekdays labels
    week_days = "LMMJVSD"
    for idx, day_letter in enumerate(week_days):
        minidaylabel = Text(
            day_letter,
            x=[miniday_size[0] * 0.5 + miniday_size[0] * idx],
            y=[0],
            class_=("mini_calendar_text"),
        )
        minidays_group.add(minidaylabel)

    # Fill month days
    n_days = current_month.n_days
    holidays = current_month.holidays
    weekdays_offset = 1
    for miniday_index, miniday_number in enumerate(
        range(1, n_days + 1), current_month.start_index
    ):
        grid_x = (miniday_index % 7) * miniday_size[0]
        grid_y = (weekdays_offset + (miniday_index // 7)) * miniday_size[1]
        holiday = True if miniday_number in holidays else False
        mininumber = Text(
            str(miniday_number),
            x=[miniday_size[0] * 0.5 + grid_x],
            y=[grid_y],
            # dominant_baseline="alphabetic",
            class_=(
                "mini_calendar_text regular-day"
                if not holiday
                else "mini_calendar_text holiday"
            ),
        )
        minidays_group.add(mininumber)

    # Fill previous month
    n_days = prev_month.n_days
    holidays = prev_month.holidays
    for miniday_index, miniday_number in enumerate(
        range(n_days - current_month.start_index + 1, n_days + 1)
    ):
        grid_x = (miniday_index % 7) * miniday_size[0]
        grid_y = weekdays_offset * miniday_size[1]
        holiday = True if miniday_number in holidays else False
        mininumber = Text(
            str(miniday_number),
            x=[miniday_size[0] * 0.5 + grid_x],
            y=[grid_y],
            # dominant_baseline="alphabetic",
            class_=(
                "mini_calendar_text off-day regular-day"
                if not holiday
                else "mini_calendar_text off-day holiday"
            ),
        )
        minidays_group.add(mininumber)

    # Fill next month
    holidays = next_month.holidays
    filled_days = current_month.start_index + current_month.n_days
    for miniday_index, miniday_number in enumerate(
        range(1, 43 - filled_days),
        filled_days,
    ):
        grid_x = (miniday_index % 7) * miniday_size[0]
        grid_y = (weekdays_offset + (miniday_index // 7)) * miniday_size[1]
        holiday = True if miniday_number in holidays else False
        mininumber = Text(
            str(miniday_number),
            x=[miniday_size[0] * 0.5 + grid_x],
            y=[grid_y],
            class_=(
                "mini_calendar_text off-day regular-day"
                if not holiday
                else "mini_calendar_text off-day holiday"
            ),
        )
        minidays_group.add(mininumber)

    minimonth_group.add(minidays_group)

    return minimonth_group


def create_minimonth_pair(
    minimonth_size, big_month_index, current_year, previous_year, next_year
):
    minimonth_pair = svgwrite.container.Group()

    # Create list of 16 month datas, from November of prev year to February of next year.
    offset_index = big_month_index + 2
    month_datas = [
        MonthData(previous_year, 10),
        MonthData(previous_year, 11),
        MonthData(current_year, 0),
        MonthData(current_year, 1),
        MonthData(current_year, 2),
        MonthData(current_year, 3),
        MonthData(current_year, 4),
        MonthData(current_year, 5),
        MonthData(current_year, 6),
        MonthData(current_year, 7),
        MonthData(current_year, 8),
        MonthData(current_year, 9),
        MonthData(current_year, 10),
        MonthData(current_year, 11),
        MonthData(next_year, 0),
        MonthData(next_year, 1),
    ]

    # Create first minimonth (previous from big month)
    before_first_minimonth_data = month_datas[offset_index - 2]
    first_minimonth_data = month_datas[offset_index - 1]
    after_first_minimonth_data = month_datas[offset_index]
    month_label = f"{YearData.month_names(first_minimonth_data.index)} {first_minimonth_data.year}"
    first_mini = create_single_minimonth(
        minimonth_size,
        month_label,
        first_minimonth_data,
        before_first_minimonth_data,
        after_first_minimonth_data,
    )
    minimonth_pair.add(first_mini)

    # Create second minimonth (next from big month)
    before_second_minimonth_data = month_datas[offset_index]
    second_minimonth_data = month_datas[offset_index + 1]
    after_second_minimonth_data = month_datas[offset_index + 2]
    month_label = f"{YearData.month_names(second_minimonth_data.index)} {second_minimonth_data.year}"
    second_mini = create_single_minimonth(
        minimonth_size,
        month_label,
        second_minimonth_data,
        before_second_minimonth_data,
        after_second_minimonth_data,
    )
    second_mini.translate(minimonth_size[0])
    minimonth_pair.add(second_mini)
    return minimonth_pair


def create_month_grid(
    day_size,
    current_month,
    previous_month,
    next_month,
):
    """
    Create the grid for a full month, plus the previous/next months' days if they fit.

    """
    # Parameters
    day_spacing = mm_to_px(1)
    weekday_label_y_offset = mm_to_px(1)
    number_text_offset = (mm_to_px(1), mm_to_px(1))

    days_in_month = current_month.n_days
    month_day_start_index = current_month.start_index
    days_in_previous_month = previous_month.n_days

    logging.debug(
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

        cell_left = current_col * x_stride
        cell_right = (current_col + 1) * x_stride
        cell_top = current_row * y_stride
        cell_bottom = (current_row + 1) * y_stride

        start_point = (cell_left + day_spacing, cell_bottom)
        corner_point = (cell_right, cell_bottom)
        end_point = (cell_right, cell_top + day_spacing)

        modifiers_classes = []
        if off_month:
            modifiers_classes.append("off-day")
        if holiday:
            modifiers_classes.append("holiday")
        else:
            modifiers_classes.append("regular-day")

        line = Polyline(
            [start_point, corner_point, end_point],
            class_=" ".join(
                ["calendar_grid_line"] + (["off-day"] if off_month else [])
            ),
        )

        number = Text(
            str(day_number),
            x=[cell_left + text_offset[0]],
            y=[cell_top + text_offset[1]],
            dominant_baseline="hanging",
            class_=" ".join(["calendar_grid_text"] + modifiers_classes),
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

        cell_left = current_col * x_stride
        cell_right = (current_col + 1) * x_stride
        cell_top = current_row * y_stride
        cell_bottom = (current_row + 1) * y_stride

        diagonal_spacing = 10
        start_point = (
            cell_left + day_spacing + diagonal_spacing,
            cell_bottom - diagonal_spacing,
        )
        end_point = (
            cell_right - diagonal_spacing,
            cell_top + day_spacing + diagonal_spacing,
        )

        line = Polyline(
            [start_point, end_point],
            class_="calendar_grid_line",
        )

        number = Text(
            str(day_number),
            x=[cell_right - text_offset[0]],
            y=[cell_bottom - text_offset[1]],
            dominant_baseline="alphabetic",
            text_anchor="end",
            class_=(
                "calendar_grid_text regular-day"
                if not holiday
                else "calendar_grid_text holiday"
            ),
        )
        group.add(line)
        group.add(number)

    # Make weekday labels
    weekdays = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]
    for idx, weekday in enumerate(weekdays):
        weekday_label = Text(
            weekday,
            x=[(day_size[0] + day_spacing) * idx],
            y=[-weekday_label_y_offset],
            class_="calendar_week_label",
        )
        grid_group.add(weekday_label)

    # Check if all month days fit in the 5 week rows.
    last_day_index = month_day_start_index + days_in_month
    full_month_fits = last_day_index < 36

    fitting_days_in_month = None
    if full_month_fits:
        fitting_days_in_month = days_in_month
    else:
        fitting_days_in_month = 35 - month_day_start_index
        logging.debug(
            f"Month did not fit, making cells until day {fitting_days_in_month}"
        )

    # Add month days
    for day_index in range(fitting_days_in_month):
        make_day_cell(
            grid_group,
            day_index + month_day_start_index,
            day_index + 1,
            day_size,
            day_spacing,
            number_text_offset,
            False,
            True if (day_index + 1) in current_month.holidays else False,
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
                number_text_offset,
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
                    number_text_offset,
                    True,
                    True if next_day_number in next_month.holidays else False,
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
                number_text_offset,
                True if extra_day_number in current_month.holidays else False,
            )
    return grid_group


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("debug.log"), logging.StreamHandler(sys.stdout)],
    )

    # Load stylesheet
    css_path = "calendar.css"
    with open(css_path, "r") as file:
        stylesheet = file.read()
    mini_font_size = getPropertyFromCSS(stylesheet, ".mini_calendar_text", "font-size")
    mini_font_size_in_mm = float(mini_font_size[:-2])
    font_cell_factors = (1.9, 1.4)
    miniday_cell_size = (
        mini_font_size_in_mm * font_cell_factors[0],
        mini_font_size_in_mm * font_cell_factors[1],
    )
    minimonth_size_from_font = (miniday_cell_size[0] * 7, miniday_cell_size[1] * 7)

    # Parameters
    content_left_edge = mm_to_px(20)
    grid_anchor = (content_left_edge, mm_to_px(66))
    day_size = (mm_to_px(47), mm_to_px(35))
    month_label_anchor = (content_left_edge, mm_to_px(38))
    month_number_label_anchor = (content_left_edge, mm_to_px(26))
    minimonths_anchor = (mm_to_px(274), mm_to_px(23))
    minimonth_size_in_mm = minimonth_size_from_font
    minimonth_size = (
        mm_to_px(minimonth_size_in_mm[0]),
        mm_to_px(minimonth_size_in_mm[1]),
    )
    logging.info(f"Maximum font size (mm): {minimonth_size_in_mm[1]/7}")

    # Prepare year data before loop
    year_2025 = YearData(2025)
    year_2026 = YearData(2026)
    year_2027 = YearData(2027)

    # Prepare full page
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

        # Add minimonths
        minimonth_pair = create_minimonth_pair(
            minimonth_size, month_index, year_2026, year_2025, year_2027
        )
        minimonth_pair.translate(minimonths_anchor[0], minimonths_anchor[1])
        dwg.add(minimonth_pair)

        # Add main grid
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
            day_size, current_month_data, previous_month_data, next_month_data
        )
        grid_group.translate(grid_anchor[0], grid_anchor[1])
        dwg.add(grid_group)

        # Add month label
        month_label = Text(
            year_2026.month_names(month_index),
            x=[month_label_anchor[0]],
            y=[month_label_anchor[1]],
            class_="calendar_label",
        )
        month_number_label = Text(
            f"{(month_index+1):02} / 2026",
            x=[month_number_label_anchor[0]],
            y=[month_number_label_anchor[1]],
            class_="calendar_number_label",
        )
        dwg.add(month_label)
        dwg.add(month_number_label)
        dwg.save()

    logging.info("Done.")
