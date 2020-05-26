from typing import List
from xml.etree import ElementTree as et

import pytest

from juupeli import to_xml_string, Codec, Context, Type, Attribute
from juupeli_tests.fixtures import get_posankka
from juupeli_tests.utils import prettify_xml


class CustomCodec(Codec):
    # Example of a custom codec that encodes all numeric and boolean primitives on instances as attributes

    def encode_primitive(self, obj, *, context: Context) -> List[et.Element]:
        if isinstance(obj, (int, bool)) and context.parent_entry.type == Type.OBJECT:
            return Attribute(context.curr_key, str(obj))
        return super().encode_primitive(obj, context=context)


@pytest.mark.parametrize("codec", (None, CustomCodec()))
def test_posankka(codec):
    person = get_posankka()
    print(prettify_xml(to_xml_string(person, codec=codec)))
