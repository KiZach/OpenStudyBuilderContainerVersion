import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Dict

import aiohttp
import requests

from ..functions.caselessdict import CaselessDict
from ..functions.utils import create_logger, load_env
from .api_bindings import ApiBinding
from .metrics import Metrics

logger = logging.getLogger("legacy_mdr_migrations - utils")

metrics = Metrics()

API_HEADERS = {"Accept": "application/json", "User-Agent": "test"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")


class TermCache:
    def __init__(self, api):
        self.api = api
        self.all_terms_attributes = self.api.get_all_from_api("/ct/terms/attributes")
        self.all_terms_name_submission_values = CaselessDict(
            self.api.get_all_identifiers(
                self.all_terms_attributes,
                identifier="name_submission_value",
                value="term_uid",
            )
        )
        self.all_terms_code_submission_values = CaselessDict(
            self.api.get_all_identifiers(
                self.all_terms_attributes,
                identifier="code_submission_value",
                value="term_uid",
            )
        )
        self.all_term_names = self.api.get_all_from_api("/ct/terms/names")
        self.all_term_name_values = CaselessDict(
            self.api.get_all_identifiers_multiple(
                self.all_term_names,
                identifier="sponsor_preferred_name",
                values=["term_uid", "catalogue_name"],
            )
        )
        self.added_terms = CaselessDict()


# Decorator to avoid starting every function with the open() context manager
def open_file():
    def open_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        return func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


# Decorator to avoid starting every function with the open() context manager
def open_file_async():
    def open_decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        await func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


class BaseImporter:
    logging_name = "legacy_mdr_migrations"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        self.log = create_logger(self.logging_name)
        if metrics_inst is None:
            self.metrics = Metrics()
        else:
            self.metrics = metrics_inst
        if api is None:
            headers = self._authenticate(API_HEADERS)
            self.api = ApiBinding(API_BASE_URL, headers, self.metrics, logger=self.log)
        else:
            self.api = api

        self.cache = cache

        self.visit_type_codelist_name = "VisitType"
        self.element_subtype_codelist_name = "Element Sub Type"

    def refresh_auth(self):
        headers = self._authenticate(API_HEADERS)
        self.api.update_headers(headers)

    @staticmethod
    def _authenticate(headers: Dict) -> Dict:
        """Authenticates with client secret flow and appends Authorization header the dict of API request headers"""

        headers = headers.copy()

        client_id = load_env("CLIENT_ID", "")

        api_token = load_env("STUDYBUILDER_API_TOKEN", "")

        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"

        elif client_id:
            client_secret = load_env("CLIENT_SECRET")
            token_endpoint = load_env("TOKEN_ENDPOINT")
            scope = load_env("SCOPE")

            response = requests.post(
                token_endpoint,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                    "scope": scope,
                },
            )

            response.raise_for_status()
            payload = response.json()

            access_token = payload.get("access_token")
            if not access_token:
                msg = "missing access token from token payload"
                logger.error(msg)
                raise RuntimeError(msg)

            token_type = payload.get("token_type")
            if not access_token:
                msg = "missing token type from token payload"
                logger.error(msg)
                raise RuntimeError(msg)

            headers["Authorization"] = f"{token_type} {access_token}"

        return headers

    def run(self):
        pass

    def prepare(self):
        pass

    def ensure_cache(self):
        if self.cache is None:
            self.log.info("Creating term cache")
            self.cache = TermCache(self.api)

    def get_cache(self):
        self.ensure_cache()
        return self.cache

    ############ helper functions ###########

    # Check if a codelist contains a term with sponsor preferred name equal to the given name.
    def search_codelist(self, codelist, name):
        for item in codelist:
            if (
                item.get("name", {}).get("sponsor_preferred_name", "").lower()
                == name.lower()
            ):
                return True
        return False

    # Search a codelist for a term with the given sponsor preferred name.
    # For use with codelists fetched like:
    # terms = self.api.get_terms_for_codelist_name("Objective Category")
    def get_uid_for_sponsor_preferred_name(self, terms, name):
        for item in terms:
            try:
                if item["name"]["sponsor_preferred_name"] == name:
                    return item["term_uid"]
            except KeyError:
                pass

    # Helper to return the first term that has a matching catalogue name.
    def _find_term_with_catalogue(self, terms, catalogue):
        for term in terms:
            if term["catalogue_name"] == catalogue:
                return term

    async def process_simple_term_migration(
        self, data: dict, session: aiohttp.ClientSession
    ):
        self.ensure_cache()
        result = None
        term_name = data["body"]["sponsor_preferred_name"]
        concept_id = data.get("term_concept_id")
        if concept_id and concept_id.lower() != "none":
            post_status = None
        else:
            post_status, post_result = await self.api.post_to_api_async(
                url="/ct/terms", body=data["body"], session=session
            )
        term_uid = None
        if post_status == 201:
            self.cache.added_terms[term_name] = post_result
            term_uid = post_result["term_uid"]
            self.log.info(f"Added term name '{term_name}' with uid '{term_uid}'")
            time.sleep(0.01)
            status, result = await self.api.approve_async(
                "/ct/terms/" + term_uid + "/names/approvals", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve term name '{term_name}' with uid '{term_uid}'"
                )
                metrics.icrement("/ct/terms--NamesApproveError")
            else:
                self.log.info(f"Approved term name '{term_name}' with uid '{term_uid}'")
                metrics.icrement("/ct/terms--NamesApprove")
            status, result = await self.api.approve_async(
                "/ct/terms/" + term_uid + "/attributes/approvals", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve term attributes '{term_name}' with uid '{term_uid}'"
                )
                metrics.icrement("/ct/terms--AttributesApproveError")
            else:
                self.log.info(
                    f"Approved term attributes '{term_name}' with uid '{term_uid}'"
                )
                metrics.icrement("/ct/terms--AttributesApprove")
        else:
            self.log.info(
                f"Failed to create new term name '{term_name}' with uid '{term_uid}', trying to link to already existing"
            )
            if concept_id and concept_id.lower() == "none":
                self.log.error(f"Term '{term_name}' should not be linked, skipping")
                return
            elif concept_id:
                catalogue = data["body"]["catalogue_name"]
                submval = data["body"]["code_submission_value"]
                self.log.info(
                    f"Looking up term with concept id '{concept_id}' with submission value '{submval}' in catalogue '{catalogue}'"
                )
                matching_terms = self.api.lookup_terms_from_concept_id(
                    concept_id, catalogue_name=catalogue, code_submission_value=submval
                )
                if len(matching_terms) == 0:
                    self.log.warning(
                        f"Could not find term with concept id '{concept_id}' with submission value '{submval}' in catalogue '{catalogue}'"
                    )
                    matching_terms = self.api.lookup_terms_from_concept_id(
                        concept_id, code_submission_value=submval
                    )
                    if len(matching_terms) == 0:
                        self.log.warning(
                            f"Could not find term with concept id '{concept_id}' with submission value '{submval}' in any catalogue'"
                        )
                        matching_terms = self.api.lookup_terms_from_concept_id(
                            concept_id, catalogue_name=catalogue
                        )
                        if len(matching_terms) == 0:
                            self.log.warning(
                                f"Could not find term with concept id '{concept_id}' with any submission value in catalogue '{catalogue}'"
                            )
                            matching_terms = self.api.lookup_terms_from_concept_id(
                                concept_id
                            )
                            if len(matching_terms) == 0:
                                self.log.error(
                                    f"Could not find term with concept id '{concept_id}' with any submission value in any catalogue, skipping"
                                )
                                return
                term_uid = matching_terms[0]["term_uid"]

                self.log.info(
                    f"Found term(s) with uid(s) {[t['term_uid'] for t in matching_terms]} for concept id '{concept_id}'"
                )
                codelist_uid = data["body"]["codelist_uid"]
                if any(
                    [
                        codelist_uid in [x["codelist_uid"] for x in t["codelists"]]
                        for t in matching_terms
                    ]
                ):
                    self.log.info(
                        f"Term name '{term_name}' already exits in the codelist with uid {codelist_uid}, not adding again"
                    )
                    return
            elif term_name in self.cache.added_terms:
                term_uid = self.cache.added_terms[term_name]["term_uid"]
                self.log.info(
                    f"Term name '{term_name}' with uid '{term_uid}' found in cache of newly added terms"
                )
            elif term_name in self.cache.all_term_name_values:
                found_terms = self.cache.all_term_name_values[term_name]
                term_in_catalogue = self._find_term_with_catalogue(
                    found_terms, data["body"]["catalogue_name"]
                )
                self.log.info(
                    f"Term name '{term_name}' found as '{[str(t['catalogue_name']) + ':' + t['term_uid'] for t in found_terms]}' among existing term names"
                )
                if term_in_catalogue is None:
                    self.log.error(
                        f"Term '{term_name}' not found in catalogue: '{data['body']['catalogue_name']}', using first match from catalogue '{found_terms[0]['catalogue_name']}'"
                    )
                    term_uid = found_terms[0]["term_uid"]
                else:
                    term_uid = term_in_catalogue["term_uid"]
                codelist_uid = data["body"]["codelist_uid"]
                codelist = self.retry_function(
                    self.api.get_terms_for_codelist_uid,
                    [codelist_uid],
                    nbr_retries=3,
                    retry_delay=0.5,
                )
                if self.search_codelist(codelist, term_name):
                    self.log.info(
                        f"Term name '{term_name}' already exits in the codelist with uid {codelist_uid}, not adding again"
                    )
                    return
            elif (
                data["body"].get("code_submission_value")
                in self.cache.all_terms_code_submission_values
            ):
                term_uid = self.cache.all_terms_code_submission_values[
                    data["body"].get("code_submission_value")
                ]
                self.log.info(
                    f"Term name '{term_name}' found with uid '{term_uid}' among existing term code submission values"
                )
            elif (
                data["body"].get("name_submission_value")
                in self.cache.all_terms_name_submission_values
            ):
                term_uid = self.cache.all_terms_name_submission_values[
                    data["body"].get("name_submission_value")
                ]
                self.log.info(
                    f"Term name '{term_name}' found with uid '{term_uid}' among existing term name submission values"
                )
            if term_uid:
                codelist_uid = data["body"]["codelist_uid"]
                self.log.info(
                    f"Add term name '{term_name}' with uid '{term_uid}' to codelist '{codelist_uid}'"
                )
                result = await self.api.post_to_api_async(
                    url="/ct/codelists/" + codelist_uid + "/terms",
                    body={"term_uid": term_uid, "order": data["body"]["order"]},
                    session=session,
                )
                post_status, post_result = result
                if post_status != 201:
                    self.log.error(
                        f"Failed to add term name '{term_name}' with uid '{term_uid}' to codelist '{codelist_uid}'"
                    )
        if data.get("valid_epoch_uids"):
            for valid_epoch_uid in data.get("valid_epoch_uids"):
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{term_uid}/parents?parent_uid={valid_epoch_uid}&relationship_type=valid_for_epoch",
                        "body": {},
                    }
                )
        if data.get("element_type_uid"):
            self.api.post_to_api(
                {
                    "path": f"/ct/terms/{term_uid}/parents?parent_uid={data.get('element_type_uid')}&relationship_type=type",
                    "body": {},
                }
            )
        return result

    # Retry a function that sporadically fails.
    # After the first failure it will sleep for retry_delay seconds,
    # then double the delay for each subsequent failure.
    def retry_function(
        self,
        function: Callable,
        args: list,
        nbr_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        for n in range(nbr_retries + 1):
            try:
                return function(*args)
            except Exception:
                self.log.warning(
                    f"Function failed, retry {n+1} of {nbr_retries} in {retry_delay} seconds"
                )
                time.sleep(retry_delay)
                retry_delay = 2 * retry_delay
