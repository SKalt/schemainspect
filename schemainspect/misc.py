import inspect
from typing import IO, Any, List, Optional, Union

from pkg_resources import resource_stream as pkg_resource_stream
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session


def connection_from_s_or_c(
    s_or_c: Union[Session, Connection]
) -> Connection:  # pragma: no cover
    if isinstance(s_or_c, Connection):
        return s_or_c
    if isinstance(s_or_c, Session):
        return s_or_c.connection()
    else:
        raise AssertionError(f"{s_or_c} is not a sqlalchemy Connection or Session")


class AutoRepr(object):  # pragma: no cover
    def __repr__(self) -> str:
        cname = self.__class__.__name__
        vals = [
            "{}={}".format(k, repr(v))
            for k, v in sorted(self.__dict__.items())
            if not k.startswith("_")
        ]
        return "{}({})".format(cname, ", ".join(vals))

    def __str__(self) -> str:
        return repr(self)

    def __ne__(self, other: Any) -> bool:
        return not self == other


def quoted_identifier(
    identifier: str,
    schema: Optional[str] = None,
    identity_arguments: Any = None,  # FIXME
) -> str:
    s = '"{}"'.format(identifier.replace('"', '""'))
    if schema:
        s = '"{}".{}'.format(schema.replace('"', '""'), s)
    if identity_arguments is not None:
        s = "{}({})".format(s, identity_arguments)
    return s


def external_caller() -> str:
    i = inspect.stack()
    names: List[str] = []
    for x in range(len(i)):
        module = inspect.getmodule(i[x][0])
        if module is not None:
            names.append(module.__name__)
    return next(
        name for name in names if name != __name__
    )  # FIXME: edge case where names == []. Return '' to preserve typing, or `assert names` to fail informatively?


def resource_stream(subpath: str) -> IO[bytes]:
    module_name = external_caller()
    return pkg_resource_stream(module_name, subpath)


def resource_text(subpath: str) -> str:
    with resource_stream(subpath) as f:
        return f.read().decode("utf-8")
