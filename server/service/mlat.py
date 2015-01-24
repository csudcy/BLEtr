import datetime
import math
import time

from sqlalchemy import or_


"""
TODO:
  Don't clear_beacons to start; update them
  Make area a db table & give them names
  Expand areas & merge where necessary
"""

def _get_beacon_lookup(db, *filters):
    """
    Get a lookup of:
        beaon_id -> {
            beacon: ...,
            connected_beacons: {
                beaon_id -> distance
            },
        }
    """
    beacon_lookup = {}

    # Add all of the beacons to the lookup
    beacon_query = db.session.query(
        db.models.Beacon
    )
    if filters:
        beacon_query = beacon_query.filter(
            *filters
        )
    beacons = beacon_query.all()
    for beacon in beacons:
        beacon_lookup[beacon.id] = {
            'beacon': beacon,
            'connected_beacons': {},
        }

    # Add all the connections
    beacon_distances = db.session.query(
        db.models.BeaconDistance
    ).all()
    for beacon_distance in beacon_distances:
        # Add the connection in both directions
        beacon_pairs = (
            (beacon_distance.beacon_id_1, beacon_distance.beacon_id_2),
            (beacon_distance.beacon_id_2, beacon_distance.beacon_id_1)
        )
        for beacon_id_1, beacon_id_2 in beacon_pairs:
            connected_beacons = beacon_lookup[beacon_id_1]['connected_beacons']
            if beacon_id_2 not in connected_beacons:
                connected_beacons[beacon_id_2] = beacon_distance.beacon_distance

    return beacon_lookup


def clear_beacons(db):
    """
    Remove all existing beacons
    """
    db.session.query(
        db.models.Beacon
    ).delete()
    db.session.commit()


def init_beacons(db):
    """
    Create all necessary beacons
    """
    # Get the list of beacons
    beacon_ids = db.session.query(
        db.models.Event.beacon_id
    ).distinct().all()

    # Create a Beacon for each beacon_id
    for beacon_id in beacon_ids:
        db.session.add(
            db.models.Beacon(
                id=beacon_id
            )
        )

    db.session.commit()


def calc_connected_count(db):
    """
    Work out how many beacons each beacon can see
    """
    # Get the lookup
    beacon_lookup = _get_beacon_lookup(db)

    # Set the connected_count's
    for beacon_info in beacon_lookup.itervalues():
        beacon_info['beacon'].connected_count = len(beacon_info['connected_beacons'])

    db.session.commit()


def _find_beacon_without_area(beacon_lookup):
    """
    Find the first beacon that is not connected
    """
    for beacon_id, beacon_info in beacon_lookup.iteritems():
        if beacon_info['beacon'].area == None:
            return beacon_id


def _populate_area(beacon_lookup, beacon_id, area):
    """
    Assign all beacons connected to this beacon (recursively) to the given area
    """
    beacon_info = beacon_lookup[beacon_id]
    # Has this beacon been visited before?
    if beacon_info['beacon'].area is not None:
        # Yes; check the areas match
        if beacon_info['beacon'].area != area:
            raise Exception('Beacon is in multiple areas???')

        # This beacon has already been done
        return

    # This beacon has not been done before
    # Assign it to this area
    beacon_info['beacon'].area = area

    # Recurse over all connected beacons to assign them this area also
    for connected_beacon_id in beacon_info['connected_beacons'].iterkeys():
        _populate_area(beacon_lookup, connected_beacon_id, area)


def calc_beacon_areas(db):
    """
    Work out connected areas for the beacons
    """
    # Get the lookup
    beacon_lookup = _get_beacon_lookup(db)

    # Repeat until all beacons have an area
    area = 0
    while (True):
        beacon_id = _find_beacon_without_area(beacon_lookup)
        if beacon_id is None:
            # All beacons now belong to an area
            break
        _populate_area(beacon_lookup, beacon_id, area)
        area += 1

    # Save all areas back to the database
    db.session.commit()


def trilaterate(side_a, side_b, side_c):
    """
    Work out the angles required for the given sides
    """

    side_a2 = math.pow(side_a, 2)
    side_b2 = math.pow(side_b, 2)
    side_c2 = math.pow(side_c, 2)

    angle_a = math.acos(
        (side_b2 + side_c2 - side_a2)
        /
        (2 * side_b * side_c)
    )

    angle_b = math.acos(
        (side_c2 + side_a2 - side_b2)
        /
        (2 * side_c * side_a)
    )

    angle_c = math.acos(
        (side_a2 + side_b2 - side_c2)
        /
        (2 * side_a * side_b)
    )

    return angle_a, angle_b, angle_c

