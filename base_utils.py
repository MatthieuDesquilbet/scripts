import csv
import sys
import os
import re
import json
import base64
import logging
import uuid
import hashlib
import subprocess
from uuid import UUID
from ipaddress import ip_address, IPv4Address, IPv6Address
from datetime import datetime, timedelta
from tabulate import tabulate

from bson import ObjectId

__all__ = (
    "cleanhtml",
    "make_dir",
    "write_csv",
    "read_csv",
    "write_json",
    "read_json",
    "read_json_line_separated",
    "write_file",
    "validate_uuid4",
    "remove_accents",
    "setup_logger",
    "make_uuid",
    "print_tabulate",
    "ask_confirmation",
    "utc_now_to_str",
)


def cleanhtml(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext.strip()


def make_dir(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def utc_now_to_str():
    return datetime.utcnow().isoformat().split(".")[0] + "Z"


def print_tabulate(items: list, fields_to_hide: set):
    if fields_to_hide is None:
        fields_to_hide = set()
    headers = sorted(list(set(items[0].keys()) - fields_to_hide))
    print(tabulate([[e[a] for a in headers] for e in items], headers=headers))


def make_uuid(text):
    payload = hashlib.sha1(text.encode()).digest()
    return str(uuid.UUID(bytes=payload[:16]))


def setup_logger(scriptname: str, env: str = "noenv", level=logging.INFO):
    scriptname = scriptname.split("/").pop()
    logfile = os.path.join(
        "/home/matt/workspace/scripts/logs/",
        "{}_{}.log".format(scriptname.replace(".py", ""), env),
    )
    subprocess.run(["touch", logfile])
    logging.basicConfig(
        level=level,
        handlers=[
            logging.FileHandler(logfile, "a", "UTF-8"),
            logging.StreamHandler(sys.stdout),
        ],
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )
    for mod in ("elasticsearch", "urllib3", "requests"):
        logging.getLogger(mod).setLevel(logging.CRITICAL)
    logging.info("----------- NEW RUN -----------")


def write_csv(data, filename="out.csv", sort_headers=False):
    if isinstance(data[0], dict):
        s = set()
        for row in data:
            s |= row.keys()
        fieldnames = list(s)
        if sort_headers:
            fieldnames = sorted(fieldnames)
        with open(filename, "w", encoding="UTF-8") as f:
            w = csv.DictWriter(f, fieldnames)
            w.writeheader()
            w.writerows(data)
    elif isinstance(data, list):
        with open(filename, "w", encoding="UTF-8") as f:
            w = csv.writer(f)
            w.writerows(data)
    else:
        raise TypeError("data must be one of dict or list")


def read_csv(filename):
    with open(filename, "r", encoding="UTF-8") as f:
        return [r for r in csv.DictReader(f)]


def write_json(data, filename="out.json"):
    with open(filename, "w", encoding="UTF-8") as f:
        print(
            json.dumps(data, default=_json_dump, indent=2, ensure_ascii=False), file=f
        )


def read_json(filename):
    with open(filename, "r", encoding="UTF-8") as f:
        return json.load(f, object_hook=_json_load)


def read_json_line_separated(filename):
    with open(filename, "r", encoding="UTF-8") as f:
        return [json.loads(l[:-1], object_hook=_json_load) for l in f.readlines()]


def write_file(string_or_array, filename="out.txt"):
    with open(filename, "w", encoding="UTF-8") as f:
        if isinstance(string_or_array, str):
            f.write(string_or_array)
        elif isinstance(string_or_array, list):
            f.writelines(string_or_array)
        else:
            raise ValueError()


def validate_uuid4(id_to_test):
    try:
        val = UUID(id_to_test, version=4)
    except ValueError:
        return False
    except Exception:
        return False
    id_to_test = re.sub(r"-", "", id_to_test)
    return id_to_test == val.hex


def remove_accents(s):
    char_sub = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "à": "a",
        "ä": "a",
        "å": "a",
        "ç": "c",
    }

    return "".join([char_sub.get(i, i) for i in s])


def ask_confirmation(msg: str):
    confirmation = input(msg)

    if confirmation != "y":
        logging.warning("Aborting.")
        exit(1)


def force_date_to_iso_format(doc, date_field):
    if date_field in doc and (
        type(doc[date_field]) is int or type(doc[date_field]) is int
    ):
        doc[date_field] = (
            datetime.fromtimestamp(float(doc[date_field]) / 1000.0)
            .isoformat()
            .split(".")[0]
            + "Z"
        )


def get_parent_path(filename=None):
    if filename:
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)), os.pardir, filename
        )
    else:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)


def redate(str_uuid: str, date: datetime):
    time = int((date - datetime(1582, 10, 15)).total_seconds() * 10000000)
    time_low = time & 0xFFFFFFFF
    time_mid = (time >> 32) & 0xFFFF
    time_high = ((time >> 48) & 0x0FFF) | 0x1000
    current_fields = uuid.UUID(str_uuid).fields
    new_id = uuid.UUID(
        fields=(
            time_low,
            time_mid,
            time_high,
            current_fields[3],
            current_fields[4],
            current_fields[5],
        )
    )
    return str(new_id)


def scramble(str_uuid: str):
    start = datetime(2017, 1, 1, tzinfo=None)
    stop = datetime(2017, 8, 1, tzinfo=None)
    delta = int((stop.timestamp() - start.timestamp()) * 1000000)
    new_date = datetime.utcfromtimestamp(
        start.timestamp() + (int(uuid.UUID(str_uuid)) % delta) / 1000000
    )
    return redate(str_uuid, new_date)


def get_uuid_date(str_uuid):
    return datetime(1582, 10, 15) + timedelta(
        microseconds=uuid.UUID(str_uuid).time // 10
    )


# Private


def _json_load(dic):
    if not isinstance(dic, dict) or not dic:
        return dic
    key = list(dic.keys())[0]
    value = dic[key]
    if key == "$ip":
        return ip_address(value)
    elif key == "$byte":
        return base64.b64decode(value)
    elif key == "$date":
        return datetime.fromtimestamp(float(value))
    elif key == "$uuid":
        return UUID(value)
    elif key == "$oid":
        return ObjectId(value)
    return dic


def _json_dump(obj):
    if isinstance(obj, (IPv4Address, IPv6Address)):
        return {"$ip": int(obj)}
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, bytes):
        return {"$byte": base64.b64encode(obj).decode()}
    elif isinstance(obj, datetime):
        return {"$date": obj.timestamp()}
    elif isinstance(obj, UUID):
        return {"$uuid": str(obj)}
    elif isinstance(obj, ObjectId):
        return {"$oid": str(obj)}
    elif isinstance(obj, frozenset):
        return list(obj)
    return obj


if __name__ == "__main__":
    setup_logger(__file__)
    logging.info("Module set up.")
