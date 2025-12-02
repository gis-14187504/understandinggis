from math import cos, sin, radians, hypot
from numpy.random import uniform
from numpy import arange
from shapely.geometry import Polygon
from geopandas import read_file
from pyproj import Geod, CRS, Transformer
from matplotlib.pyplot import subplots, savefig
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib.patches import Patch


def compute_offset(origin, distance, direction):
    x1, y1 = origin
    dx = cos(radians(direction)) * distance
    dy = sin(radians(direction)) * distance
    return x1 + dx, y1 + dy


def evaluate_distortion(
        g, transformer,
        minx, miny, maxx, maxy,
        minr=10000, maxr=1000000,
        sample_number=1000,
        vertices=16):

    # random circle centres & radii
    xs = uniform(low=minx, high=maxx, size=sample_number)
    ys = uniform(low=miny, high=maxy, size=sample_number)
    rs = uniform(low=minr, high=maxr, size=sample_number)

    forward_azimuths = arange(0, 360, 360/vertices)

    area_indices = []
    shape_indices = []
    distance_indices = []


    for x, y, r in zip(xs, ys, rs):

        # circle on ellipsoid
        lons, lats = g.fwd(
            [x]*vertices, [y]*vertices, forward_azimuths, [r]*vertices
        )[:2]

        # project ellipsoidal circle
        e_coords = [
            transformer.transform(lon, lat, direction="FORWARD")
            for lon, lat in zip(lons, lats)
        ]
        ell_area = Polygon(e_coords).area

        # planar circle
        cx, cy = transformer.transform(x, y, direction="FORWARD")
        p_coords = [
            compute_offset((cx, cy), r, az)
            for az in forward_azimuths
        ]
        plan_area = Polygon(p_coords).area

        # area distortion
        a = abs(ell_area - plan_area) / abs(ell_area + plan_area)
        area_indices.append(a)

        # shape distortion
        radial = [
            hypot(cx - ex, cy - ey)
            for ex, ey in e_coords
        ]
        radial_sum = sum(radial)
        shape = [
            abs((1/vertices) - (d/radial_sum))
            for d in radial
        ]
        shape_indices.append(sum(shape))

    for _ in range(sample_number):
        x1 = uniform(minx, maxx)
        y1 = uniform(miny, maxy)
        x2 = uniform(minx, maxx)
        y2 = uniform(miny, maxy)

        ell_d = g.line_length([x1, x2], [y1, y2])

        px1, py1 = transformer.transform(x1, y1, direction="FORWARD")
        px2, py2 = transformer.transform(x2, y2, direction="FORWARD")
        plan_d = hypot(px2 - px1, py2 - py1)

        d = abs(ell_d - plan_d) / abs(ell_d + plan_d)
        distance_indices.append(d)

    # mean values
    Ea = sum(area_indices) / sample_number
    Es = sum(shape_indices) / sample_number
    Ep = sum(distance_indices) / sample_number

    return Ep, Es, Ea


def make_bounds_square(ax):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    w = x1 - x0
    h = y1 - y0
    if w > h:
        b = (w - h)/2
        ax.set_ylim(y0 - b, y1 + b)
    else:
        b = (h - w)/2
        ax.set_xlim(x0 - b, x1 + b)


if __name__ == "__main__":

    world = read_file("D:/understandinggis/data/natural-earth/ne_10m_admin_0_countries.shp")
    land_cover = read_file("D:/understandinggis/data/iceland/gis_osm_natural_a_free_1.shp")

    iceland = world.loc[world.ISO_A3 == "ISL"]
    ice = land_cover.loc[land_cover.fclass == "glacier"]

    minx, miny, maxx, maxy = iceland.total_bounds

    geo_string = "+proj=longlat +datum=WGS84 +no_defs"
    g = Geod(ellps="WGS84")


    projections = [
        {
            "name": "Web Mercator",
            "description": "Global Conformal",
            "proj": "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        },
        {
            "name": "Eckert IV",
            "description": "Global Equal Area",
            "proj": "+proj=eck4 +lon_0=0 +datum=WGS84 +units=m +no_defs"
        },
        {
            "name": "Iceland Albers",
            "description": "Local Equal Area",
            "proj": "+proj=aea +lat_1=64 +lat_2=66 +lat_0=65 +lon_0=-19 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
        }
    ]


    fig, axs = subplots(2, 2, figsize=(10, 10), constrained_layout=True)
    fig.suptitle("How much Ice is in Iceland?\n", fontsize=20)
    text_summary = ""


    for i, proj in enumerate(projections):

        ax_row = i // 2
        ax_col = i % 2

        transformer = Transformer.from_crs(
            CRS.from_proj4(geo_string),
            CRS.from_proj4(proj["proj"]),
            always_xy=True
        )

        Ep, Es, Ea = evaluate_distortion(
            g, transformer,
            minx, miny, maxx, maxy,
            10000, 1000000, 1000
        )

        ice_area_km2 = ice.to_crs(proj["proj"]).geometry.area.sum() / 1e6

        # summary text
        text_summary += (
            f"{proj['name']:<15} "
            f"$E_p={Ep:.4f}$  $E_s={Es:.4f}$  $E_a={Ea:.4f}$\n\n"
        )

        axs[ax_row][ax_col].set_title(
            f"{proj['name']} ({proj['description']})\n"
            f"Ice area: {ice_area_km2:,.0f} km sq."
        )
        axs[ax_row][ax_col].axis("off")
        axs[ax_row][ax_col].set_facecolor("#000000")

        iceland.to_crs(proj["proj"]).plot(
            ax=axs[ax_row][ax_col],
            color="#b2df8a",
            edgecolor="#33a02c",
            linewidth=0.3
        )

        ice.to_crs(proj["proj"]).plot(
            ax=axs[ax_row][ax_col],
            color="#e6f5f9",
            edgecolor="#e6f5f9",
            linewidth=0.2
        )

        axs[ax_row][ax_col].add_artist(ScaleBar(dx=1, units="m", location="lower right"))
        make_bounds_square(axs[ax_row][ax_col])

    axs[1][1].axis("off")

    axs[1][1].legend(
        [Patch(facecolor="#e6f5f9", edgecolor="#e6f5f9")],
        ["Glacier"], loc="lower right"
    )

    x, y, L = 0.9, 0.3, 0.15
    axs[1][1].annotate(
        "N", xy=(x, y), xytext=(x, y-L),
        arrowprops=dict(facecolor="black", width=3, headwidth=9),
        ha="center", va="center",
        fontsize=16, xycoords=axs[1][1].transAxes
    )

    axs[1][1].text(0.1, 0.45, text_summary, fontfamily="monospace")

    savefig("D:/understandinggis/out/week5.png", dpi=300)
    print("done!")
