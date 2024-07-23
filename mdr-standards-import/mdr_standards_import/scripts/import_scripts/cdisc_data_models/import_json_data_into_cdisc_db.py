import json, time, traceback
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
    DataModelType,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.version import Version

from os import listdir, path

from mdr_standards_import.scripts.repositories.repository import (
    await_indexes,
    create_indexes_if_not_existent,
    create_data_model_import_node,
    create_data_model_import,
)
from mdr_standards_import.scripts.exceptions.version_exists import VersionExists
from mdr_standards_import.scripts.utils import get_classes_directory_name


def print_summary(tx, import_id, start_time):
    result = tx.run(
        """
        MATCH (import:DataModelImport) WHERE id(import) = $import_id
        RETURN
            import.catalogue as catalogue,
            import.version_number as version_number,
            import.data_model_type as data_model_type
        """,
        import_id=import_id,
    ).single()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"==")
    print(f"== Summary for the import into the CDISC DB:")
    print(f"==")
    print(f"==      catalogue: {result.get('catalogue', 'n/a')}")
    print(f"==      version number: {result.get('version_number', 'n/a')}")
    print(f"==      type: {result.get('data_model_type', 'n/a')}")
    print(f"==")
    print(f"== Duration: {round(elapsed_time, 1)} seconds")


def finish_import(tx, import_id):
    tx.run(
        """
        MATCH (import:DataModelImport) WHERE id(import) = $import_id
        REMOVE import:Running
        """,
        import_id=import_id,
    ).single()


def import_data_model_json_data_into_cdisc_db(
    library: str,
    catalogue: str,
    version_number: str,
    data_directory: str,
    cdisc_import_neo4j_driver,
    cdisc_import_db_name: str,
    user_initials: str,
):
    """
    Import the new data found on disc into the intermediate CDISC database

    Args:
        catalogue (str): Data Model catalogue name
        version (str): version number
        data_directory (str): the path of the directory in which the JSON files reside;
        if this is relative, it needs to be relative to the location of this script
        cdisc_import_neo4j_driver : the Neo4j driver instance that is used in order to connect to the Neo4j DBMS
        that holds the cdisc-import database (cf. cdisc_import_db_name);
        https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Driver
        cdisc_import_db_name (str): the name of the Neo4j database in which the CDISC data is loaded
        in the first place (after it will be loaded into the default MDR db)
        user_initials (str): the initials of the user that triggers this step
    """

    try:
        start_time = time.time()
        dm_import = DataModelImport(
            library=library,
            catalogue=catalogue,
            version_number=version_number,
            user_initials=user_initials,
        )

        with cdisc_import_neo4j_driver.session(database="system") as session:
            session.run(
                "CREATE DATABASE $database IF NOT EXISTS", database=cdisc_import_db_name
            )

        with cdisc_import_neo4j_driver.session(
            database=cdisc_import_db_name
        ) as session:
            session.write_transaction(create_indexes_if_not_existent)
            session.write_transaction(await_indexes)

            filename = path.join(
                data_directory, catalogue, "models", f"{version_number}.json"
            )
            print(f"==  * Processing file: '{filename}'.")
            with open(filename, "r") as version_file:
                version_json_data = json.load(version_file)
                version = Version(dm_import, version_number=version_number)
                version.load_from_json_data(version_json_data)
                dm_import.set_type(DataModelType(version.data_model_type))
                dm_import.set_implements_data_model(version.get_implements_data_model())
                dm_import.add_version(version)
                classes_sub_directory = get_classes_directory_name(
                    version.data_model_type
                )
                classes_sub_directory_path = path.join(
                    data_directory, catalogue, classes_sub_directory, version_number
                )
                if path.exists(classes_sub_directory_path):
                    class_files = [
                        file_name
                        for file_name in listdir(classes_sub_directory_path)
                        if file_name.endswith(".json")
                    ]
                    print(f"===  * Found {len(class_files)} classes to process.")
                    for file_name in class_files:
                        with open(
                            path.join(classes_sub_directory_path, file_name), "r"
                        ) as class_file:
                            version.load_class_from_json_data(
                                class_json_data=json.load(class_file),
                                version_json_data=version_json_data,
                                catalogue=catalogue,
                            )

                    # TODO If the directory contains a scenarios subfolder, import them
                    # This creates scenarios and associated variables
                    scenario_sub_directory_path = path.join(
                        classes_sub_directory_path, "scenarios"
                    )
                    if path.exists(scenario_sub_directory_path):
                        scenario_files = [
                            file_name
                            for file_name in listdir(scenario_sub_directory_path)
                            if file_name.endswith(".json")
                        ]
                        print(
                            f"===  ** Additionally found {len(scenario_files)} scenarii to process."
                        )
                        for file_name in scenario_files:
                            with open(
                                path.join(scenario_sub_directory_path, file_name), "r"
                            ) as scenario_file:
                                version.load_scenario_from_json_data(
                                    scenario_json_data=json.load(scenario_file),
                                    catalogue=catalogue,
                                    data_model_type=version.data_model_type,
                                )
                else:
                    print(
                        f"===  * No classes or datasets found for the catalogue='{catalogue}' in version='{version_number}'."
                    )

            import_id = session.write_transaction(
                create_data_model_import_node, dm_import
            )
            create_data_model_import(dm_import, session)

            with session.begin_transaction() as tx:
                finish_import(tx, import_id)
                print_summary(tx, import_id, start_time)
                tx.commit()

            session.close()

    except VersionExists:
        print(
            f"== The `DataModelImport` node already exists. Skipping the import for the catalogue='{catalogue}' in version='{version_number}'."
        )
    except Exception as e:
        print(f"== Exception:")
        traceback.print_exception(type(e), e, e.__traceback__)
        print(
            f"== Aborting the import for the catalogue='{catalogue}' in version='{version_number}'."
        )
    finally:
        print(f"============================================")
