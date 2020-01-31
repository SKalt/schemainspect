from typing import Optional, Union

from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from .inspector import DBInspector, NullInspector
from .misc import connection_from_s_or_c
from .pg import PostgreSQL

SUPPORTED = {"postgresql": PostgreSQL}


def get_inspector(
    x: Union[None, Session, Connection], schema: str = None
) -> Union[NullInspector]:
    """
    Get an inspector for
    """
    if x is None:
        return NullInspector()

    c = connection_from_s_or_c(x)
    try:
        ic = SUPPORTED[c.dialect.name]
    except KeyError:
        raise NotImplementedError

    inspected: DBInspector = ic(c)
    if schema:
        inspected.one_schema(schema)
    return inspected
