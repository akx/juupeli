from dataclasses import dataclass, field
from typing import Optional, List


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


def get_posankka() -> Person:
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
    return person
