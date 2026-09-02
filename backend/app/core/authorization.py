from fastapi import HTTPException, status

ROLE_OPERATIONS = {
    "read": {"Admin", "Approver", "Clerk", "Viewer"},
    "statistics": {"Admin", "Approver", "Viewer"},
    "upload": {"Admin", "Approver", "Clerk"},
    "approve": {"Admin", "Approver"},
    "delete": {"Admin"},
    "supplier_admin": {"Admin"},
}


class AuthorizationPolicy:
    _roles_by_operation = ROLE_OPERATIONS

    def allows(self, operation: str, roles: list[str]) -> bool:
        return bool(self._roles_by_operation.get(operation, set()).intersection(roles))

    def permissions_for(self, roles: list[str]) -> set[str]:
        return {operation for operation in self._roles_by_operation if self.allows(operation, roles)}

    def authorize(self, operation: str, roles: list[str]) -> None:
        if not self.allows(operation, roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
