from geopandas import read_file
from math import sqrt

def distance(x1,y1,x2,y2):
    return sqrt((x2-x1)**2+(y2-y1)**2)

def get_effective_area(a, b, c):
	# calculate the length of each side
	side_a = distance(b[0], b[1], c[0], c[1])
	side_b = distance(a[0], a[1], c[0], c[1])
	side_c = distance(a[0], a[1], b[0], b[1])

	# calculate semi-perimeter of the triangle (perimeter / 2)
	s = (side_a + side_b + side_c) / 2

	# apply Heron's formula and return
	return sqrt(s * (s - side_a) * (s - side_b) * (s - side_c))

# open a dataset of all countries in the world
world = read_file("P:/UGIS/understandinggis/data/natural-earth/ne_10m_admin_0_countries.shp")

# extract the UK, project, and extract the geometry
uk = world[world['ISO_A3']=='GBR'].to_crs(epsg=4326).geometry.iloc[0]	# COMPLETE THIS LINE

# report geometry type
print(f"geometry type: {uk.geom_type}")

if uk.geom_type != 'MultiPolygon':
  print("Geometry is not a MultiPolygon, exiting...")
  exit()
  
  # initialise variables to hold the coordinates and area of the largest polygon
biggest_area = 0
coord_list = []

# loop through each polygon in the multipolygon and find the biggest (mainland Great Britain)
for poly in uk.geoms:

	# if it is the biggest so far
	if 	poly.area > biggest_area:# COMPLETE THIS LINE
    
		# store the new value for biggest area
		biggest_area = poly.area
        
     # store the coordinates of the polygon
		coord_list = list(poly.boundary.coords)	# COMPLETE THIS LINE (look at the variables that you defined before the loop)
        
# set the percentage of nodes that you want to remove
SIMPLIFICATION_PERC = 98

# how many nodes do we need?
n_nodes = int(len(coord_list) / 100.0 * (100 - SIMPLIFICATION_PERC))

# ensure that there are at least 3 nodes (minimum for a polygon)
if n_nodes < 3:
    odes = 3 

# loop through each node, excluding the end points
areas = []
for i in range(1, len(coord_list)-1):

  # get the effective area
  area = get_effective_area(coord_list[i-1], coord_list[i], coord_list[i+1] )	# COMPLETE THIS LINE

  # append the node and effective area to the list
  areas.append({"point": coord_list[i], "area": area})
  print(areas)