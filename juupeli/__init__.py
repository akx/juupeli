import xml.etree.ElementTree as et
from collections import namedtuple
from dataclasses import dataclass, replace, field, asdict, is_dataclass
from enum import Enum
from typing import List, Any, Optional, Union, Callable


class Type(Enum):
    LIST = "list"
    LIST_ITEM = "list_item"
    DICT = "dict"
    DICT_ITEM = "dict_item"
    OBJECT = "object"
    INSTANCE_ITEM = "instance_item"


ITEM_TYPES = {Type.DICT_ITEM, Type.LIST_ITEM, Type.INSTANCE_ITEM}
KEYED_ITEM_TYPES = {Type.DICT_ITEM, Type.INSTANCE_ITEM}


class Attribute(namedtuple("_Attribute", ("key", "value"))):
    key: str
    value: str


@dataclass(frozen=True)
class ContextEntry:
    type: Type
    object: Any
    element: Any = None

    @property
    def key(self) -> Optional[Any]:
        if self.type in ITEM_TYPES:
            return self.object[0]
        return None


@dataclass(frozen=True)
class Context:
    ancestry: List[ContextEntry] = field(default_factory=list)

    def child(self, *, type, object, element=None) -> "Context":
        cen = ContextEntry(type=type, object=object, element=element)
        return replace(self, ancestry=self.ancestry + [cen],)

    @property
    def parent_entry(self) -> Optional[ContextEntry]:
        return self.ancestry[-2] if len(self.ancestry) > 1 else None

    @property
    def curr_entry(self) -> ContextEntry:
        return self.ancestry[-1]

    @property
    def curr_type(self) -> Type:
        return self.ancestry[-1].type

    @property
    def curr_object(self) -> Any:
        return self.ancestry[-1].object

    @property
    def curr_key(self) -> Optional[Any]:
        return self.ancestry[-1].key


class Codec:
    type_encoders = {}

    def encode(self, obj, *, context=Context()) -> List[Union[et.Element, Attribute]]:
        encoder = self.get_element_encoder(obj, context=context)
        if encoder:
            return encoder(obj, context=context)
        return self.encode_default(obj, context=context)

    def get_element_encoder(self, obj, *, context) -> Optional[Callable]:
        if isinstance(obj, dict):
            return self.encode_dict
        if isinstance(obj, (list, tuple, set)):
            return self.encode_list
        if is_dataclass(obj):
            return self.encode_object
        if isinstance(obj, (int, str, float, bool)):
            return self.encode_primitive
        type_encoder = self.type_encoders.get(type(obj))
        if type_encoder is not None:
            return type_encoder(obj, context=context)
        if isinstance(obj, object):
            return self.encode_object

    def encode_list(self, lst: list, *, context: Context) -> List[et.Element]:
        return self._encode_container(
            lst,
            root_getter=self.get_list_root,
            root_type=Type.LIST,
            item_type=Type.LIST_ITEM,
            mapping_getter=enumerate,
            context=context,
        )

    def encode_dict(self, dct: dict, *, context: Context) -> List[et.Element]:
        return self._encode_container(
            dct,
            root_getter=self.get_dict_root,
            root_type=Type.DICT,
            item_type=Type.DICT_ITEM,
            mapping_getter=lambda d: d.items(),
            context=context,
        )

    def encode_object(self, obj, *, context: Context) -> List[et.Element]:
        if is_dataclass(obj):
            mapping_getter = lambda d: asdict(d).items()
        else:
            mapping_getter = lambda d: vars(d).items()
        return self._encode_container(
            obj,
            root_getter=self.get_object_root,
            root_type=Type.OBJECT,
            item_type=Type.INSTANCE_ITEM,
            mapping_getter=mapping_getter,
            context=context,
        )

    def _encode_container(
        self,
        obj,
        *,
        root_getter,
        root_type,
        item_type,
        mapping_getter,
        context: Context,
    ) -> List[et.Element]:
        root = root_getter(
            context=context.child(type=root_type, object=obj, element=None)
        )
        if root is None:  # Skip serialization
            return []
        context = context.child(type=root_type, object=obj, element=root)
        self._encode_mapping(
            root, mapping=mapping_getter(obj), item_type=item_type, context=context
        )
        if isinstance(root, list):
            return root
        return [root]

    def _encode_mapping(
        self, root: Union[et.Element, list], mapping, item_type, context
    ):
        for key, value in mapping:
            result = self.encode(
                value,
                context=context.child(
                    object=(key, value), element=root, type=item_type
                ),
            )
            if result is None:
                continue

            for obj in result:
                if isinstance(result, Attribute):
                    # TODO: crash more gracefully if `root` is a bare list
                    root.attrib[result.key] = result.value
                else:
                    root.append(obj)

    def get_list_root(self, *, context: Context) -> Union[et.Element, list, None]:
        par_entry = context.parent_entry
        if par_entry:
            if (
                par_entry.type in KEYED_ITEM_TYPES
            ):  # Encoding a list within an instance; wrap in the key
                return et.Element(par_entry.key)
        return []

    def get_dict_root(self, *, context: Context) -> Union[et.Element, list, None]:
        tag = "dict"
        if (
            context.parent_entry and context.parent_entry.type in KEYED_ITEM_TYPES
        ):  # Encoding a dict within an instance
            tag = context.parent_entry.key
        elif context.curr_type in KEYED_ITEM_TYPES:
            tag = context.curr_key

        return et.Element(tag)

    def get_object_root(self, *, context: Context):
        tag = "object"
        if context.curr_type == Type.OBJECT:
            obj = context.curr_object
            tag = getattr(obj, "_xml_name", obj.__class__.__name__.lower())
        return et.Element(tag)

    def encode_default(self, obj, *, context: Context) -> List[et.Element]:
        raise NotImplementedError(f"Encoding {obj} (type {type(obj)} not supported")

    def encode_primitive(self, obj, *, context: Context) -> List[et.Element]:
        if context.curr_type in ITEM_TYPES:
            el = et.Element(self.get_primitive_item_tag(obj, context=context))
            el.text = str(obj)
            return [el]
        raise NotImplementedError(
            f"Encoding primitive {obj} (type {type(obj)} in context {context.curr_type} not supported"
        )

    def get_primitive_item_tag(self, obj, *, context: Context) -> str:
        if context.curr_type == Type.LIST_ITEM:
            return "element"
        return str(context.curr_key)


DEFAULT_CODEC = Codec()


def to_xml_string(obj, codec: Codec = None, root_tag: str = "document") -> str:
    if codec is None:
        codec = DEFAULT_CODEC
    els = codec.encode(obj)
    if len(els) > 1:
        root = et.Element(root_tag)
        root.extend(els)
        els = [root]
    return et.tostring(els[0], encoding="unicode")
