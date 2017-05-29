try:
    import fiona
    import fiona.transform
except ImportError:
    raise ImportError("Missing optional dependency: \"fiona\"")


def transform_layer(layer, epsg=4326):
    """
    Transform single layer to EPSG:4326 rounded to 6 decimal places.
    """
    layer['geometry'] = fiona.transform.transform_geom(
        'EPSG:{}'.format(epsg), 'EPSG:4326', layer['geometry'], precision=6
    )
    return layer


def prepare_geodata(path, default_epsg=None):
    """
    Given a path to an OGR-compatible spatial file, open file, convert to
    EPSG:4326, round to 6 decimal places (11mm precision), and yield GeoJSON
    Features from that file.
    """
    with fiona.open(path) as data:
        epsg = data.crs.get('init', str(default_epsg)).split(':')[-1]
        for layer in data:
            yield transform_layer(layer, epsg=epsg)
