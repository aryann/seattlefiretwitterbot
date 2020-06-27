import enum
import json
import logging
import urllib.parse


# Source: https://en.wikipedia.org/wiki/Seattle_Fire_Department
#
# TODO(aryann): Many of the unit types are missing from this list.
UNIT_MAP = {
    'A': 'Basic Life Support',
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
    'M': 'Advanced Life Support',
    'MAR': 'Fire Marshall',
    'MARINE': 'Marine Unit',
    'R': 'Technical Rescue Unit',
    'REHAB': 'Rehabilitation',
    'SAFT': 'Safety Chief',
    'STAF': 'Support Unit',
}


class ParsingState(enum.Enum):
    OUTSIDE_INCIDENT = 1
    EXPECT_DATETIME = 2
    EXPECT_INCIDENT_ID = 3
    EXPECT_LEVEL = 4
    EXPECT_UNITS = 5
    EXPECT_LOCATION = 6
    EXPECT_TYPE = 7


def extract_cell_data(line):
    first_idx = line.index('>')
    result = line[first_idx + 1:]
    last_idx = result.index('<')
    result = result[:last_idx]
    return result


def process_location(location):
    return location.replace('/', 'and').upper()


def get_unit_type(unit):
    for i, char in enumerate(unit):
        if char.isdigit():
            return unit[:i]
    return unit


def process_units(units_data):
    units = []
    for unit in units_data.split():
        unit_type = UNIT_MAP.get(get_unit_type(unit))
        if not unit_type:
            logging.warning(
                'Encountered unknown unit type "%s"; data line: %s', unit, units_data)
            continue
        units.append(unit_type + ' ' + unit[1:])

    units.sort()
    if not units:
        return []
    elif len(units) == 1:
        return units[0]
    elif len(units) == 2:
        return f'{units[0]} and {units[1]}'
    else:
        units[-1] = f'and {units[-1]}'
        return ', '.join(units)


def get_incidents(lines):
    state = ParsingState.OUTSIDE_INCIDENT
    incidents = []
    curr = {}

    for line in lines:
        if state == ParsingState.OUTSIDE_INCIDENT:
            if "onMouseOver='rowOn(row" in line:
                curr = {}
                state = ParsingState.EXPECT_DATETIME

        elif state == ParsingState.EXPECT_DATETIME:
            curr['datatime'] = extract_cell_data(line)
            state = ParsingState.EXPECT_INCIDENT_ID

        elif state == ParsingState.EXPECT_INCIDENT_ID:
            curr['incident_id'] = extract_cell_data(line)
            state = ParsingState.EXPECT_LEVEL

        elif state == ParsingState.EXPECT_LEVEL:
            curr['level'] = extract_cell_data(line)
            state = ParsingState.EXPECT_UNITS

        elif state == ParsingState.EXPECT_UNITS:
            curr['units'] = process_units(extract_cell_data(line))
            state = ParsingState.EXPECT_LOCATION

        elif state == ParsingState.EXPECT_LOCATION:
            location = process_location(extract_cell_data(line))
            curr['location'] = location
            map_query = urllib.parse.quote(location)
            curr['map_link'] = f'https://www.google.com/maps/search/?api=1&query={map_query}'
            state = ParsingState.EXPECT_TYPE

        elif state == ParsingState.EXPECT_TYPE:
            curr['type'] = extract_cell_data(line)
            incidents.append(curr)
            state = ParsingState.OUTSIDE_INCIDENT

        else:
            raise ValueError(f'Unexpected state: {state}')

    return incidents


if __name__ == '__main__':
    with open('testdata/20200627.html') as f:
        incidents = get_incidents(f.readlines())
    print(json.dumps(incidents, indent=2))
