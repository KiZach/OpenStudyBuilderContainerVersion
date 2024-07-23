import csv
import json

from .functions.parsers import map_boolean
from .functions.utils import load_env
from .utils.api_bindings import (
    CODELIST_COMPOUND_DISPENSED_IN,
    CODELIST_DELIVERY_DEVICE,
    CODELIST_DOSAGE_FORM,
    CODELIST_NAME_MAP,
    CODELIST_ROUTE_OF_ADMINISTRATION,
    CODELIST_SDTM_DOMAIN_ABBREVIATION,
    UNIT_SUBSET_AGE,
    UNIT_SUBSET_DOSE,
    UNIT_SUBSET_STRENGTH,
)
from .utils.importer import BaseImporter, open_file
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_COMPOUNDS = load_env("MDR_MIGRATION_COMPOUNDS")

compounds = lambda row, headers, dose_values, strength_values, half_life_value, delivery_devices, dispensers, lag_times, admin_routes, dosage_forms: {
    "path": "/concepts/compounds",
    "uid": "<uid>",
    "body": {
        "nnc_short_number": row[headers.index("NNC_SHORT")]
        if row[headers.index("NNC_SHORT")] != ""
        else None,
        "nnc_long_number": row[headers.index("NNC_LONG")]
        if row[headers.index("NNC_LONG")] != ""
        else None,
        "change_description": "Creating Compound",
        "name": f"{row[headers.index('NAME')]}",
        "name_sentence_case": f"{row[headers.index('NAME')]}".lower(),
        "definition": None,
        "dose_values_uids": [val["uid"] for val in dose_values],
        "strength_values_uids": [val["uid"] for val in strength_values],
        "lag_times_uids": [val["uid"] for val in lag_times],
        "half_life_uid": half_life_value,
        "delivery_devices_uids": [val["term_uid"] for val in delivery_devices],
        "dispensers_uids": [val["term_uid"] for val in dispensers],
        "library_name": "Sponsor",
        "is_sponsor_compound": True,
        "is_name_inn": True,
        "analyte_number": row[headers.index("ANALYTE")]
        if row[headers.index("ANALYTE")] != ""
        else None,
        "route_of_administration_uids": [val["term_uid"] for val in admin_routes],
        "dosage_form_uids": [val["term_uid"] for val in dosage_forms],
    },
}

compound_alias = lambda uid, compound_data: {
    "path": "/concepts/compound-aliases",
    "uid": "<uid>",
    "body": {
        "name": compound_data["name"],
        "name_sentence_case": compound_data["name_sentence_case"],
        "definition": compound_data["definition"],
        "library_name": compound_data["library_name"],
        "compound_uid": uid,
        "is_preferred_synonym": True,
    },
}

# Not used yet:
# "projects_uids": [],
# "brands_uids": [],
# "dose_frequency_uids": [],

numeric_value = lambda value, unit_uid: {
    "path": "/concepts/numeric-values-with-unit",
    "uid": "<uid>",
    "body": {
        "library_name": "Sponsor",
        "template_parameter": False,
        "value": value,
        "unit_definition_uid": unit_uid,
    },
}

lag_time = lambda value, unit_uid, sdtm_domain_uid: {
    "path": "/concepts/lag-times",
    "uid": "<uid>",
    "body": {
        "library_name": "Sponsor",
        "template_parameter": False,
        "value": value,
        "unit_definition_uid": unit_uid,
        "sdtm_domain_uid": sdtm_domain_uid,
    },
}


