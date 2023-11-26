import logging
from base_utils import setup_logger, read_csv, write_csv

INPUT_FILE = "in/compta_7S.csv"
OUTPUT_FILE = "out/compta_7S_out.csv"
ENV = "local"
ALL_REFS = []


def compute_internal_ref(facture, number):
    if facture["1 - Ref interne"] != '':
        ALL_REFS.append(facture["1 - Ref interne"].strip())
        return facture["1 - Ref interne"]
    [jour, mois, annee] = facture["3 - Date"].split("/")
    type_code = facture["6 - Type de dépense"][:3].upper().replace("É", "E")
    ref = f"ELE_{annee}{mois}{jour}_{type_code}_0{number}"
    if ref in ALL_REFS:
        return compute_internal_ref(facture, number+1)
    ALL_REFS.append(ref)
    return ref


def add_internal_ref(facture):
    facture["1 - Ref interne"] = compute_internal_ref(facture, 1)
    return facture


def main():
    factures = [f for f in read_csv(INPUT_FILE) if f["7 - Montant HT"] != "0,00 €"]
    write_csv([add_internal_ref(f) for f in factures], OUTPUT_FILE, True)
    return True


if __name__ == "__main__":
    setup_logger(__file__, ENV, level=logging.INFO)
    main()
