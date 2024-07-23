"""
Tests for /standards/sponsor-models endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable,
)
from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_model_catalogue_name: str
data_model: DataModel
data_model_ig: DataModelIG
dataset_classes: list[DatasetClass]
variable_classes: list[VariableClass]
datasets: list[Dataset]
dataset_variables: list[DatasetVariable]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "sponsor-models.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global data_model_catalogue_name
    global data_model
    global data_model_ig
    global dataset_classes
    global variable_classes
    global datasets
    global dataset_variables

    data_model_catalogue_name = TestUtils.create_data_model_catalogue(
        name="DataModelCatalogue name"
    )
    data_model = TestUtils.create_data_model(name="DataModel A")
    data_model_ig = TestUtils.create_data_model_ig(
        name="DataModelIG A", version_number="1"
    )
    dataset_classes = [
        TestUtils.create_dataset_class(
            label=f"DatasetClass{i} label",
            data_model_uid=data_model.uid,
            data_model_catalogue_name=data_model_catalogue_name,
        )
        for i in range(3)
    ]
    variable_classes = [
        TestUtils.create_variable_class(
            label=f"VariableClass{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            dataset_class_uid=dataset_classes[i].uid,
            data_model_name=data_model.uid,
            data_model_version=data_model.version_number,
        )
        for i in range(3)
    ]
    datasets = [
        TestUtils.create_dataset(
            label=f"Dataset{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_ig_uid=data_model_ig.uid,
            data_model_ig_version_number=data_model_ig.version_number,
            implemented_dataset_class_name=dataset_classes[i].uid,
        )
        for i in range(3)
    ]
    dataset_variables = [
        TestUtils.create_dataset_variable(
            label=f"DatasetVariable{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_ig_name=data_model_ig.uid,
            data_model_ig_version=data_model_ig.version_number,
            dataset_uid=datasets[i].uid,
            class_variable_uid=variable_classes[i].uid,
        )
        for i in range(3)
    ]

    yield

    drop_db(db_name)


def test_post_sponsor_model(api_client):
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": 1,
        },
    )
    res = response.json()
    assert response.status_code == 201
    assert (
        res["name"]
        == f"{data_model_ig.uid.lower()}_mastermodel_{data_model_ig.version_number}_NN1"
    )
    assert res["version"] == data_model_ig.version_number


def test_post_dataset_class(api_client):
    url = "/standards/sponsor-models/dataset-classes"
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    common_params = {
        "dataset_class_uid": dataset_classes[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "is_basic_std": True,
    }

    # Making a POST request to create a dataset class with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == common_params["dataset_class_uid"]

    # Making another POST request to create a dataset class with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )

    assert response.status_code == 400
    res = response.json()
    assert (
        res["message"]
        == "The given Sponsor Model version non_existent_sponsor_model does not exist in the database."
    )

    # Making another POST request to create a dataset class with a dataset class which does not exist in CDISC
    params3 = common_params.copy()
    params3["dataset_class_uid"] = "NewDatasetClass"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == params3["dataset_class_uid"]


def test_post_variable_class(api_client):
    url = "/standards/sponsor-models/variable-classes"

    # Create a sponsor model
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    # Create a sponsor model dataset class
    dataset_class = TestUtils.create_sponsor_dataset_class(
        dataset_class_uid=dataset_classes[0].uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
    )

    common_params = {
        "dataset_class_uid": dataset_class.uid,
        "variable_class_uid": variable_classes[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "is_basic_std": True,
        "order": 10,
    }

    # Making a POST request to create a variable class with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == common_params["variable_class_uid"]
    assert res["order"] == common_params["order"]

    # Making another POST request to create a variable class with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )

    assert response.status_code == 400
    res = response.json()
    assert (
        res["message"]
        == f"The DatasetClass {common_params['dataset_class_uid']} is not instantiated in this version of the sponsor model."
    )

    # Making another POST request to create a variable class with a dataset class which does not exist in CDISC
    params3 = common_params.copy()
    params3["dataset_class_uid"] = "NonexistentDatasetClass"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert response.status_code == 400
    assert (
        res["message"]
        == f"The DatasetClass {params3['dataset_class_uid']} is not instantiated in this version of the sponsor model."
    )

    # Making another POST request to create a variable class with a variable class which does not exist in CDISC
    params4 = common_params.copy()
    params4["variable_class_uid"] = "NonexistentVariableClass"
    response = api_client.post(
        url,
        json=params4,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == params4["variable_class_uid"]


def test_post_dataset(api_client):
    url = "/standards/sponsor-models/datasets"
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    common_params = {
        "dataset_uid": datasets[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "is_basic_std": True,
        "enrich_build_order": 10,
    }

    # Making a POST request to create a dataset with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == common_params["dataset_uid"]
    assert res["enrich_build_order"] == common_params["enrich_build_order"]

    # Making another POST request to create a dataset with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )

    assert response.status_code == 400
    res = response.json()
    assert (
        res["message"]
        == "The given Sponsor Model version non_existent_sponsor_model does not exist in the database."
    )

    # Making another POST request to create a dataset with a dataset that does not exist in CDISC
    params3 = common_params.copy()
    params3["dataset_uid"] = "NewDataset"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == params3["dataset_uid"]


def test_post_dataset_variable(api_client):
    url = "/standards/sponsor-models/dataset-variables"

    # Create a sponsor model
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    # Create a sponsor dataset
    dataset = TestUtils.create_sponsor_dataset(
        dataset_uid=datasets[0].uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
    )

    common_params = {
        "dataset_uid": dataset.uid,
        "dataset_variable_uid": dataset_variables[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "is_basic_std": True,
        "order": 20,
    }

    # Making a POST request to create a dataset variable with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == common_params["dataset_variable_uid"]
    assert res["order"] == common_params["order"]

    # Making another POST request to create a dataset variable with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )
    assert response.status_code == 400
    res = response.json()
    assert (
        res["message"]
        == f"The Dataset {common_params['dataset_uid']} is not instantiated in this version of the sponsor model."
    )

    # Making another POST request to create a dataset variable with a dataset class which does not exist in CDISC
    params3 = common_params.copy()
    params3["dataset_uid"] = "NonexistentDataset"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert response.status_code == 400
    assert (
        res["message"]
        == f"The Dataset {params3['dataset_uid']} is not instantiated in this version of the sponsor model."
    )

    # Making another POST request to create a dataset variable with a dataset variable which does not exist in CDISC
    params4 = common_params.copy()
    params4["dataset_variable_uid"] = "NonexistentDatasetVariable"
    response = api_client.post(
        url,
        json=params4,
    )
    res = response.json()
    assert response.status_code == 201
    assert res["uid"] == params4["dataset_variable_uid"]
