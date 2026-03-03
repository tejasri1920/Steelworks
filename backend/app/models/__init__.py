# app/models/__init__.py
#
# Imports all ORM models so that when `Base.metadata.create_all(engine)` is
# called (e.g., in tests), SQLAlchemy has seen all table definitions.
# Without these imports, models defined in sub-modules would be unknown to
# `Base.metadata` and `create_all` would create an empty database.

from app.models.lot import Lot                          # noqa: F401
from app.models.production import ProductionRecord      # noqa: F401
from app.models.inspection import InspectionRecord      # noqa: F401
from app.models.shipping import ShippingRecord          # noqa: F401
from app.models.data_completeness import DataCompleteness  # noqa: F401
