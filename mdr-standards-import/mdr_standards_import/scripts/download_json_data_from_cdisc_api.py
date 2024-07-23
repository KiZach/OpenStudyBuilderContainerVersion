import json
from typing import Sequence
import requests
from requests.exceptions import HTTPError
from os import listdir
from os import environ
from os import mkdir
from os import path
from pathlib import Path
from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport
from mdr_standards_import.scripts.entities.cdisc_data_models.version import Version
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from mdr_standards_import.scripts.utils import (
    get_cdisc_neo4j_driver,
    is_newer_than,
    get_classes_directory_name,
)
from neo4j.exceptions import ServiceUnavailable


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")
AUTH_TOKEN = environ.get("CDISC_AUTH_TOKEN")
HEADERS = {"api-key": AUTH_TOKEN, "Accept": "application/json"}
BASE_URL = environ.get("CDISC_BASE_URL")


def download_newer_packages_than(last_effective_date: str, to_directory: str):
    """
    Downloads those packages from the CDISC REST API where the effective date is newer than the specified
    <last_effective_date>.
    Stores the data in JSON files on disc.

    :param last_effective_date: string (YYYY-MM-DD, e.g. "2020-12-31"), the date of the last loaded package.
        Only packages newer than this date will be loaded. May be None: in that case 2014-01-01 is used as default date.
    """

    if last_effective_date is None:
        last_effective_date = "2014-01-01"

    print(
        f"Checking for packages newer than the effective_date='{last_effective_date}'.",
        end="",
    )

    available_packages_in_api = get_available_packages_meta_data_from_api()

    packages_to_load = []
    for package in available_packages_in_api["_links"]["packages"]:
        href = package["href"]
        # example for the href property: "/mdr/ct/packages/adamct-2014-09-26"
        # the package_id is the part of the href after the last slash (/)
        # e.g. "adamct-2014-09-26"
        package_id = path.basename(href)
        # Strip off the date
        name = package_id.rsplit("-", 3)[0]
        # the effective date is at the end of the package id
        # e.g. "2014-09-26"
        effective_date = "-".join(package_id.rsplit("-", 3)[-3:])
        ct_import = CTImport(effective_date, "TMP")
        if is_newer_than(effective_date, last_effective_date):
            package = Package(ct_import)
            package.set_catalogue_name(href)
            package.set_href(href)
            packages_to_load.append(package)

    if len(packages_to_load) > 0:
        download_packages_data(packages_to_load, to_directory)
    else:
        print(f" -> No packages found for downloading.")


def get_available_packages_meta_data_from_api() -> json:
    """
    Gets the CT packages list from the CDISC REST API.

    The JSON result has the following form:
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages",
                "title": "Product Group Terminology",
                "type": "Controlled Terminology Package List"
            },
            "packages": [
                {
                    "href": "/mdr/ct/packages/sdtmct-2019-12-20",
                    "title": "SDTM Controlled Terminology Package 40 Effective 2019-12-20",
                    "type": "Terminology"
                }
            ]
        }
    }
    """
    response = requests.get(BASE_URL + "/mdr/ct/packages", headers=HEADERS)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))
    return response.json()


