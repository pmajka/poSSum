import math
import sys, os
import numpy as np

template = """
    <!DOCTYPE html>
    <html>
    <body>

    <svg height="256" width="256">
    <defs>
        <radialGradient id="grad1" cx="50%%" cy="50%%" r="50%%" fx="50%%" fy="50%%">
        <stop offset="0%%" style="stop-color:rgb(255,255,255);stop-opacity:0" />
        <stop offset="100%%" style="stop-color:rgb(0,0,0);stop-opacity:1" />
        </radialGradient>
    </defs>
    <ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="url(#grad1)" />
    Sorry, your browser does not support inline SVG.
    </svg>

    </body>
    </html>
"""

def get_image(i, cx, cy, rx, ry):
    fl = template % (cx, cy, rx, ry)
    open("%04d.svg" % i, "w").write(fl)
    os.system("convert %04d.svg -density 150 -alpha off -negate %04d.png" % (i,i))
    os.system("rm %04d.svg" % i)

cxx = np.sin(np.linspace(0,1,100)*2*np.pi) * 32 + 128
cyy = np.cos(np.linspace(0,1,100)*2*np.pi) * 32 + 128

rxx = np.arange(256) * 0 + 64
ryy = np.arange(256) * 0 + 64

for i in range(len(cxx)):
    print i
    get_image(i, cxx[i], cyy[i], rxx[i], ryy[i])
