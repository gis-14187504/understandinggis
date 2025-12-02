from pandas import DataFrame
from time import perf_counter
from geopandas import read_file
from week5 import evaluate_distortion
from pyproj import Geod, CRS, Transformer
from concurrent.futures import ProcessPoolExecutor
import pandas as pd


def distortion_worker(name, proj_string, geo_string, g, minx, miny, maxx, maxy,
                      minr=10000, maxr=1000000, samples=10000):
    """
    Returns (name, Ep, Es, Ea)
    """

    transformer = Transformer.from_crs(
        CRS.from_proj4(geo_string),
        CRS.from_proj4(proj_string),
        always_xy=True
    )

    Ep, Es, Ea = evaluate_distortion(
        g, transformer, minx, miny, maxx, maxy,
        minr, maxr, samples
    )

    return name, Ep, Es, Ea


if __name__ == "__main__":

    # list of projections
    projections = [
        {'name': 'Mollweide',   'proj': '+proj=moll +lon_0=0 +datum=WGS84 +units=m +no_defs'},
        {'name': 'Hammer',      'proj': '+proj=hammer +lon_0=0 +datum=WGS84 +units=m +no_defs'},
        {'name': 'Equal Earth', 'proj': '+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs'},
        {'name': 'Eckert IV',   'proj': '+proj=eck4 +lon_0=0 +datum=WGS84 +units=m +no_defs'},
        {'name': 'Wagner IV',   'proj': '+proj=wag4 +lon_0=0 +datum=WGS84 +units=m +no_defs'},
        {'name': 'Wagner VII',  'proj': '+proj=wag7 +lon_0=0 +datum=WGS84 +units=m +no_defs'}
    ]

    geo_string = "+proj=longlat +datum=WGS84 +no_defs"
    g = Geod(ellps='WGS84')

    # load world shapefile
    world = read_file("D:/System/桌面/understandinggis/understandinggis/data/natural-earth/ne_10m_admin_0_countries.shp")

    # extract Iceland
    country = world.loc[world.ISO_A3 == "ISL"]
    minx, miny, maxx, maxy = country.total_bounds

    start = perf_counter()

    tasks = []
    for p in projections:
        tasks.append((p['name'], p['proj']))

    results_list = []

    with ProcessPoolExecutor() as executor:
        futures = []

        for name, proj_string in tasks:
            future = executor.submit(
                distortion_worker,
                name, proj_string, geo_string, g,
                minx, miny, maxx, maxy,
                10000, 1000000, 10000
            )
            futures.append(future)

        for f in futures:
            results_list.append(f.result())

    df = pd.DataFrame(results_list, columns=['name', 'Ep', 'Es', 'Ea']).sort_values('Ea')

    print(df)
    print(f"\nCompleted in {perf_counter() - start:.2f} seconds.")