def download_packages_data(packages_to_download: Sequence[Package], to_directory: str):
    """
    Downloads the CDISC CT package data for those packages specified by <packages_to_download>.
    Stores the data in JSON files on disc.

    If the corresponding JSON files are already present for one or more packages, those packages will be skipped.

    :param packages_to_download: a list of those packages that shall be downloaded.
    """

    create_cdisc_data_dir(to_directory)
    print("")
    print(f"Storing files in directory='{to_directory}'.")
    existing_packages = set(
        [
            path.splitext(path.basename(x))[0]
            for x in listdir(to_directory)
            if path.splitext(x)[1] == ".json"
        ]
    )
    step = 1
    number_of_packages = len(packages_to_download)
    for package in packages_to_download:
        package_id = (
            package.catalogue_name + "-" + package.get_ct_import().effective_date
        )
        if path.basename(package_id.lower()) in existing_packages:
            print(
                f"  Step: {step}/{number_of_packages} - Package '{package_id}' already downloaded."
            )
        else:
            print(
                f"  Step: {step}/{number_of_packages} - Downloading package '{package_id}'."
            )
            try:
                response = requests.get(BASE_URL + package.href, headers=HEADERS)
                response.raise_for_status()
                package_data = response.json()
            except HTTPError as http_err:
                print(f"    HTTP error occurred: {http_err}")
            except Exception as err:
                print(f"    Other error occurred: {err}")
            else:
                filename = package_id.split("/")[-1].lower() + ".json"
                with open(path.join(to_directory, filename), "w") as ctpkg_file:
                    ctpkg_file.write(json.dumps(package_data))
                    ctpkg_file.write("\n")
        step += 1


def get_available_model_versions_meta_data_from_api() -> json:
    """
    Gets the Models and IG versions list from the CDISC REST API.
    Several endpoints need to be called.

    The general JSON result has the following form:
    {
        "_links": {
            "self": {
                "href": "/mdr/products/DataTabulation",
                "title": "Product Group Data Tabulation",
                "type": "CDISC Library Product Group"
            },
            "sdtm": [
                {
                    "href": "/mdr/sdtm/1-8",
                    "title": "Study Data Tabulation Model Version 1.8 (Final)",
                    "type": "Foundational Model"
                }
            ],
            "sdtmig": [
                {
                    "href": "/mdr/sdtmig/3-3",
                    "title": "Study Data Tabulation Model Implementation Guide: Human Clinical Trials Version 3.3 (Final)",
                    "type": "Implementation Guide"
                }
            ],
            }
        }

    Returns:
        json: Concatenated json with objects returned from the different endpoints
        Note : _links top level and self objects are removed before concatenating to prevent conflicts
    """
    # Get data tabulation (SDTM, SEND)
    response = requests.get(BASE_URL + "/mdr/products/DataTabulation", headers=HEADERS)
    response.raise_for_status()
    data_tabulation = response.json()
    if "self" in data_tabulation["_links"]:
        del data_tabulation["_links"]["self"]

    # Get data collection (CDASH)
    # response = requests.get(BASE_URL + "/mdr/products/DataCollection", headers=HEADERS)
    # response.raise_for_status()
    # data_collection = response.json()
    # if "self" in data_collection["_links"]:
    #     del data_collection["_links"]["self"]

    # Get data analysis (ADaM)
    # response = requests.get(BASE_URL + "/mdr/products/DataAnalysis", headers=HEADERS)
    # response.raise_for_status()
    # data_analysis = response.json()
    # if "self" in data_analysis["_links"]:
    #     del data_analysis["_links"]["self"]

    # return {
    #     **data_tabulation["_links"],
    #     **data_collection["_links"],
    #     **data_analysis["_links"],
    # }

    return {**data_tabulation["_links"]}


def download_newer_data_model_versions_than(
    last_available_versions: dict, to_directory: str, library: str="CDISC"
):
    """
    Downloads the versions from the CDISC REST API where the version number is higher than the specified
    versions for each catalogue, as defined in <last_available_versions>.
    Stores the data in JSON files on disc.

    Args:
        last_available_versions (dict): Dictionary with last version number available for each catalogue. e.g. {"sdtm": "1.8", "cdashig": "1.1"}
        to_directory (str): Directory where to store the downloaded data
        library (str): Library name to use in the DataModelImport object. Default is "CDISC"
    """

    available_versions_in_api = get_available_model_versions_meta_data_from_api()
    for catalogue in available_versions_in_api:
        versions_to_load = []
        versions = available_versions_in_api[catalogue]
        catalogue = catalogue.upper()
        for _version in versions:
            href = _version["href"]
            data_model_type = _version["type"]
            # example for the href property: "/mdr/sdtm/1-8"
            # the version number is the part of the href after the last slash (/) for all except ADaM
            # For ADaM, the href is : "/mdr/adam/adamig-1-1" so version is the part after last slash without 'adamig'
            version_number = path.basename(href)

            data_model_import = DataModelImport(
                library=library, catalogue=catalogue, version_number=version_number, user_initials="TMP"
            )
            if (catalogue not in last_available_versions) or (
                catalogue in last_available_versions
                and version_number not in last_available_versions[catalogue]
            ):
                version = Version(data_model_import, version_number)
                version.set_catalogue_name(catalogue)
                version.set_href(href)
                versions_to_load.append(version)

        if len(versions_to_load) > 0:
            download_versions_data(
                catalogue, data_model_type, versions_to_load, to_directory
            )
        else:
            print(f" -> No versions in catalogue {catalogue} found for downloading.")


