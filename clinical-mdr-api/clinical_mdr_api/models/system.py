"""System models."""

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SystemInformation(BaseModel):
    api_version: str = Field(
        ..., title="API version", description="Version of the API specification"
    )
    db_version: str = Field(
        ...,
        title="Database version",
        description="Version information from the Neo4j database the application is using",
    )
    db_name: str = Field(
        ...,
        title="Database name",
        description="Name of the database the application is using",
    )
    build_id: str = Field(
        ...,
        title="Build identifier",
        description="The Build.BuildNumber identifier from the pipeline run",
    )
    commit_id: str | None = Field(
        None,
        title="VCS commit identifier",
        description="The reference to the repository state: the id of the last commit to the branch at build",
    )
    branch_name: str | None = Field(
        None,
        title="Repository branch name",
        description="Name of the VCS repository branch the app was built from",
    )
