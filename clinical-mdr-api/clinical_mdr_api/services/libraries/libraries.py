from clinical_mdr_api import exceptions
from clinical_mdr_api.repositories import libraries as libraries_repository


def get_libraries(is_editable: bool | None):
    return libraries_repository.find_all(is_editable)


def create(name: str, is_editable: bool):
    if libraries_repository.find_by_name(name):
        raise exceptions.ValidationException(f"Library '{name}' already exists")
    return libraries_repository.create(name, is_editable)
