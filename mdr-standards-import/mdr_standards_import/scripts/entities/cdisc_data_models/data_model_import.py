import datetime
from mdr_standards_import.scripts.entities.cdisc_data_models.version import Version
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_type import (
    DataModelType,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_class import (
    DataModelClass,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_scenario import (
    DataModelScenario,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)


class DataModelImport:
    def __init__(self, library:str, catalogue: str, version_number: str, user_initials: str):
        self.import_date_time: str = datetime.datetime.now().astimezone().isoformat()
        self.library: str = library
        self.catalogue: str = catalogue
        self.version_number: str = version_number
        self.user_initials: str = user_initials
        self.automatic_resolution_done: bool = False

        self.__version: Version = None

        # a dictionary used as hash map where
        # - the key is the name of the class and
        # - the value is the Class object
        self.__classes: dict[str, DataModelClass] = dict()
        self.__scenarios: dict[str, DataModelScenario] = dict()
        self.__variables: dict[str, DataModelVariable] = dict()

    def get_version(self):
        return self.__version

    def add_version(self, version: Version):
        self.__version = version

    def get_type(self):
        return self.__data_model_type

    def set_type(self, data_model_type: DataModelType):
        self.__data_model_type = data_model_type

    def get_implements_data_model(self):
        return self.__implements_data_model

    def set_implements_data_model(self, data_model_href):
        self.__implements_data_model: str = data_model_href

    def get_classes(self):
        return self.__classes.values()

    def get_classes_as_dict(self):
        return self.__classes

    def get_variables_as_dict(self):
        return self.__variables

    def merge_class(self, name: str) -> DataModelClass:
        _class: DataModelClass = self.__classes.get(name, DataModelClass(name))
        self.__classes[name] = _class
        return _class

    def get_variables(self):
        return self.__variables.values()

    def merge_variable(self, href: str) -> DataModelVariable:
        _variable: DataModelVariable = self.__variables.get(
            href, DataModelVariable(href)
        )
        self.__variables[href] = _variable
        return _variable

    def get_scenarios(self):
        return self.__scenarios.values()

    def merge_scenario(self, href: str, class_name: str) -> DataModelScenario:
        _scenario: DataModelScenario = self.__scenarios.get(
            href, DataModelScenario(href)
        )
        self.__scenarios[href] = _scenario
        # If a class (dataset) already exists with the scenario's parent class name
        # Drop its variables. This is because when a class has a single scenario,
        # CDISC creates a duplicate variable by leaving it in the class file, with a different href.
        parent_class = self.get_classes_as_dict()[class_name]
        parent_class_variables = [v.href for v in parent_class.get_variables()]
        all_variables = self.get_variables_as_dict()
        [all_variables.pop(key) for key in parent_class_variables]
        parent_class.drop_variables()
        return _scenario
