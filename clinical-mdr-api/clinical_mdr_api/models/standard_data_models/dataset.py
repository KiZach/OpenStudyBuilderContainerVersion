from pydantic import Field

from clinical_mdr_api.models.standard_data_models.variable_class import (
    SimpleDatasetClass,
)
from clinical_mdr_api.models.utils import BaseModel


class SimpleDataModelIG(BaseModel):
    ordinal: str | None = Field(
        None,
        title="ordinal",
        description="ordinal",
    )
    data_model_ig_name: str = Field(
        ...,
        title="data_model_ig_name",
        description="The name of the data model ig",
    )


class Dataset(BaseModel):
    class Config:
        orm_mode = True

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
    catalogue_name: str = Field(
        ...,
        title="catalogue",
        description="catalogue",
    )
    implemented_dataset_class: SimpleDatasetClass | None = Field(
        None,
        title="implements_dataset_class",
        description="implements_dataset_class",
        nullable=True,
    )
    data_model_ig: SimpleDataModelIG = Field(
        ...,
        title="data_model_ig",
        description="data_model_ig",
    )

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            catalogue_name=input_dict.get("catalogue_name"),
            parent_class=input_dict.get("parent_class_name"),
            implemented_dataset_class=SimpleDatasetClass(
                ordinal=input_dict.get("implemented_dataset_class").get("ordinal"),
                dataset_class_name=input_dict.get("implemented_dataset_class").get(
                    "dataset_class_name"
                ),
            )
            if input_dict.get("implemented_dataset_class")
            else None,
            data_model_ig=SimpleDataModelIG(
                ordinal=input_dict.get("data_model_ig").get("ordinal"),
                data_model_ig_name=input_dict.get("data_model_ig").get(
                    "data_model_ig_name"
                ),
            ),
        )
