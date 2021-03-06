from __future__ import print_function

import base64
from math import pi, sin, cos
import pandas as pd

from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.resources import INLINE
from bokeh.browserlib import view

from bokeh.glyphs import Wedge, AnnularWedge, ImageURL, Text
from bokeh.objects import ColumnDataSource, Plot, Glyph, Range1d
from bokeh.colors import skyblue, limegreen, orange, purple, orangered, lightgray
from bokeh.sampledata.browsers import browsers_nov_2013, icons

df = browsers_nov_2013

xdr = Range1d(start=-2, end=2)
ydr = Range1d(start=-2, end=2)

title = "Web browser market share (November 2013)"
plot = Plot(title=title, x_range=xdr, y_range=ydr, width=800, height=800)

colors = {"Chrome": limegreen, "Firefox": orange, "Safari": purple, "Opera": orangered, "IE": skyblue, "Other": lightgray}

aggregated = df.groupby("Browser").agg(sum)
selected = aggregated[aggregated.Share >= 1].copy()
selected.loc["Other"] = aggregated[aggregated.Share < 1].sum()
browsers = selected.index.tolist()

radians = lambda x: 2*pi*(x/100)
angles = selected.Share.map(radians).cumsum()

end_angles = angles.tolist()
start_angles = [0] + end_angles[:-1]

browsers_source = ColumnDataSource(dict(
    start  = start_angles,
    end    = end_angles,
    colors = [colors[browser] for browser in browsers ],
))
plot.data_sources.append(browsers_source)

glyph = Wedge(x=0, y=0, radius=1, start_angle="start", end_angle="end", fill_color="colors")
renderer = Glyph(data_source=browsers_source, xdata_range=xdr, ydata_range=ydr, glyph=glyph)
plot.renderers.append(renderer)

def polar_to_cartesian(r, start_angles, end_angles):
    cartesian = lambda r, alpha: (r*cos(alpha), r*sin(alpha))
    points = []

    for start, end in zip(start_angles, end_angles):
        points.append(cartesian(r, (end + start)/2))

    return zip(*points)

for browser, start_angle, end_angle in zip(browsers, start_angles, end_angles):
    versions = df[(df.Browser == browser) & (df.Share >= 0.5)]
    angles = versions.Share.map(radians).cumsum() + start_angle
    end = angles.tolist() + [end_angle]
    start = [start_angle] + end[:-1]
    base_color = colors[browser]
    fill = [ base_color.lighten(i*0.05) for i in range(len(versions) + 1) ]
    text = [ number if share >= 1 else "" for number, share in zip(versions.VersionNumber, versions.Share) ]
    x, y = polar_to_cartesian(1.25, start, end)

    source = ColumnDataSource(dict(start=start, end=end, fill=fill))
    plot.data_sources.append(source)
    glyph = AnnularWedge(x=0, y=0, inner_radius=1, outer_radius=1.5, start_angle="start", end_angle="end", fill_color="fill")
    renderer = Glyph(data_source=source, xdata_range=xdr, ydata_range=ydr, glyph=glyph)
    plot.renderers.append(renderer)

    text_source = ColumnDataSource(dict(text=text, x=x, y=y))
    plot.data_sources.append(text_source)
    glyph = Text(x="x", y="y", text="text", angle=0, text_align="center", text_baseline="middle")
    renderer = Glyph(data_source=text_source, xdata_range=xdr, ydata_range=ydr, glyph=glyph)
    plot.renderers.append(renderer)

def to_base64(png):
    return "data:image/png;base64," + base64.b64encode(png).decode("utf-8")

urls = [ to_base64(icons.get(browser, b"")) for browser in browsers ]
x, y = polar_to_cartesian(1.7, start_angles, end_angles)

icons_source = ColumnDataSource(dict(urls=urls, x=x, y=y))
plot.data_sources.append(icons_source)

glyph = ImageURL(url="urls", x="x", y="y", angle=0.0, anchor="center")
renderer = Glyph(data_source=icons_source, xdata_range=xdr, ydata_range=ydr, glyph=glyph)
plot.renderers.append(renderer)

text = [ "%.02f%%" % value for value in selected.Share ]
x, y = polar_to_cartesian(0.7, start_angles, end_angles)

text_source = ColumnDataSource(dict(text=text, x=x, y=y))
plot.data_sources.append(text_source)

glyph = Text(x="x", y="y", text="text", angle=0, text_align="center", text_baseline="middle")
renderer = Glyph(data_source=text_source, xdata_range=xdr, ydata_range=ydr, glyph=glyph)
plot.renderers.append(renderer)

doc = Document()
doc.add(plot)

if __name__ == "__main__":
    filename = "donut.html"
    with open(filename, "w") as f:
        f.write(file_html(doc, INLINE, "Donut Chart"))
    print("Wrote %s" % filename)
    view(filename)
