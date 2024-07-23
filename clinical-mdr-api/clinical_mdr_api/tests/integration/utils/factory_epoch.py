from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpochCreateInput,
    StudyEpochEditInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)


def create_study_epoch_codelists_ret_cat_and_lib(use_test_utils: bool = False):
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils)
    ct_term_service = CTTermService()
    codelist = create_codelist(
        "Epoch Type", "CTCodelist_00002", catalogue_name, library_name
    )
    type1 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Type",
        "EpochType_0001",
        1,
        catalogue_name,
        library_name,
    )
    type2 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Type1",
        "EpochType_0002",
        2,
        catalogue_name,
        library_name,
    )
    type3 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Type2",
        "EpochType_0003",
        3,
        catalogue_name,
        library_name,
    )
    type4 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Type3",
        "EpochType_0004",
        4,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Epoch Sub Type", "CTCodelist_00003", catalogue_name, library_name
    )
    subtype1 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype",
        "EpochSubType_0001",
        1,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=subtype1.uid, parent_uid=type1.uid, relationship_type="type"
    )
    subtype2 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype1",
        "EpochSubType_0002",
        2,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=subtype2.uid, parent_uid=type2.uid, relationship_type="type"
    )
    subtype3 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype2",
        "EpochSubType_0003",
        3,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=subtype3.uid, parent_uid=type3.uid, relationship_type="type"
    )
    subtype4 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype3",
        "EpochSubType_0004",
        4,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=subtype4.uid, parent_uid=type4.uid, relationship_type="type"
    )
    supplemental_subtype = create_ct_term(
        codelist.codelist_uid,
        "Basic",
        "Basic_uid",
        5,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=supplemental_subtype.uid,
        parent_uid=type1.uid,
        relationship_type="type",
    )

    codelist = create_codelist("Epoch", "C99079", catalogue_name, library_name)

    ep1 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype 1",
        "Epoch_0001",
        2,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep1.uid, parent_uid=subtype1.uid, relationship_type="subtype"
    )
    ep2 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype 2",
        "Epoch_0002",
        3,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep2.uid, parent_uid=subtype1.uid, relationship_type="subtype"
    )
    ep3 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype 3",
        "Epoch_0003",
        4,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep3.uid, parent_uid=subtype1.uid, relationship_type="subtype"
    )

    ep4 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype1 1",
        "Epoch_0004",
        6,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep4.uid, parent_uid=subtype2.uid, relationship_type="subtype"
    )
    ep5 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype1 2",
        "Epoch_0005",
        7,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep5.uid, parent_uid=subtype2.uid, relationship_type="subtype"
    )

    ep6 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype2 1",
        "Epoch_0006",
        9,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep6.uid, parent_uid=subtype3.uid, relationship_type="subtype"
    )
    ep7 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype2 2",
        "Epoch_0007",
        10,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep7.uid, parent_uid=subtype3.uid, relationship_type="subtype"
    )

    ep8 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype3 1",
        "Epoch_0008",
        12,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep8.uid, parent_uid=subtype3.uid, relationship_type="subtype"
    )
    ep9 = create_ct_term(
        codelist.codelist_uid,
        "Epoch Subtype3 2",
        "Epoch_0009",
        13,
        catalogue_name,
        library_name,
    )
    ct_term_service.add_parent(
        term_uid=ep9.uid, parent_uid=subtype3.uid, relationship_type="subtype"
    )


def create_study_epoch(epoch_subtype_uid, study_uid="study_root"):
    study_epoch_create_input = StudyEpochCreateInput(
        study_uid=study_uid,
        start_rule="start_rule",
        end_rule="end_rule",
        description="test_description",
        epoch_subtype=epoch_subtype_uid,
        duration=0,
        color_hash="#1100FF",
    )
    item = StudyEpochService().create(
        study_uid, study_epoch_input=study_epoch_create_input
    )
    return item


def edit_study_epoch(epoch_uid, study_uid="study_root"):
    study_epoch_edit_input = StudyEpochEditInput(
        study_uid=study_uid,
        change_description="edit to test",
        start_rule="second_new_start_rule",
    )
    item = StudyEpochService().edit(
        study_uid=study_uid,
        study_epoch_uid=epoch_uid,
        study_epoch_input=study_epoch_edit_input,
    )
    return item
