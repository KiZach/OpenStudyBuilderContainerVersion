from xml.etree.ElementTree import Element


def xml_diff(expected: Element, actual: Element, path: str = "Root"):
    """
    Compare two XML documents.
    Order of tags and attributes matters.
    """
    assert expected.tag == actual.tag, (
        f"\nPATH: {path}\n"
        f"EXPECTED tag: {expected.tag}\n"
        f"ACTUAL tag: {actual.tag}\n\n\n"
    )
    if isinstance(expected.text, str) and isinstance(actual.text, str):
        expected_text = expected.text.strip()
        actual_text = actual.text.strip()
        assert expected_text == actual_text, (
            f"\nPATH: {path}\n"
            f"Values of {expected.tag} don't match:\n"
            f"EXPECTED: {expected_text}\n"
            f"ACTUAL: {actual_text}\n\n\n"
        )
    assert set(expected.items()) == set(actual.items()), (
        f"\nPATH: {path}\n"
        f"Attributes of {expected.tag} don't match:\n"
        f"EXPECTED: {expected.items()}\n"
        f"ACTUAL: {actual.items()}\n\n\n"
    )

    expected_sub_elements = list(expected)
    actual_sub_elements = list(actual)

    for idx, elm in enumerate(actual_sub_elements):
        xml_diff(
            expected_sub_elements[idx],
            elm,
            f"{path}->{idx}:{expected_sub_elements[idx].tag}",
        )
