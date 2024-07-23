from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.ct_import import CTImport
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_import import (
    DataModelImport,
)
from mdr_standards_import.scripts.entities.inconsistency import Inconsistency
from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.exceptions.effective_date_exists import (
    EffectiveDateExists,
)
from mdr_standards_import.scripts.exceptions.version_exists import VersionExists
from mdr_standards_import.scripts.repositories.mapping import (
    map_codelists,
    map_inconsistent_codelist_attributes,
    map_inconsistent_term_attributes,
    map_term_submission_value,
    map_packages,
    map_terms,
    map_version,
    map_classes,
    map_variables,
    map_scenarios,
)
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term


def create_indexes_if_not_existent(tx):
    for querystring in [
        "CREATE INDEX index_codelist_concept_id IF NOT EXISTS FOR (n:Codelist) ON (n.concept_id)",
        "CREATE INDEX index_term_concept_id IF NOT EXISTS FOR (n:Term) ON (n.concept_id)",
        "CREATE INDEX index_variable IF NOT EXISTS FOR (n:DataModelVariable) ON (n.href)",
        "CREATE CONSTRAINT constraint_import_effective_date IF NOT EXISTS FOR (n:Import) REQUIRE (n.effective_date) IS NODE KEY",
        "CREATE CONSTRAINT data_model_import_node_key IF NOT EXISTS FOR (n:DataModelImport) REQUIRE (n.catalogue, n.version_number) IS NODE KEY",
        "CREATE CONSTRAINT data_model_class_node_key IF NOT EXISTS FOR (n:DataModelClass) REQUIRE (n.catalogue, n.version_number, n.name) IS NODE KEY",
        "CREATE CONSTRAINT data_model_scenario_node_key IF NOT EXISTS FOR (n:DataModelScenario) REQUIRE (n.href) IS NODE KEY",
        "CREATE CONSTRAINT constraint_package_uid IF NOT EXISTS FOR (n:Package) REQUIRE (n.name) IS NODE KEY",
        "CREATE CONSTRAINT contraint_version_name IF NOT EXISTS FOR (n:Version) REQUIRE (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_codelist_uid IF NOT EXISTS FOR (n:Codelist) REQUIRE (n.effective_date, n.concept_id) IS NODE KEY",
        "CREATE CONSTRAINT constraint_term_uid IF NOT EXISTS FOR (n:Term) REQUIRE (n.effective_date, n.concept_id, n.code_submission_value) IS NODE KEY",
    ]:
        tx.run(querystring)


def await_indexes(tx):
    tx.run("CALL db.awaitIndexes(5000)")


def create_import_node(tx, ct_import: CTImport):
    """
    Creates the `Import` node for the specified <effective_date> if it doesn't exist.

    Returns the internal Neo4j id of the created node on success.
    Returns False if the node was not created. Reasons might include: the node was already existent, db error.
    """

    if _does_import_node_exists(tx, ct_import):
        raise EffectiveDateExists

    result = tx.run(
        """
        CREATE (import:Import{
            effective_date: date($effective_date),
            user_initials: $user_initials
        })
        SET
            import:Running,
            import.import_date_time = datetime($import_date_time)
        RETURN id(import) AS import_id
        """,
        effective_date=ct_import.effective_date,
        user_initials=ct_import.user_initials,
        import_date_time=ct_import.import_date_time,
    ).single()

    import_id = result.get("import_id", None)
    if import_id is None:
        raise Exception
    return import_id


