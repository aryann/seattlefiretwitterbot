import collections
import enum
import json
import logging
import os
import urllib.parse


# Source: https://en.wikipedia.org/wiki/Seattle_Fire_Department
#
# TODO(aryann): Many of the unit types are missing from this list.
_UNIT_MAP = {
    'A': 'Basic Life',
    'AIR': 'Air Unit',
    'B': 'Battalion Chief',
    'CHAP': 'Chaplain Unit',
    'COM': 'Communication Unit',
    'DECON': 'Decontamination Unit',
    'DEP': 'Deputy Chief',
    'E': 'Engine',
    'FB': 'Fire Boat',
    'FRB': 'Fire Rescue Boat',
    'HAZ': 'HAZMAT Unit',
    'HOSE': 'Hose/Foam Wagon',
    'ICS': 'Incident Command System',
    'L': 'Ladder',
    'M': 'Advanced Life',
    'MAR': 'Fire Marshall',
    'MARINE': 'Marine Unit',
    'PIO': 'Public Information Officer Unit',
    'R': 'Technical Rescue Unit',
    'REHAB': 'Rehabilitation',
    'SAFT': 'Safety Chief',
    'STAF': 'Support Unit',
}

_PRIORITY = [
    'E',
    'L',
    'M',
    'A',
]

_MAX_UNIT_CHARS = 100

_TEST_DATA_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'testdata')


class _ParsingState(enum.Enum):
    OUTSIDE_INCIDENT = 1
    EXPECT_DATETIME = 2
    EXPECT_INCIDENT_ID = 3
    EXPECT_LEVEL = 4
    EXPECT_UNITS = 5
    EXPECT_LOCATION = 6
    EXPECT_TYPE = 7


def _extract_cell_data(line):
    first_idx = line.index('>')
    result = line[first_idx + 1:]
    last_idx = result.index('<')
    result = result[:last_idx]
    return result


def _process_location(location):
    return location.replace('/', 'and').upper()


def _split_unit(unit):
    for i, char in enumerate(unit):
        if char.isdigit():
            return unit[:i], unit[i:]
    return unit, None


def _process_units(units_data):
    units = collections.defaultdict(list)
    for unit in units_data.split():
        unit_type, unit_number = _split_unit(unit)
        units[unit_type].append(unit_number)

    char_count = 0
    combined_units = []
    for unit_type in _PRIORITY:
        unit_numbers = units.get(unit_type)
        if not unit_numbers:
            continue
        unit_type_name = _UNIT_MAP[unit_type]
        combined_units.append(
            f'{unit_type_name} {"/".join(sorted(unit_numbers))}')
        char_count += len(combined_units[-1])
        del units[unit_type]

    unaccounted_units = 0
    for unit_type, unit_numbers in sorted(units.items()):
        unit_type_name = _UNIT_MAP.get(unit_type)
        if not unit_type_name:
            logging.warning('encountered unknown unit type: %s', unit_type)
            unaccounted_units += 1
            continue
        unit_numbers = [number for number in unit_numbers if number]
        text = f'{unit_type_name} {"/".join(sorted(unit_numbers))}'.strip()
        if char_count + len(text) < _MAX_UNIT_CHARS:
            combined_units.append(text)
            char_count += len(text)
        else:
            unaccounted_units += len(unit_numbers)

    if unaccounted_units:
        if combined_units:
            text = f'{unaccounted_units} other unit'
        else:
            text = f'{unaccounted_units} unit'
        if unaccounted_units > 1:
            text += 's'
        combined_units.append(text)

    if len(combined_units) == 1:
        return combined_units[0]
    elif len(combined_units) == 2:
        return ' and '.join(combined_units)
    else:
        combined_units[-1] = 'and ' + combined_units[-1]
        return ', '.join(combined_units)


def get_incidents(lines):
    state = _ParsingState.OUTSIDE_INCIDENT
    incidents = []
    curr = {}

    for line in lines:
        if state == _ParsingState.OUTSIDE_INCIDENT:
            if "onMouseOver='rowOn(row" in line:
                curr = {}
                state = _ParsingState.EXPECT_DATETIME

        elif state == _ParsingState.EXPECT_DATETIME:
            curr['datetime'] = _extract_cell_data(line)
            state = _ParsingState.EXPECT_INCIDENT_ID

        elif state == _ParsingState.EXPECT_INCIDENT_ID:
            curr['incident_id'] = _extract_cell_data(line)
            state = _ParsingState.EXPECT_LEVEL

        elif state == _ParsingState.EXPECT_LEVEL:
            curr['level'] = _extract_cell_data(line)
            state = _ParsingState.EXPECT_UNITS

        elif state == _ParsingState.EXPECT_UNITS:
            curr['units'] = _process_units(_extract_cell_data(line))
            state = _ParsingState.EXPECT_LOCATION

        elif state == _ParsingState.EXPECT_LOCATION:
            location = _process_location(_extract_cell_data(line))
            curr['location'] = location
            map_query = urllib.parse.quote(f'{location}, SEATTLE, WA')
            curr['map_link'] = (
                f'https://www.google.com/maps/search/?api=1&query={map_query}')
            state = _ParsingState.EXPECT_TYPE

        elif state == _ParsingState.EXPECT_TYPE:
            curr['type'] = _extract_cell_data(line)
            incidents.append(curr)
            state = _ParsingState.OUTSIDE_INCIDENT

        else:
            raise ValueError(f'Unexpected state: {state}')

    return incidents


if __name__ == '__main__':
    incidents = []
    for test_file in reversed(sorted(os.listdir(_TEST_DATA_DIR))):
        with open(os.path.join(_TEST_DATA_DIR, test_file)) as f:
            incidents.extend(get_incidents(f.readlines()))
    print(json.dumps(incidents, indent=2))
