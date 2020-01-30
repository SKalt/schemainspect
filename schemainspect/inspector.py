import sys
from typing import Any, Dict, Type, TypeVar, Union

from sqlalchemy.dialects.postgresql import dialect as postgresql
from sqlalchemy.engine import Connection
from typing_extensions import Protocol  # new in 3.8

T = TypeVar("T")


# FIXME: mypy should infer the dialect types
class SqlalchemyType(Protocol[T]):
    python_type: Type[T]


def to_pytype(sqla_dialect: postgresql, typename: str) -> Union[Type[None], Type[T]]:
    try:
        ischema_names: Dict[str, SqlalchemyType[T]] = sqla_dialect.ischema_names
        sqla_obj = ischema_names[typename]()
    except KeyError:
        return type(None)

    try:
        return sqla_obj.python_type

    except (NotImplementedError):
        return type(sqla_obj)


class DBInspector(object):
    # TODO: load_all
    def __init__(self, c: Connection, include_internal: bool = False) -> None:
        self.c = c
        self.engine = self.c.engine
        self.dialect = self.engine.dialect
        self.include_internal = include_internal
        self.load_all()  # <-- ????

    def to_pytype(self, typename: str) -> Union[Type[None], Type[T]]:
        return to_pytype(self.dialect, typename)


class NullInspector(DBInspector):
    def __init__(self) -> None:
        pass

    def __getattr__(self, name: str) -> Dict[Any, Any]:
        return {}
