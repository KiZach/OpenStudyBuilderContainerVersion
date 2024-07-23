from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleDataModel(BaseModel):
    data_model_name: str = Field(
        ...,
        title="data_model_name",
        description="data_model_name",
    )
    ordinal: str | None = Field(
        None,
        title="ordinal",
        description="ordinal",
    )


class SimpleDataset(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="uid",
    )
    dataset_name: str = Field(
        ...,
        title="dataset_name",
        description="dataset_name",
    )


class DatasetClass(BaseModel):
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
        title="catalogue_name",
        description="catalogue_name",
    )
    parent_class: str | None = Field(
        None, title="parent_class_name", description="parent_class_name", nullable=True
    )
    data_models: list[SimpleDataModel] = Field(...)

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            catalogue_name=input_dict.get("catalogue_name"),
            parent_class=input_dict.get("parent_class_name"),
            data_models=[
                SimpleDataModel(
                    data_model_name=data_model.get("data_model_name"),
                    ordinal=data_model.get("ordinal"),
                )
                for data_model in input_dict.get("data_models")
            ],
        )
