from dataclasses import dataclass, field
from typing import List, Optional
from xml.etree import ElementTree as et

from xml.dom import minidom

from juupeli import to_xml_string, Codec, Context, Type, Attribute


def prettify_xml(xml_string):
    dom = minidom.parseString(xml_string)
    return dom.toprettyxml()


class Address:
    city: str
    state: str


@dataclass
class Person:
    id: int
    first_name: str
    last_name: str
    main_address: Optional[Address]
    addresses: List[Address]
    cool: bool
    age: int = 332
    extra: dict = field(default_factory=dict)


# Not dataclasses
addr1 = Address()
addr1.city = "turku"
addr1.state = "ulkomaat"
addr2 = Address()
addr2.city = "espoo"
addr2.state = "uusimaa"

# Dataclass
person = Person(
    id=811,
    first_name="pos",
    last_name="ankka",
    main_address=addr1,
    cool=True,
    addresses=[addr1, addr2],
    extra={"hello": "world"},
)


class CustomCodec(Codec):
    # Example of a custom codec that encodes all numeric and boolean primitives on instances as attributes

    def encode_primitive(self, obj, *, context: Context) -> List[et.Element]:
        if isinstance(obj, (int, bool)) and context.parent_entry.type == Type.OBJECT:
            return Attribute(context.curr_key, str(obj))
        return super().encode_primitive(obj, context=context)


def test_juupeli(codec=None):
    print(prettify_xml(to_xml_string(person, codec=codec)))


if __name__ == "__main__":
    test_juupeli()
    test_juupeli(codec=CustomCodec())
