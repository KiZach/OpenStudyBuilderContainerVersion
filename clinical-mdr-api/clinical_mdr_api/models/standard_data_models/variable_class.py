from pydantic import Field

from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    SimpleMappingTarget,
)
from clinical_mdr_api.models.utils import BaseModel


class SimpleReferencedCodelist(BaseModel):
    uid: str | None = Field(
        None,
        title="uid",
        description="The uid of the referenced codelist",
    )
    name: str | None = Field(
        None,
        title="uid",
        description="The name of the referenced codelist",
    )


class SimpleDatasetClass(BaseModel):
    ordinal: str | None = Field(
        None,
        title="ordinal",
        description="ordinal",
    )
    dataset_class_name: str | None = Field(
        None,
        title="uid",
        description="The name of the dataset class",
    )


class SimpleVariableClass(BaseModel):
    uid: str | None = Field(
        None,
        title="uid",
        description="uid",
    )
    name: str | None = Field(
        None,
        title="name",
        description="name",
    )


class VariableClass(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The uid of the dataset",
    )
    label: str = Field(
        ...,
        title="label",
        description="The label of the dataset",
    )
    title: str = Field(
        ...,
        title="title",
        description="The title of the dataset",
    )
    description: str | None = Field(
        None, title="description", description="description", nullable=True
    )
    implementation_notes: str | None = Field(
        None,
        title="implementation_notes",
        description="implementation_notes",
        nullable=True,
    )
    mapping_instructions: str | None = Field(
        None,
        title="mapping_instructions",
        description="mapping_instructions",
        nullable=True,
    )
    core: str | None = Field(None, title="core", description="core", nullable=True)
    completion_instructions: str | None = Field(
        None,
        title="completion_instructions",
        description="completion_instructions",
        nullable=True,
    )
    prompt: str | None = Field(
        None, title="prompt", description="prompt", nullable=True
    )
    question_text: str | None = Field(
        None, title="question_text", description="question_text", nullable=True
    )
    simple_datatype: str | None = Field(
        None,
        title="simple_datatype",
        description="simple_datatype",
    )
    role: str | None = Field(None, title="role", description="role", nullable=True)
    described_value_domain: str | None = Field(
        None,
        title="described_value_domain",
        description="described_value_domain",
        nullable=True,
    )
    notes: str | None = Field(None, title="notes", description="notes", nullable=True)
    usage_restrictions: str | None = Field(
        None,
        title="usage_restrictions",
        description="usage_restrictions",
        nullable=True,
    )
    examples: str | None = Field(
        None, title="examples", description="examples", nullable=True
    )
    dataset_class: SimpleDatasetClass = Field(...)
    dataset_variable_name: str | None = Field(
        None,
        title="dataset_variable_name",
        description="dataset_variable_name",
        nullable=True,
    )
    catalogue_name: str = Field(
        ...,
        title="catalogue",
        description="catalogue",
    )
    data_model_names: list[str] = Field(
        ...,
        title="Versions of associated data models",
        description="Versions of associated data models",
    )
    has_mapping_target: SimpleMappingTarget | None = Field(None, nullable=True)
    referenced_codelist: SimpleReferencedCodelist | None = Field(None, nullable=True)
    qualifies_variable: SimpleVariableClass | None = Field(None, nullable=True)

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            implementation_notes=input_dict.get("standard_value").get(
                "implementation_notes"
            ),
            mapping_instructions=input_dict.get("standard_value").get(
                "mapping_instructions"
            ),
            core=input_dict.get("standard_value").get("core"),
            completion_instructions=input_dict.get("standard_value").get(
                "completion_instructions"
            ),
            prompt=input_dict.get("standard_value").get("prompt"),
            question_text=input_dict.get("standard_value").get("question_text"),
            simple_datatype=input_dict.get("standard_value").get("simple_datatype"),
            role=input_dict.get("standard_value").get("role"),
            described_value_domain=input_dict.get("standard_value").get(
                "described_value_domain"
            ),
            notes=input_dict.get("standard_value").get("notes"),
            usage_restrictions=input_dict.get("standard_value").get(
                "usage_restrictions"
            ),
            examples=input_dict.get("standard_value").get("examples"),
            catalogue_name=input_dict.get("catalogue_name"),
            dataset_class=SimpleDatasetClass(
                dataset_class_name=input_dict.get("dataset_class").get(
                    "dataset_class_name"
                ),
                ordinal=input_dict.get("dataset_class").get("ordinal"),
            ),
            dataset_variable_name=input_dict.get("dataset_variable_name"),
            data_model_names=input_dict.get("data_model_names"),
            referenced_codelist=SimpleReferencedCodelist(
                uid=input_dict.get("referenced_codelist").get("uid"),
                name=input_dict.get("referenced_codelist").get("name"),
            )
            if input_dict.get("referenced_codelist")
            else None,
            has_mapping_target=SimpleMappingTarget(
                uid=input_dict.get("has_mapping_target").get("uid"),
                name=input_dict.get("has_mapping_target").get("name"),
            )
            if input_dict.get("has_mapping_target")
            else None,
            qualifies_variable=SimpleVariableClass(
                uid=input_dict.get("qualifies_variable").get("uid"),
                name=input_dict.get("qualifies_variable").get("name"),
            )
            if input_dict.get("qualifies_variable")
            else None,
        )
