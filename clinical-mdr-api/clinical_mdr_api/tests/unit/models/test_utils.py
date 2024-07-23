import unittest

import pytest
from parameterized import parameterized
from pydantic import BaseModel

import clinical_mdr_api.utils
from clinical_mdr_api.domains.libraries.parameter_term import (
    ParameterTermEntryVO,
    ParameterTermVO,
)
from clinical_mdr_api.models import utils


class TestModelUtils(unittest.TestCase):
    @parameterized.expand(
        [
            (True, "yes", "yes"),
            (False, "yes", "no"),
            (1, "yes", "yes"),
            (0, "yes", "no"),
            (1, "y", "y"),
            (0, "y", "n"),
            (1, "t", "t"),
            (0, "t", "f"),
            (1, "true", "true"),
            (0, "true", "false"),
            (1, "on", "on"),
            (0, "on", "off"),
            (1, "1", "1"),
            (0, "1", "0"),
        ]
    )
    def test_booltostr(self, boolean, true_format, expected):
        assert clinical_mdr_api.utils.booltostr(boolean, true_format) == expected

    def test_booltostr_raises_exception(self):
        self.assertRaises(
            ValueError, clinical_mdr_api.utils.booltostr, 1, "NonExistingTrueFormat"
        )

    @parameterized.expand(
        [
            ("<p>[abc] dfg</p>", "[abc] dfg", "<p>[Abc] dfg</p>"),
            ("<p>[a]</p>", "[a]", "<p>[A]</p>"),
            ("<p>[]</p>", "[]", "<p>[]</p>"),
            ("<p>[</p>", "[", "<p>[</p>"),
            ("<p>abc def</p>", "abc def", "<p>abc def</p>"),
            ("[abc] dfg", "[abc] dfg", "[Abc] dfg"),
            ("[a]", "[a]", "[A]"),
            ("[]", "[]", "[]"),
            ("[", "[", "["),
            ("abc def", "abc def", "abc def"),
            ("", "", ""),
        ]
    )
    def test_capitalize_first_letter_if_template_parameter(
        self, name, template_plain_name, expected
    ):
        assert (
            utils.capitalize_first_letter_if_template_parameter(
                name,
                template_plain_name,
                [ParameterTermEntryVO([ParameterTermVO("good"), "", ""], "", "")],
            )
            == expected
        )

    @parameterized.expand(
        [
            ("snake_case_input", "snakeCaseInput"),
            ("snake_32_case_input_", "snake32CaseInput"),
            ("..._snake_____case_input____", "...SnakeCaseInput"),
            ("zzz_snake_____case_input____", "zzzSnakeCaseInput"),
        ]
    )
    def test_snake_to_camel(self, input_data, expected):
        assert utils.snake_to_camel(input_data) == expected

    @parameterized.expand(
        [
            ("camelCaseInput", "camel_case_input"),
            ("camel32CaseInput_", "camel32_case_input_"),
            ("...Camel____CaseInput____", "..._camel_____case_input____"),
            ("zzzCamel____CaseInput____", "zzz_camel_____case_input____"),
        ]
    )
    def test_camel_to_snake(self, input_data, expected):
        assert utils.camel_to_snake(input_data) == expected

    @parameterized.expand(
        [
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                False,
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                },
            ),
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                True,
                {
                    "_camel_case_input": "x",
                    "_camel32_case_input_": "y",
                },
            ),
        ]
    )
    def test_snake_case_data(self, input_data, privates, expected):
        assert utils.snake_case_data(input_data, privates) == expected

    @parameterized.expand(
        [
            (
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                    "_camel32_case_input_": "y",
                },
                # pylint: disable=duplicate-key
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput": "y",
                },
            )
        ]
    )
    def test_camel_case_data(self, input_data, expected):
        assert utils.camel_case_data(input_data) == expected

    def test_is_attribute_in_model(self):
        model = type("model", (BaseModel,), {"z": "somehing", "x": 123})

        assert utils.is_attribute_in_model("x", model)
        assert not utils.is_attribute_in_model("y", model)


@pytest.mark.parametrize(
    "value, result",
    [
        ("0", 0),
        ("1", 1),
        ("yes", 1),
        ("No", 0),
        ("YES", 1),
        ("yEs", 1),
        ("no", 0),
        ("tRue", 1),
        ("False", 0),
        ("false", 0),
        ("Off", 0),
        ("on", 1),
        ("OFF", 0),
        ("oN", 1),
    ],
)
def test_strtobool(value, result):
    assert clinical_mdr_api.utils.strtobool(value) == result


@pytest.mark.parametrize(
    "value, exception_type",
    [
        (True, AttributeError),
        (False, AttributeError),
        (None, AttributeError),
        (0, AttributeError),
        (1, AttributeError),
        (-1, AttributeError),
        (0.1, AttributeError),
        ({}, AttributeError),
        ([1, 2], AttributeError),
        ("foo", ValueError),
        ("BAR", ValueError),
        ("Nein", ValueError),
        ("ni", ValueError),
        ("null", ValueError),
        ("NULL", ValueError),
        ("", ValueError),
        (" ", ValueError),
    ],
)
def test_strtobool_raises_exception(value, exception_type):
    with pytest.raises(exception_type):
        clinical_mdr_api.utils.strtobool(value)
