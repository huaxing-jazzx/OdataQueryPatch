import enum
import pytest
from sqlalchemy import Column, Enum, Integer, select

from odata_query.sqlalchemy import apply_odata_query
from .models import Base


class TestStatus(str, enum.Enum):
    enabled = "enabled"
    disabled = "disabled"


class TestType(str, enum.Enum):
    collection = "collection"
    tool = "tool"


class ResourceWithEnum(Base):
    __tablename__ = "resource_with_enum"

    id = Column(Integer, primary_key=True)
    status = Column(Enum(TestStatus))
    resource_type = Column(Enum(TestType))


@pytest.fixture
def sample_data_sess(db_session):
    s = db_session()
    r1 = ResourceWithEnum(status=TestStatus.enabled, resource_type=TestType.collection)
    r2 = ResourceWithEnum(status=TestStatus.disabled, resource_type=TestType.tool)
    r3 = ResourceWithEnum(status=TestStatus.enabled, resource_type=TestType.tool)
    s.add_all([r1, r2, r3])
    s.flush()
    yield s
    s.rollback()


@pytest.mark.parametrize(
    "query, exp_results",
    [
        ("status eq TestStatus'enabled'", 2),
        ("status eq TestStatus'disabled'", 1),
        ("resource_type eq TestType'collection'", 1),
        ("resource_type eq TestType'tool'", 2),
        ("status eq TestStatus'enabled' and resource_type eq TestType'collection'", 1),
        ("status eq TestStatus'enabled' and resource_type eq TestType'tool'", 1),
    ],
)
def test_enum_querying(query: str, exp_results: int, sample_data_sess):
    base_q = select(ResourceWithEnum)
    q = apply_odata_query(base_q, query)
    results = sample_data_sess.execute(q).scalars().all()
    assert len(results) == exp_results


@pytest.mark.parametrize(
    "query",
    [
        "status eq TestStatus'invalid'",  # Invalid enum value
        "status eq WrongEnum'enabled'",   # Invalid enum type
        "status eq 'enabled'",            # Missing enum type prefix
    ],
)
def test_invalid_enum_queries(query: str, sample_data_sess):
    base_q = select(ResourceWithEnum)
    with pytest.raises(Exception):  # Should raise appropriate exception
        q = apply_odata_query(base_q, query)
        sample_data_sess.execute(q).scalars().all()
