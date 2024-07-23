import asyncio
import csv
import time

import aiohttp

from .functions.parsers import find_term_by_concept_id, find_term_by_name, map_boolean
from .functions.utils import load_env
from .run_import_standardcodelistterms2 import StandardCodelistTerms2
from .utils.importer import BaseImporter, open_file, open_file_async
from .utils.metrics import Metrics
from .utils.path_join import path_join

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_SPONSOR_EPOCH = load_env("MDR_MIGRATION_SPONSOR_EPOCH")
MDR_MIGRATION_EPOCH = load_env("MDR_MIGRATION_EPOCH")
MDR_MIGRATION_EPOCH_SUB_TYPE = load_env("MDR_MIGRATION_EPOCH_SUB_TYPE")
MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS = load_env(
    "MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS"
)
MDR_MIGRATION_ENDPOINT_LEVEL = load_env("MDR_MIGRATION_ENDPOINT_LEVEL")
MDR_MIGRATION_OBJECTIVE_LEVEL = load_env("MDR_MIGRATION_OBJECTIVE_LEVEL")
MDR_MIGRATION_OPERATOR = load_env("MDR_MIGRATION_OPERATOR")
MDR_MIGRATION_EPOCH_TYPE = load_env("MDR_MIGRATION_EPOCH_TYPE")
MDR_MIGRATION_CODELIST_PARAMETER_SET = load_env("MDR_MIGRATION_CODELIST_PARAMETER_SET")


epoch_sub_type = lambda row, headers: {
    "path": "/ct/terms",
    "codelist": "GEN_EPOCH_SUB_TYPE",
    "body": {
        "catalogue_name": "SDTM CT",
        "code_submission_value": row[headers.index("GEN_EPOCH_SUB_TYPE_CD")],
        "name_submission_value": row[headers.index("GEN_EPOCH_SUB_TYPE_CD")],
        "nci_preferred_name": "UNK",
        "definition": "",
        "sponsor_preferred_name": row[headers.index("GEN_EPOCH_SUB_TYPE")],
        "sponsor_preferred_name_sentence_case": row[
            headers.index("GEN_EPOCH_SUB_TYPE")
        ].lower(),
        "order": row[headers.index("CD_VAL_SORT_SEQ")],
        "library_name": "Sponsor",
    },
}

epoch = {
    "EPOCH": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": "Epoch",
        "body": {
            "catalogue_name": "SDTM CT",
            "code_submission_value": row[headers.index("GEN_EPOCH_CD")],
            "name_submission_value": row[headers.index("GEN_EPOCH_CD")],
            "nci_preferred_name": "UNK",
            "definition": "",
            "sponsor_preferred_name": row[headers.index("GEN_EPOCH_LB")],
            "sponsor_preferred_name_sentence_case": row[
                headers.index("GEN_EPOCH_LB")
            ].lower(),
            "order": row[headers.index("CD_VAL_SORT_SEQ")],
            "library_name": "Sponsor",
        },
    }
}

endpoint_level = {
    "MDR_MIGRATION_ENDPOINT_LEVEL": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CD_LIST_ID")],
        "uid": row[headers.index("CT_CD")],
        "body": {
            "order": row[headers.index("CD_VAL_SORT_SEG")],
            "sponsor_preferred_name": row[headers.index("CD_VAL_LB")],
            "sponsor_preferred_name_sentence_case": row[headers.index("CD_VAL_LB_LC")],
            "change_description": "Migration",
        },
    }
}


objective_level = {
    "MDR_MIGRATION_OBJECTIVE_LEVEL": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CT_CD_LIST_SUBMVAL")],
        "uid": row[headers.index("CT_CD")],
        "body": {
            "order": row[headers.index("ORDER")],
            "sponsor_preferred_name": row[headers.index("CT_NAME")],
            "sponsor_preferred_name_sentence_case": row[
                headers.index("NAME_SENTENSE_CASE")
            ],
            "change_description": "Migration",
        },
    }
}

time_units = {
    "COMMON_MAPPING": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CODELIST_NAME")],
        "term_uid": row[headers.index("CT_CD")],
    }
}

# ---------------------------------------------------------------
# Utilities for parsing and converting data
# ---------------------------------------------------------------
#


def sample_from_dict(d, sample=10):
    if SAMPLE:
        keys = list(d)[0:sample]
        values = [d[k] for k in keys]
        return dict(zip(keys, values))
    else:
        return d


