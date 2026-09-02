import pytest
from fastapi import HTTPException

from backend.app.core.authorization import AuthorizationPolicy


OPERATIONS = ("read", "statistics", "upload", "approve", "delete", "supplier_admin")
PERMISSIONS_BY_ROLE = {
    "Admin": set(OPERATIONS),
    "Approver": {"read", "statistics", "upload", "approve"},
    "Clerk": {"read", "upload"},
    "Viewer": {"read", "statistics"},
}


@pytest.mark.parametrize("role, expected", PERMISSIONS_BY_ROLE.items())
def test_permissions_match_the_approved_role_matrix(role, expected):
    policy = AuthorizationPolicy()

    assert policy.permissions_for([role]) == expected


@pytest.mark.parametrize(
    "role, operation, allowed",
    [
        (role, operation, operation in permissions)
        for role, permissions in PERMISSIONS_BY_ROLE.items()
        for operation in OPERATIONS
    ],
)
def test_authorization_policy_allows_only_approved_operations(role, operation, allowed):
    policy = AuthorizationPolicy()

    assert policy.allows(operation, [role]) is allowed


def test_authorize_raises_for_a_denied_direct_operation():
    with pytest.raises(HTTPException) as error:
        AuthorizationPolicy().authorize("delete", ["Viewer"])

    assert error.value.status_code == 403
