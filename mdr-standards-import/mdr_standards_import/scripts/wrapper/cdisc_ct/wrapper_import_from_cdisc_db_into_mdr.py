from os import environ
from mdr_standards_import.scripts.import_scripts.cdisc_ct.import_into_mdr_db import (
    import_from_cdisc_db_into_mdr,
)
from mdr_standards_import.scripts.utils import (
    get_cdisc_neo4j_driver,
    get_mdr_neo4j_driver,
)


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc")
MDR_DATABASE = environ.get("NEO4J_MDR_DATABASE", "neo4j")


def wrapper_import_cdisc_ct_from_cdisc_db_into_mdr(
    user_initials: str, effective_date: str
):
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()
    mdr_neo4j_driver = get_mdr_neo4j_driver()

    print(f"============================================")
    print(
        f"== Importing from the cdisc-DB='{CDISC_IMPORT_DATABASE}' into the MDR-DB='{MDR_DATABASE}' for the effective_date='{effective_date}'..."
    )
    print(f"==")
    import_from_cdisc_db_into_mdr(
        effective_date,
        cdisc_neo4j_driver,
        CDISC_IMPORT_DATABASE,
        mdr_neo4j_driver,
        MDR_DATABASE,
        user_initials,
    )

    mdr_neo4j_driver.close()
    cdisc_neo4j_driver.close()
