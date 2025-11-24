from numpy import zeros, column_stack
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from rasterio.transform import rowcol
from skimage.draw import line, circle_perimeter
from sys import exit
from math import hypot, floor, ceil
from geopandas import GeoSeries
from shapely.geometry import Point
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.pyplot import subplots, savefig
from matplotlib_scalebar.scalebar import ScaleBar


# open the elevation data file
with rio_open("../data/helvellyn/Helvellyn-50.tif") as dem:

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1)

    # create a new 'band' of raster data the same size
    output = zeros(dem_data.shape, dtype='uint8')

def coord_2_img(transform, x, y):
    r, c = rowcol(transform, x, y)
    return (int(r), int(c))

def adjust_height(height, distance, earth_diameter=12740000, refraction_coefficient=0.13):
	"""
	* Adjust the apparant height of an object at a certain distance, accounting for the
	* 	curvature of the earth and atmospheric refraction
	"""
    
	return height - (distance**2 / earth_diameter) * (1 - refraction_coefficient)

def line_of_sight(r0, c0, height0,
                  r1, c1, height1,
                  radius, dem_data, transform,
                  output):

    max_dydx = -float('inf')

    # pixels along the line (skip first)
    for r, c in column_stack(line(r0, c0, r1, c1))[1:]:

        # distance from observer (in pixels)
        dx = hypot(r - r0, c - c0)

        # stop if beyond radius or outside DEM
        if dx > radius or not (0 <= r < dem_data.shape[0]) or not (0 <= c < dem_data.shape[1]):
            break

        # elevation of this cell
        ground = dem_data[r, c]

        # convert pixel distance to metres
        distance_m = dx * transform[0]

        # adjust the heights for curvature + refraction
        ground_adj = adjust_height(ground, distance_m)
        target_tip_adj = adjust_height(ground + height1, distance_m)

        # compute dydx using adjusted heights
        base_dydx = (ground_adj - height0) / dx
        tip_dydx  = (target_tip_adj - height0) / dx

        # if tip is visible, mark cell
        if tip_dydx > max_dydx:
            output[r, c] = 1

        # update max
        max_dydx = max(max_dydx, base_dydx)

    return output


def viewshed(x0, y0, radius_m, observer_height, target_height, dem_data, transform):
    r0, c0 = rowcol(transform, x0, y0)
    r0 = int(r0)
    c0 = int(c0)
    print(f"Origin in image space: row={r0}, col={c0}")
    
    #make sure that we are within the dataset
    if not (0 <= r0 < dem_data.shape[0]) or not (0 <= c0 < dem_data.shape[1]):
       print(f"Sorry, {(x0, y0)} is not within the elevation dataset.")
       exit()

    radius_px = int(radius_m / transform[0])
    print(f"Radius (in pixels): {radius_px}")

    # get the observer height (above sea level)
    height0 = dem_data[r0, c0] + observer_height
    print(f"Observer height ASL: {height0:.2f} m")
    
    output = zeros(dem_data.shape, dtype='uint8')
       
    output[r0, c0] = 1
    
    # get pixels in the perimeter of the viewshed
    for r, c in column_stack(circle_perimeter(r0, c0, radius_px)):

	# calculate line of sight to each pixel, pass output and get a new one back each time
    	output = line_of_sight(r0, c0, height0, r, c, target_height, radius_px, dem_data, transform, output)

    # return the resulting viewshed
    return output   



x = 334170
y = 515165

# set origin for viewshed
x0, y0 = 330000, 512500

# transform the coordinates for the summit of Helvellyn into image space
row, col = coord_2_img(dem.transform, x, y)

# print out the elevation at that location by reading it from the dataset
print(f"{dem_data[row][col]:.0f}m")	# note that this makes use of an f-string to format the number

# calculate the viewshed
output = viewshed(x0, y0, 20000, 1.8, 100, dem_data, dem.transform)

print(column_stack(line(row, col, row, col+50)))

output[row, col] = 1

output[line(row, col, row, col+50)] = 1

output[circle_perimeter(row, col, 50)] = 1

# output image
fig, my_ax = subplots(1, 1, figsize=(16, 10))
my_ax.set_title("Viewshed Analysis")

	# draw dem
rio_show(
	dem_data,
	ax=my_ax,
	transform = dem.transform,
	cmap = 'viridis',
	)

	# draw dem as contours
rio_show(
	dem_data,
	ax=my_ax,
	contour=True,
	transform = dem.transform,
	colors = ['white'],
	linewidths = [0.5],
	)

# add viewshed
rio_show(
	output,
	ax=my_ax,
	transform=dem.transform,
	cmap = LinearSegmentedColormap.from_list('binary_viewshed', [(0, 0, 0, 0), (1, 0, 0, 0.5)], N=2)
	)

# add origin point
GeoSeries(Point(x0, y0)).plot(
	ax = my_ax,
	markersize = 60,
	color = 'black',
	edgecolor = 'white'
	)

# add a colour bar
fig.colorbar(ScalarMappable(norm=Normalize(vmin=floor(dem_data.min()), vmax=ceil(dem_data.max())), cmap='viridis'), ax=my_ax, pad=0.01)

# add north arrow
x, y, arrow_length = 0.97, 0.99, 0.1
my_ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
	arrowprops=dict(facecolor='black', width=5, headwidth=15),
	ha='center', va='center', fontsize=20, xycoords=my_ax.transAxes)

# add scalebar
my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))

# add legend for point
my_ax.legend(
	handles=[
		Patch(facecolor=(1, 0, 0, 0.5), edgecolor=None, label=f'Visible Area'),
		Line2D([0], [0], marker='o', color=(1,1,1,0), label='Viewshed Origin', markerfacecolor='black', markersize=8)
	], loc='lower left')

# save the result	
savefig('./out/7.png', bbox_inches='tight')
print("done!")



