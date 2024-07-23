"""Common Role-Based Access Control dependencies as re-usable constants"""

from fastapi import Depends

from clinical_mdr_api.oauth.dependencies import RequiresAnyRole

ADMIN_READ = Depends(RequiresAnyRole({"Admin.Read"}))
ADMIN_WRITE = Depends(RequiresAnyRole({"Admin.Write"}))
LIBRARY_READ = Depends(RequiresAnyRole({"Library.Read"}))
LIBRARY_WRITE = Depends(RequiresAnyRole({"Library.Write"}))
STUDY_READ = Depends(RequiresAnyRole({"Study.Read"}))
STUDY_WRITE = Depends(RequiresAnyRole({"Study.Write"}))
LIBRARY_WRITE_OR_STUDY_WRITE = Depends(
    RequiresAnyRole({"Library.Write", "Study.Write"})
)
ANY = Depends(
    RequiresAnyRole({"Library.Write", "Study.Write", "Library.Read", "Study.Read"})
)