def _does_import_node_exists(tx, ct_import: CTImport):
    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        WITH import LIMIT 1
        RETURN count(import) = 1 AS does_import_exist
        """,
        effective_date=ct_import.effective_date,
    ).single()

    return result is not None and result["does_import_exist"] == True


def create_ct_import(ct_import: CTImport, session):
    effective_date = ct_import.effective_date

    packages_data = map_packages(ct_import.get_packages(), ct_import.effective_date)

    codelists_data = map_codelists(ct_import.get_codelists(), ct_import.effective_date)
    terms_data = map_terms(ct_import.get_terms(), ct_import.effective_date)

    with session.begin_transaction() as tx:
        _create_packages(tx, effective_date, packages_data)
        _create_codelists(tx, effective_date, codelists_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_terms(tx, effective_date, terms_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_package_contains_codelist(tx, effective_date, packages_data)
        _create_codelist_contains_term(tx, effective_date, codelists_data)
        _create_package_contains_term(tx, effective_date, packages_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_inconsistent_attributes_for_codelists(
            tx, ct_import.get_codelists(), effective_date
        )
        _create_inconsistent_attributes_and_submission_values_for_terms(
            tx, ct_import.get_terms(), effective_date
        )

    with session.begin_transaction() as tx:
        for inconsistency in ct_import.get_inconsistencies():
            _create_inconsistency(tx, inconsistency, effective_date)
        tx.commit()


def create_data_model_import_node(tx, dm_import: DataModelImport):
    """
    Creates the `DataModelImport` node for the specified catalogue and version if it doesn't exist.

    Returns the internal Neo4j id of the created node on success.
    Returns False if the node was not created. Reasons might include: the node was already existent, db error.
    """

    if _does_data_model_import_node_exists(tx, dm_import):
        raise VersionExists

    result = tx.run(
        """
        CREATE (import:DataModelImport{
            library: $library,
            catalogue: $catalogue,
            version_number: $version_number,
            implements_data_model: $implements_data_model,
            data_model_type: $data_model_type,
            user_initials: $user_initials
        })
        SET
            import:Running,
            import.import_date_time = datetime($import_date_time)
        RETURN id(import) AS import_id
        """,
        library=dm_import.library,
        catalogue=dm_import.catalogue,
        version_number=dm_import.version_number,
        data_model_type=dm_import.get_type().value,
        implements_data_model=dm_import.get_implements_data_model(),
        user_initials=dm_import.user_initials,
        import_date_time=dm_import.import_date_time,
    ).single()

    import_id = result.get("import_id", None)
    if import_id is None:
        raise Exception
    return import_id


def _does_data_model_import_node_exists(tx, dm_import: DataModelImport):
    result = tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $version_number})
        WITH import LIMIT 1
        RETURN count(import) = 1 AS does_import_exist
        """,
        catalogue=dm_import.catalogue,
        version_number=dm_import.version_number,
    ).single()

    return result is not None and result["does_import_exist"] == True


def create_data_model_import(dm_import: DataModelImport, session):
    catalogue = dm_import.catalogue
    version_number = dm_import.version_number

    version_data = map_version(dm_import.get_version())
    classes_data = map_classes(dm_import.get_classes())
    scenarios_data = map_scenarios(dm_import.get_scenarios())
    variables_data = map_variables(dm_import.get_variables())

    with session.begin_transaction() as tx:
        _create_version(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            version_data=version_data,
        )
        _create_classes(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            classes_data=classes_data,
        )
        if scenarios_data is not None and len(scenarios_data) > 0:
            _create_scenarios(
                tx,
                catalogue=catalogue,
                version_number=version_number,
                scenarios_data=scenarios_data,
            )
        _create_variables(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            variables_data=variables_data,
        )
        tx.commit()

    with session.begin_transaction() as tx:
        _create_version_contains_class(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            version_data=version_data,
        )
        _create_class_contains_variable(
            tx,
            catalogue=catalogue,
            version_number=version_number,
            classes_data=classes_data,
        )
        if scenarios_data is not None and len(scenarios_data) > 0:
            _create_scenario_contains_variable(
                tx,
                catalogue=catalogue,
                version_number=version_number,
                scenarios_data=scenarios_data,
            )
        tx.commit()