def sample_from_list(d, sample=10):
    if SAMPLE:
        return d[0:sample]
    else:
        return d


# Standard codelists terms in sponsor library
# TODO the split between StandardCodeListTerms1 and 2
# is just done because all the things in part 2 are handled
# in a standardised way, while part 1 (this file) uses
# specific functions for each part.
# Can the things in this file also be standardized in a similar fashion?
class StandardCodelistTerms1(BaseImporter):
    logging_name = "standard_codelistterms1"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.sponsor_codelist_legacy_name_map = {}
        self.init_legacy_map(MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS)
        self.code_lists_uids = self.api.get_code_lists_uids()

    @open_file()
    def init_legacy_map(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            legacy_codelist_id = row[headers.index("legacy_codelist_id")]
            new_codelist_name = row[headers.index("new_codelist_name")]
            if legacy_codelist_id == "" or legacy_codelist_id == None:
                if new_codelist_name == "Objective Level":
                    self.sponsor_codelist_legacy_name_map[
                        "ObjectiveLevel"
                    ] = new_codelist_name
                elif new_codelist_name == "Endpoint Level":
                    self.sponsor_codelist_legacy_name_map[
                        "EndpointLevel"
                    ] = new_codelist_name
            else:
                self.sponsor_codelist_legacy_name_map[
                    legacy_codelist_id
                ] = new_codelist_name

    @open_file()
    def handle_epoch_subtype(self, csvfile):
        self.ensure_cache()
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        parent_type_terms = self.api.get_terms_for_codelist_name("Epoch Type")
        all_epoch_terms = self.api.get_terms_for_codelist_name("Epoch")
        for row in readCSV:
            parent_term_uid = find_term_by_name(
                row[headers.index("GEN_EPOCH_TYPE")], parent_type_terms
            )

            data = epoch_sub_type(row, headers)
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.error(
                    f"Epoch subtype '{row[headers.index('CD_LIST_ID')]}' not found in legacy name map, skipping"
                )
                self.metrics.icrement(
                    data["path"]
                    + "-Names Epoch Sub Type - SkippedASMissingcodelist_uid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map["GEN_EPOCH_SUB_TYPE"]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelist_uid"] = self.code_lists_uids[codelist_name]
            else:
                self.log.error(f"Codelist '{codelist_name}' not found, skipping")
                self.metrics.icrement(
                    data["path"]
                    + "-Names Epoch Sub Type - SkippedASMissingcodelist_uid"
                )
                continue
            reused_item = False
            # connect cdisc epoch sub type term with a sponsor epoch sub type term
            concept_id = row[headers.index("CT_CD")]
            if concept_id.startswith("C") and parent_term_uid:
                reused_item = True
                if "|" in concept_id:
                    cids = concept_id.split("|")
                else:
                    cids = [concept_id]
                for cid in cids:
                    term_uid = find_term_by_concept_id(cid, all_epoch_terms)
                    if term_uid is not None:
                        break
                self.log.info(
                    f"Epoch subtype '{row[headers.index('GEN_EPOCH_SUB_TYPE')]}' links to existing Epoch term '{term_uid}'"
                )
            elif (
                find_term_by_name(
                    row[headers.index("GEN_EPOCH_SUB_TYPE_CD")], all_epoch_terms
                )
                is not None
            ):
                reused_item = True
                term_uid = find_term_by_name(
                    row[headers.index("GEN_EPOCH_SUB_TYPE_CD")], all_epoch_terms
                )
                self.log.info(
                    f"Epoch subtype '{row[headers.index('GEN_EPOCH_SUB_TYPE')]}' links to existing Epoch term '{term_uid}'"
                )
            else:
                res = self.api.post_to_api(data)
                subtype = row[headers.index("GEN_EPOCH_SUB_TYPE")]
                subtype_code = row[headers.index("GEN_EPOCH_SUB_TYPE_CD")]
                if res is not None:
                    term_uid = res["term_uid"]
                    self.log.info(
                        f"Epoch subtype '{row[headers.index('GEN_EPOCH_SUB_TYPE')]}' links to new term '{term_uid}'"
                    )
                    self.cache.added_terms[subtype] = res
                    # Approve Names
                    self.api.simple_approve2(
                        data["path"], f"/{term_uid}/names/approvals", label="Names"
                    )
                    # Approve attributes
                    self.api.simple_approve2(
                        "/ct/terms",
                        f"/{term_uid}/attributes/approvals",
                        label="Attributes",
                    )
                else:
                    term_uid = None
                    if subtype in self.cache.added_terms:
                        term_uid = self.cache.added_terms[subtype]["term_uid"]
                    elif subtype_code in self.cache.all_terms_code_submission_values:
                        term_uid = self.cache.all_terms_code_submission_values[
                            subtype_code
                        ]
                    elif subtype_code in self.cache.all_terms_name_submission_values:
                        term_uid = self.cache.all_terms_name_submission_values[
                            subtype_code
                        ]
                    elif subtype in self.cache.all_term_name_values:
                        term_uid = self.cache.all_term_name_values[subtype]["term_uid"]
                    reused_item = True
                    if term_uid:
                        self.log.info(
                            f"Epoch subtype '{row[headers.index('GEN_EPOCH_SUB_TYPE')]}' links to existing term '{term_uid}'"
                        )

            if term_uid and parent_term_uid:
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{term_uid}/parents?parent_uid={parent_term_uid}&relationship_type=type",
                        "body": {},
                    }
                )
                if reused_item:
                    codelist_uid = data["body"]["codelist_uid"]
                    # add a term to the epoch sub type codelist
                    self.api.post_to_api(
                        {
                            "path": f"/ct/codelists/{codelist_uid}/terms",
                            "body": {
                                "term_uid": term_uid,
                                "order": data["body"]["order"],
                            },
                        }
                    )
                    # Start a new version
                    self.api.post_to_api(
                        {
                            "path": f"/ct/terms/{term_uid}/names/versions",
                            "body": {},
                        }
                    )
                    # patch the names
                    data["body"]["change_description"] = "Migration modification"
                    _res = self.api.simple_patch(
                        data["body"],
                        f"/ct/terms/{term_uid}/names",
                        "/ct/terms/{uid}/names",
                    )
                    # Approve Names
                    self.api.simple_approve2(
                        "/ct/terms", f"/{term_uid}/names/approvals", label="Names"
                    )

    @open_file()
    def handle_epoch(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        parent_sub_type_terms = self.api.get_terms_for_codelist_name("Epoch Sub Type")
        all_epoch_terms = self.api.get_terms_for_codelist_name("Epoch")
        for row in readCSV:
            parent_term_uid = find_term_by_name(
                row[headers.index("GEN_EPOCH_SUB_TYPE")], parent_sub_type_terms
            )

            _class = "EPOCH"
            data = epoch[_class](row, headers)
            data["body"]["codelist_uid"] = "C99079"

            # Look up the uid of the Epoch term in the Epoch codelist
            term_uid = find_term_by_name(
                row[headers.index("GEN_EPOCH_CD")], all_epoch_terms
            )
            if term_uid and parent_term_uid:
                self.log.info(
                    f"Adding epoch {row[headers.index('GEN_EPOCH_LB')]} with term: {term_uid}, parent: {parent_term_uid}"
                )
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{term_uid}/parents?parent_uid={parent_term_uid}&relationship_type=subtype",
                        "body": {},
                    }
                )
                codelist_uid = data["body"]["codelist_uid"]
                # add a term to the epoch codelist
                self.api.post_to_api(
                    {
                        "path": f"/ct/codelists/{codelist_uid}/terms",
                        "body": {"term_uid": term_uid, "order": data["body"]["order"]},
                    }
                )
                # Start a new version
                self.api.post_to_api(
                    {"path": f"/ct/terms/{term_uid}/names/versions", "body": {}}
                )
                # patch the names
                data["body"]["change_description"] = "Migration modification"
                res = self.api.simple_patch(
                    data["body"], f"/ct/terms/{term_uid}/names", "/ct/terms/{uid}/names"
                )
                self.api.simple_patch(
                    {"codelist_uid": codelist_uid, "new_order": data["body"]["order"]},
                    f"/ct/terms/{term_uid}/order",
                    "/ct/terms/order",
                )
                # Approve Names
                self.api.simple_approve2(
                    "/ct/terms", f"/{term_uid}/names/approvals", label="Names"
                )
            else:
                self.log.warning(
                    f"Epoch term for epoch {row[headers.index('GEN_EPOCH_LB')]} not found, skipping"
                )

    @open_file()
    def handle_endpoint_level(self, csvfile):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_ENDPOINT_LEVEL"
            data = endpoint_level[_class](row, headers)
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.metrics.icrement(
                    data["path"] + "-Names Endpoint Level- SkippedASMissingcodelist_uid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map[
                row[headers.index("CD_LIST_ID")]
            ]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelist_uid"] = self.code_lists_uids[codelist_name]
            else:
                self.metrics.icrement(
                    data["path"]
                    + "-Names Visit Day Type - SkippedASMissingcodelist_uid"
                )
                continue
            # Start a new version
            self.api.post_to_api(
                {"path": f"/ct/terms/{data['uid']}/names/versions", "body": {}}
            )
            # path the names
            res = self.api.simple_patch(
                data["body"], f"/ct/terms/{data['uid']}/names", "/ct/terms/{uid}/names"
            )
            # Approve
            if res is not None:
                # Approve Names
                if self.api.simple_approve2(
                    "/ct/terms", f"/{res['term_uid']}/names/approvals", label="Names"
                ):
                    # add the term to the sponsor list
                    codelist_uid = data["body"]["codelist_uid"]
                    self.api.post_to_api(
                        {
                            "path": f"/ct/codelists/{codelist_uid}/terms",
                            "body": {
                                "term_uid": res["term_uid"],
                                "order": row[headers.index("CD_VAL_SORT_SEG")],
                            },
                        }
                    )
            else:
                self.api.simple_approve2(
                    "/ct/terms", f"/{data['uid']}/names/approvals", label="Names"
                )

    @open_file()
    def handle_objective_level(self, csvfile):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_OBJECTIVE_LEVEL"
            data = objective_level[_class](row, headers)
            if (
                row[headers.index("CT_CD_LIST_SUBMVAL")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.warning(
                    f"Codelist '{row[headers.index('CT_CD_LIST_SUBMVAL')]} not found in legacy map, skipping'"
                )
                self.metrics.icrement(
                    data["path"]
                    + "-Names Objective Level- SkippedASMissingcodelist_uid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map[
                row[headers.index("CT_CD_LIST_SUBMVAL")]
            ]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelist_uid"] = self.code_lists_uids[codelist_name]
            else:
                self.log.warning(f"Codelist '{codelist_name} not found, skipping'")
                self.metrics.icrement(
                    data["path"]
                    + "-Names Objective Level - SkippedASMissingcodelist_uid"
                )
                continue
            # Start a new version
            self.api.post_to_api(
                {"path": f"/ct/terms/{data['uid']}/names/versions", "body": {}}
            )
            # path the names
            res = self.api.simple_patch(
                data["body"], f"/ct/terms/{data['uid']}/names", "/ct/terms/{uid}/names"
            )
            # Approve
            if res is not None:
                # Approve Names
                if self.api.simple_approve2(
                    "/ct/terms", f"/{res['term_uid']}/names/approvals", label="Names"
                ):
                    # add the term to the sponsor list
                    codelist_uid = data["body"]["codelist_uid"]
                    self.api.post_to_api(
                        {
                            "path": f"/ct/codelists/{codelist_uid}/terms",
                            "body": {
                                "term_uid": res["term_uid"],
                                "order": row[headers.index("ORDER")],
                            },
                        }
                    )

    @open_file_async()
    async def handle_epoch_type(self, csvfile, session):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        for row in readCSV:
            codelist_name = None
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.warning(
                    f"Codelist id '{row[headers.index('CD_LIST_ID')]}' not found in legacy map, skipping."
                )
                self.metrics.icrement(
                    "/ct/codelists/-Names Epoch Type - SkippedASMissingcodelist_uid"
                )
                continue
            else:
                codelist_name = self.sponsor_codelist_legacy_name_map[
                    row[headers.index("CD_LIST_ID")]
                ]
            codelist_uid = ""
            if codelist_name in self.code_lists_uids:
                codelist_uid = self.code_lists_uids[codelist_name]
            else:
                self.log.warning(
                    f"Codelist '{codelist_name}' not found in provided list, skipping."
                )
                # self.metrics.icrement(data["path"] + "-Names Epoch Type - SkippedASMissingcodelist_uid")
                continue
            data = {
                "codelist": row[headers.index("CD_LIST_ID")],
                "term_name": row[headers.index("CD_VAL_LB")],
                "concept_id": row[headers.index("CT_CD")],
                "body": {
                    "catalogue_name": "SDTM CT",
                    "codelist_uid": codelist_uid,
                    "code_submission_value": row[headers.index("CD_VAL")],
                    "name_submission_value": row[headers.index("CD_VAL")],
                    "nci_preferred_name": "UNK",
                    "definition": "",
                    "sponsor_preferred_name": row[headers.index("CD_VAL_LB")],
                    "sponsor_preferred_name_sentence_case": row[
                        headers.index("CD_VAL_LB")
                    ].lower(),
                    "library_name": "Sponsor",
                    "order": row[headers.index("CD_VAL_SORT_SEQ")],
                },
            }
            # TODO check if already exists
            self.log.info(
                f"Adding epoch type '{data['term_name']}' to codelist '{data['codelist']}'"
            )
            api_tasks.append(self.process_epoch_type(data=data, session=session))
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_codelist_definitions(self, csvfile, session):
        # General handler for creating codelists in libraries.
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        for row in readCSV:
            new_codelist_name = row[headers.index("new_codelist_name")]
            try:
                idx = headers.index("extensible")
                extensible = map_boolean(row[idx], raise_exception=True)
            except ValueError as e:
                self.log.warning(
                    f"Error parsing boolean at index {idx} in line \n{row}\nerror: {e}\nDefaulting to False"
                )
                extensible = False
            try:
                idx = headers.index("template_parameter")
                template_parameter = map_boolean(row[idx], raise_exception=True)
            except ValueError as e:
                self.log.warning(
                    f"Error parsing boolean at index {idx} in line\n{row}\nerror: {e}\nDefaulting to False"
                )
                template_parameter = False
            data = {
                "path": "/ct/codelists",
                "body": {
                    "catalogue_name": "SDTM CT",
                    "name": new_codelist_name,
                    "submission_value": row[headers.index("submission_value")],
                    "nci_preferred_name": row[headers.index("preferred_term")],
                    "definition": row[headers.index("definition")],
                    "extensible": extensible,
                    "sponsor_preferred_name": row[headers.index("new_codelist_name")],
                    "template_parameter": template_parameter,
                    "library_name": row[headers.index("library")],
                    "terms": [],
                },
            }
            # TODO Add check if we already have the code list
            self.log.info(
                f"Adding codelist name '{new_codelist_name}' to library '{data['body']['library_name']}'"
            )
            api_tasks.append(
                self.post_codelist_approve_name_or_attribute(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_codelist_parameter_set(self, csvfile, session):
        # Mark codelist parameters as a template parameters
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        for row in readCSV:
            url = path_join(
                "/ct/codelists", row[headers.index("CODELIST_CONCEPT_ID")], "names"
            )
            change_description = f"Marking {row[headers.index('DESCRIPTION')]} as TemplateParameter in the migration"
            data = {
                "get_path": url,
                "path": path_join(url, "versions"),
                "patch_path": url,
                "approve_path": path_join(url, "approvals"),
                "body": {
                    "template_parameter": True,
                    "change_description": change_description,
                },
            }
            # TODO check if already exists
            self.log.info(
                f"Adding codelist parameter set '{row[headers.index('CODELIST_CONCEPT_ID')]}' with description '{row[headers.index('DESCRIPTION')]}'"
            )
            api_tasks.append(
                self.process_codelist_parameter(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    ############ helper functions ###########
    async def post_codelist_approve_name_or_attribute(
        self, data: dict, session: aiohttp.ClientSession
    ):
        status, response = await self.api.post_to_api_async(
            url=data["path"], body=data["body"], session=session
        )
        uid = response.get("codelist_uid")
        if uid != None:
            # Give the backend a little time before approving, otherwise approve may fail.
            # Seems to be a problem only when running locally.
            # We do all these in parallel, this sleep should not affect the time it takes to run the import.
            time.sleep(0.05)
            status, result = await self.api.approve_async(
                f"/ct/codelists/{uid}/names/approvals", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve name for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-NamesApproveError")
            else:
                self.log.info(f"Approved name for codelist: {data['body']['name']}")
                self.metrics.icrement("/ct/codelists/-NamesApprove")
            time.sleep(0.05)
            status, result = await self.api.approve_async(
                f"/ct/codelists/{uid}/attributes/approvals", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve attributes for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-AttributesApproveError")
            else:
                self.log.info(
                    f"Approved attributes for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-AttributesApprove")
            return result
        elif status == 400 and "already exists" in response.get("message", ""):
            self.log.info(
                f"Codelist {data['body']['name']} already exists, skipping approve."
            )
            return response
        else:
            self.log.error(f"Failed to create codelist: {data['body']['name']}, response: {response}")
            self.metrics.icrement("/ct/codelists-ERROR")
            return response

    async def process_codelist_parameter(
        self, data: dict, session: aiohttp.ClientSession
    ):
        get_result = {}
        async with session.get(
            path_join(API_BASE_URL, data["get_path"]), headers=self.api.api_headers
        ) as response:
            status = response.status
            get_result = await response.json()
        if get_result is not None and get_result.get("template_parameter") is True:
            self.metrics.icrement("/ct/codelists-AlreadyIsTemplateParameter")
            return get_result
        status, post_result = await self.api.post_to_api_async(
            url=data["path"], body={}, session=session
        )
        patch_status, patch_result = await self.api.patch_to_api_async(
            path=data["patch_path"], body=data["body"], session=session
        )
        status, result = await self.api.approve_async(
            data["approve_path"], session=session
        )
        if status != 201:
            self.metrics.icrement("/ct/codelists/-NamesApproveError")
        else:
            self.metrics.icrement("/ct/codelists/-NamesApprove")
        return result

    async def process_epoch_type(self, data: dict, session: aiohttp.ClientSession):
        self.ensure_cache()
        term_name = data["term_name"]
        # if concept_id starts with C it means that we should take existing CDISC term
        # and add it to the Epoch Type codelist
        if data["concept_id"].startswith("C"):
            # TODO we should not assume that the uid follows this pattern exactly,
            # better to look it up by concept_id from the Epoch codelist.
            # Could there be relevant terms in any other codelist?
            term_uid = f"{data['concept_id']}_{data['body']['code_submission_value']}"
            codelist_uid = data["body"]["codelist_uid"]
            status, result = await self.api.post_to_api_async(
                url=f"/ct/codelists/{codelist_uid}/terms",
                body={"term_uid": term_uid, "order": data["body"]["order"]},
                session=session,
            )
            return result
        else:
            post_status, post_result = await self.api.post_to_api_async(
                url="/ct/terms", body=data["body"], session=session
            )
            if post_status == 201:
                self.cache.added_terms[term_name] = post_result
                status, result = await self.api.approve_async(
                    f"/ct/terms/{post_result['term_uid']}/names/approvals",
                    session=session,
                )
                if status != 201:
                    self.metrics.icrement("/ct/terms-NamesApproveError")
                else:
                    self.metrics.icrement("/ct/terms-NamesApprove")
                status, result = await self.api.approve_async(
                    f"/ct/terms/{post_result['term_uid']}/attributes/approvals",
                    session=session,
                )
                if status != 201:
                    self.metrics.icrement("/ct/terms-AttributesApproveError")
                else:
                    self.metrics.icrement("/ct/terms-AttributesApprove")
                return result

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_codelist_definitions(
                MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS, session
            )
            await self.handle_codelist_parameter_set(
                MDR_MIGRATION_CODELIST_PARAMETER_SET, session
            )

            # We need to import the sponsor defined epochs before we can import epoch types and subtypes.
            # We can use the mechanisms from StandardCodelistTerms2 to do this.
            await self.handle_sponsor_defined_epochs(session)

            # epoch type codelist
            await self.handle_epoch_type(MDR_MIGRATION_EPOCH_TYPE, session)

    async def handle_sponsor_defined_epochs(self, session):
        term_importer = StandardCodelistTerms2(
            metrics_inst=self.metrics, cache=self.cache
        )
        code_lists_uids = self.api.get_code_lists_uids()
        await term_importer.migrate_term(
            MDR_MIGRATION_SPONSOR_EPOCH,
            codelist_name="Epoch",
            code_lists_uids=code_lists_uids,
            session=session,
        )

    def run(self):
        self.log.info("Importing standard codelists")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.handle_epoch_subtype(MDR_MIGRATION_EPOCH_SUB_TYPE)
        self.handle_epoch(MDR_MIGRATION_EPOCH)
        self.handle_endpoint_level(MDR_MIGRATION_ENDPOINT_LEVEL)
        self.handle_objective_level(MDR_MIGRATION_OBJECTIVE_LEVEL)
        self.log.info("Done importing standard codelists")


def main():
    metr = Metrics()
    migrator = StandardCodelistTerms1(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
