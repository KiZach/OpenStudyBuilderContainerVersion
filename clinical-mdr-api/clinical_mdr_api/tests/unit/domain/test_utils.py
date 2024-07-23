import unittest

import pytest
from parameterized import parameterized

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains import _utils


class TestServiceUtils(unittest.TestCase):
    @parameterized.expand(
        [
            ("ak", "639-1", "names", ["Akan"]),
            ("ak", "639-1", "639-1", "ak"),
            ("ak", "639-1", "639-2/T", "aka"),
            ("ak", "639-1", "639-2/B", "aka"),
            ("ak", "639-1", "639-3", ["aka", "fat", "twi"]),
            (
                "ak",
                "639-1",
                None,
                {
                    "names": ["Akan"],
                    "639-1": "ak",
                    "639-2/T": "aka",
                    "639-2/B": "aka",
                    "639-3": ["aka", "fat", "twi"],
                },
            ),
            ("aka", "639-3", "names", ["Akan"]),
            ("aka", "639-3", "639-1", "ak"),
            ("aka", "639-3", "639-2/T", "aka"),
            ("aka", "639-3", "639-2/B", "aka"),
            ("aka", "639-3", "639-3", ["aka", "fat", "twi"]),
            (
                "aka",
                "639-3",
                None,
                {
                    "names": ["Akan"],
                    "639-1": "ak",
                    "639-2/T": "aka",
                    "639-2/B": "aka",
                    "639-3": ["aka", "fat", "twi"],
                },
            ),
        ]
    )
    def test_get_iso_lang_data(self, value, key, return_key, expected):
        assert _utils.get_iso_lang_data(value, key, return_key) == expected

    def test_get_iso_lang_data_raises_exception(self):
        self.assertRaises(
            KeyError, _utils.get_iso_lang_data, "AK", "639-1", "639-3", False
        )
        self.assertRaises(
            KeyError, _utils.get_iso_lang_data, "ak", "639-1", "NonExistingKey"
        )
        self.assertRaises(
            exceptions.ValidationException,
            _utils.get_iso_lang_data,
            "ak",
            "NonExistingKey",
            "639-3",
        )
        self.assertRaises(
            KeyError, _utils.get_iso_lang_data, "NonExistingValue", "639-1", "639-3"
        )
        self.assertRaises(TypeError, _utils.get_iso_lang_data, 1, "639-1", "639-3")

    @parameterized.expand(
        [
            ("<title>This is a title</title>", "This is a title"),
            (
                """<html>
                    <head>
                        <title>Page Title</title>
                    </head>
                    <body>
                        <h1>This is a Heading</h1>
                        <p>This is a paragraph.</p>
                    </body>
                </html>""",
                "\n\nPage Title\n\n\nThis is a Heading\nThis is a paragraph.\n\n",
            ),
        ]
    )
    def test_strip_html(self, html, expected):
        assert _utils.strip_html(html) == expected

    @parameterized.expand(
        [
            ("text with [parameter]", "text with parameter"),
            (
                "<title>This is a title with a [parameter]</title>",
                "This is a title with a parameter",
            ),
        ]
    )
    def test_convert_to_plain(self, text, expected):
        assert _utils.convert_to_plain(text) == expected

    @parameterized.expand(
        [
            ("text only", []),
            ("text with [x]", ["x"]),
            ("text with [x] and [y]", ["x", "y"]),
        ]
    )
    def test_extract_parameters(self, name, expected):
        assert _utils.extract_parameters(name) == expected

    @parameterized.expand(
        [
            ("", False),
            (" ", False),
            ("x [", False),
            ("x ]", False),
            ("x []", False),
            ("x ] y [", False),
            ("x [y[a]]", False),
            ("x", True),
            ("x [y]", True),
            ("x ()", True),
        ]
    )
    def test_is_syntax_of_template_name_correct(self, name, expected):
        assert _utils.is_syntax_of_template_name_correct(name) == expected

    def test_is_syntax_of_template_name_correct_raises_exception(self):
        self.assertRaises(TypeError, _utils.is_syntax_of_template_name_correct, 1)

    @parameterized.expand(
        [
            ({"x": "aaa", "y": "bbb"}, {"_x": "aaa", "_y": "bbb"}),
            ({"_x": "aaa", "__y": "bbb"}, {"_x": "aaa", "__y": "bbb"}),
        ]
    )
    def test_factorize_dict(self, data, expected):
        assert _utils.factorize_dict(data) == expected

    @parameterized.expand(
        [
            ({"x": "aaa", "y": "bbb"}, {"x": "aaa", "y": "bbb"}),
            ({"_x": "aaa", "__y": "bbb"}, {"x": "aaa", "_y": "bbb"}),
        ]
    )
    def test_defactorize_dict(self, data, expected):
        assert _utils.defactorize_dict(data) == expected


@pytest.mark.parametrize(
    "inpt, result",
    [
        pytest.param("", None),
        pytest.param("   ", None),
        pytest.param("x", "x"),
        pytest.param(" x ", "x"),
        pytest.param("Hello ", "Hello"),
        pytest.param(" world", "world"),
        pytest.param(" Lord ", "Lord"),
        pytest.param("TomAte", "TomAte"),
        pytest.param(" 007", "007"),
        pytest.param(" lATe sh3r!0ck #holme Z", "lATe sh3r!0ck #holme Z"),
        pytest.param(None, None),
    ],
)
def test_normalize_string(inpt: str | None, result: str | None):
    assert _utils.normalize_string(inpt) == result


@pytest.mark.parametrize(
    "inpt, exception_class",
    [
        pytest.param(1, AttributeError),
        pytest.param(3.14, AttributeError),
        pytest.param(True, AttributeError),
    ],
)
def test_normalize_string_exceptions(inpt: str | None, exception_class):
    with pytest.raises(exception_class):
        _utils.normalize_string(inpt)
