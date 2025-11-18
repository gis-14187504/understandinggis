from numpy import zeros
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from matplotlib.pyplot import subplots, savefig
from matplotlib.colors import LinearSegmentedColormap
from rasterio.transform import rowcol, xy

# open the elevation data file
with rio_open("../data/helvellyn/Helvellyn-50.tif") as dem:

    # read the data out of band 1 in the dataset
    dem_data = dem.read(1)

    # create a new 'band' of raster data the same size
    output = zeros(dem_data.shape, dtype='uint8')

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
    cmap = LinearSegmentedColormap.from_list('binary_viewshed', [(0, 0, 0, 0), (1, 0, 0, 0.5)], N=2)
    )
savefig('./out/bresenham.png', bbox_inches='tight')# -*- coding: utf-8 -*-

def coord_2_img(transform, x, y):
    """convert coordinate space (x,y) → image space (row,col)."""
    r, c = rowcol(transform, x, y)
    return int(r), int(c)

x = 334170
y = 515165

row, col = coord_2_img(dem.transform, x, y)
print("row, col =", row, col)

output[row-1:row+2, col-1:col+2] = 1

red_cmap = LinearSegmentedColormap.from_list(
    'red_point',
    [(0, 0, 0, 0), (1, 0, 0, 1)],
    N=2
)
