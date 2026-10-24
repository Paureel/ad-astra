"""Rasterize an auditable Hipparcos V<6.5 reference sky, not a sky photograph.

The measured catalogue positions and relative V fluxes are retained. B-V is a
warm/cool display encoding; a Gaussian display PSF and a fixed exposure make
unresolved stars visible. This is not calibrated spectral photometry.
"""
from __future__ import annotations

import argparse
import base64
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
QUERY = "SELECT hip_number,ra_deg,dec_deg,vmag,bv_color FROM hipparcos WHERE vmag<6.5 ORDER BY hip_number"
URL = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync?" + urllib.parse.urlencode(
    dict(REQUEST="doQuery",LANG="ADQL",FORMAT="votable",MAXREC=12000,QUERY=QUERY))


def read_votable(raw):
    root = ET.fromstring(raw)
    if any(e.attrib.get("value") in ("ERROR","OVERFLOW") for e in root.iter() if e.tag.endswith("INFO")):
        raise ValueError("Catalogue query failed or was truncated.")
    if not any(e.tag.endswith("}BINARY") for e in root.iter()):
        raise ValueError("Expected the documented VOTable BINARY field encoding.")
    data = base64.b64decode(next(e.text for e in root.iter() if e.tag.endswith("}STREAM")))
    offset=0; rows=[]; excluded=[]
    while offset<len(data):
        hip=struct.unpack_from(">i",data,offset)[0];offset+=4
        coordinates=[]
        for _ in range(2):
            length=struct.unpack_from(">i",data,offset)[0];offset+=4
            word=data[offset:offset+length].decode();offset+=length
            coordinates.append(float(word) if word.strip() else None)
        mag,bv=struct.unpack_from(">dd",data,offset);offset+=16
        if any(x is None or not math.isfinite(x) for x in coordinates):
            excluded.append(hip);continue
        if not (0<=coordinates[0]<360 and -90<=coordinates[1]<=90 and math.isfinite(mag) and mag<6.5):
            raise ValueError("Unexpected catalogue coordinate/magnitude.")
        rows.append([hip,*coordinates,mag,bv if math.isfinite(bv) else None])
    return rows,excluded


def png(path, rgb):
    height,width,_=rgb.shape
    def chunk(name,data):
        return struct.pack(">I",len(data))+name+data+struct.pack(">I",zlib.crc32(name+data)&0xffffffff)
    scan=b"".join(b"\0"+row.tobytes() for row in rgb)
    path.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b""))


def raster(stars,width=4096,height=2048):
    image=np.zeros((height,width,3),dtype=np.float32)
    for _,ra,dec,mag,bv in stars:
        if mag >= 5.5:
            continue
        # u is longitude in atan2(y,x), v is asin(z). Top PNG row is north.
        x=(ra/360+.5)%1*width; y=(.5-dec/180)*height
        # Gaussian angular PSF: a display/instrument choice, not stellar radius.
        sy=.70; sx=sy/max(.04,math.cos(math.radians(dec)))
        ix=np.arange(math.floor(x-4*sx),math.ceil(x+4*sx)+1)
        iy=np.arange(max(0,math.floor(y-4*sy)),min(height,math.ceil(y+4*sy)+1))
        stamp=np.exp(-.5*((ix[None,:]-x)**2/sx**2+(iy[:,None]-y)**2/sy**2))/(2*math.pi*sx*sy)
        warm=np.clip(((bv if bv is not None else .65)+.3)/2.3,0,1)
        color=(1-warm)*np.array([.58,.74,1.])+warm*np.array([1.,.53,.27])
        color/=np.max(color)
        flux=10**(-.4*mag)
        image[iy[:,None],(ix%width)[None,:]] += (stamp[:,:,None]*color*flux*40).astype(np.float32)
    # Fixed global exposure and Reinhard tone mapping, then sRGB encoding.
    image=image/(1+image)
    rgb=np.where(image<=.0031308,12.92*image,1.055*np.maximum(image,0)**(1/2.4)-.055)
    return np.round(np.clip(rgb,0,1)*255).astype(np.uint8)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--votable",type=Path,help="Use a previously downloaded NASA VOTable.")
    inputs.add_argument("--catalogue",type=Path,help="Rebuild the raster offline from the committed catalogue.")
    args=parser.parse_args()
    if args.catalogue:
        previous=json.loads(args.catalogue.read_text())
        stars=previous["stars"];excluded=previous["excluded_missing_coordinates_HIP"]
        source_digest=previous["source_votable_sha256"]
    else:
        raw=args.votable.read_bytes() if args.votable else urllib.request.urlopen(URL,timeout=60).read()
        stars,excluded=read_votable(raw)
        source_digest=sha256(raw).hexdigest()
    payload={"source":"ESA Hipparcos Catalogue (1997), NASA HEASARC hipparcos mirror",
             "url":"https://heasarc.gsfc.nasa.gov/W3Browse/catalog/hipparcos.html","query":QUERY,
             "epoch":"J1991.25, ICRS (J2000 equator); no proper motion applied",
             "display":{"magnitude_limit":5.5,"exposure":40,"PSF_sigma_latitude_pixels":.7,"width":4096,"height":2048},
             "source_votable_sha256":source_digest,"excluded_missing_coordinates_HIP":excluded,
             "generator_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
             "columns":["HIP","RA_deg","Dec_deg","Vmag","B-V"],"stars":stars}
    png(ROOT/"web/stars.png",raster(stars))
    payload["png_sha256"]=sha256((ROOT/"web/stars.png").read_bytes()).hexdigest()
    (ROOT/"web/stars.json").write_text(json.dumps(payload,separators=(",",":"),allow_nan=False)+"\n")
    print(f"Rendered {sum(row[3]<5.5 for row in stars)} of {len(stars)} catalogue stars; {len(excluded)} entries lack coordinates; 4096×2048 sRGB PNG.")


if __name__=="__main__":main()
