import collections
import enum
import json
import logging


UNIT_MAP = {
    'A': 'Aid Unit',
    'B': 'Battalion Chief',
    'E': 'Engine',
    'ICS': 'Incident Command System',
    'L': 'Ladder',
    'M': 'Medic Unit',
    'R': 'Technical Rescue Unit',
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


def process_units(units_data):
    # TODO(aryann): Handle unexpected unit types.
    units = []
    for unit in units_data.split():
        unit_type = UNIT_MAP.get(unit[: 1])
        if len(unit) < 2 or not unit_type or not unit[1].isdigit():
            logging.warning('Encountered unknown unit type: %s', units_data)
            continue
        units.append(unit_type + ' ' + unit[1:])

    units.sort()
    if not units:
        return []
    if len(units) == 1:
        return units[0]
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
            curr['location'] = process_location(extract_cell_data(line))
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
