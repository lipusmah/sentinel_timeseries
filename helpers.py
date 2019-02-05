from datetime import datetime, timedelta
import re
import os

####

class logger:
    def __init__(self, path = ".\\log.txt"):
        from pathlib import Path
        self.path = path

        if Path(path).is_file():
            pass
        else:
            with open(path, "w") as log_file:
                log_file.write(f"{str(datetime.now()).split('.')[0]}: Logger inited\n")

    def log(self, msg):
        with open(self.path, "a") as fajl:
            fajl.write(f"{str(datetime.now()).split('.')[0]}: {msg}\n")



####
def wkt_poly(poly_list):
    """
    poly_list: list of tuples representing points
                -> [(x1, y1), (x2, y2), ..., (x1, y1)]

    Supports only single simple polygon feature (no nested lists)
    """
    try:
        geom = ",".join([f"{round(x,2)} {round(y,2)}" for x, y in poly_list])
    except:
        Exception("not the right input format")

    return f"POLYGON(({geom}))"

def wkt2pythonlist(wkt_poly):
     nums = re.findall(r'\d+(?:\.\d*)?', wkt_poly.rpartition(',')[0])
     return [float(i) for i in nums]

def daterange_days(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def daterange_months(start_date, end_date):
    for n in range(int((end_date - start_date).months) + 1):
        yield start_date + timedelta(n)

def wkt2pythonlist(wkt):
    points = []
    inner = re.findall(r'-?(?:\.\d+|\d+(?:\.\d*)?)', wkt)
    pointed = inner.split(",")
    for p in pointed:
        x, y = p.strip().split(" ")
        points.append((round(float(x), 4), round(float(y), 4)))
    return points

def time_range_to_xaxis(dates):
    min_time = datetime.strptime(dates[0].split()[0], "%Y-%m-%d")
    max_time = datetime.strptime(dates[-1].split()[0], "%Y-%m-%d")
    x = []

    ranged = list(daterange_days(min_time, max_time))

    i = 0
    for day in ranged:
        d = str(day).split()[0]

        try:
            ind = dates.index(d)
            j = 0
            while d == dates[ind + j]:
                x.append(i + j)
                j += 1

            i += j
        except:
            i += 1
            continue

    return x

def avg_num_epoch(conn):
    pass
