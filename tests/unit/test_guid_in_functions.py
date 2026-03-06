"""Tests for GUID support in string functions like contains, startswith, endswith."""
import pytest

from odata_query import ast, typing


class TestGUIDInStringFunctions:
    """Test that GUID literals can be used in string matching functions."""

    def test_contains_with_guid_infers_boolean(self):
        """Test that contains() with a GUID parameter returns Boolean type."""
        node = ast.Call(
            ast.Identifier("contains"),
            [ast.Identifier("field"), ast.GUID("7a7f024c-d21f-40b1-8296-b664a0de278c")],
        )
        result = typing.infer_type(node)
        assert result is ast.Boolean

    def test_startswith_with_guid_infers_boolean(self):
        """Test that startswith() with a GUID parameter returns Boolean type."""
        node = ast.Call(
            ast.Identifier("startswith"),
            [ast.Identifier("field"), ast.GUID("7a7f024c-d21f-40b1-8296-b664a0de278c")],
        )
        result = typing.infer_type(node)
        assert result is ast.Boolean

    def test_endswith_with_guid_infers_boolean(self):
        """Test that endswith() with a GUID parameter returns Boolean type."""
        node = ast.Call(
            ast.Identifier("endswith"),
            [ast.Identifier("field"), ast.GUID("7a7f024c-d21f-40b1-8296-b664a0de278c")],
        )
        result = typing.infer_type(node)
        assert result is ast.Boolean

    def test_guid_literal_infers_as_guid_type(self):
        """Test that GUID literals are properly typed."""
        node = ast.GUID("7a7f024c-d21f-40b1-8296-b664a0de278c")
        result = typing.infer_type(node)
        assert result is ast.GUID

    def test_typecheck_accepts_guid_for_substring_param(self):
        """Test that typecheck accepts GUID types for substring parameters."""
        guid_node = ast.GUID("7a7f024c-d21f-40b1-8296-b664a0de278c")
        # Should not raise an exception
        typing.typecheck(guid_node, (ast.String, ast.GUID), "substring")

    def test_typecheck_accepts_string_for_substring_param(self):
        """Test that typecheck still accepts String types for substring parameters."""
        string_node = ast.String("test")
        # Should not raise an exception
        typing.typecheck(string_node, (ast.String, ast.GUID), "substring")
