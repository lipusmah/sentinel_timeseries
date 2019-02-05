import os
import re
from sentinelhub import WmsRequest, BBox, CRS, MimeType, CustomUrlParam, get_area_dates
from s2cloudless import S2PixelCloudDetector, CloudMaskRequest
from pyproj import Proj, transform
import numpy as np
from slite_api import *
from graphs import *
from PIL import Image, ImageDraw
from geomet import wkt
import time

working_dir = os.path.dirname(os.path.abspath(__file__))
api_key = "6b3365db-b23d-487f-8916-b035229bb13b"


def get_all_bands(bbox, layer):

    minx, miny = bbox[0][0] #bbox[0:2]
    maxx, maxy = bbox[0][2] #bbox[4:6]

    right, bot = transform(Proj(init='epsg:3912'), Proj(init='epsg:4326'), maxx, miny)
    left, top = transform(Proj(init='epsg:3912'), Proj(init='epsg:4326'), minx, maxy)

    bounding_box = BBox([top, left, bot, right], crs=CRS.WGS84)


    #lat, lon = top-bot, right-left
    height, width = round(maxy-miny), round(maxx-minx)

    bands_script = "return [B01,B02,B03,B04,B05,B08,B8A,B09,B10,B11,B12]"
    wms_bands_request = WmsRequest(layer=layer,
                                   custom_url_params={
                                       CustomUrlParam.EVALSCRIPT: bands_script,
                                       CustomUrlParam.ATMFILTER: 'NONE'
                                   },
                                   bbox=bounding_box,
                                   time=('2017-01-01', '2018-12-01'),
                                   width=width, height=height,
                                   image_format=MimeType.TIFF_d32f,
                                   instance_id=api_key)


    # if wms_bands_request.is_valid_request():
    #     wms_bands = wms_bands_request.get_data()
    # else:
    #     raise Exception("Ne dela prav")

    all_cloud_masks = CloudMaskRequest(ogc_request=wms_bands_request, threshold=0.1)

    masks = []
    wms_bands = []
    for idx, [prob, mask, data] in enumerate(all_cloud_masks):
        masks.append(mask)
        wms_bands.append(data)

    return wms_bands, masks, wms_bands_request.get_dates()

def extract_ndvi(timef_bands):
    """
    timef_bands  = numpy array [w, h, 10]
    bands_script = "return [B01,B02,B03,B04,B05,B08,B8A,B09,B10,B11,B12]"
    """
    b08 = timef_bands[:, :, 5]
    b04 = timef_bands[:, :, 3]

    return (b08-b04)/(b08+b04)


def toRaster(polygon, bbox):
    left, top = bbox[0][-2]
    right, bot = bbox[0][1]

    whole_poly = []
    for part in polygon[0]:
        whole_poly.append([ (round(y-left), abs(round(x-top)) ) for y, x in part])

    width = round(right-left)
    height = round(top-bot)


    img = Image.new("L", [width, height], 0)
    for part in whole_poly:
        ImageDraw.Draw(img).polygon(part, outline=1, fill=1)

    mask = np.array(img)
    return mask

def get_sentinel_data_procedure(conn, poly_id, layer, logger):

    t0 = time.time()
    polygon, bbox = api_poly_bbox(conn, poly_id)

    t1 = time.time()
    all_bands_12, all_cloud_masks, dates = get_all_bands(bbox, layer)
    t2 = time.time()

    ndvi_r = [extract_ndvi(epoch) for epoch in all_bands_12]
    poly_mask = toRaster(polygon, bbox)
    t3 = time.time()
    logger.log(f"GET sentinel data: {round(t2-t1, 2)} s, obdelava: {round( (t1-t0)+(t3-t2), 2)} s")
    print(f"GET sentinel data: {round(t2-t1, 2)} s, obdelava: {round( (t1-t0)+(t3-t2), 2)} s")
    return all_cloud_masks, ndvi_r, poly_mask, dates

if __name__ == "__main__":

    #testing
    conn = sqliteConnector(r".\\dbs\raba_2018.sqlite")
    poly_id = 123
    layer = "ALL-BANDS"

    all_clouds_masks, ndvis, poly_mask, dates = get_sentinel_data_procedure(conn, poly_id, layer)

    print()