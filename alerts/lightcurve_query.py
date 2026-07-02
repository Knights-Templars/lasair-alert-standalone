from lasair import lasair_client as lasair

import os
from astropy.time import Time
from django.utils.timezone import make_aware
from zoneinfo import ZoneInfo
from datetime import datetime
from pathlib import Path
import json


API_TOKEN = os.getenv('LASAIR_LSST_TOKEN')
ENDPOINT = "https://api.lasair.lsst.ac.uk/api"


LASAIR_OBJECT_URL = "https://lasair.lsst.ac.uk/object/{object_id}"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "lightcurves"


def get_lasair_client():

    if not API_TOKEN:
        raise ValueError(
            "LASAIR_LSST_TOKEN NOT SET."
        )
    
    return lasair(API_TOKEN, endpoint=ENDPOINT)


def mjd_to_iso(mjd):

    try:
        return Time(mjd, format='mjd').datetime
    except Exception:
        return 'N/A'
    


def fetch_light_curve(object_id):


    client = get_lasair_client()

    lsst_object = client.object(object_id, lasair_added=True, lite=False)


    return lsst_object


def get_light_curve(object_id):

    
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    filepath = DATA_DIR / f"{object_id}.json"

    if filepath.exists():
        print(f"⚡ Using cached light curve for {object_id}")

        with open(filepath) as f:

            return json.load(f)
        

    print (f"Not in Cache, Downloading data for {object_id} from Lasair:")

    lc_data = fetch_light_curve(object_id)

    with open(filepath, "w") as f:
        json.dump(lc_data, f, indent=4)

    return lc_data