def _calc_beacon_coords_for_area(db, area):
    """
    Work out the coordinates for all the beacons in the given area
    """
    # Get all the beacons in this area
    area_beacons = _get_beacon_lookup(
        db,
        # Only look at beacons in this area
        db.models.Beacon.area == area,
        # Only beacons connected to at least 2 other beacons can be positioned
        db.models.Beacon.connected_count >= 2
    )
    if len(area_beacons) < 3:
        raise Exception(
            'Cannot calculate coordinates for an area ({area}) with less than 3 beacons in!'.format(
                area=area,
            )
        )

    # Get the list of beacons we need to find coordinates for
    beacon_ids_with_coordinates = set()
    beacon_ids_without_coordinates = set()
    for beacon_id, beacon_info in area_beacons.iteritems():
        if beacon_info['beacon'].x is None or beacon_info['beacon'].y is None:
            beacon_ids_without_coordinates.add(beacon_id)
        else:
            beacon_ids_with_coordinates.add(beacon_id)

    if len(beacon_ids_with_coordinates) == 1:
        raise Exception('Why is there only 1 beacon with coordinates?')

    if len(beacon_ids_with_coordinates) == 0:
        # Assume:
        #  1. A random beacon without coordinates is at (0, 0)
        #  2. Another random beacon without coordinates is at (0, distance from first beacon)

        beacon_id_1 = beacon_ids_without_coordinates.pop()
        beacon_id_2 = beacon_ids_without_coordinates.pop()

        area_beacons[beacon_id_1]['beacon'].x = 0
        area_beacons[beacon_id_1]['beacon'].y = 0

        area_beacons[beacon_id_2]['beacon'].x = area_beacons[beacon_id_1]['connected_beacons'][beacon_id_2]
        area_beacons[beacon_id_2]['beacon'].y = 0

        beacon_ids_with_coordinates.add(beacon_id_1)
        beacon_ids_with_coordinates.add(beacon_id_2)

    # Iterate over all beacon_ids_without_coordinates until they all have coordinates
    while len(beacon_ids_without_coordinates) > 0:
        # Get a random beacon from the list
        beacon_id = beacon_ids_without_coordinates.pop()
        beacon_info = area_beacons[beacon_id]

        # Work out which connected_beacons have coordinates
        connected_beacon_ids = set(beacon_info['connected_beacons'].keys())
        connected_beacon_ids_with_coordinates = connected_beacon_ids & beacon_ids_with_coordinates

        # Check we have enough to give this beacon coords
        if len(connected_beacon_ids_with_coordinates) < 2:
            # This beacon is not connected to enough other beacons with coords yet
            # Add it back to the list and try again later when more beacons have coords
            beacon_ids_without_coordinates.add(beacon_id)

        # Now, do some maths!
        beacon_id_1 = connected_beacon_ids_with_coordinates.pop()
        beacon_id_2 = connected_beacon_ids_with_coordinates.pop()
        side_a = beacon_info['connected_beacons'][beacon_id_1]
        side_b = beacon_info['connected_beacons'][beacon_id_2]
        side_c = area_beacons[beacon_id_1]['connected_beacons'][beacon_id_2]

        angle_a, angle_b, angle_c = trilaterate(side_a, side_b, side_c)

        # ^Total = ^1-to-2 + ^B
        # Coords = ^Total * side_a
        diff_x = area_beacons[beacon_id_2]['beacon'].x - area_beacons[beacon_id_1]['beacon'].x
        diff_y = area_beacons[beacon_id_2]['beacon'].y - area_beacons[beacon_id_1]['beacon'].y
        angle_1to2 = math.atan(diff_y / diff_x)
        angle_total = angle_1to2 + angle_b

        beacon_info['beacon'].x = area_beacons[beacon_id_1]['beacon'].x + side_a * math.cos(angle_total)
        beacon_info['beacon'].y = area_beacons[beacon_id_1]['beacon'].y + side_a * math.sin(angle_total)

        print '1. (%s, %s)' % (area_beacons[beacon_id_1]['beacon'].x, area_beacons[beacon_id_1]['beacon'].y)
        print '2. (%s, %s)' % (area_beacons[beacon_id_2]['beacon'].x, area_beacons[beacon_id_2]['beacon'].y)
        print '?. (%s, %s)' % (beacon_info['beacon'].x, beacon_info['beacon'].y)


def calc_beacon_coords(db):
    """
    Work out the coordinates for all the beacons
    """
    # Get the list of areas
    areas = db.session.query(
        db.models.Beacon.area
    ).distinct().all()

    # Create a Beacon for each beacon_id
    for area in areas:
        _calc_beacon_coords_for_area(db, area)

    db.session.commit()


def calc_all(db):
    """
    Calculate everything necessary for multilateration
    """
    clear_beacons(db)
    init_beacons(db)
    calc_connected_count(db)
    calc_beacon_areas(db)
    calc_beacon_coords(db)


def get_historical_position(db, user_id, current_time):
    """
    Find events at the given time and use them to calculate a position
    """
    # Get events from the database
    event_objs = db.session.query(
        db.models.Event
    ).filter(
        db.models.Event.user_id == user_id,
        db.models.Event.seen_at >= current_time - datetime.timedelta(seconds=2),
        db.models.Event.seen_at <= current_time,
    ).all()

    # Create the events structure for get_position
    events = {}
    for event_obj in event_objs:
        events[event_obj.beacon_id] = event_obj.beacon_distance

    # Now work out the position!
    return get_position(events)


def get_position(events):
    """
    Calculate a position from the given events
    events is a dict of beacon_id -> distance
    Returns x, y, radius
    """
    import pdb
    pdb.set_trace()


def test_get_position(db):
    """
    """
    event_timeranges = db.session.query(
        db.models.EventTimerange
    ).all()
    time_step = datetime.timedelta(seconds=5)
    for event_timerange in event_timeranges:
        current_time = event_timerange.start_time
        while current_time < event_timerange.end_time:
            print get_historical_position(
                db,
                event_timerange.user_id,
                current_time,
            )
            current_time += time_step
