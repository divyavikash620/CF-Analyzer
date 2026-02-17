from sqlalchemy.orm import declarative_base

# All ORM models should inherit from this `Base`.
# Keep business logic out of models — models define schema only.
Base = declarative_base()
