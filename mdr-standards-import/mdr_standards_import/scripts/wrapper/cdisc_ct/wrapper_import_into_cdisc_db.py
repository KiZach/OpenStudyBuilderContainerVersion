from os import environ

from mdr_standards_import.scripts.download_json_data_from_cdisc_api import (
    download_ct_json_data_from_cdisc_api,
)
from mdr_standards_import.scripts.import_scripts.cdisc_ct.import_json_data_into_cdisc_db import (
    import_json_data_into_cdisc_db,
)
from mdr_standards_import.scripts.utils import (
    get_cdisc_neo4j_driver,
    get_ordered_package_dates,
)


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")


def wrapper_import_cdisc_ct_into_cdisc_db(
    user_initials: str, json_data_directory: str = "", skip_download_step: bool = False
):
    """
    Downloads the CDISC CT packages from the CDISC REST API
    and calls the import step to transform the JSON files into the CDISC CT graph structure.
    """
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()

    if skip_download_step:
        print(f"Skipping CDISC download step for CT.")
    else:
        download_ct_json_data_from_cdisc_api(json_data_directory)

    package_dates = get_ordered_package_dates(json_data_directory)
    print(f"Found the following dates: {str(package_dates)}")
    for effective_date in package_dates:
        print(f"============================================")
        print(
            f"== Importing JSON data into the cdisc-DB='{CDISC_IMPORT_DATABASE}' for the effective_date='{effective_date}'."
        )
        print(f"==")
        import_json_data_into_cdisc_db(
            effective_date,
            json_data_directory,
            cdisc_neo4j_driver,
            CDISC_IMPORT_DATABASE,
            user_initials,
        )

    cdisc_neo4j_driver.close()
