"""Custom Lookups."""
from typing import Any

from django.db.models import Lookup


class Like(Lookup):  # type: ignore
    lookup_name = "ilike"

    def as_sql(self, compiler: Any, connection: Any) -> Any:
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s ILIKE %s" % (lhs, rhs), params