# Create nodes
def _create_packages(tx, effective_date, packages_data):
    tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        UNWIND $packages AS p
            CREATE (package:Package{
                name: p.name
            })
            SET
                package.catalogue_name = p.catalogue_name,
                package.registration_status = p.registration_status,
                package.label = p.label,
                package.description = p.description,
                package.source = p.source,
                package.href = p.href
            CREATE (import)-[:INCLUDES]->(package)
        """,
        effective_date=effective_date,
        packages=packages_data,
    )


def _create_codelists(tx, effective_date, codelists_data):
    tx.run(
        """
        UNWIND $codelists AS c
            CREATE (codelist:Codelist{
                effective_date: date($effective_date),
                concept_id: c.concept_id
            })
            SET 
                codelist.name = c.name,
                codelist.submission_value = c.submission_value,
                codelist.preferred_term = c.preferred_term,
                codelist.definition = c.definition,
                codelist.extensible = c.extensible,
                codelist.synonyms = c.synonyms
        """,
        codelists=codelists_data,
        effective_date=effective_date,
    )


def _create_terms(tx, effective_date, terms_data):
    tx.run(
        """
        UNWIND $terms AS t
            CREATE (term:Term{
                effective_date: date($effective_date),
                concept_id: t.concept_id,
                code_submission_value: t.code_submission_value
            })
            SET
                term.name_submission_value = t.name_submission_value,
                term.preferred_term = t.preferred_term,
                term.definition = t.definition,
                term.synonyms = t.synonyms
        """,
        terms=terms_data,
        effective_date=effective_date,
    )


def _create_version(tx, catalogue, version_number, version_data):
    tx.run(
        """
        MATCH (import:DataModelImport{catalogue: $catalogue, version_number: $version_number})
        WITH import, $version AS v
        CREATE (version:Version{
            name: v.name
        })
        SET
            version.label = v.label,
            version.description = v.description,
            version.source = v.source,
            version.registration_status = v.registration_status,
            version.version_number = v.version_number,
            version.effective_date = v.effective_date,
            version.href = v.href,
            version.prior_version = v.prior_version
        CREATE (import)-[:INCLUDES]->(version)
        """,
        catalogue=catalogue,
        version_number=version_number,
        version=version_data,
    )


def _create_classes(tx, catalogue, version_number, classes_data):
    tx.run(
        """
        UNWIND $classes AS c
            CREATE (class:DataModelClass{
                catalogue: $catalogue,
                version_number: $version_number,
                name: c.name
            })
            SET
                class.title = c.title,
                class.label = c.label,
                class.description = c.description,
                class.ordinal = c.ordinal,
                class.href = c.href,
                class.implements_class = c.implements_class,
                class.subclasses = c.subclasses,
                class.prior_version = c.prior_version
        """,
        catalogue=catalogue,
        version_number=version_number,
        classes=classes_data,
    )


def _create_scenarios(tx, catalogue, version_number, scenarios_data):
    tx.run(
        """
        UNWIND $scenarios AS s
            CREATE (scenario:DataModelScenario{
                catalogue: $catalogue,
                version_number: $version_number,
                title: s.title
            })
            SET
                scenario.label = s.label,
                scenario.ordinal = s.ordinal,
                scenario.href = s.href

            WITH s, scenario
            MATCH (dataset:DataModelClass{href: s.dataset_href})
            CREATE (dataset)-[:CONTAINS]->(scenario)
        """,
        catalogue=catalogue,
        version_number=version_number,
        scenarios=scenarios_data,
    )


def _create_variables(tx, catalogue, version_number, variables_data):
    tx.run(
        """
        UNWIND $variables AS v
            CREATE (variable:DataModelVariable{href: v.href})
            SET
                variable.catalogue = $catalogue,
                variable.version_number = $version_number,
                variable.name = v.name,
                variable.title = v.title,
                variable.label = v.label,
                variable.description = v.description,
                variable.ordinal = v.ordinal,
                variable.role = v.role,
                variable.notes = v.notes,
                variable.variable_c_code = v.variable_c_code,
                variable.usage_restrictions = v.usage_restrictions,
                variable.examples = v.examples,
                variable.value_list = v.value_list,
                variable.described_value_domain = v.described_value_domain,
                variable.qualifies_variables = v.qualifies_variables,
                variable.role_description = v.role_description,
                variable.simple_datatype = v.simple_datatype,
                variable.length = v.length,
                variable.implementation_notes = v.implementation_notes,
                variable.mapping_instructions = v.mapping_instructions,
                variable.prompt = v.prompt,
                variable.question_text = v.question_text,
                variable.completion_instructions = v.completion_instructions,
                variable.core = v.core,
                variable.codelists = v.codelists,
                variable.implements_variables = v.implements_variables,
                variable.mapping_targets = v.mapping_targets,
                variable.prior_version = v.prior_version
        """,
        catalogue=catalogue,
        version_number=version_number,
        variables=variables_data,
    )


# Create inconsistencies
def _create_inconsistent_attributes_for_codelists(
    tx, codelists: "list[Codelist]", effective_date: str
):
    for codelist in codelists:
        if not codelist.has_consistent_attributes():
            for attributes in codelist.get_inconsistent_attributes_set():
                tx.run(
                    """
                    MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: $concept_id})
                    CREATE (codelist)-[:HAS]->(ia:InconsistentAttributes)
                    SET
                        ia.name = $attributes_data.name,
                        ia.submission_value = $attributes_data.submission_value,
                        ia.preferred_term = $attributes_data.preferred_term,
                        ia.definition = $attributes_data.definition,
                        ia.extensible = $attributes_data.extensible,
                        ia.synonyms = $attributes_data.synonyms
                    WITH ia
                    MATCH (package:Package) WHERE package.name IN $attributes_data.package_names
                    CREATE (ia)-[:ARE_DEFINED_IN]->(package)
                    """,
                    effective_date=effective_date,
                    concept_id=codelist.concept_id,
                    attributes_data=map_inconsistent_codelist_attributes(attributes),
                )


def _create_inconsistent_attributes_and_submission_values_for_terms(
    tx, terms: "list[Term]", effective_date: str
):
    for term in terms:
        if not term.has_consistent_attributes():
            _create_inconsistent_attributes_for_term(tx, term, effective_date)
        if not term.has_consistent_submission_values():
            _create_inconsistent_submission_values_for_term(tx, term, effective_date)


def _create_inconsistent_attributes_for_term(tx, term: Term, effective_date: str):
    for attributes in term.get_inconsistent_attributes_set():
        attributes_data = map_inconsistent_term_attributes(attributes)
        result = tx.run(
            """
            MATCH (term:Term{
                effective_date: date($effective_date),
                concept_id: $concept_id,
                code_submission_value: $code_submission_value
            })
            CREATE (term)-[:HAS]->(ia:InconsistentAttributes)
            SET
                ia.name_submission_value = $attributes_data.name_submission_value,
                ia.preferred_term = $attributes_data.preferred_term,
                ia.definition = $attributes_data.definition,
                ia.synonyms = $attributes_data.synonyms
            RETURN id(ia) AS inconsistent_attributes_id
            """,
            effective_date=effective_date,
            concept_id=term.concept_id,
            code_submission_value=term.code_submission_value,
            attributes_data=attributes_data,
        ).single()
        inconsistent_attributes_id = result.get("inconsistent_attributes_id")

        tx.run(
            """
            MATCH (ia) WHERE id(ia) = $inconsistent_attributes_id
            MATCH (codelist:Codelist) WHERE codelist.concept_id IN $codelist_concept_ids
            CREATE (ia)-[:ARE_DEFINED_IN]->(codelist)
            """,
            inconsistent_attributes_id=inconsistent_attributes_id,
            codelist_concept_ids=attributes_data.get("codelist_concept_ids", []),
        )

        tx.run(
            """
            MATCH (ia) WHERE id(ia) = $inconsistent_attributes_id
            MATCH (package:Package) WHERE package.name IN $package_names
            CREATE (ia)-[:ARE_DEFINED_IN]->(package)
            """,
            inconsistent_attributes_id=inconsistent_attributes_id,
            package_names=attributes_data.get("package_names", []),
        )


def _create_inconsistent_submission_values_for_term(
    tx, term: Term, effective_date: str
):
    for tsv in term.get_term_submission_values():
        sv_data = map_term_submission_value(tsv)
        result = tx.run(
            """
            MATCH (term:Term{
                effective_date: date($effective_date),
                concept_id: $concept_id,
                code_submission_value: $code_submission_value
            })
            CREATE (term)-[:HAS]->(sv:InconsistentSubmissionValue)
            SET
                sv.submission_value = $sv_data.submission_value   
            RETURN id(sv) AS sv_id
            """,
            effective_date=effective_date,
            concept_id=term.concept_id,
            code_submission_value=term.code_submission_value,
            sv_data=sv_data,
        ).single()
        sv_id = result.get("sv_id")

        tx.run(
            """
            MATCH (sv) WHERE id(sv) = $sv_id
            MATCH (codelist:Codelist) WHERE codelist.concept_id IN $codelist_concept_ids
            CREATE (sv)-[:IS_DEFINED_IN]->(codelist)
            """,
            sv_id=sv_id,
            codelist_concept_ids=sv_data.get("codelist_concept_ids", []),
        )

        tx.run(
            """
            MATCH (sv) WHERE id(sv) = $sv_id
            MATCH (package:Package) WHERE package.name IN $package_names
            CREATE (sv)-[:IS_DEFINED_IN_PACKAGE]->(package)
            """,
            sv_id=sv_id,
            package_names=sv_data.get("package_names", []),
        )


# Create relationships
def _create_package_contains_codelist(tx, effective_date, packages_data):
    tx.run(
        """
        UNWIND $packages AS p
            MATCH (package:Package{name: p.name})
            UNWIND p.codelists AS c
                MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: c.concept_id})
                CREATE (package)-[contains:CONTAINS]->(codelist)
                SET contains.inconsistent_term_concept_ids=c.inconsistent_term_concept_ids
        """,
        packages=packages_data,
        effective_date=effective_date,
    )


def _create_package_contains_term(tx, effective_date, packages_data):
    tx.run(
        """
        UNWIND $packages AS p
            MATCH (package:Package{name: p.name})
            UNWIND p.terms AS t
                MATCH (term:Term{
                    effective_date:date($effective_date),
                    concept_id: t.concept_id,
                    code_submission_value: t.code_submission_value
                })
                CREATE (package)-[:CONTAINS_TERM]->(term)
        """,
        packages=packages_data,
        effective_date=effective_date,
    )


def _create_codelist_contains_term(tx, effective_date, codelists_data):
    tx.run(
        """
        UNWIND $codelists AS c
            MATCH (codelist:Codelist{effective_date: date($effective_date), concept_id: c.concept_id})
            UNWIND c.terms AS t
                MATCH (term:Term{effective_date: date($effective_date), concept_id: t.concept_id, code_submission_value: t.code_submission_value})
                CREATE (codelist)-[:CONTAINS]->(term)
        """,
        codelists=codelists_data,
        effective_date=effective_date,
    )


def _create_version_contains_class(tx, catalogue, version_number, version_data):
    tx.run(
        """
        WITH $version AS v
        MATCH (version:Version{name: v.name})
        UNWIND v.classes AS c
            MATCH (class:DataModelClass{
                catalogue: $catalogue,
                version_number: $version_number,
                name: c.name
            })
            CREATE (version)-[contains:CONTAINS]->(class)
        """,
        catalogue=catalogue,
        version_number=version_number,
        version=version_data,
    )


def _create_class_contains_variable(tx, catalogue, version_number, classes_data):
    tx.run(
        """
        UNWIND $classes AS c
            MATCH (class:DataModelClass{name: c.name, catalogue: $catalogue, version_number: $version_number})
            UNWIND c.variables AS v
                MATCH (variable:DataModelVariable{href: v.href})
                CREATE (class)-[contains:CONTAINS]->(variable)
        """,
        catalogue=catalogue,
        version_number=version_number,
        classes=classes_data,
    )


def _create_scenario_contains_variable(tx, catalogue, version_number, scenarios_data):
    tx.run(
        """
        UNWIND $scenarios AS s
            MATCH (scenario:DataModelScenario{href: s.href})
            UNWIND s.variables AS v
                MATCH (variable:DataModelVariable{href: v.href})
                CREATE (scenario)-[contains:CONTAINS]->(variable)
        """,
        catalogue=catalogue,
        version_number=version_number,
        scenarios=scenarios_data,
    )


def _create_inconsistency(tx, inconsistency: Inconsistency, effective_date):
    label = "ResolvedInconsistency" if inconsistency.is_resolved() else "Inconsistency"

    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        CREATE (import)-[:HAS]->(log:"""
        + label
        + """)
        SET
            log.date_time = datetime($date),
            log.tagline = $tagline,
            log.message = $message,
            log.comment = $comment,
            log.user_initials = $user_initials
        RETURN id(log) AS inconsistency_id
        """,
        effective_date=effective_date,
        date=inconsistency.date_time,
        tagline=inconsistency.tagline,
        message=inconsistency.message,
        comment=inconsistency.comment,
        user_initials=inconsistency.user_initials,
    ).single()
    inconsistency_id = result.get("inconsistency_id")
    if inconsistency.affected_package is not None:
        _create_affects_package(inconsistency_id, inconsistency.affected_package, tx)
    if inconsistency.affected_codelist is not None:
        _create_affects_codelist(
            inconsistency_id, inconsistency.affected_codelist, effective_date, tx
        )
    if inconsistency.affected_term is not None:
        _create_affects_term(
            inconsistency_id, inconsistency.affected_term, effective_date, tx
        )


def _create_affects_package(inconsistency_id: int, package: Package, tx):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (package:Package{name: $package_name})
        CREATE (log)-[:AFFECTS_PACKAGE]->(package)
        """,
        inconsistency_id=inconsistency_id,
        package_name=package.name,
    )


def _create_affects_codelist(
    inconsistency_id: int, codelist: Codelist, effective_date: str, tx
):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: $codelist_concept_id})
        CREATE (log)-[:AFFECTS_CODELIST]->(codelist)
        """,
        inconsistency_id=inconsistency_id,
        effective_date=effective_date,
        codelist_concept_id=codelist.concept_id,
    )


def _create_affects_term(inconsistency_id: int, term: Term, effective_date: str, tx):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (term:Term{
            effective_date:date($effective_date),
            concept_id: $term_concept_id,
            code_submission_value: $code_submission_value
            })
        CREATE (log)-[:AFFECTS_TERM]->(term)
        """,
        inconsistency_id=inconsistency_id,
        effective_date=effective_date,
        code_submission_value=term.code_submission_value,
        term_concept_id=term.concept_id,
    )
