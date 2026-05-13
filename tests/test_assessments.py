"""Placeholder tests for the Azure CSA agent."""

from csa.assessments import QUERIES


def test_queries_are_defined():
    """Ensure all standard assessment queries are present."""
    expected = [
        "resource_count", "untagged_resources", "public_ips", "orphaned_disks",
        "nsg_any_rules", "vms_no_ahb", "advisor_cost", "management_groups",
        "vnets", "private_endpoints",
    ]
    for name in expected:
        assert name in QUERIES, f"Missing query: {name}"


def test_queries_are_nonempty_strings():
    """All queries should be non-empty KQL strings."""
    for name, query in QUERIES.items():
        assert isinstance(query, str) and len(query.strip()) > 10, f"Query '{name}' is invalid"
