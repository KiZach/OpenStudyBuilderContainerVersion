# pylint: disable=unused-argument,redefined-outer-name

import logging

from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundInput,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.studies.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.studies.study_interventions import (
    StudyInterventionsService,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)


def test_get_table(
    tst_study, study_epochs, study_arms, study_elements, study_design_cells
):
    # Create CT Terms
    ct_term_dosage = TestUtils.create_ct_term(sponsor_preferred_name="dosage_form_1")
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1"
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsor_preferred_name="dose_frequency_1"
    )
    ct_term_dispenser = TestUtils.create_ct_term(sponsor_preferred_name="dispenser_1")
    ct_term_roa = TestUtils.create_ct_term(
        sponsor_preferred_name="route_of_administration_1"
    )

    # Create Numeric values with unit
    strength_value = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")
    half_life = TestUtils.create_numeric_value_with_unit(value=8, unit="hours")

    # Create Lag-times
    lag_time = TestUtils.create_lag_time(value=7, unit="days")

    # Create Brands
    brands = [
        TestUtils.create_brand(name=name) for name in ["Brand A", "Brand B", "Brand C"]
    ]

    # Create compounds
    compound1: Compound = TestUtils.create_compound(
        name="name-AAA",
        dosage_form_uids=[ct_term_dosage.term_uid],
        delivery_devices_uids=[ct_term_delivery_device.term_uid],
        dispensers_uids=[ct_term_dispenser.term_uid],
        route_of_administration_uids=[ct_term_roa.term_uid],
        strength_values_uids=[strength_value.uid],
        dose_frequency_uids=[ct_term_dose_frequency.term_uid],
        dose_values_uids=[dose_value.uid],
        lag_times_uids=[lag_time.uid],
        half_life_uid=half_life.uid,
        substance_terms_uids=[],
        brands_uids=[brands[0].uid, brands[1].uid],
    )
    compound_alias1a: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound1.uid
    )
    compound_alias1b: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound1.uid
    )

    compound2: Compound = TestUtils.create_compound(
        name="name-BBB",
        dosage_form_uids=[ct_term_dosage.term_uid],
        delivery_devices_uids=[ct_term_delivery_device.term_uid],
        dispensers_uids=[ct_term_dispenser.term_uid],
        route_of_administration_uids=[ct_term_roa.term_uid],
        strength_values_uids=[strength_value.uid],
        dose_frequency_uids=[ct_term_dose_frequency.term_uid],
        dose_values_uids=[dose_value.uid],
        lag_times_uids=[lag_time.uid],
        half_life_uid=half_life.uid,
        substance_terms_uids=[],
        brands_uids=[brands[2].uid, brands[1].uid],
    )
    compound_alias2a: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound2.uid
    )
    compound_alias2b: CompoundAlias = TestUtils.create_compound_alias(
        compound_uid=compound2.uid
    )

    CompoundService().approve(compound1.uid)
    CompoundService().approve(compound2.uid)
    CompoundAliasService().approve(compound_alias1a.uid)
    CompoundAliasService().approve(compound_alias2a.uid)
    CompoundAliasService().approve(compound_alias1b.uid)
    CompoundAliasService().approve(compound_alias2b.uid)

    # Make a compound selection with compound alias 'compound_alias1a'
    study_compound_created1: StudySelectionCompound = TestUtils.create_study_compound(
        study_uid=tst_study.uid,
        compound_alias_uid=compound_alias1a.uid,
        dosage_form_uid=ct_term_dosage.term_uid,
        device_uid=ct_term_delivery_device.term_uid,
        dispensed_in_uid=ct_term_dispenser.term_uid,
        route_of_administration_uid=ct_term_roa.term_uid,
        strength_value_uid=strength_value.uid,
    )

    # Make a compound selection with another compound alias, while keeping all other details the same
    study_compound_created2: StudySelectionCompound = (
        StudyCompoundSelectionService().make_selection(
            study_uid=tst_study.uid,
            selection_create_input=StudySelectionCompoundInput(
                compound_alias_uid=compound_alias2a.uid,
                dosage_form_uid=ct_term_dosage.term_uid,
                device_uid=ct_term_delivery_device.term_uid,
                dispensed_in_uid=ct_term_dispenser.term_uid,
                route_of_administration_uid=ct_term_roa.term_uid,
                strength_value_uid=strength_value.uid,
            ),
        )
    )

    study_compound_dosing_selection_service = StudyCompoundDosingSelectionService()

    # Make a compound dosing selection with just-created study compound 'study_compound_created1'
    study_compound_dosing_selection_service.make_selection(
        study_uid=tst_study.uid,
        selection_create_input=StudyCompoundDosingInput(
            study_compound_uid=study_compound_created1.study_compound_uid,
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            dose_value_uid=dose_value.uid,
            study_element_uid=study_elements[0].element_uid,
        ),
    )

    # Make a compound dosing selection with another study compound, while keeping all other details the same
    study_compound_dosing_selection_service.make_selection(
        study_uid=tst_study.uid,
        selection_create_input=StudyCompoundDosingInput(
            study_compound_uid=study_compound_created2.study_compound_uid,
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            dose_value_uid=dose_value.uid,
            study_element_uid=study_elements[1].element_uid,
        ),
    )

    table = StudyInterventionsService().get_table(tst_study.uid)

    assert len(table.rows) == 14, "Incorrect number of rows"
    assert len(table.rows[0].cells) == 3, "Incorrect number of columns"
    assert table.num_header_rows == 1, "Incorrect number of header rows"
    assert table.num_header_cols == 1, "Incorrect number of header columns"

    for row in table.rows:
        assert len(row.cells) == 3

    assert table.rows[0].cells[1].text == study_arms[0].name, "arm name mismatch"
    assert table.rows[0].cells[2].text == study_arms[1].name, "arm name mismatch"
    assert table.rows[1].cells[1].text == compound1.name, "compound name mismatch"
    assert table.rows[1].cells[2].text == compound2.name, "compound name mismatch"
    # table.data[2] intervention type is missing from test data
    # table.data[3] is not implemented
    assert (
        table.rows[4].cells[1].text
        == table.rows[4].cells[2].text
        == ct_term_dosage.sponsor_preferred_name
    )
    assert (
        table.rows[5].cells[1].text
        == table.rows[5].cells[2].text
        == ct_term_roa.sponsor_preferred_name
    )

    assert ct_term_delivery_device.sponsor_preferred_name in table.rows[6].cells[1].text
    assert ct_term_dispenser.sponsor_preferred_name in table.rows[6].cells[1].text
    assert table.rows[6].cells[1].text == table.rows[6].cells[2].text
