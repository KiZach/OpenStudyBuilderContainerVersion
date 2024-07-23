from clinical_mdr_api.models.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneCreateInput,
)
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)


def create_study_disease_milestone_codelists_ret_cat_and_lib():
    catalogue_name, library_name = get_catalogue_name_library_name()
    codelist = create_codelist(
        "Disease Milestone Type", "CTCodelist_00004", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelist_uid,
        "Disease Milestone Type",
        "Disease_Milestone_Type_0001",
        222,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Disease Milestone Type 2",
        "Disease_Milestone_Type_0002",
        223,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Disease Milestone Type 3",
        "Disease_Milestone_Type_0003",
        224,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Disease Milestone Type 4",
        "Disease_Milestone_Type_0004",
        225,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelist_uid,
        "Disease Milestone Type 5",
        "Disease_Milestone_Type_0005",
        226,
        catalogue_name,
        library_name,
    )


def create_study_disease_milestone(disease_milestone_type):
    study_disease_milestone_create_input = StudyDiseaseMilestoneCreateInput(
        study_uid="study_root",
        disease_milestone_type=disease_milestone_type,
        repetition_indicator=True,
    )
    item = StudyDiseaseMilestoneService().create(
        "study_root", study_disease_milestone_input=study_disease_milestone_create_input
    )
    return item
