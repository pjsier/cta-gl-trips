from __future__ import print_function, division
import os
import json
import pandas as pd
from shapely.ops import split, snap
from shapely.geometry import Point, LineString


BASE_DIR = os.path.dirname(__file__)

def get_seconds(time_str):
    return sum(x * int(t) for x, t in zip([3600, 60, 1], time_str.split(":")))

START_TIME = get_seconds('08:00:00')
END_TIME = get_seconds('18:00:00')
MAX_TIME_VAL = 1800

EL_ROUTE_IDS = ['Red', 'P', 'Y', 'Blue', 'Pink', 'G', 'Org', 'Brn']
# EL_COLOR_MAP = {
#     'Red Line': [198, 12, 48],
#     'Purple Line': [82, 35, 152],
#     'Yellow Line': [249, 227, 0],
#     'Blue Line': [0, 161, 222],
#     'Pink Line': [226, 126, 166],
#     'Green Line': [0, 155, 58],
#     'Orange Line': [249, 70, 28],
#     'Brown Line': [98, 54, 27]
# }

def get_line_segment(linestring, origin, destination):
    if linestring.type == 'GeometryCollection':
        linestring = linestring[0]
    origin_dist = linestring.project(origin)
    dest_dist = linestring.project(destination)

    line_coords = [linestring.interpolate(origin_dist)]
    for coord in linestring.coords:
        pt = Point(coord)
        if (linestring.project(pt) >= origin_dist) and (linestring.project(pt) <= dest_dist):
            line_coords.append(pt)
    if len(line_coords) == 1:
        return None
    line_coords.append(linestring.interpolate(dest_dist))
    return LineString(line_coords)


def get_time_scaled(int_time):
    return ((int_time - START_TIME) / (END_TIME - START_TIME)) * MAX_TIME_VAL


def interpolate_time_points(trip_id, route_name, trip_line, trip_stop_time_df, stop_map):
    trip_obj = {
        'route': route_name,
        'trip_id': trip_id,
        'segments': []
    }
    trip_stop_records = trip_stop_time_df.loc[
        trip_stop_time_df['trip_id'] == trip_id
    ].sort_values(by='stop_sequence').to_dict(orient='records')

    full_trip_line_segment = get_line_segment(
        trip_line,
        stop_map[trip_stop_records[0]['stop_id']],
        stop_map[trip_stop_records[-1]['stop_id']]
    )
    if not full_trip_line_segment:
        return None

    for idx, trip_stop in enumerate(trip_stop_records):
        stop = stop_map.get(trip_stop['stop_id'])
        if idx == 0:
            trip_obj['segments'].append(
                [stop.x, stop.y, get_time_scaled(trip_stop['departure_time'])]
            )
        else:
            last_trip_stop = trip_stop_records[idx - 1]
            if not stop_map.get(last_trip_stop['stop_id']):
                last_trip_stop = trip_stop_records[idx - 2]
            line_seg = get_line_segment(
                full_trip_line_segment,
                stop_map.get(last_trip_stop['stop_id']),
                stop
            )
            if not line_seg or line_seg.length == 0:
                continue
            for lpt_idx, line_pt in enumerate(line_seg.coords):
                if lpt_idx == 0:
                    continue
                elif lpt_idx == (len(line_seg.coords) - 1):
                    trip_obj['segments'].append([
                        line_pt[0], line_pt[1], 
                        get_time_scaled(trip_stop['departure_time'])
                    ])
                else:
                    lpt_dist = line_seg.project(Point(line_pt))
                    interp_sec = (
                        (lpt_dist / line_seg.length) *
                        (trip_stop['departure_time'] - last_trip_stop['departure_time'])
                    ) + last_trip_stop['departure_time']
                    trip_obj['segments'].append(
                        [line_pt[0], line_pt[1], get_time_scaled(interp_sec)]
                    )
    return trip_obj


if __name__ == '__main__':
    shape_df = pd.read_csv(os.path.join(BASE_DIR, 'shapes.txt'))
    shape_ids = shape_df['shape_id'].unique()

    # Create mapping of shape IDs and their LineString geometry
    shape_map = {}
    for shape_id in shape_ids:
        shape_rows = shape_df.loc[shape_df['shape_id'] == shape_id].to_dict(orient='records')
        shape_map[shape_id] = LineString(
            [Point(s['shape_pt_lon'], s['shape_pt_lat']) for s in shape_rows]
        ).simplify(0.01)

    route_rows = pd.read_csv(os.path.join(BASE_DIR, 'routes.txt')).to_dict(orient='records')
    route_map = {r['route_id']: r['route_long_name'] for r in route_rows}

    # Create mapping of stop IDs to points
    stop_df = pd.read_csv(os.path.join(BASE_DIR, 'stops.txt'))
    stop_rows = stop_df.to_dict(orient='records')
    stop_map = {s['stop_id']: Point(s['stop_lon'], s['stop_lat']) for s in stop_rows}
    
    # Find the most common service and all trip IDs for the service
    trip_df = pd.read_csv(os.path.join(BASE_DIR, 'trips.txt'))
    service_ids = trip_df['service_id'].unique().tolist()
    max_service_id = max(
        service_ids, 
        key=lambda s: trip_df.loc[trip_df['service_id'] == s, 'route_id'].count()
    )
    trips = trip_df.loc[
        (trip_df['service_id'] == max_service_id) |
        (trip_df['route_id'].isin(EL_ROUTE_IDS))
    ].copy()
    trip_ids = trips['trip_id'].tolist()

    # Get all stop times for that trip and service between 8am and 6pm
    stop_time_df = pd.read_csv(os.path.join(BASE_DIR, 'stop_times.txt'))
    stop_time_df['departure_time'] = stop_time_df['departure_time'].apply(get_seconds)

    trip_stops = stop_time_df.loc[
        (stop_time_df['trip_id'].isin(trip_ids)) &
        (stop_time_df['departure_time'] > START_TIME) &
        (stop_time_df['departure_time'] < END_TIME)
    ].copy()

    # Update trip IDs with those found in trip stops
    trip_ids = trip_stops['trip_id'].unique().tolist()
    trip_records = trips.loc[trips['trip_id'].isin(trip_ids)].to_dict(orient='records')

    trip_segment_list = []
    for trip in trip_records:
        trip_line = shape_map.get(trip['shape_id'])
        route_name = route_map.get(trip['route_id'], 'No route')
        trip_segments = interpolate_time_points(
            trip['trip_id'], route_name, trip_line, trip_stops, stop_map
        )
        if trip_segments:
            trip_segment_list.append(trip_segments)
    
    with open(os.path.join(BASE_DIR, 'trip_line_segments.json'), 'w') as trip_f:
        json.dump(trip_segment_list, trip_f)
