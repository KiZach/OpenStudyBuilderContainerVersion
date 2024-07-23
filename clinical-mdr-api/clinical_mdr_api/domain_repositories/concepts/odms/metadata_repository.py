from neomodel import db

from clinical_mdr_api.exceptions import NotFoundException


class MetadataRepository:
    CSV_EXPORT_QUERY = """
    CALL apoc.export.csv.query(query, null, {stream:true, params:{target_uid: $target_uid}})
    YIELD data, rows
    RETURN data, rows;"""

    OPTIONAL_FORM_MATCH = """
    OPTIONAL MATCH (OdmStudyEventRoot)
    -[:FORM_REF]->(OdmFormRoot:OdmFormRoot)
    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmFormValue:OdmFormValue)
    CALL {
        WITH OdmFormRoot, OdmFormValue
        MATCH (OdmFormRoot)-[hv:HAS_VERSION]-(OdmFormValue)
        WHERE hv.status in ['Final', 'Retired'] 
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmFormLatest
    }
    """
    OPTIONAL_ITEM_GROUP_MATCH = """
    OPTIONAL MATCH (OdmFormRoot)
    -[:ITEM_GROUP_REF]->(OdmItemGroupRoot:OdmItemGroupRoot)
    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemGroupValue:OdmItemGroupValue)
    CALL {
        WITH OdmItemGroupRoot, OdmItemGroupValue
        MATCH (OdmItemGroupRoot)-[hv:HAS_VERSION]-(OdmItemGroupValue)
        WHERE hv.status in ['Final', 'Retired'] 
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmItemGroupLatest
    }
    """
    OPTIONAL_ITEM_MATCH = """
    OPTIONAL MATCH (OdmItemGroupRoot)
    -[:ITEM_REF]->(OdmItemRoot:OdmItemRoot)
    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemValue:OdmItemValue)
    CALL {
        WITH OdmItemRoot, OdmItemValue
        MATCH (OdmItemRoot)-[hv:HAS_VERSION]-(OdmItemValue)
        WHERE hv.status in ['Final', 'Retired']
        WITH hv
        ORDER BY
            toInteger(split(hv.version, '.')[0]) ASC,
            toInteger(split(hv.version, '.')[1]) ASC,
            hv.end_date ASC,
            hv.start_date ASC
        WITH collect(hv) as hvs
        RETURN last(hvs) as OdmItemLatest
    }
    """
    OPTIONAL_UNIT_DEFINITION_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_UNIT_DEFINITION]->(UnitDefinitionRoot:UnitDefinitionRoot)
    -[:LATEST]->(UnitDefinitionValue:UnitDefinitionValue)
    """
    OPTIONAL_CODELIST_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_CODELIST]->(CTCodelistRoot:CTCodelistRoot)
    -[:HAS_ATTRIBUTES_ROOT]->(CTCodelistAttributesRoot:CTCodelistAttributesRoot)
    -[:LATEST]->(CTCodelistAttributesValue:CTCodelistAttributesValue)
    """
    OPTIONAL_CODELIST_TERM_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_CODELIST_TERM]->(CTTermRoot:CTTermRoot)
    -[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot:CTTermAttributesRoot)
    -[:LATEST]->(CTTermAttributesValue:CTTermAttributesValue)
    """

    STUDY_EVENT_NAME_RETURN = "OdmStudyEventValue.name AS StudyEvent_Name"
    STUDY_EVENT_VERSION_RETURN = "OdmStudyEventLatest.version AS StudyEvent_Version"
    FORM_NAME_RETURN = "OdmFormValue.name AS Form_Name"
    FORM_REPEATING_RETURN = """
    (CASE WHEN OdmFormValue.repeating IS NULL THEN ''
    WHEN OdmFormValue.repeating THEN  'yes' ELSE 'no' END) AS Form_Repeating
    """
    FORM_VERSION_RETURN = "OdmFormLatest.version AS Form_Version"
    ITEM_GROUP_NAME_RETURN = "OdmItemGroupValue.name AS ItemGroup_Name"
    ITEM_GROUP_VERSION_RETURN = "OdmItemGroupLatest.version AS ItemGroup_Version"
    ITEM_NAME_RETURN = "OdmItemValue.name AS Item_Name"
    ITEM_DATATYPE_RETURN = "OdmItemValue.datatype AS Item_Datatype"
    ITEM_VERSION_RETURN = "OdmItemLatest.version AS Item_Version"
    ITEM_UNIT_RETURN = (
        "apoc.text.join(COLLECT(DISTINCT UnitDefinitionValue.name), '|') as Item_Units"
    )
    ITEM_CODELIST_RETURN = "CTCodelistAttributesValue.name AS Item_Codelist"
    ITEM_TERM_RETURN = "apoc.text.join(COLLECT(DISTINCT CTTermAttributesValue.code_submission_value), '|') as Item_Terms"

    def get_odm_study_event(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmStudyEventRoot:OdmStudyEventRoot {{uid: $target_uid}})
                    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmStudyEventValue:OdmStudyEventValue)
                    CALL {{
                        WITH OdmStudyEventRoot, OdmStudyEventValue
                        MATCH (OdmStudyEventRoot)-[hv:HAS_VERSION]-(OdmStudyEventValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmStudyEventLatest
                    }}
                    {self.OPTIONAL_FORM_MATCH}
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.STUDY_EVENT_NAME_RETURN},
                    {self.STUDY_EVENT_VERSION_RETURN},
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(
                f"ODM Study Event with uid {target_uid} does not exist."
            )

        return result[0][0]

    def get_odm_form(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmFormRoot:OdmFormRoot {{uid: $target_uid}})-[:LATEST_FINAL|LATEST_RETIRED]->(OdmFormValue:OdmFormValue)
                    CALL {{
                        WITH OdmFormRoot, OdmFormValue
                        MATCH (OdmFormRoot)-[hv:HAS_VERSION]-(OdmFormValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmFormLatest
                    }}
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(f"ODM Form with uid {target_uid} does not exist.")

        return result[0][0]

    def get_odm_item_group(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmItemGroupRoot:OdmItemGroupRoot {{uid: $target_uid}})
                    -[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemGroupValue:OdmItemGroupValue)
                    CALL {{
                        WITH OdmItemGroupRoot, OdmItemGroupValue
                        MATCH (OdmItemGroupRoot)-[hv:HAS_VERSION]-(OdmItemGroupValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmItemGroupLatest
                    }}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(
                f"ODM Item Group with uid {target_uid} does not exist."
            )

        return result[0][0]

    def get_odm_item(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmItemRoot:OdmItemRoot {{uid: $target_uid}})-[:LATEST_FINAL|LATEST_RETIRED]->(OdmItemValue:OdmItemValue)
                    CALL {{
                        WITH OdmItemRoot, OdmItemValue
                        MATCH (OdmItemRoot)-[hv:HAS_VERSION]-(OdmItemValue)
                        WHERE hv.status in ['Final', 'Retired']
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as OdmItemLatest
                    }}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(f"ODM Item with uid {target_uid} does not exist.")

        return result[0][0]
