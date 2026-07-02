from lasair import LasairError, lasair_client as lasair
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
DATA_DIR = BASE_DIR / "data" / "alerts"


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


def query_objects():

    selected = 'objects.diaObjectId, objects.ra, objects.decl, \
                round(-2.5*log10(objects.latest_psfFlux)+31.4, 2) as latestMag, \
                objects.firstDiaSourceMjdTai, \
                objects.lastDiaSourceMjdTai, objects.r_psfFlux, objects.r_latestMJD, objects.g_psfFlux, objects.i_psfFlux, objects.z_psfFlux, objects.u_psfFlux, \
                mjdnow(), sherlock_classifications.classification AS predicted_classification'  

    
    tables = 'objects,sherlock_classifications'
    
    conditions = 'objects.decl > -25 AND objects.latest_psfFlux > 0 AND mjdnow()-objects.lastDiaSourceMjdTai < 20 \
                 AND sherlock_classifications.classification in ("SN") AND objects.nDiaSources > 5 \
                 ORDER BY objects.lastDiaSourceMjdTai DESC'
    

    client = get_lasair_client()

    raw_results = client.query(selected, tables, conditions)

    processed = []

    for obj in raw_results:
        obj['firstDiaSourceMjdTai_iso'] = mjd_to_iso(obj['firstDiaSourceMjdTai'])
        obj['lastDiaSourceMjdTai_iso'] = mjd_to_iso(obj['lastDiaSourceMjdTai'])
        obj['mjdnow_iso'] = make_aware(mjd_to_iso(obj['mjdnow()']), timezone=ZoneInfo("UTC"))
        obj['lasair_url'] = LASAIR_OBJECT_URL.format(
            object_id=obj['diaObjectId']
        )

        processed.append(obj)

    return processed

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        return super().default(obj)


def fetch_lasair_alerts():

    processed_data = query_objects()
    alert_number = len(processed_data)
    print (f"Found {alert_number} alerts today")

    today = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = DATA_DIR / f"{today}_alerts.json"

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": datetime.utcnow().isoformat(),
        "alerts": processed_data
    }

    with open(filepath, 'w') as f:
        json.dump(output, f, cls=DateTimeEncoder, indent=2)

    print(f"Saved {filepath} successful on {today}")