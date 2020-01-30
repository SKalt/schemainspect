from typing import Any, List, Optional

from .misc import AutoRepr, quoted_identifier

# TODO: consider using jinja2-style subclassing of str to mark
# templated SQL as safe.


class Inspected(AutoRepr):
    name: str
    schema: str

    @property
    def quoted_full_name(self) -> str:
        return "{}.{}".format(
            quoted_identifier(self.schema), quoted_identifier(self.name)
        )

    @property
    def signature(self) -> str:
        return self.quoted_full_name

    @property
    def unquoted_full_name(self) -> str:
        return "{}.{}".format(self.schema, self.name)

    @property
    def quoted_name(self) -> str:
        return quoted_identifier(self.name)

    @property
    def quoted_schema(self) -> str:
        return quoted_identifier(self.schema)

    def __ne__(self, other: Any) -> bool:
        return not self == other


class TableRelated(object):
    schema: str
    table_name: str

    @property
    def quoted_full_table_name(self) -> str:
        return "{}.{}".format(
            quoted_identifier(self.schema), quoted_identifier(self.table_name)
        )


class ColumnInfo(AutoRepr):
    def __init__(
        self,
        name: str,
        dbtype,
        pytype,
        default=None,
        not_null: bool = False,
        is_enum: bool = False,
        enum=None,
        dbtypestr: Optional[str] = None,
        collation=None,
    ) -> None:
        self.name = name or ""
        self.dbtype = dbtype
        self.dbtypestr = dbtypestr or dbtype
        self.pytype = pytype
        self.default = default or None
        self.not_null = not_null
        self.is_enum = is_enum
        self.enum = enum
        self.collation = collation

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ColumnInfo):
            return (
                self.name == other.name
                and self.dbtype == other.dbtype
                and self.dbtypestr == other.dbtypestr
                and self.pytype == other.pytype
                and self.default == other.default
                and self.not_null == other.not_null
                and self.enum == other.enum
                and self.collation == other.collation
            )
        else:
            return False

    def alter_clauses(self, other: ColumnInfo) -> List[str]:
        clauses: List[str] = []
        if self.default != other.default:
            clauses.append(self.alter_default_clause)
        if self.not_null != other.not_null:
            clauses.append(self.alter_not_null_clause)
        if self.dbtypestr != other.dbtypestr or self.collation != other.collation:
            clauses.append(self.alter_data_type_clause)
        return clauses

    def change_enum_to_string_statement(self, table_name: str) -> str:
        if self.is_enum:
            return "alter table {} alter column {} set data type varchar using {}::varchar;".format(
                table_name, self.quoted_name, self.quoted_name
            )

        else:
            raise ValueError

    def change_string_to_enum_statement(self, table_name: str) -> str:
        if self.is_enum:
            return "alter table {} alter column {} set data type {} using {}::{};".format(
                table_name,
                self.quoted_name,
                self.dbtypestr,
                self.quoted_name,
                self.dbtypestr,
            )

        else:
            raise ValueError

    def alter_table_statements(self, other: ColumnInfo, table_name: str) -> List[str]:
        prefix = "alter table {}".format(table_name)
        return ["{} {};".format(prefix, c) for c in self.alter_clauses(other)]

    @property
    def quoted_name(self) -> str:
        return quoted_identifier(self.name)

    @property
    def creation_clause(self) -> str:
        clause = "{} {}".format(self.quoted_name, self.dbtypestr)
        if self.not_null:
            clause += " not null"
        if self.default:
            clause += " default {}".format(self.default)
        return clause

    @property
    def add_column_clause(self) -> str:
        return "add column {}{}".format(self.creation_clause, self.collation_subclause)

    @property
    def drop_column_clause(self) -> str:
        return "drop column {k}".format(k=self.quoted_name)

    @property
    def alter_not_null_clause(self) -> str:
        keyword = "set" if self.not_null else "drop"
        return "alter column {} {} not null".format(self.quoted_name, keyword)

    @property
    def alter_default_clause(self) -> str:
        if self.default:
            alter = "alter column {} set default {}".format(
                self.quoted_name, self.default
            )
        else:
            alter = "alter column {} drop default".format(self.quoted_name)
        return alter

    @property
    def collation_subclause(self) -> str:
        if self.collation:
            collate = " collate {}".format(quoted_identifier(self.collation))
        else:
            collate = ""
        return collate

    @property
    def alter_data_type_clause(self) -> str:
        return "alter column {} set data type {}{} using {}::{}".format(
            self.quoted_name,
            self.dbtypestr,
            self.collation_subclause,
            self.quoted_name,
            self.dbtypestr,
        )


class InspectedSelectable(Inspected):
    def __init__(
        self,
        name: str,
        schema: str,
        columns,
        inputs=None,
        definition=None,
        dependent_on: Optional[List] = None,
        dependents: Optional[List] = None,
        comment: Optional[str] = None,
        relationtype: str = "unknown",
        parent_table=None,
        partition_def=None,
        rowsecurity: bool = False,
        forcerowsecurity: bool = False,
    ):
        self.name = name
        self.schema = schema
        self.inputs = inputs or []
        self.columns = columns
        self.definition = definition
        self.relationtype = relationtype
        self.dependent_on = dependent_on or []
        self.dependents = dependents or []
        self.dependent_on_all = []
        self.dependents_all = []
        self.constraints = {}
        self.indexes = {}
        self.comment = comment
        self.parent_table = parent_table
        self.partition_def = partition_def
        self.rowsecurity = rowsecurity
        self.forcerowsecurity = forcerowsecurity

    def __eq__(self, other: Any) -> bool:
        return (
            type(self) == type(other)
            and self.relationtype == other.relationtype
            and self.name == other.name
            and self.schema == other.schema
            and dict(self.columns) == dict(other.columns)
            and self.inputs == other.inputs
            and self.definition == other.definition
            and self.parent_table == other.parent_table
            and self.partition_def == other.partition_def
            and self.rowsecurity == other.rowsecurity
        )
