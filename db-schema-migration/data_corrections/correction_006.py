""" PRD Data Corrections, for release 1.6"""

import os

from migrations.utils.utils import get_logger
from data_corrections.utils.utils import (
    get_db_driver,
    run_cypher_query,
    print_counters_table,
    capture_changes,
    save_md_title,
)

# import pytest
# pytest.register_assert_rewrite("verifications.correction_verification_006")

from verifications import correction_verification_006

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.6"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    delete_unwanted_studies(DB_DRIVER, LOGGER, run_label)
    remove_na_version_properties(DB_DRIVER, LOGGER, run_label)
    add_missing_end_dates(DB_DRIVER, LOGGER, run_label)
    adjust_late_end_dates(DB_DRIVER, LOGGER, run_label)
    adjust_cdisc_has_had_terms(DB_DRIVER, LOGGER, run_label)
    remove_duplicated_terms_in_objective_cat(DB_DRIVER, LOGGER, run_label)


@capture_changes(task_level=1)
def delete_unwanted_study(db_driver, log, run_label, study_number):
    """
    ## Delete one complete study

    See `delete_unwanted_studies` for details.
    """
    desc = f"Deleting study number {study_number} from the database"
    log.info(f"Run: {run_label}, {desc}")

    # This query deletes a complete study from the database
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sr:StudyRoot)-[hsv]-(sv:StudyValue)
        WHERE (sr)--(:StudyValue {study_number: $study_number}) 
        OPTIONAL MATCH (sr)-[at:AUDIT_TRAIL]->(sa:StudyAction)
        OPTIONAL MATCH (sa)-[before_after_sel:BEFORE|AFTER]->(ss:StudySelection)
        DETACH DELETE ss
        WITH *
        OPTIONAL MATCH (sv)-[hsf]->(sf:StudyField)
        DETACH DELETE sf
        WITH *
        OPTIONAL MATCH (sv)-[hss]->(ss2:StudySelection)
        DETACH DELETE ss2
        DETACH DELETE sr, sv, sa
        """,
        {"study_number": study_number},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    docs_only=True, verify_func=correction_verification_006.test_delete_unwanted_studies,
    has_subtasks=True
)
def delete_unwanted_studies(db_driver, log, run_label):
    """
    ## Remove unwanted studies

    ### Change Description
    Some studies were imported into the production environment that should not be there.
    These are either test studies or related to the NN304 project.

    ### Nodes and relationships affected
    - All study nodes for the following study numbers are deleted:
      - Project NN304:
        - 1335, 1336, 1337, 1372, 1373, 1374, 1375
        - 1379, 1385, 1430, 1431, 1447, 1448, 1476
        - 1477, 1530, 1558, 1569, 1582, 1595, 1604
        - 1630, 1632, 1659, 1687, 1689, 1690, 1768
        - 1833, 2175, 3511, 3785, 4093
      - Test or demo:
        - 0, 0001, 9000, 9001, 9002, 9004, 9999
    - Expected changes: ~3500 nodes deleted, ~10000 relationships deleted
    """

    desc = f"Deleting unwanted studies from the database"
    log.info(f"Run: {run_label}, {desc}")

    unwanted = [
        ## NN304 project
        "1335",
        "1336",
        "1337",
        "1372",
        "1373",
        "1374",
        "1375",
        "1379",
        "1385",
        "1430",
        "1431",
        "1447",
        "1448",
        "1476",
        "1477",
        "1530",
        "1558",
        "1569",
        "1582",
        "1595",
        "1604",
        "1630",
        "1632",
        "1659",
        "1687",
        "1689",
        "1690",
        "1768",
        "1833",
        "2175",
        "3511",
        "3785",
        "4093",
        # Dummy studies
        "0",
        "0001",
        "9000",
        "9001",
        "9002",
        "9004",
        "9999",
    ]
    any_did_update = False
    for study_number in unwanted:
        did_update = delete_unwanted_study(db_driver, log, run_label, study_number)
        any_did_update = any_did_update or did_update
    return any_did_update


@capture_changes(
    verify_func=correction_verification_006.test_remove_na_version_properties
)
def remove_na_version_properties(db_driver, log, run_label):
    """
    ## Remove versioning properties of NA template parameter value LATEST_FINAL

    ### Change Description
    The neo4j init script creates an "NA" template parameter
    with versioning properties on the `LATEST_FINAL` relationship.
    These should not exist as the versioning is carried by the `HAS_VERSION` relationship.

    - [Related PR](https://dev.azure.com/novonordiskit/Clinical-MDR/_git/neo4j-mdr-db/pullrequest/112369)

    ### Nodes and relationships affected
    - `LATEST_FINAL` from `TemplateParameterValueRoot` node with uid "NA"
    - Expected changes: 6 relationship properties deleted
    """

    desc = "Deleting unwanted versioning properties for NA TemplateParameterValueRoot"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:TemplateParameterValueRoot {uid: "NA"})-[lf:LATEST_FINAL]-()
        SET lf = {}
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(verify_func=correction_verification_006.test_add_missing_end_dates)
def add_missing_end_dates(db_driver, log, run_label):
    """
    ## Add missing end date on HAS_VERSION relationships that are not the latest version.

    ### Change Description
    When a new version of an item is created the `HAS_VERSION`
    linking to the previous version must get an end date.
    There are a few old items where this has not worked.
    This correction fixes this by setting the missing end date
    to the start date of the following version.

    ### Nodes and relationships affected
    - Non-latest `HAS_VERSION` between `nnnRoot` and `nnnValue`, with missing `end_date` property.
    - Expected changes: 1 relationship property added
    """

    desc = "Adding end dates for HAS_VERSION relationships that are not the latest"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (root)-[:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN [
            "ClassVariableRoot",
            "DatasetClassRoot",
            "DatasetRoot",
            "DatasetScenarioRoot",
            "DatasetVariableRoot",
            "StudyRoot"
        ])
        CALL {
            WITH root
            MATCH (root)-[hv:HAS_VERSION]-() 
            WITH hv
            // Sort by version and dates
            ORDER BY
                toInteger(split(hv.version, '.')[0]) DESC,
                toInteger(split(hv.version, '.')[1]) DESC,
                hv.end_date DESC,
                hv.start_date DESC
            WITH collect(hv) as has_versions
            UNWIND RANGE(1, size(has_versions)) as i
                WITH has_versions, has_versions[i] as v, has_versions[i-1] as vp
                WHERE v.end_date IS NULL
                SET v.end_date = vp.start_date
            }
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(verify_func=correction_verification_006.test_adjust_late_end_dates)
def adjust_late_end_dates(db_driver, log, run_label):
    """
    ## Adjust too late end date on HAS_VERSION relationships that are not the latest version.

    ### Change Description
    When a new version of an item is created the `HAS_VERSION`
    linking to the previous version must get an end date.
    There are a few old items where the end date is a
    fraction of a second later than the start date of the next version.
    This causes a slight overlap of versions which is not allowed.
    This correction fixes this by setting the missing end date
    to the start date of the following version.

    ### Nodes and relationships affected
    - Non-latest `HAS_VERSION` between `nnnRoot` and `nnnValue`,
      where property `end_date` is before the `start_date` of the next version.
    - Expected changes: ~9500 relationship properties changed
    """

    desc = (
        "Adjusting late end dates for HAS_VERSION relationships that are not the latest"
    )
    log.info(f"Run: {run_label}, {desc}")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN [
            "ClassVariableRoot",
            "DatasetClassRoot",
            "DatasetRoot",
            "DatasetScenarioRoot",
            "DatasetVariableRoot",
            "StudyRoot"
        ])
        WITH root, hv ORDER BY hv.start_date DESC
        WITH root, collect(hv) as hv
        WHERE size(hv)>1
        UNWIND RANGE(1, size(hv)) as n
            WITH n, hv[n] as vprev, hv[n-1] as v
            WHERE vprev.end_date > v.start_date
            SET vprev.end_date = v.start_date
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_006.test_adjust_cdisc_has_had_terms
)
def adjust_cdisc_has_had_terms(db_driver, log, run_label):
    """
    ## Correct start and end dates of HAD_TERM relationships.

    ### Change Description
    When a codelist term is removed from a codelist,
    it is linked to the codelist root via a `HAD_TERM` relationship.
    A new term with the same concept it may then be added,
    linked via a `HAS_TERM` relationship.
    There are a few old items where the end date of the `HAD_TERM`
    does not match the start date of the `HAS_TERM` that replaces it.
    This correction fixes this by changing the start
    and end dates of the terms to put them in sequence.

    ### Nodes and relationships affected
    - `HAD_TERM` and `HAS_TERM` between
      - `CTCodelistRoot` with uids "C66726" and terms with concept id "C134876"
      - `CTCodelistRoot` with uids "C74456" and terms with concept id "C102286"
    - Expected changes: 3 relationship properties changed
    """

    desc = "Adjusting dates for term C134876 in codelist C66726, and term C102286 in codelist C74456"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot {uid: "C66726"})
        MATCH (clr)-[hdt:HAD_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t1 {concept_id: "C134876"}) 
        MATCH (clr)-[hst:HAS_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t2 {concept_id: "C134876"})
        SET hst.start_date = hdt.end_date
        """,
    )

    counters1 = summary.counters
    print_counters_table(counters1)

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot {uid: "C74456"})
        MATCH (clr)-[hdt1:HAD_TERM {start_date: datetime("2014-09-26T00:00:00Z")}]-(t1 {concept_id: "C102286"}) 
        MATCH (clr)-[hdt2:HAD_TERM {start_date: datetime("2018-12-21T00:00:00Z")}]-(t2 {concept_id: "C102286"})
        MATCH (clr)-[hst:HAS_TERM {start_date: datetime("2020-11-06T00:00:00Z")}]-(t3 {concept_id: "C102286"})
        SET hdt1.end_date = hdt2.start_date
        SET hst.start_date = hdt2.end_date
        """,
    )

    counters2 = summary.counters
    print_counters_table(counters2)
    return counters1.contains_updates or counters2.contains_updates


@capture_changes(
    verify_func=correction_verification_006.test_remove_duplicated_terms_in_objective_cat
)
def remove_duplicated_terms_in_objective_cat(db_driver, log, run_label):
    """
    ## Remove unwanted sponsor terms from Objective Category codelist.

    ### Change Description
    At some point, a bug in the import script created and added sponsor defined terms
    to the "Objective Category" codelist.
    These terms have the same names as the CDISC terms that are supposed to be in the list.
    The result is that every term appears twice, as one CDISC and one sponsor defined version.
    This correction removes the sponsor defined terms.
    Any node linking to one of these sponsor defined terms is modified to instead link to the
    corresponding CDISC term.

    ### Nodes and relationships affected
    - All nodes and relationships related to the unwanted terms are deleted:
      - Term root: `CTTermRoot`,
      - Term names: `CTTermNameRoot`, `CTTermNameValue`, `HAS_NAME_ROOT`, `HAS_VERSION`
      - Term attributes: `CTTermAttributesRoot`, `CTTermAttributesValue`, `HAS_ATTRIBUTES_ROOT`, `HAS_VERSION`
    - Items linking to the affected terms are modified:
      - `HAS_CATEGORY` relationships are moved to point at the `CTTermRoot` of the corresponding CDISC term.
    - Expected changes: 25 nodes deleted, 60 relatiohsips deleted, 10 relatiophsips created
    """

    desc = "Remove unwanted sponsor terms in Objective Category codelist"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM|HAD_TERM]-(tr:CTTermRoot)<-[ct:CONTAINS_TERM]-(lib:Library {name: "CDISC"})
        MATCH (cnv:CTCodelistNameValue)<-[hcnv]-(nr:CTCodelistNameRoot)<-[hcnr:HAS_NAME_ROOT]-(clr)
        MATCH (ctnv:CTTermNameValue)<-[chnv]-(ctnr:CTTermNameRoot)<-[chtnr:HAS_NAME_ROOT]-(tr)
        WHERE cnv.name = 'Objective Category'
        WITH clr, collect(DISTINCT ctnv.name) as names
        UNWIND names as name
            MATCH (clr)-[ht:HAS_TERM|HAD_TERM]-(str:CTTermRoot)<-[cst:CONTAINS_TERM]-(lib:Library {name: "Sponsor"}) 
            MATCH (stnv:CTTermNameValue)<-[shnv]-(stnr:CTTermNameRoot)<-[shtnr:HAS_NAME_ROOT]-(str)
            WHERE trim(stnv.name) = name
            MATCH (stav:CTTermAttributesValue)<-[shav]-(star:CTTermAttributesRoot)<-[shtar:HAS_ATTRIBUTES_ROOT]-(str)
            OPTIONAL MATCH (str)<-[hascat:HAS_CATEGORY]-(termuser)
            WITH *, collect(termuser) as users
            MATCH (clr)-[:HAS_TERM]-(cdisc_term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(CTTermNameRootValue {name: name})
            FOREACH (n IN users | MERGE (n)-[:HAS_CATEGORY]->(cdisc_term_root))
            DETACH DELETE str, star, stav, stnr, stnv
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()
