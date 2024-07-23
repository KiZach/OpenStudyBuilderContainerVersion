from mdr_standards_import.scripts.entities.cdisc_ct.codelist import Codelist
from mdr_standards_import.scripts.entities.cdisc_ct.codelist_attributes import (
    CodelistAttributes,
)


class TestCodelist:
    def test__add_attributes__same_attributes__consistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", True, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is True

    def test__add_attributes__different_name__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name1", "sv", "preferred_term", "definition", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name2", "sv", "preferred_term", "definition", True, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__add_attributes__different_sv__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv1", "preferred_term", "definition", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name", "sv2", "preferred_term", "definition", True, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__add_attributes__different_pterm__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv", "preferred_term1", "definition", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name", "sv", "preferred_term2", "definition", True, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__add_attributes__different_definition__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition1", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition2", True, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__add_attributes__different_extensible__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", True, [""]
        )
        attributes2 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", False, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__add_attributes__different_synonyms__inconsistent(self):
        # given
        codelist = Codelist("C123")
        attributes1 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", False, []
        )
        attributes2 = CodelistAttributes(
            "name", "sv", "preferred_term", "definition", False, [""]
        )

        # when
        codelist.add_attributes(attributes1, None)
        codelist.add_attributes(attributes2, None)

        # then
        assert codelist.has_consistent_attributes() is False

    def test__is_name_ok_for_single_codelist__not_ok(self):
        # given
        codelist = Codelist("c1")
        codelist.add_attributes(
            CodelistAttributes("Dictionary Name", None, None, None, None, None), None
        )

        # when
        # then
        assert codelist.is_name_ok_for_single_codelist() == False

    def test__is_name_ok_for_single_codelist__ok(self):
        # given
        codelist = Codelist("c1")
        codelist.add_attributes(
            CodelistAttributes(
                "Dictionary Name Codelist", None, None, None, None, None
            ),
            None,
        )

        # when
        # then
        assert codelist.is_name_ok_for_single_codelist() == True
