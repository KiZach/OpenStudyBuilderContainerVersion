from typing import Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TopicCdDef(BaseModel):
    lb: str = Field(None, title="lb", description="Label")
    topic_cd: str = Field(None, title="topic_cd", description="Topic Code")
    short_topic_cd: str = Field(
        None, title="short_topic_cd", description="Short Topic Code"
    )
    description: str = Field(
        None, title="description", description="Description", nullable=True
    )
    molecular_weight: float = Field(
        None, title="molecular_weight", description="Molecular Weight", nullable=True
    )
    sas_display_format: str = Field(
        None,
        title="sas_display_format",
        description="SAS Display Format",
        nullable=True,
    )
    general_domain_class: str = Field(
        None,
        title="general_domain_class",
        description="General Domain Class",
        nullable=True,
    )
    sub_domain_class: str = Field(
        None, title="sub_domain_class", description="Sub Domain Class", nullable=True
    )
    sub_domain_type: str = Field(
        None, title="sub_domain_type", description="Sub Domain Type", nullable=True
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            lb=query_result["lb"],
            topic_cd=query_result["topic_cd"],
            short_topic_cd=query_result["short_topic_cd"],
            description=query_result["description"],
            molecular_weight=query_result["molecular_weight"],
            sas_display_format=query_result["sas_display_format"],
            general_domain_class=query_result["general_domain_class"],
            sub_domain_class=query_result["sub_domain_class"],
            sub_domain_type=query_result["sub_domain_type"],
        )


class MetaData(BaseModel):
    dataset_name: str = Field(None, title="dataset_name", description="name of dataset")
    dataset_label: str = Field(
        None, title="dataset_label", description="label of dataset"
    )
    name: str = Field(None, title="name", description="name of variable")
    type: str = Field(None, title="type", description="type of variable")
    length: float = Field(None, title="length", description="length of variable")
    label: str = Field(None, title="label", description="label of variable")
    format: str = Field(None, title="format", description="SAS format of variable")
    informat: str = Field(
        None, title="informat", description="SAS informat of variable"
    )

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            dataset_name=query_result["dataset_name"],
            dataset_label=query_result["dataset_label"],
            name=query_result["name"],
            type=query_result["type"],
            length=query_result["length"],
            label=query_result["label"],
            format=query_result["format"],
            informat=query_result["informat"],
        )


CT_SCOPE = "CT scope"
CT_VERSION = "CT version"
PACKAGE_NAME = "Package name"


class CDISCCTVer(BaseModel):
    ct_scope: str = Field(None, title=CT_SCOPE, description=CT_SCOPE)
    ct_ver: str = Field(None, title="CT version", description=CT_VERSION)
    pkg_nm: str = Field(None, title=PACKAGE_NAME, description=PACKAGE_NAME)

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_scope=query_result["ct_scope"],
            ct_ver=query_result["ct_ver"],
            pkg_nm=query_result["pkg_nm"],
        )


class CDISCCTPkg(BaseModel):
    pkg_scope: str = Field(None, title="Package scope", description=CT_SCOPE)
    pkg_nm: str = Field(None, title=PACKAGE_NAME, description=PACKAGE_NAME)

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(pkg_scope=query_result["pkg_scope"], pkg_nm=query_result["pkg_nm"])


class CDISCCTList(BaseModel):
    ct_cd_list_cd: str = Field(None, title="CT codelist", description="CT codelist")

    ct_cd_list_extensible: str = Field(
        None, title="CT codelist extensible", description="Is CT codelist extensible"
    )
    ct_cd_list_nm: str = Field(
        None, title="CT codelist name", description="Name of CT codelist"
    )
    ct_cd_list_submval: str = Field(
        None,
        title="CT codelist submission value",
        description="CT codelist submission value",
    )
    ct_scope: str = Field(None, title=CT_SCOPE, description=CT_SCOPE)
    ct_ver: str = Field(None, title=CT_VERSION, description=CT_VERSION)
    definition: str = Field(None, title="definition", description="definition")
    nci_pref_term: str = Field(
        None, title="NCI preferred term", description="NCI preferred term"
    )
    pkg_nm: str = Field(None, title=PACKAGE_NAME, description=PACKAGE_NAME)
    synonyms: str = Field(None, title="Synonyms", description="Synonyms")

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_cd_list_cd=query_result["ct_cd_list_cd"],
            ct_cd_list_extensible=query_result["ct_cd_list_extensible"],
            ct_cd_list_nm=query_result["ct_cd_list_nm"],
            ct_cd_list_submval=query_result["ct_cd_list_submval"],
            ct_scope=query_result["ct_scope"],
            ct_ver=query_result["ct_ver"],
            definition=query_result["definition"],
            nci_pref_term=query_result["nci_pref_term"],
            pkg_nm=query_result["pkg_nm"],
            synonyms=query_result["synonyms"],
        )


class CDISCCTVal(BaseModel):
    ct_cd: str = Field(None, title="CT Code", description="CT Code")
    ct_cd_list_submval: str = Field(
        None,
        title="CT codelist submission value",
        description="CT codelist submission value",
    )
    ct_scope: str = Field(None, title=CT_SCOPE, description=CT_SCOPE)
    ct_submval: str = Field(
        None, title="CT code submission value", description="CT code submission value"
    )
    ct_ver: str = Field(None, title=CT_VERSION, description=CT_VERSION)
    definition: str = Field(None, title="definition", description="definition")
    nci_pref_term: str = Field(
        None, title="NCI preferred term", description="NCI preferred term"
    )
    pkg_nm: str = Field(None, title=PACKAGE_NAME, description=PACKAGE_NAME)
    synonyms: str = Field(None, title="Synonyms", description="Synonyms")

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_cd=query_result["ct_cd"],
            ct_cd_list_submval=query_result["ct_cd_list_submval"],
            ct_scope=query_result["ct_scope"],
            ct_submval=query_result["ct_submval"],
            ct_ver=query_result["ct_ver"],
            definition=query_result["definition"],
            nci_pref_term=query_result["nci_pref_term"],
            pkg_nm=query_result["pkg_nm"],
            synonyms=query_result["synonyms"],
        )
