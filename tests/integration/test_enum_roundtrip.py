import pytest

from odata_query.roundtrip import AstToODataVisitor


@pytest.mark.parametrize(
    "odata_query",
    [
        # Basic enum comparisons
        "status eq TestStatus'enabled'",
        "status eq TestStatus'disabled'",
        "resource_type eq TestType'collection'",
        "resource_type eq TestType'tool'",
        
        # Combined conditions
        "status eq TestStatus'enabled' and resource_type eq TestType'collection'",
        "status eq TestStatus'disabled' or resource_type eq TestType'tool'",
        
        # Complex conditions
        "(status eq TestStatus'enabled' or status eq TestStatus'disabled') and resource_type eq TestType'collection'",
        "not (status eq TestStatus'disabled')",
        
        # Multiple conditions with different operators
        "status eq TestStatus'enabled' and (resource_type eq TestType'collection' or resource_type eq TestType'tool')",
        
        # Enum in lists
        "status in (TestStatus'enabled', TestStatus'disabled')",
        "resource_type in (TestType'collection', TestType'tool')",
        
        # Mixed conditions with enums and other types
        "status eq TestStatus'enabled' and id eq 123",
        "resource_type eq TestType'collection' and created_at gt 2023-01-01",
    ],
)
def test_enum_roundtrip(odata_query: str, lexer, parser):
    """Test that enum values are correctly preserved during roundtrip conversion."""
    ast = parser.parse(lexer.tokenize(odata_query))
    transformer = AstToODataVisitor()
    result = transformer.visit(ast)

    assert result == odata_query


@pytest.mark.parametrize(
    "odata_query",
    [
        # Test with different enum type names
        "user_status eq UserStatus'active'",
        "role_type eq RoleType'admin'",
        
        # Test with enum types containing dots
        "my.namespace.Status eq my.namespace.Status'pending'",
        
        # Test with enum values containing special characters
        "status eq TestStatus'with_underscore'",
        "status eq TestStatus'with-hyphen'",
        "status eq TestStatus'with.dot'",
    ],
)
def test_enum_variations_roundtrip(odata_query: str, lexer, parser):
    """Test that various enum type and value formats are preserved during roundtrip."""
    ast = parser.parse(lexer.tokenize(odata_query))
    transformer = AstToODataVisitor()
    result = transformer.visit(ast)

    assert result == odata_query