class Compounds(BaseImporter):
    logging_name = "compounds"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.dose_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_DOSE}"
            ),
            identifier="name",
            value="uid",
        )
        self.age_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_AGE}"
            ),
            identifier="name",
            value="uid",
        )
        self.strength_units = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/concepts/unit-definitions?subset={UNIT_SUBSET_STRENGTH}"
            ),
            identifier="name",
            value="uid",
        )
        self.sdtm_domains = self.api.get_all_from_api(
            f"/ct/terms?codelist_name={CODELIST_SDTM_DOMAIN_ABBREVIATION}"
        )

    def add_numeric_values(self, values, units, available_units):
        added_values = []
        for val, unit in zip(values, units):
            if unit not in available_units:
                unit = unit.upper()
                if unit not in available_units:
                    unit = unit.lower()
                    if unit not in available_units:
                        self.log.warning(
                            f"Unit '{unit}' not found, skipping value {val}"
                        )
                        continue
            self.log.info(f"Adding numeric value {val} with unit '{unit}'")
            val = self.api.post_to_api(numeric_value(val, available_units[unit]))
            added_values.append(val)
        return added_values

    def add_lag_times(self, values, units, sdtm_domains):
        added_values = []
        for val, unit, domain in zip(values, units, sdtm_domains):
            if unit not in self.age_units:
                self.log.warning(f"Unit '{unit}' not found, skipping value {val}")
                continue
            if domain not in [x["term_uid"] for x in self.sdtm_domains]:
                self.log.warning(
                    f"SDTM domain '{domain}' not found, skipping lag time '{val} {unit}'"
                )
                continue
            self.log.info(f"Adding lag time '{val} {unit}' for SDTM domain '{domain}'")
            val = self.api.post_to_api(lag_time(val, self.age_units[unit], domain))
            added_values.append(val)
        return added_values

    @open_file()
    def handle_compounds(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)

        # TODO this is a dummy value, get this from the data instead
        lag_times = self.add_lag_times([7], ["days"], ["C49562_AE"])

        unii_codelists = self.api.get_all_from_api(
            "/dictionaries/codelists", params={"library": "UNII"}
        )

        all_unii_terms = {}
        for unii_codelist in unii_codelists:
            all_unii_terms.update(
                self.api.get_all_identifiers(
                    self.api.get_all_from_api(
                        "/dictionaries/terms",
                        params={"codelist_uid": unii_codelist["codelist_uid"]},
                    ),
                    "dictionary_id",
                    "term_uid",
                )
            )

        for row in readCSV:
            if len(row) == 0:
                continue
            self.log.info(f'Process compound {row[headers.index("NAME")]}')
            hl_val = row[headers.index("HALF_LIFE")]
            hl_unit = row[headers.index("HALF_LIFE_U")]
            half_life_value = None
            if hl_val != "" and hl_unit != "":
                half_life_resp = self.add_numeric_values(
                    [float(hl_val)], [hl_unit], self.age_units
                )
                if len(half_life_resp) > 0:
                    half_life_value = half_life_resp[0].get("uid", None)

            dose_val = row[headers.index("DOSE")]
            dose_unit = row[headers.index("DOSE_U")]
            dose_values = []
            if dose_val != "" and dose_unit != "":
                vals = []
                units = []
                for val, unit in zip(dose_val.split("|"), dose_unit.split("|")):
                    vals.append(float(val))
                    units.append(unit)
                dose_values = self.add_numeric_values(vals, units, self.dose_units)
            strength_val = row[headers.index("STRENGTH")]
            strength_unit = row[headers.index("STRENGTH_U")]
            strength_values = []
            if strength_val != "" and strength_unit != "":
                vals = []
                units = []
                for val, unit in zip(strength_val.split("|"), strength_unit.split("|")):
                    vals.append(float(val))
                    units.append(unit)
                strength_values = self.add_numeric_values(
                    vals, units, self.strength_units
                )
            devices = row[headers.index("DELIVERY_DEVICE")]
            delivery_devices = []
            if devices != "":
                devs = devices.split("|")
                filt = {"name.sponsor_preferred_name": {"v": devs, "op": "eq"}}
                delivery_devices = self.api.get_all_from_api(
                    f"/ct/terms?codelist_name={CODELIST_DELIVERY_DEVICE}&filters={json.dumps(filt)}"
                )
            dispensers = row[headers.index("DISPENSED_IN")]
            dispensed_in = []
            if dispensers != "":
                disps = dispensers.split("|")
                disps = [d.title() for d in disps]
                filt = {"name.sponsor_preferred_name": {"v": disps, "op": "eq"}}
                dispensed_in = self.api.get_all_from_api(
                    f"/ct/terms?codelist_name={CODELIST_COMPOUND_DISPENSED_IN}&filters={json.dumps(filt)}"
                )
            routes = row[headers.index("ROUTE_OF_ADMINISTRATION")]
            admin_routes = []
            if routes != "":
                rts = routes.split("|")
                filt = {"attributes.code_submission_value": {"v": rts, "op": "eq"}}
                admin_routes = self.api.get_all_from_api(
                    f"/ct/terms?codelist_uid={CODELIST_NAME_MAP[CODELIST_ROUTE_OF_ADMINISTRATION]}&filters={json.dumps(filt)}"
                )
            dosage = row[headers.index("DOSAGE_FORM")]
            dosage_forms = []
            if dosage != "":
                df = dosage.split("|")
                filt = {"attributes.code_submission_value": {"v": df, "op": "eq"}}
                dosage_forms = self.api.get_all_from_api(
                    f"/ct/terms?codelist_uid={CODELIST_NAME_MAP[CODELIST_DOSAGE_FORM]}&filters={json.dumps(filt)}"
                )

            data = compounds(
                row,
                headers,
                dose_values,
                strength_values,
                half_life_value,
                delivery_devices,
                dispensed_in,
                lag_times,
                admin_routes,
                dosage_forms,
            )
            if row[headers.index("unii_substance_cd")] != "":
                unii_terms = row[headers.index("unii_substance_cd")]
                term_uids = []
                for unii_term in unii_terms.split("|"):
                    term = all_unii_terms.get(unii_term)
                    if term:
                        term_uids.append(term)
                    data["body"]["substance_terms_uids"] = term_uids
            if row[headers.index("SPONSOR_YN")] != "":
                try:
                    data["body"]["is_sponsor_compound"] = map_boolean(
                        row[headers.index("SPONSOR_YN")], raise_exception=True
                    )
                except ValueError:
                    pass
            if row[headers.index("INN_YN")] != "":
                try:
                    data["body"]["is_name_inn"] = map_boolean(
                        row[headers.index("INN_YN")], raise_exception=True
                    )
                except ValueError:
                    pass
            # print("--- compound to post")
            # print(json.dumps(data, indent=2))
            # Create Compound
            res = self.api.post_to_api(data)
            if res is not None:
                # Approve
                res_approve = self.api.approve_item(
                    uid=res["uid"], url="/concepts/compounds/"
                )
                if res_approve:
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.metrics.icrement(data["path"] + "--ApproveError")

                # Create a default alias
                self.log.info(f'Create alias for compound {row[headers.index("NAME")]}')
                alias = compound_alias(res["uid"], data["body"])
                alias_res = self.api.post_to_api(alias)
                if alias_res is not None:
                    # Approve
                    res_approve = self.api.approve_item(
                        uid=alias_res["uid"], url="/concepts/compound-aliases"
                    )
                    if res_approve:
                        self.metrics.icrement(alias["path"] + "--Approve")
                    else:
                        self.metrics.icrement(alias["path"] + "--ApproveError")

    def run(self):
        self.log.info("Importing compounds")
        self.handle_compounds(MDR_MIGRATION_COMPOUNDS)
        self.log.info("Done importing compounds")


def main():
    metr = Metrics()
    migrator = Compounds(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
