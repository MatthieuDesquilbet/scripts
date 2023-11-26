import logging
from pprint import pprint
from base_utils import setup_logger, read_csv, print_tabulate

ENV = "local"
F_DISPOS = "in/adele_dispos.csv"
F_SCENES = "in/adele_scenes.csv"
F_DISTRIBUTION = "in/adele_distribution.csv"
CURRENT_DISTRIB = "3"


def prettify_results(res):
    for k, v in res.items():
        logging.info("------------{}--------------".format(k))
        for i in v:
            logging.info(i)


def reverse_data(json_arr, key_field):
    json_obj = {i: [] for i in json_arr[0].keys() if i != key_field}
    for i in json_arr:
        for k, v in i.items():
            if k == key_field:
                continue
            json_obj[k].append((i[key_field], v))
    return json_obj


def main():
    all_dispos = read_csv(F_DISPOS)
    scenes_raw = read_csv(F_SCENES)
    scenes = [
        (i, scenes_raw[i]["role"].split("|"), scenes_raw[i]["name"])
        for i in range(len(scenes_raw))
    ]
    distrib = read_csv(F_DISTRIBUTION)
    current_distrib = {
        i[0]: i[1] for i in reverse_data(distrib, "role")[CURRENT_DISTRIB]
    }
    logging.info(current_distrib)
    results = {}
    for date, dispos in reverse_data(all_dispos, "nom").items():
        presents = [n[0] for n in dispos if n[1] == "1"]
        results[date] = []
        for s_number, s_roles, s_name in scenes:
            if (
                len(
                    set([current_distrib[r] for r in s_roles if r != "choeur"])
                    - set(presents)
                )
                == 0
            ) and s_number not in [0, 29]:
                results[date].append("{} - {} ".format(s_number, s_name))
    results["not possible"] = []
    for s_number, s_roles, s_name in scenes:
        ok = False
        for d, v in results.items():
            if "{} - {} ".format(s_number, s_name) in v:
                ok = True
        if not ok:
            results["not possible"].append("{} - {} ".format(s_number, s_name))
    prettify_results(results)


if __name__ == "__main__":
    setup_logger(__file__, ENV, level=logging.INFO)
    main()
