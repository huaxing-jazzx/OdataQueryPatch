from typing import Type

import sqlalchemy as sa
from sqlalchemy.sql.expression import BinaryExpression, ClauseElement, ColumnClause, BindParameter, literal
from sqlalchemy.types import Enum as SQLAEnum

from odata_query import ast, exceptions as ex, visitor

from . import common


class AstToSqlAlchemyCoreVisitor(common._CommonVisitors, visitor.NodeVisitor):
    """
    :class:`NodeVisitor` that transforms an :term:`AST` into a SQLAlchemy where
    clause using Core features.

    Args:
        table: A SQLalchemy table
    """

    def __init__(self, table: Type[sa.Table]):
        self.table = table

    def visit_Identifier(self, node: ast.Identifier) -> ColumnClause:
        """:meta private:"""
        try:
            return self.table.c[node.name]
        except KeyError:
            raise ex.InvalidFieldException(node.name)

    def visit_Attribute(self, node: ast.Attribute) -> ColumnClause:
        """:meta private:"""
        raise NotImplementedError(
            "Relationship traversal is not yet implemented for the SQLAlchemy Core visitor."
        )

    def visit_Compare(self, node: ast.Compare) -> BinaryExpression:
        """:meta private:"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.visit(node.comparator)
        return op(left, right)

    def visit_CollectionLambda(self, node: ast.CollectionLambda) -> ClauseElement:
        """:meta private:"""
        raise NotImplementedError(
            "Collection lambda is not yet implemented for the SQLAlchemy Core visitor."
        )

    def _get_column_for_identifier(self, name: str):
        try:
            return self.table.c[name]
        except KeyError:
            raise ex.InvalidFieldException(name)

    def visit_Enum(self, node: ast.Enum) -> BindParameter:
        ":meta private:"
        column = self._get_column_for_identifier(node.type_name)
        if not isinstance(column.type, SQLAEnum):
            raise ex.FilterValueError(
                f"Column {node.type_name} is not an Enum type"
            )
        
        # Validate that the enum value exists
        if node.value not in column.type.enums:
            raise ex.FilterValueError(
                f"Invalid enum value '{node.value}' for {node.type_name}. "
                f"Valid values are: {', '.join(column.type.enums)}"
            )
        
        return literal(node.value)
