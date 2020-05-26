from dataclasses import dataclass

import pytest

from juupeli import (
    to_xml_string,
    BaseCodec,
    Context,
    Type,
    Attribute,
    annotate,
    EncodeResult,
)
from juupeli_tests.fixtures import get_posankka
from juupeli_tests.utils import prettify_xml


class CustomCodec(BaseCodec):
    # Example of a custom codec that encodes all numeric and boolean primitives on instances as attributes

    def encode_primitive(self, obj, *, context: Context) -> EncodeResult:
        if isinstance(obj, (int, bool)) and context.parent_entry.type == Type.OBJECT:
            return [Attribute(context.curr_key, str(obj))]
        return super().encode_primitive(obj, context=context)


@pytest.mark.parametrize("codec", (None, BaseCodec(), CustomCodec()))
def test_posankka(codec):
    person = get_posankka()
    print(prettify_xml(to_xml_string(person, codec=codec)))


def test_no_instances():
    # TODO: This will result (somewhat buggily) in
    #       ...
    #       <adjectives>
    #       	<element>hernekeitto</element>
    #       	<element>viina</element>
    #       	<element>teline</element>
    #       	<element>johannes</element>
    #       </adjectives>
    #       ...
    thing = [
        {
            "hello": "world",
            "adjectives": {"hernekeitto", ("viina", "teline"), "johannes"},
        },
        [1, 2, 4, "hello", {"nnep": "pen"}],
        "aha!",
    ]
    xml = prettify_xml(to_xml_string(thing))
    print(xml)


def test_attribute_annotation():
    @annotate(as_attributes={"x", "y"})
    @dataclass
    class Coordinate:
        x: int
        y: int
        color: str

    coords = [
        Coordinate(x=15, y=33, color="purple"),
        Coordinate(x=25, y=13, color="yes, please"),
    ]
    xml = prettify_xml(to_xml_string(coords, root_tag="coordinates"))
    print(xml)
    assert 'coordinate x="15" y="33"' in xml


def test_attribute_annotation():
    @annotate(as_attributes={"attr_dict"})
    @dataclass
    class Wall:
        color: str
        attr_dict: dict

    coords = [
        Wall(attr_dict={"ayy": "lmao"}, color="purple"),
        Wall(attr_dict={"ayy": "lmes"}, color="yes, please"),
    ]
    xml = prettify_xml(to_xml_string(coords, root_tag="room"))
    print(xml)
    assert 'wall ayy="lmao"' in xml
