from mdr_standards_import.scripts.entities.cdisc_ct.package import Package
from mdr_standards_import.scripts.entities.cdisc_ct.term import Term
from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.term_submission_value import (
    TermSubmissionValue,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.version import Version
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_class import (
    DataModelClass,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_scenario import (
    DataModelScenario,
)
from mdr_standards_import.scripts.entities.cdisc_data_models.data_model_variable import (
    DataModelVariable,
)


def map_packages(packages: "list[Package]", effective_date):
    packages_data = []
    for package in packages:
        packages_data.append(
            {
                "effective_date": effective_date,
                "name": package.name,
                "catalogue_name": package.catalogue_name,
                "registration_status": package.registration_status,
                "label": package.label,
                "description": package.description,
                "source": package.source,
                "href": package.href,
                "codelists": map_codelists_of_package(package),
                "terms": tmap(package.get_terms()),
            }
        )
    return packages_data


def map_version(version: Version):
    return {
        "name": version.name,
        "label": version.label,
        "description": version.description,
        "source": version.source,
        "registration_status": version.registration_status,
        "version_number": version.get_version_number(),
        "effective_date": version.effective_date,
        "href": version.href,
        "implements_data_model": version.get_implements_data_model(),
        "prior_version": version.prior_version,
        "classes": map_classes_of_version(version),
    }


def map_classes_of_version(version: Version):
    data = []
    for _class in version.get_classes():
        if _class is None:
            continue
        data.append({"name": _class.name})
    return data


def map_classes(classes: "list[DataModelClass]"):
    classes_data = []
    for _class in classes:
        classes_data.append(
            {
                "name": _class.name,
                "title": _class.title,
                "label": _class.label,
                "description": _class.description,
                "ordinal": _class.ordinal,
                "href": _class.href,
                "implements_class": _class.implements_class,
                "subclasses": _class.subclasses,
                "prior_version": _class.prior_version,
                "variables": map_variables_of_class(_class),
            }
        )
    return classes_data


def map_variables_of_class(_class: DataModelClass):
    data = []
    for _variable in _class.get_variables():
        if _variable is None:
            continue
        data.append({"href": _variable.href})
    return data


def map_scenarios(scenarios: "list[DataModelScenario]"):
    scenario_data = []
    for scenario in scenarios:
        scenario_data.append(
            {
                "title": scenario.title,
                "label": scenario.label,
                "ordinal": scenario.ordinal,
                "href": scenario.href,
                "dataset_href": scenario.dataset_href,
                "variables": map_variables_of_class(scenario),
            }
        )
    return scenario_data


def map_variables_of_scenario(scenario: DataModelScenario):
    data = []
    for _variable in scenario.get_variables():
        if _variable is None:
            continue
        data.append({"href": _variable.href})
    return data


def map_variables(variables: "list[DataModelVariable]"):
    variables_data = []
    for _variable in variables:
        variables_data.append(
            {
                "name": _variable.name,
                "title": _variable.title,
                "label": _variable.label,
                "description": _variable.description,
                "ordinal": _variable.ordinal,
                "href": _variable.href,
                "role": _variable.role,
                "notes": _variable.notes,
                "variable_c_code": _variable.variable_c_code,
                "usage_restrictions": _variable.usage_restrictions,
                "examples": _variable.examples,
                "value_list": _variable.value_list,
                "described_value_domain": _variable.described_value_domain,
                "qualifies_variables": _variable.qualifies_variables,
                "role_description": _variable.role_description,
                "simple_datatype": _variable.simple_datatype,
                "length": _variable.length,
                "implementation_notes": _variable.implementation_notes,
                "mapping_instructions": _variable.mapping_instructions,
                "prompt": _variable.prompt,
                "question_text": _variable.question_text,
                "completion_instructions": _variable.completion_instructions,
                "core": _variable.core,
                "codelists": _variable.codelists,
                "implements_variables": _variable.implements_variables,
                "mapping_targets": _variable.mapping_targets,
                "prior_version": _variable.prior_version,
            }
        )
    return variables_data


def pmap(packages):
    data = []
    for package in packages:
        if package is None:
            continue
        data.append(
            {
                "name": package.name,
            }
        )
    return data


def map_codelists_of_package(package: Package):
    data = []
    for codelist in package.get_codelists():
        if codelist is None:
            continue
        itcids = (
            package.get_term_concept_ids_for_codelist(codelist)
            if codelist.has_inconsistent_terms()
            else None
        )
        data.append(
            {"concept_id": codelist.concept_id, "inconsistent_term_concept_ids": itcids}
        )
    return data


def map_codelists(codelists: "list[Codelist]", effective_date):
    codelists_data = []
    for codelist in codelists:
        attributes = codelist.get_attributes()
        codelists_data.append(
            {
                "effective_date": effective_date,
                "concept_id": codelist.concept_id,
                "name": attributes.name,
                "submission_value": attributes.submission_value,
                "preferred_term": attributes.preferred_term,
                "definition": attributes.definition,
                "extensible": attributes.extensible,
                "synonyms": attributes.synonyms,
                "terms": tmap(codelist.get_terms()),
            }
        )
    return codelists_data


def map_inconsistent_codelist_attributes(attributes):
    return {
        "name": attributes.name,
        "submission_value": attributes.submission_value,
        "preferred_term": attributes.preferred_term,
        "definition": attributes.definition,
        "extensible": attributes.extensible,
        "synonyms": attributes.synonyms,
        "package_names": [package.name for package in attributes.get_packages()],
    }


def map_inconsistent_term_attributes(attributes):
    return {
        "name_submission_value": attributes.name_submission_value,
        "preferred_term": attributes.preferred_term,
        "definition": attributes.definition,
        "synonyms": attributes.synonyms,
        "codelist_concept_ids": [
            codelist.concept_id for codelist in attributes.get_codelists()
        ],
        "package_names": [package.name for package in attributes.get_packages()],
    }


def map_term_submission_value(tsv: TermSubmissionValue):
    return {
        "submission_value": tsv.get_value(),
        "codelist_concept_ids": [
            codelist.concept_id for codelist in tsv.get_codelists()
        ],
        "package_names": [package.name for package in tsv.get_packages()],
    }


def tmap(terms):
    data = []
    for term in terms:
        if term is None:
            continue
        data.append(
            {
                "concept_id": term.concept_id,
                "code_submission_value": term.code_submission_value,
            }
        )
    return data


def map_terms(terms: "list[Term]", effective_date):
    terms_data = []
    for term in terms:
        attributes = term.get_attributes()
        terms_data.append(
            {
                "effective_date": effective_date,
                "concept_id": term.concept_id,
                "code_submission_value": term.code_submission_value,
                "name_submission_value": attributes.name_submission_value,
                "preferred_term": attributes.preferred_term,
                "definition": attributes.definition,
                "synonyms": attributes.synonyms,
            }
        )
    return terms_data
