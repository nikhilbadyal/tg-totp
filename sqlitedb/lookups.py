"""Custom Lookups."""

from typing import Any, Self

from django.db.models import Lookup


class ILike(Lookup):  # type: ignore[type-arg]
    """Custom Like lookup."""

    lookup_name = "ilike"

    def as_sql(self: Self, compiler: Any, connection: Any) -> Any:
        """SQL from ilike django opr."""
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return f"{lhs} ILIKE {rhs}", params
