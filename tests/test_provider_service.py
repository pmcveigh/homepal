from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import ServiceProvider
from homepal.services.task_service import TaskService


def test_create_and_filter_providers():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        svc = TaskService(session)
        svc.create_provider(
            name="Octopus Energy",
            service_type="Energy (Electricity)",
            account_number="A-001",
            phone_number="0808 164 1088",
            monthly_cost_estimate=Decimal("92.40"),
            contract_end_date=date(2027, 4, 1),
        )
        svc.create_provider(name="Thames Water", service_type="Water", account_number="W-99")
        session.commit()

        filtered = svc.list_providers(service_type="Water")
        assert len(filtered) == 1
        assert filtered[0].name == "Thames Water"

        searched = svc.list_providers(search="a-001")
        assert len(searched) == 1
        assert searched[0].name == "Octopus Energy"


def test_update_and_delete_provider():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        svc = TaskService(session)
        provider = svc.create_provider(name="British Gas", service_type="Energy (Gas)")
        session.commit()

        svc.update_provider(provider.id, name="British Gas HomeCare", service_type="Boiler Cover", phone_number="0333 202 9802")
        session.commit()

        stored = session.get(ServiceProvider, provider.id)
        assert stored is not None
        assert stored.name == "British Gas HomeCare"
        assert stored.service_type == "Boiler Cover"

        svc.delete_provider(provider.id)
        session.commit()
        assert session.get(ServiceProvider, provider.id) is None
