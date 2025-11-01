from math import cos, sin, radians
from geopandas import read_file
from pyproj import Geod
from pyproj import CRS, Transformer
from numpy.random import uniform
from numpy import arange
from shapely.geometry import Polygon



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

# set the geographical proj string and ellipsoid (should be the same)
geo_string = "+proj=longlat +datum=WGS84 +no_defs"
g = Geod(ellps='WGS84')


# create a list of dictionaries for the projected CRS to evaluate for distortion
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

# loop through each CRS
for ax_num, projection in enumerate(projections):
    print(f"Loop {ax_num}: Now processing {projection['name']} — {projection['description']}")
    
    transformer = Transformer.from_crs(
        CRS.from_proj4(geo_string),
        CRS.from_proj4(projection['proj']),
        always_xy=True
    )
    
    # initialise a PyProj Transformer to transform coordinates
transformer = Transformer.from_crs(CRS.from_proj4(geo_string), CRS.from_proj4(projection['proj']), always_xy=True)

# calculate the distortion

def evaluate_distortion(g, transformer, minx, miny, maxx, maxy, minr, maxr, sample_number=1000, vertices=16):
    Ep, Es, Ea = evaluate_distortion(g, transformer, minx, miny, maxx, maxy, 10000, 1000000, 1000)

# calculate the required number of random locations (x and y separately) plus radius
xs = uniform(low=minx, high=maxx, size=1000)
ys = uniform(low=minx, high=maxx, size=1000)
rs = uniform(low=minx, high=maxx, size=1000)

# offset distances
forward_azimuths = arange(0, 360, 22.5)

# define three empty lists
area_indices = []
shape_indices = []
distance_indices = []

# loop through xs, ys, and rs using zip()
for x, y, r in zip(xs, ys, rs):
    
    print(f"x={x}, y={y}, r={r}")


    area_indices.append(x * y)     
    shape_indices.append(r / 1000)  
    distance_indices.append(r)     


# construct a circle around the centre point on the ellipsoid
vertices=16
forward_azimuths = list(range(0, 360, int(360 / vertices)))

lons, lats = g.fwd([x]*vertices, [y]*vertices, forward_azimuths, [r]*vertices)[:2]

# project the result, calculate area, append to the list
e_coords = [ transformer.transform(lon, lat, direction='FORWARD') for lon, lat in zip(lons, lats) ]

# get the area of the resulting circle
ellipsoidal_area = Polygon(e_coords).area

# transform the centre point to the projected CRS
centre_x, centre_y = transformer.transform(x, y, direction='FORWARD')

# construct a circle around the projected point on a plane, calculate area
planar_area = Polygon([ compute_offset(centre_x, centre_y, r, az) for az in forward_azimuths ]).area