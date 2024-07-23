"""
This script serves as the entry point for the pipeline step 'Import CT from CDISC DB into MDR DB'.

It is meant to be called e.g. via:

> `python -m pipenv run pipeline_step_import_ct_from_cdisc_db_into_mdr <user initials> <effective date>`

The script expects the following parameters:

1. <user initials> - The Novo Nordisk user initials of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <effective date> - The CDISC effective date to be imported.
"""
from mdr_standards_import.scripts.utils import get_effective_date, get_user_initials
from mdr_standards_import.scripts.wrapper.cdisc_ct.wrapper_import_from_cdisc_db_into_mdr import (
    wrapper_import_cdisc_ct_from_cdisc_db_into_mdr,
)

wrapper_import_cdisc_ct_from_cdisc_db_into_mdr(
    get_user_initials(1), get_effective_date(2)
)