def download_versions_data(
    catalogue: str,
    data_model_type: str,
    versions_to_download: Sequence[Version],
    to_directory: str,
):
    """
    Downloads the CDISC Data Model version data for those versions specified by <versions_to_download>.
    Stores the data in JSON files on disc.

    If the corresponding JSON files are already present for one or more versions, those versions will be skipped.

    :param catalogue: name of the catalogue
    :param type: type of the model (Foundational Model or Implementation Guide)
    :param versions_to_download: a list of those versions that shall be downloaded.
    :param to_directory: directory in which to download the files
    """
    sub_directory = f"{to_directory}/{catalogue}/models"
    create_cdisc_data_dir(sub_directory)
    print("")
    print(f"Storing files in directory='{to_directory}{catalogue}.")
    existing_versions = set(
        [
            path.splitext(path.basename(x))[0]
            for x in listdir(sub_directory)
            if path.splitext(x)[1] == ".json"
        ]
    )
    step = 1
    number_of_versions = len(versions_to_download)
    for version in versions_to_download:
        version_number = version.get_version_number()
        if version_number in existing_versions:
            print(
                f" Catalogue {catalogue} - Step: {step}/{number_of_versions} - Version '{version_number}' already downloaded."
            )
        else:
            print(
                f"  Catalogue {catalogue} - Step: {step}/{number_of_versions} - Downloading version '{version_number}'."
            )
            try:
                response = requests.get(BASE_URL + version.href, headers=HEADERS)
                response.raise_for_status()
                version_data = response.json()
            except HTTPError as http_err:
                print(f"    HTTP error occurred: {http_err}")
            except Exception as err:
                print(f"    Other error occurred: {err}")
            else:
                filename = f"{version_number}.json"
                with open(path.join(sub_directory, filename), "w") as version_file:
                    version_file.write(json.dumps(version_data))
                    version_file.write("\n")

                url_suffix = _map_classes_or_datasets_url_suffix(
                    catalogue=catalogue, data_model_type=data_model_type
                )
                classes_datasets_sub_directory = get_classes_directory_name(
                    data_model_type
                )
                download_classes_data(
                    base_version_href=version.href,
                    suffix=url_suffix,
                    to_directory=path.join(
                        to_directory,
                        catalogue,
                        classes_datasets_sub_directory,
                        version_number,
                    ),
                )
        step += 1


