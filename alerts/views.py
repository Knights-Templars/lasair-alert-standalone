from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
from pathlib import Path
import json
import numpy as np
from datetime import datetime
from .lightcurve_query import get_light_curve
from .gpfit import fit_gp

# Bokeh #

from bokeh.plotting import figure
from bokeh.embed import components


OBJECTS_PER_PAGE = 50
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "alerts"

def alert_list(request):

    error_message = None
    object_list = []

    files = list(DATA_DIR.glob("*_alerts.json"))
    
    try:
        # pick the file with the latest modification time
        latest_file = max(files, key=lambda f: f.stat().st_mtime)

        print(f"Using latest file: {latest_file}")
               
        with open(latest_file) as f:
            data = json.load(f)

        object_list = data.get("alerts", [])
        updated = datetime.fromisoformat(data["updated"])
    
    except ValueError as exc:
        error_message = f'Configuration error: {exc}'


    total_count = len(object_list)

    paginator = Paginator(object_list, OBJECTS_PER_PAGE)

    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)

    except PageNotAnInteger:
        page_obj = paginator.page(1)

    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    
    context = {
        'page_obj': page_obj,
        'error_message': error_message,
        'total_count': total_count,   
        'updated': updated
        }

    return render(request, 'alerts/alerts_list.html', context)



def build_band_data(obj, selected_bands):

    band_data = {}

    for band in selected_bands:

        rows = []

        for s in obj.get('diaSourcesList', []):
            if s.get('band') == band and s['psfFlux'] > 0:
                mjd = s['midpointMjdTai']
                flux = s['psfFlux']
                fluxerror = s['psfFluxErr']
                mag = -2.5 * np.log10(s["psfFlux"]) + 31.4
                mag_error = 1.0857 * (s['psfFluxErr'] / s['psfFlux'])

                rows.append((mjd, mag, mag_error))

        if len(rows) == 0:
            continue
        
        rows.sort(key=lambda x: x[0])

        mjd_sorted, mag_sorted, mag_error_sorted = map(list, zip(*rows))

        band_data[band] = (mjd_sorted, mag_sorted, mag_error_sorted)
        
    return band_data



def raw_plot(band_data, selected_bands, diaobjectid):

    p = figure(
        title = f"Lasair Light Curve for {diaobjectid}",
        x_axis_label = "MJD",
        y_axis_label = "MAGNITUDE",
        width = 800,
        height = 400,
        tools='pan,wheel_zoom,box_zoom,reset,save',
    )


    colors = {'u': '#0077b6',
              'g': '#90be6d',
              'r': '#d62828',
              'i': '#6f1d1b',
              'z': '#cdb4db'}
    

    for band in selected_bands:

        if band in band_data.keys():
            mjd, mag, error = band_data[band]        
            # TODO: Plot with error bars
            p.scatter(mjd, mag, size=7, color=colors.get(band, "white"), legend_label=band)

    p.legend.location = "top_left"
    p.background_fill_color = "#edede9"
    p.border_fill_color = "#05070f"

    p.xaxis.major_label_text_color = "white"
    p.yaxis.major_label_text_color = "white"
    p.xaxis.axis_label_text_color = "white"
    p.yaxis.axis_label_text_color = "white"
    p.y_range.flipped = True

    p.title.text_color = "white"


    return p


def gp_plot(band_data, selected_bands, diaobjectid):

    colors = {'u': '#0077b6',
              'g': '#90be6d',
              'r': '#d62828',
              'i': '#6f1d1b',
              'z': '#cdb4db'}

    p = figure(
        title = f"Lasair Light Curve for {diaobjectid}",
        x_axis_label = "MJD",
        y_axis_label = "MAGNITUDE",
        width = 800,
        height = 400,
        tools='pan,wheel_zoom,box_zoom,reset,save',
    )

    for band in selected_bands:
        mjd, mag, error = band_data[band]
        if len(mjd) > 3:
            x_gp, y_gp, sigma = fit_gp(mjd, mag, error)
            p.line(x_gp, y_gp, color=colors.get(band, "white"))

            p.varea(x=x_gp,
                    y1=y_gp-sigma,
                    y2=y_gp+sigma,
                    alpha=0.4,
                    color=colors.get(band, "white"))
    p.y_range.flipped = True
            
    return p



def object_view(request, object_id):

    

    all_bands = ["u", "g", "r", "i", "z", "y", "a"]


    obj = get_light_curve(object_id)
    print("OBJECT ID:", object_id)
    diaobjectid = obj['diaObjectId']
    
    object_info = {
        'ra': obj['diaObject']['ra'],
        'decl': obj['diaObject']['decl'],
        'tns_name': obj['lasairData']['tns_name'],
        'type': obj['lasairData']['TNS']['type'],
        'z': obj['lasairData']['TNS']['z'],
        'disc_mag': obj['lasairData']['TNS']['disc_mag'],
        'disc_date': obj['lasairData']['TNS']['disc_date'],
        'ObjectID': obj['diaObjectId'],
    }

    band_data = build_band_data(obj, all_bands)

    plot_raw = raw_plot(band_data, all_bands, diaobjectid)

    raw_script, raw_div = components(plot_raw)

    gp_script, gp_div = None, None
    selected_bands = request.GET.getlist("band")
    use_gp = request.GET.get("gp", "1") == "1"
    clear = request.GET.get("clear") == "1"

    if clear:
        use_gp=False

    if not request.GET:
        selected_bands = ['r']
        use_gp=False

    if use_gp:
        band_data = build_band_data(obj, selected_bands)
        plot_gp = gp_plot(band_data, selected_bands, diaobjectid)
        gp_script, gp_div = components(plot_gp)

    

    return render(request,
                  "alerts/lightcurve.html",
                  {    
                      "obj": object_info,
                      "object_id" : diaobjectid,
                      "raw_script": raw_script,
                      "raw_div": raw_div,
                      "gp_script": gp_script,
                      "gp_div": gp_div,
                      "selected_bands": selected_bands,
                  })