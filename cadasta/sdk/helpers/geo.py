try:
    import fiona
    import fiona.transform
except ImportError:
    raise ImportError("Missing optional dependency: \"fiona\"")


def transform_bbox(bbox, epsg=4326):
    """
    Convert bounding box to EPSG:4326 values. Expects an array/tuple of
    [x0, y0, x1, y1]. Returns in the same format.
    """
    x0, y0, x1, y1 = bbox
    # Group values into tuples (eg [x0,y0,x1,y1] -> [(x0,y0),(x1,y1)])
    paired = zip(*(iter(bbox),) * 2)
    # Split into types (eg [(x0,y0),(x1,y1)] -> [(x0,x1),(y0,y1)])
    separated = zip(*paired)
    (x0, x1), (y0, y1) = fiona.transform.transform(
        'EPSG:{}'.format(epsg), 'EPSG:4326', *separated)
    return [round(x, 6) for x in [x0, y0, x1, y1]]


def transform_layer(layer, epsg=4326):
    """
    Transform single layer to EPSG:4326 rounded to 6 decimal places.
    """
    layer['geometry'] = fiona.transform.transform_geom(
        'EPSG:{}'.format(epsg), 'EPSG:4326', layer['geometry'], precision=6
    )
    return layer


def prepare_geodata(path):
    """
    Given a path to an OGR-compatible spatial file, open file, convert
    to EPSG:4326, round to 6 decimal places (11mm precision), and return
    as a GeoJSON compatible dictionary.
    """
    with fiona.open(path) as data:
        epsg = data.crs['init'].split(':')[-1]
        bbox = []
        if len(data) == 1:
            return dict(transform_layer(data[0], epsg=epsg), bbox=bbox)
        return dict({
            'type': 'FeatureCollection',
            'features': [transform_layer(layer, epsg=epsg) for layer in data]
        }, bbox=bbox)
