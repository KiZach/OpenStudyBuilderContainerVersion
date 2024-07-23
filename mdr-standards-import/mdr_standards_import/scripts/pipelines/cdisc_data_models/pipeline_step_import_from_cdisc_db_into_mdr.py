"""
This script serves as the entry point for the pipeline step 'Import Data Models from CDISC DB into MDR DB'.

It is meant to be called e.g. via:

> `python -m pipenv run pipeline_step_import_data_models_from_cdisc_db_into_mdr <user initials> <effective date>`

The script expects the following parameters:

1. <user initials> - The Novo Nordisk user initials of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <effective date> - The CDISC effective date to be imported.
"""
from mdr_standards_import.scripts.utils import get_user_initials, get_directory_name
from mdr_standards_import.scripts.wrapper.cdisc_data_models.wrapper_import_from_cdisc_db_into_mdr import (
    wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr,
)

wrapper_import_cdisc_data_models_from_cdisc_db_into_mdr(
    get_user_initials(1), get_directory_name(2)
)
