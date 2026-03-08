from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from homepal.models import ServiceProvider
from homepal.services.task_service import ProviderListRow, TaskService


@dataclass(slots=True)
class ProviderSaveDTO:
    id: str | None = None
    name: str = ""
    service_type: str = ""
    account_number: str = ""
    phone_number: str = ""
    website: str = ""
    monthly_cost_estimate: Decimal | None = None
    contract_end_date: date | None = None
    notes: str = ""


class ProviderService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    def list_providers(self, *, service_type: str = "all", search: str = "") -> list[ProviderListRow]:
        return self.task_service.list_providers(service_type=service_type, search=search)

    def save_provider(self, dto: ProviderSaveDTO) -> ServiceProvider:
        if dto.id:
            return self.task_service.update_provider(
                dto.id,
                name=dto.name,
                service_type=dto.service_type,
                account_number=dto.account_number,
                phone_number=dto.phone_number,
                website=dto.website,
                monthly_cost_estimate=dto.monthly_cost_estimate,
                contract_end_date=dto.contract_end_date,
                notes=dto.notes,
            )

        return self.task_service.create_provider(
            name=dto.name,
            service_type=dto.service_type,
            account_number=dto.account_number,
            phone_number=dto.phone_number,
            website=dto.website,
            monthly_cost_estimate=dto.monthly_cost_estimate,
            contract_end_date=dto.contract_end_date,
            notes=dto.notes,
        )

    def delete_provider(self, provider_id: str) -> None:
        self.task_service.delete_provider(provider_id)