def download_classes_data(base_version_href: str, suffix: str, to_directory: str):
    """
    For given Data Model version, will download the children classes

    :param base_version_href: base href for the version for which to download classes
    :param suffix: url suffix for downloading classes/datasets
    :param to_directory: directory in which to download the classes, including version_number
    """
    print(" * Downloading classes/datasets.")
    try:
        classes_url = f"{BASE_URL}{base_version_href}/{suffix.lower()}"
        response = requests.get(classes_url, headers=HEADERS)
        response.raise_for_status()
        classes_data = response.json()
    except HTTPError as http_err:
        print(f"    HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"    Other error occurred: {err}")
    else:
        if suffix in classes_data["_links"]:
            classes = classes_data["_links"][suffix]
            for _class in classes:
                class_data = _download_element(
                    to_directory=to_directory, element_ref=_class
                )

                if "scenarios" in class_data["_links"]:
                    scenarios = class_data["_links"]["scenarios"]
                    for _scenario in scenarios:
                        _download_element(
                            to_directory=path.join(to_directory, "scenarios"),
                            element_ref=_scenario,
                        )
        else:
            print(f" -- No {suffix} found for version.")


def _download_element(to_directory: str, element_ref: dict) -> dict:
    href = element_ref["href"]
    response = requests.get(BASE_URL + href, headers=HEADERS)
    response.raise_for_status()
    download_data = response.json()
    _file = Path(path.join(to_directory, f"{path.basename(href)}.json"))
    _file.parent.mkdir(exist_ok=True, parents=True)
    with open(_file, "w") as download_file:
        download_file.write(json.dumps(download_data))
        download_file.write("\n")

    return download_data


def _map_classes_or_datasets_url_suffix(catalogue: str, data_model_type: str) -> str:
    """
    Returns the suffix to use for datasets download for the given catalogue

    Args:
        catalogue (str): Name of the catalogue
        data_model_type (str): Data model type (Foundational Model or Implementation Guide)

    Returns:
        str: Suffix to use in the GET URL to retrieve the datasets
    """
    if catalogue == "ADAM":
        return "dataStructures"
    elif data_model_type == DataModelType.FOUNDATIONAL.value:
        return "classes"
    elif catalogue == "CDASHIG":
        return "domains"
    elif catalogue == "SDTMIG":
        return "datasets"
    elif catalogue == "SENDIG":
        return "datasets"


def create_cdisc_data_dir(directory: str):
    try:
        Path(directory).mkdir(0o750, True, True)
    except OSError as error:
        # ignore [Errno 17] File exists
        if error.errno != 17:
            print(error)


def get_latest_effective_date():
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()
    try:
        with cdisc_neo4j_driver.session(database="system") as session:
            session.run(
                "CREATE DATABASE $database IF NOT EXISTS",
                database=CDISC_IMPORT_DATABASE,
            )
    except ServiceUnavailable:
        print("Can't connect to neo4j database, using default latest date")
        return None

    with cdisc_neo4j_driver.session(database=CDISC_IMPORT_DATABASE) as session:
        with session.begin_transaction() as tx:
            record = tx.run(
                """
                MATCH (import:Import)
                WITH import.effective_date AS effective_date
                ORDER BY effective_date DESC
                LIMIT 1
                RETURN
                    effective_date.year + '-' + right('0' + effective_date.month, 2) + '-' + right('0' + effective_date.day, 2)
                        AS effective_date
                """
            ).single()
            return record["effective_date"] if record is not None else None


def get_latest_data_model_versions():
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()
    try:
        with cdisc_neo4j_driver.session(database="system") as session:
            session.run(
                "CREATE DATABASE $database IF NOT EXISTS",
                database=CDISC_IMPORT_DATABASE,
            )
    except ServiceUnavailable:
        print("Can't connect to neo4j database, using default latest version")
        return {}

    with cdisc_neo4j_driver.session(database=CDISC_IMPORT_DATABASE) as session:
        with session.begin_transaction() as tx:
            output = {}
            result = tx.run(
                """
                MATCH (import:DataModelImport)
                WITH import.catalogue as catalogue, collect(import.version_number) AS versions
                RETURN catalogue, versions
                """
            )
            for record in result.data():
                output[record["catalogue"]] = record["versions"]
            return output


def download_ct_json_data_from_cdisc_api(to_directory: str):
    download_newer_packages_than(get_latest_effective_date(), to_directory)


def download_data_model_json_data_from_cdisc_api(to_directory: str):
    download_newer_data_model_versions_than(
        get_latest_data_model_versions(), to_directory
    )
