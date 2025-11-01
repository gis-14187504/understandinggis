from math import cos, sin, radians
from geopandas import read_file
from pyproj import Geod
from pyproj import CRS, Transformer

def evaluate_distortion(g, transformer, minx, miny, maxx, maxy, minr, maxr, sample_number, vertices=16):
    Ep=0
    Es=0
    Ea=0
    return Ep, Es, Ea

def compute_offset(origin, distance, direction):
    """
    Compute the location of a point at a given distance and direction from a specified location using trigonometry
    """
    offset_x = origin[0] + distance * cos(radians(direction))
    offset_y = origin[1] + distance * sin(radians(direction))
    return (offset_x, offset_y)

# this code tests whether your function works correctly
origin = (345678, 456789)
destination = compute_offset(origin, 1011, 123)	# move 1011m in a direction of 123 degrees 
print("CORRECT!!" if (int(destination[0]), int(destination[1])) == (345127, 457636) else f"INCORRECT!! Error: {(int(destination[0])-345127, int(destination[1])-457636)}")

world = read_file("D:/understandinggis/data/natural-earth/ne_10m_admin_0_countries.shp")

iceland = world[world['ISO_A3'] == 'ISL'].to_crs(epsg=4326)

land_cover = read_file("D:/understandinggis/data/iceland/gis_osm_natural_a_free_1.shp")

ice = land_cover[land_cover['fclass'] == "glacier"]

minx, miny, maxx, maxy = iceland.total_bounds

print(f"{minx:.4f}, {miny:.4f}, {maxx:.4f}, {maxy:.4f}")

geo_string = "+proj=longlat +datum=WGS84 +no_defs"
g = Geod(ellps='WGS84')

projections = [
    {
        'name': 'Web Mercator',
        'description': 'Global Conformal',
        'proj': 'EPSG:3857'   # Web Mercator projection
    },
    {
        'name': 'Eckert IV',
        'description': 'Global Equal Area',
        'proj': '+proj=eck4 +lon_0=0 +datum=WGS84 +units=m +no_defs'   # Eckert IV projection
    },
    {
        'name': 'Albers Equal Area (Local)',
        'description': 'Local Equal Area',
        'proj': '+proj=aea +lat_1=49 +lat_2=61 +lon_0=-96 +datum=WGS84 +units=m +no_defs'  # Albers Conic projection (example local)
    }
]

for ax_num, projection in enumerate(projections):
    transformer = Transformer.from_crs(CRS.from_proj4(geo_string), CRS.from_proj4(projection['proj']), always_xy=True)
    
# calculate the distortion
Ep, Es, Ea = evaluate_distortion(g, transformer, minx, miny, maxx, maxy, 10000, 1000000, 1000)