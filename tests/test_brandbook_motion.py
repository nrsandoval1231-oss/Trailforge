"""Resolve the actual stylesheet against paused and running DOM states."""
from pathlib import Path
from xml.etree import ElementTree

import cssselect2
import pytest
import tinycss2

CSS = Path(__file__).resolve().parents[1] / "brand/trailforge-v1/brandbook.css"


def computed_motion(state):
    document = ElementTree.fromstring(f'<html data-motion="{state}"><body><a /></body></html>')
    root = cssselect2.ElementWrapper.from_html_root(document)
    matcher = cssselect2.Matcher()
    for rule in tinycss2.parse_stylesheet(CSS.read_text(), skip_comments=True, skip_whitespace=True):
        if rule.type != "qualified-rule":
            continue  # No OS reduced-motion override in this fixture.
        declarations = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
        for selector in cssselect2.compile_selector_list(rule.prelude):
            matcher.add_selector(selector, declarations)
    values = {}
    for element in root.iter_subtree():
        for specificity, order, pseudo, declarations in matcher.match(element):
            for declaration in declarations:
                if declaration.type != "declaration":
                    continue
                key = (element.etree_element.tag, pseudo, declaration.lower_name)
                priority = (declaration.important, specificity, order)
                if key not in values or priority >= values[key][0]:
                    values[key] = (priority, tinycss2.serialize(declaration.value).strip())
    return {key: value for key, (_, value) in values.items()}


@pytest.mark.parametrize("tag", ["html", "body", "a"])
@pytest.mark.parametrize("pseudo", [None, "before", "after"])
def test_pause_disables_motion_on_root_descendants_and_pseudo_elements(tag, pseudo):
    values = computed_motion("off")
    assert values.get((tag, pseudo, "scroll-behavior")) == "auto"
    assert values.get((tag, pseudo, "transition")) == "none"
    assert values.get((tag, pseudo, "animation")) == "none"


def test_resume_restores_smooth_scroll_and_body_transition():
    values = computed_motion("on")
    assert values[("html", None, "scroll-behavior")] == "smooth"
    assert values[("body", None, "transition")] == "background .25s,color .25s"
