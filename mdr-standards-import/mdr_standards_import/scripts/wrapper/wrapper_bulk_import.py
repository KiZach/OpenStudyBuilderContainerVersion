from os import environ

from mdr_standards_import.scripts.dev_scripts.bulk_import import bulk_import

CDISC_DIR = environ.get("CDISC_DATA_DIR", "json_data/packages")


def wrapper_bulk_import(
    user_initials: str, json_data_directory: str = "", skip_download_step: bool = False
):
    """
    Import CDISC CT packages into the intermediate DB and immediately after, without manual
    intervention, import the packages from the intermediate DB to the MDR DB.
    """
    bulk_import(user_initials, json_data_directory, skip_download_step)
