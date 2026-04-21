"""Persistence helpers for the catalog admin API."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from app.features.catalog.schemas import CatalogState

CATALOG_STORE = Path("volumes/catalog.json")


class CatalogService:
    @staticmethod
    async def load_catalog() -> CatalogState:
        if not CATALOG_STORE.exists():
            return CatalogState.model_validate(CatalogService._seed_catalog())

        try:
            payload = json.loads(CATALOG_STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = CatalogService._seed_catalog()

        return CatalogState.model_validate(payload)

    @staticmethod
    async def save_catalog(state: CatalogState | dict) -> CatalogState:
        if isinstance(state, CatalogState):
            payload = state.model_dump(mode="json")
        else:
            payload = CatalogState.model_validate(state).model_dump(mode="json")

        payload.setdefault("meta", {})
        payload["meta"]["updated_at"] = datetime.now(UTC).isoformat()
        payload["meta"].setdefault("schema_version", 1)

        CATALOG_STORE.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_STORE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return CatalogState.model_validate(payload)

    @staticmethod
    def _seed_catalog() -> dict:
        return deepcopy(
            {
                "meta": {
                    "schema_version": 1,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
                "countries": [
                    {
                        "id": "country-kz",
                        "name": "Казахстан",
                        "code": "KZ",
                        "sort_order": 1,
                    },
                    {
                        "id": "country-kg",
                        "name": "Кыргызстан",
                        "code": "KG",
                        "sort_order": 2,
                    },
                ],
                "configurations": [
                    {
                        "id": "cfg-kz-buh",
                        "country_id": "country-kz",
                        "name": "Бухгалтерия для Казахстана, редакция 3.0",
                        "version_code": "3.0",
                        "extension_version": "1.0",
                        "sort_order": 1,
                    },
                    {
                        "id": "cfg-kz-ut",
                        "country_id": "country-kz",
                        "name": "Управление торговлей для Казахстана, редакция 3.0",
                        "version_code": "3.0",
                        "extension_version": "1.0",
                        "sort_order": 2,
                    },
                ],
                "versions": [
                    {
                        "id": "ver-kz-buh-30591",
                        "configuration_id": "cfg-kz-buh",
                        "version": "3.0.59.1",
                        "release": "3.0.59.1",
                        "sort_order": 1,
                    },
                    {
                        "id": "ver-kz-buh-30651",
                        "configuration_id": "cfg-kz-buh",
                        "version": "3.0.65.1",
                        "release": "3.0.65.1",
                        "sort_order": 2,
                    },
                    {
                        "id": "ver-kz-ut-30321",
                        "configuration_id": "cfg-kz-ut",
                        "version": "3.0.32.1",
                        "release": "3.0.32.1",
                        "sort_order": 1,
                    },
                ],
                "clients": [
                    {
                        "id": "client-sample-1",
                        "name": "ТОО Sample Trade",
                        "bin": "123456789012",
                        "active": True,
                        "sort_order": 1,
                    },
                    {
                        "id": "client-sample-2",
                        "name": "ТОО Service House",
                        "bin": "987654321098",
                        "active": True,
                        "sort_order": 2,
                    },
                ],
                "queries": [
                    {
                        "id": "query-root-buh",
                        "parent_id": None,
                        "code": "000000001",
                        "name": "Бухгалтерия для Казахстана, редакция 3.0",
                        "query_type": "general",
                        "hide_from_client": False,
                        "client_id": None,
                        "country_id": "country-kz",
                        "configuration_ids": ["cfg-kz-buh"],
                        "version_ids": ["ver-kz-buh-30591", "ver-kz-buh-30651"],
                        "query_text": "ВЫБРАТЬ ...",
                        "parameters_text": "ПараметрыК_Запросу.Вставить(...)",
                        "sort_order": 1,
                        "columns": [
                            {
                                "id": "col-1",
                                "report_name": "РеализацияТоваров",
                                "report_prefix": "Отчет_",
                                "eng_name": "zaregistrirovannayaorganizaciya",
                                "rus_name": "ЗарегистрированнаяОрганизация",
                                "column_number": 1,
                                "visible": True,
                                "grouped": False,
                                "column_type": "Организация",
                            },
                            {
                                "id": "col-2",
                                "report_name": "РеализацияТоваров",
                                "report_prefix": "Отчет_",
                                "eng_name": "dokum",
                                "rus_name": "Документ",
                                "column_number": 2,
                                "visible": True,
                                "grouped": False,
                                "column_type": "Строка",
                            },
                        ],
                    },
                    {
                        "id": "query-child-rt",
                        "parent_id": "query-root-buh",
                        "code": "000000002",
                        "name": "РеализацияТоваров",
                        "query_type": "general",
                        "hide_from_client": False,
                        "client_id": None,
                        "country_id": "country-kz",
                        "configuration_ids": ["cfg-kz-buh"],
                        "version_ids": ["ver-kz-buh-30591"],
                        "query_text": "ВЫБРАТЬ ...",
                        "parameters_text": "",
                        "sort_order": 1,
                        "columns": [
                            {
                                "id": "col-3",
                                "report_name": "РеализацияТоваров",
                                "report_prefix": "Отчет_",
                                "eng_name": "organizaciya",
                                "rus_name": "Организация",
                                "column_number": 1,
                                "visible": True,
                                "grouped": False,
                                "column_type": "Организация",
                            },
                            {
                                "id": "col-4",
                                "report_name": "РеализацияТоваров",
                                "report_prefix": "Отчет_",
                                "eng_name": "podrazdelenie",
                                "rus_name": "Подразделение",
                                "column_number": 2,
                                "visible": True,
                                "grouped": False,
                                "column_type": "Подразделение организации",
                            },
                        ],
                    },
                    {
                        "id": "query-child-individual",
                        "parent_id": "query-root-buh",
                        "code": "000000011",
                        "name": "РеестрРеализаций",
                        "query_type": "individual",
                        "hide_from_client": True,
                        "client_id": "client-sample-1",
                        "country_id": "country-kz",
                        "configuration_ids": ["cfg-kz-buh"],
                        "version_ids": ["ver-kz-buh-30591"],
                        "query_text": "ВЫБРАТЬ ...",
                        "parameters_text": "",
                        "sort_order": 2,
                        "columns": [
                            {
                                "id": "col-5",
                                "report_name": "РеестрРеализаций",
                                "report_prefix": "Отчет_",
                                "eng_name": "dokument",
                                "rus_name": "Документ",
                                "column_number": 1,
                                "visible": True,
                                "grouped": False,
                                "column_type": "Строка",
                            }
                        ],
                    },
                ],
            }
        )
