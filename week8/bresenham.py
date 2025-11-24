from numpy import zeros
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap
from rasterio.transform import rowcol, xy
from skimage.draw import line
from numpy import column_stack
from skimage.draw import circle_perimeter


# open the elevation data file
with rio_open("../data/helvellyn/Helvellyn-50.tif") as dem:

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1)

    # create a new 'band' of raster data the same size
    output = zeros(dem_data.shape, dtype='uint8')

def coord_2_img(transform, x, y):
    r, c = rowcol(transform, x, y)
    return (int(r), int(c))

x = 334170
y = 515165

# transform the coordinates for the summit of Helvellyn into image space
row, col = coord_2_img(dem.transform, x, y)

# print out the elevation at that location by reading it from the dataset
print(f"{dem_data[row][col]:.0f}m")	# note that this makes use of an f-string to format the number

print(column_stack(line(row, col, row, col+50)))

output[row, col] = 1

output[line(row, col, row, col+50)] = 1

output[circle_perimeter(row, col, 50)] = 1

# plot the dataset
fig, my_ax = subplots(1, 1, figsize=(16, 10))

# add the DEM
rio_show(
  dem_data,
  ax=my_ax,
  transform = dem.transform,
)
# add the drawing layer
rio_show(
    output,
    ax=my_ax,
    transform=dem.transform,
    cmap = LinearSegmentedColormap.from_list('binary_viewshed', [(0, 0, 0, 0), (1, 0, 0, 0.8)], N=2)
    )



savefig('./out/bresenham.png', bbox_inches='tight')# -*- coding: utf-8 -*-





