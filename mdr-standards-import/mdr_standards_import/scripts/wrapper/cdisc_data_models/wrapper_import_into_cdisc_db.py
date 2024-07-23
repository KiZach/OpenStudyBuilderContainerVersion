from os import environ

from mdr_standards_import.scripts.download_json_data_from_cdisc_api import (
    download_data_model_json_data_from_cdisc_api,
)
from mdr_standards_import.scripts.import_scripts.cdisc_data_models.import_json_data_into_cdisc_db import (
    import_data_model_json_data_into_cdisc_db,
)
from mdr_standards_import.scripts.import_scripts.cdisc_data_models.import_csv_data_into_cdisc_db import (
    import_data_model_csv_data_into_cdisc_db,
)
from mdr_standards_import.scripts.utils import (
    get_cdisc_neo4j_driver,
    get_ordered_data_model_versions,
)


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")


def wrapper_import_cdisc_data_models_into_cdisc_db(
    user_initials: str, json_data_directory: str = "", skip_download_step: bool = False
):
    """
    Downloads the CDISC Standards Data Model versions from the CDISC REST API
    and calls the import step to transform the JSON files into the CDISC graph structure.
    It also calls the import step to load the lab specifications data into the CDISC graph structure.
    """
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()

    if skip_download_step:
        print(f"Skipping CDISC download step for Data models and IG.")
    else:
        download_data_model_json_data_from_cdisc_api(json_data_directory)

    versions = get_ordered_data_model_versions(json_data_directory)
    print(f"============================================")
    print(f"Found the following data model versions: {str(versions)}")
    for catalogue in versions:
        print(f"============================================")
        print(
            f"== Importing JSON data into the cdisc-DB='{CDISC_IMPORT_DATABASE}' for the catalogue='{catalogue}'."
        )
        for version_number in versions[catalogue]:
            print(f"==== Importing version {version_number}.")

            if catalogue in ["FBDE"]:
                import_data_model_csv_data_into_cdisc_db(
                    library="Sponsor",
                    catalogue=catalogue,
                    version_number=version_number,
                    data_directory=json_data_directory,
                    cdisc_import_neo4j_driver=cdisc_neo4j_driver,
                    cdisc_import_db_name=CDISC_IMPORT_DATABASE,
                    user_initials=user_initials,
                )
            elif catalogue in ["FBDEIG"]:
                # Already imported by above condition
                pass
            else:
                import_data_model_json_data_into_cdisc_db(
                    library="CDISC",
                    catalogue=catalogue,
                    version_number=version_number,
                    data_directory=json_data_directory,
                    cdisc_import_neo4j_driver=cdisc_neo4j_driver,
                    cdisc_import_db_name=CDISC_IMPORT_DATABASE,
                    user_initials=user_initials,
                )

    cdisc_neo4j_driver.close()
