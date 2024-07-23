import unittest

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundInput,
    StudySelectionElement,
    StudySelectionElementCreateInput,
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
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
    STARTUP_STUDY_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import STUDY_UID, TestUtils


class TestStudyCompoundsService(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("study.compounds.service")

        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_STUDY_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        super().setUp()

    def test_make_selection(self):
        # Create some library compounds and aliases, and select some of them as study interventions

        compound1: Compound = TestUtils.create_compound(
            name="name-AAA",
            dosage_form_uids=["dosage_form_uid1"],
            delivery_devices_uids=["delivery_device_uid1"],
            dispensers_uids=["dispenser_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            strength_values_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            dose_values_uids=["NumericValueWithUnit_000001"],
        )
        compound_alias1a: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )
        compound_alias1b: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )

        compound2: Compound = TestUtils.create_compound(
            name="name-BBB",
            dosage_form_uids=["dosage_form_uid1"],
            delivery_devices_uids=["delivery_device_uid1"],
            dispensers_uids=["dispenser_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            strength_values_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            dose_values_uids=["NumericValueWithUnit_000001"],
        )
        compound_alias2a: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )
        compound_alias2b: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )

        CompoundService().approve(compound1.uid)
        CompoundService().approve(compound2.uid)
        CompoundAliasService().approve(compound_alias1a.uid)
        CompoundAliasService().approve(compound_alias2a.uid)
        CompoundAliasService().approve(compound_alias1b.uid)
        CompoundAliasService().approve(compound_alias2b.uid)

        study_selection_element: StudySelectionElement = (
            StudyElementSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionElementCreateInput(
                    name="Elem1", short_name="el1", element_subtype_uid="term1"
                ),
            )
        )

        # Make a compound selection with compound alias 'compound_alias1a'
        study_compound_created1: StudySelectionCompound = (
            TestUtils.create_study_compound(
                study_uid=STUDY_UID,
                compound_alias_uid=compound_alias1a.uid,
                dosage_form_uid="dosage_form_uid1",
                device_uid="delivery_device_uid1",
                dispensed_in_uid="dispenser_uid1",
                route_of_administration_uid="route_of_administration_uid1",
                strength_value_uid="NumericValueWithUnit_000001",
            )
        )
        assert study_compound_created1.study_compound_uid == "StudyCompound_000001"

        # Make a compound selection with another compound alias, while keeping all other details the same
        study_compound_created2: StudySelectionCompound = (
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias2a.uid,
                    dosage_form_uid="dosage_form_uid1",
                    device_uid="delivery_device_uid1",
                    dispensed_in_uid="dispenser_uid1",
                    route_of_administration_uid="route_of_administration_uid1",
                    strength_value_uid="NumericValueWithUnit_000001",
                ),
            )
        )
        assert study_compound_created2.study_compound_uid == "StudyCompound_000003"

        # Try to make a compound selection with the same compound alias 'compound_alias1a' and all other details
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    dosage_form_uid="dosage_form_uid1",
                    device_uid="delivery_device_uid1",
                    dispensed_in_uid="dispenser_uid1",
                    route_of_administration_uid="route_of_administration_uid1",
                    strength_value_uid="NumericValueWithUnit_000001",
                ),
            )
        msg = (
            "Compound selection with the specified combination of compound, "
            + "pharmaceutical dosage form, strength, route of administration, dispenser and delivery device already exists."
        )
        assert context.exception.msg == msg

        # Make a compound dosing selection with just-created study compound 'study_compound_created1'
        study_compound_dosing_created1: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created1.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uid1",
                    dose_value_uid="NumericValueWithUnit_000001",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        )

        assert (
            study_compound_dosing_created1.study_compound_dosing_uid
            == "StudyCompoundDosing_000001"
        )

        # Make a compound dosing selection with another study compound, while keeping all other details the same
        study_compound_dosing_created2: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created2.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uid1",
                    dose_value_uid="NumericValueWithUnit_000001",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        )
        assert (
            study_compound_dosing_created2.study_compound_dosing_uid
            == "StudyCompoundDosing_000002"
        )

        # Try to make a compound dosing selection with the same study compound and all other details
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created1.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uid1",
                    dose_value_uid="NumericValueWithUnit_000001",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        msg = "Compound dosing selection with the specified compound, dose value and dose frequency already exists."
        assert context.exception.msg == msg

        # Try to make a compound intervention with invalid selection values for:
        #   - Pharmaceutical dosage form
        #   - Compound strength value
        #   - Route of administration
        #   - Dispenser
        #   - Delivery device
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    dosage_form_uid="dosage_form_uidXYZ",
                ),
            )
        msg = (
            "Selected pharmaceutical dosage form is not valid for compound 'name-AAA'."
        )
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    device_uid="delivery_device_uidXYZ",
                ),
            )
        msg = "Selected delivery device is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    dispensed_in_uid="dispenser_uidXYZ",
                ),
            )
        msg = "Selected dispenser is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    route_of_administration_uid="route_of_administration_uidXYZ",
                ),
            )
        msg = "Selected route of administration is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    strength_value_uid="NumericValueWithUnit_00000XYZ",
                ),
            )
        msg = "Selected strength value is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        # Try to make a compound dosing intervention with invalid selection values for:
        #   - dose value
        #   - dose frequency
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created1.study_compound_uid,
                    dose_value_uid="NumericValueWithUnit_00000XYZ",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        msg = "Selected dose value is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created1.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uidXYZ",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        msg = "Selected dose frequency is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

    def test_audit_trail(self):
        compound1: Compound = TestUtils.create_compound(
            name="name-AAA",
            dosage_form_uids=["dosage_form_uid1"],
            delivery_devices_uids=["delivery_device_uid1"],
            dispensers_uids=["dispenser_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            strength_values_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            dose_values_uids=["NumericValueWithUnit_000001"],
        )
        compound_alias1a: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )
        compound_alias1b: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )

        compound2: Compound = TestUtils.create_compound(
            name="name-BBB",
            dosage_form_uids=["dosage_form_uid1"],
            delivery_devices_uids=["delivery_device_uid1"],
            dispensers_uids=["dispenser_uid1"],
            route_of_administration_uids=["route_of_administration_uid1"],
            strength_values_uids=["NumericValueWithUnit_000001"],
            dose_frequency_uids=["dose_frequency_uid1"],
            dose_values_uids=["NumericValueWithUnit_000001"],
        )
        compound_alias2a: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )
        compound_alias2b: CompoundAlias = TestUtils.create_compound_alias(
            compound_uid=compound1.uid
        )

        CompoundService().approve(compound1.uid)
        CompoundService().approve(compound2.uid)
        CompoundAliasService().approve(compound_alias1a.uid)
        CompoundAliasService().approve(compound_alias2a.uid)
        CompoundAliasService().approve(compound_alias1b.uid)
        CompoundAliasService().approve(compound_alias2b.uid)

        study_selection_element: StudySelectionElement = (
            StudyElementSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionElementCreateInput(
                    name="Elem1", short_name="el1", element_subtype_uid="term1"
                ),
            )
        )

        # Make a compound selection with compound alias 'compound_alias1a'
        study_compound_created1: StudySelectionCompound = (
            TestUtils.create_study_compound(
                study_uid=STUDY_UID,
                compound_alias_uid=compound_alias1a.uid,
                dosage_form_uid="dosage_form_uid1",
                device_uid="delivery_device_uid1",
                dispensed_in_uid="dispenser_uid1",
                route_of_administration_uid="route_of_administration_uid1",
                strength_value_uid="NumericValueWithUnit_000001",
            )
        )
        assert study_compound_created1.study_compound_uid == "StudyCompound_000001"

        # Make a compound selection with another compound alias, while keeping all other details the same
        study_compound_created2: StudySelectionCompound = (
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias2a.uid,
                    dosage_form_uid="dosage_form_uid1",
                    device_uid="delivery_device_uid1",
                    dispensed_in_uid="dispenser_uid1",
                    route_of_administration_uid="route_of_administration_uid1",
                    strength_value_uid="NumericValueWithUnit_000001",
                ),
            )
        )
        assert study_compound_created2.study_compound_uid == "StudyCompound_000003"

        # Try to make a compound selection with the same compound alias 'compound_alias1a' and all other details
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compound_alias_uid=compound_alias1a.uid,
                    dosage_form_uid="dosage_form_uid1",
                    device_uid="delivery_device_uid1",
                    dispensed_in_uid="dispenser_uid1",
                    route_of_administration_uid="route_of_administration_uid1",
                    strength_value_uid="NumericValueWithUnit_000001",
                ),
            )
        msg = (
            "Compound selection with the specified combination of compound, "
            + "pharmaceutical dosage form, strength, route of administration, dispenser and delivery device already exists."
        )
        assert context.exception.msg == msg

        # Make a compound dosing selection with just-created study compound 'study_compound_created1'
        study_compound_dosing_created1: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created1.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uid1",
                    dose_value_uid="NumericValueWithUnit_000001",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        )

        assert (
            study_compound_dosing_created1.study_compound_dosing_uid
            == "StudyCompoundDosing_000001"
        )

        # Make a compound dosing selection with another study compound, while keeping all other details the same
        study_compound_dosing_created2: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService().make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    study_compound_uid=study_compound_created2.study_compound_uid,
                    dose_frequency_uid="dose_frequency_uid1",
                    dose_value_uid="NumericValueWithUnit_000001",
                    study_element_uid=study_selection_element.element_uid,
                ),
            )
        )
        assert (
            study_compound_dosing_created2.study_compound_dosing_uid
            == "StudyCompoundDosing_000002"
        )

        # Now call audit trail
        items = StudyCompoundDosingSelectionService().get_all_selection_audit_trail(
            STUDY_UID
        )
        assert len(items) == 2
