"""
This script serves as the entry point for the pipeline step 'Import CDISC CT into CDISC DB'.

This script is meant to be called e.g. via:

> `python -m pipenv run pipeline_step_import_cdisc_ct_into_cdisc_db <user initials> <JSON directory name> <skip download step>`

The script expects the following parameters:

1. <user initials> - The Novo Nordisk user initials of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"
3. <skip download step> - Optional, default "false". Denotes whether or not the download step is skipped. String, e.g. "true" or "false"
"""


from mdr_standards_import.scripts.wrapper.cdisc_ct.wrapper_import_into_cdisc_db import (
    wrapper_import_cdisc_ct_into_cdisc_db,
)
from mdr_standards_import.scripts.utils import (
    get_directory_name,
    get_skip_download_step,
    get_user_initials,
)

wrapper_import_cdisc_ct_into_cdisc_db(
    get_user_initials(1), get_directory_name(2, "cdisc_ct"), get_skip_download_step(3)
)
