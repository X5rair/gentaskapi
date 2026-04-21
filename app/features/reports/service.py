"""Service layer for reports and integration management."""

from __future__ import annotations

import hashlib
import json
import secrets
import string
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.features.reports.schemas import OrganizationSettings

STATE_STORE = Path("volumes/reports_state.json")


class ReportsService:
    @staticmethod
    async def list_organizations() -> list[dict[str, Any]]:
        state = await ReportsService._load_state()
        return state["organizations"]

    @staticmethod
    async def create_organization(name: str, bin_value: str) -> dict[str, Any]:
        state = await ReportsService._load_state()
        if any(item["bin"] == bin_value for item in state["organizations"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization with this BIN already exists.",
            )
        now = datetime.now(UTC).isoformat()
        organization = {
            "id": f"org-{uuid4().hex[:10]}",
            "name": name,
            "bin": bin_value,
            "created_at": now,
            "updated_at": now,
            "settings": OrganizationSettings().model_dump(mode="json"),
        }
        state["organizations"].append(organization)
        await ReportsService._save_state(state)
        return organization

    @staticmethod
    async def get_organization_settings(organization_id: str) -> dict[str, Any]:
        state = await ReportsService._load_state()
        organization = ReportsService._find_by_id(state["organizations"], organization_id)
        return organization["settings"]

    @staticmethod
    async def update_organization_settings(
        organization_id: str,
        payload: OrganizationSettings | dict[str, Any],
    ) -> dict[str, Any]:
        state = await ReportsService._load_state()
        organization = ReportsService._find_by_id(state["organizations"], organization_id)
        prepared = (
            payload.model_dump(mode="json")
            if isinstance(payload, OrganizationSettings)
            else OrganizationSettings.model_validate(payload).model_dump(mode="json")
        )
        organization["settings"] = prepared
        organization["updated_at"] = datetime.now(UTC).isoformat()
        await ReportsService._save_state(state)
        return prepared

    @staticmethod
    async def create_database(payload: dict[str, Any]) -> dict[str, Any]:
        state = await ReportsService._load_state()
        ReportsService._find_by_id(state["organizations"], payload["organization_id"])

        mysql_name = ReportsService._build_unique_mysql_name(
            state=state,
            one_c_name=payload["one_c_database_name"],
        )
        now = datetime.now(UTC).isoformat()
        database = {
            "id": f"db-{uuid4().hex[:10]}",
            "organization_id": payload["organization_id"],
            "one_c_database_name": payload["one_c_database_name"],
            "customer_display_name": payload["customer_display_name"],
            "configuration": payload["configuration"],
            "release": payload["release"],
            "mysql_database_name": mysql_name,
            "api_key": ReportsService._new_api_key(),
            "active": True,
            "last_sync_at": None,
            "created_at": now,
            "updated_at": now,
        }
        state["databases"].append(database)
        await ReportsService._save_state(state)
        return database

    @staticmethod
    async def list_databases(organization_id: str | None = None) -> list[dict[str, Any]]:
        state = await ReportsService._load_state()
        if organization_id is None:
            return state["databases"]
        return [item for item in state["databases"] if item["organization_id"] == organization_id]

    @staticmethod
    async def delete_database(database_id: str) -> None:
        state = await ReportsService._load_state()
        database = ReportsService._find_by_id(state["databases"], database_id)
        state["databases"] = [item for item in state["databases"] if item["id"] != database_id]
        state["md5_tables"] = [
            item
            for item in state["md5_tables"]
            if not (
                item["database_id"] == database["id"]
            )
        ]
        await ReportsService._save_state(state)

    @staticmethod
    async def get_auth_keys(database_id: str) -> dict[str, Any]:
        state = await ReportsService._load_state()
        database = ReportsService._find_by_id(state["databases"], database_id)
        return {
            "database_id": database["id"],
            "api_key": database["api_key"],
            "mysql_database_name": database["mysql_database_name"],
            "updated_at": database["updated_at"],
        }

    @staticmethod
    async def create_invite(payload: dict[str, Any]) -> dict[str, Any]:
        state = await ReportsService._load_state()
        ReportsService._find_by_id(state["organizations"], payload["organization_id"])
        now = datetime.now(UTC).isoformat()
        invite = {
            "id": f"inv-{uuid4().hex[:10]}",
            "organization_id": payload["organization_id"],
            "email": payload["email"],
            "status": "pending",
            "can_view_reports": payload["can_view_reports"],
            "can_view_charts": payload["can_view_charts"],
            "can_view_comparisons": payload["can_view_comparisons"],
            "can_view_settlements": payload["can_view_settlements"],
            "can_view_db_and_keys": payload["can_view_db_and_keys"],
            "created_at": now,
        }
        state["invites"].append(invite)
        await ReportsService._save_state(state)
        return invite

    @staticmethod
    async def list_invites(organization_id: str | None = None) -> list[dict[str, Any]]:
        state = await ReportsService._load_state()
        if organization_id is None:
            return state["invites"]
        return [item for item in state["invites"] if item["organization_id"] == organization_id]

    @staticmethod
    async def create_settlement(payload: dict[str, Any]) -> dict[str, Any]:
        state = await ReportsService._load_state()
        ReportsService._find_by_id(state["organizations"], payload["organization_id"])
        settlement = {
            "id": f"set-{uuid4().hex[:10]}",
            "organization_id": payload["organization_id"],
            "document_type": payload["document_type"],
            "document_number": payload["document_number"],
            "amount": payload["amount"],
            "due_date": payload["due_date"],
            "paid": payload["paid"],
            "document_url": payload["document_url"],
            "created_at": datetime.now(UTC).isoformat(),
        }
        state["settlements"].append(settlement)
        await ReportsService._save_state(state)
        return settlement

    @staticmethod
    async def list_settlements(organization_id: str) -> list[dict[str, Any]]:
        state = await ReportsService._load_state()
        return [item for item in state["settlements"] if item["organization_id"] == organization_id]

    @staticmethod
    async def get_report_access_status(organization_id: str) -> dict[str, Any]:
        settlements = await ReportsService.list_settlements(organization_id=organization_id)
        unpaid = sum(1 for item in settlements if not item["paid"])
        return {
            "organization_id": organization_id,
            "reports_blocked": unpaid > 0,
            "unpaid_documents": unpaid,
        }

    @staticmethod
    async def md5_upsert(
        database_id: str,
        table_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        state = await ReportsService._load_state()
        database = ReportsService._find_by_id(state["databases"], database_id)
        table = ReportsService._find_or_create_md5_table(state, database_id, table_name)
        known_hashes = {row["md5"] for row in table["rows"]}

        inserted = 0
        skipped = 0
        for row in records:
            payload = row.get("payload", {})
            md5_hash = row.get("md5") or ReportsService._calc_md5(payload)
            if md5_hash in known_hashes:
                skipped += 1
                continue
            table["rows"].append(
                {
                    "md5": md5_hash,
                    "payload": payload,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
            known_hashes.add(md5_hash)
            inserted += 1

        now = datetime.now(UTC).isoformat()
        table["updated_at"] = now
        database["last_sync_at"] = now
        database["updated_at"] = now
        await ReportsService._save_state(state)
        return {
            "database_id": database_id,
            "table_name": table_name,
            "inserted": inserted,
            "skipped_existing": skipped,
            "total_after": len(table["rows"]),
        }

    @staticmethod
    async def md5_hash_list(database_id: str, table_name: str) -> dict[str, Any]:
        state = await ReportsService._load_state()
        ReportsService._find_by_id(state["databases"], database_id)
        table = ReportsService._find_or_create_md5_table(state, database_id, table_name)
        return {
            "database_id": database_id,
            "table_name": table_name,
            "hashes": [item["md5"] for item in table["rows"]],
        }

    @staticmethod
    async def md5_delete(database_id: str, table_name: str, hashes: list[str]) -> dict[str, Any]:
        state = await ReportsService._load_state()
        database = ReportsService._find_by_id(state["databases"], database_id)
        table = ReportsService._find_or_create_md5_table(state, database_id, table_name)
        before = len(table["rows"])
        target = set(hashes)
        table["rows"] = [item for item in table["rows"] if item["md5"] not in target]
        deleted = before - len(table["rows"])
        now = datetime.now(UTC).isoformat()
        table["updated_at"] = now
        database["last_sync_at"] = now
        database["updated_at"] = now
        await ReportsService._save_state(state)
        return {
            "database_id": database_id,
            "table_name": table_name,
            "deleted": deleted,
            "total_after": len(table["rows"]),
        }

    @staticmethod
    async def _load_state() -> dict[str, Any]:
        if not STATE_STORE.exists():
            return ReportsService._seed_state()
        try:
            return json.loads(STATE_STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return ReportsService._seed_state()

    @staticmethod
    async def _save_state(state: dict[str, Any]) -> None:
        STATE_STORE.parent.mkdir(parents=True, exist_ok=True)
        STATE_STORE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _seed_state() -> dict[str, Any]:
        return {
            "organizations": [],
            "databases": [],
            "invites": [],
            "settlements": [],
            "md5_tables": [],
        }

    @staticmethod
    def _find_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
        for item in items:
            if item.get("id") == item_id:
                return item
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource not found: {item_id}",
        )

    @staticmethod
    def _build_unique_mysql_name(state: dict[str, Any], one_c_name: str) -> str:
        prefix = "".join(ch if ch.isalnum() else "_" for ch in one_c_name.strip().lower()).strip("_")
        if not prefix:
            prefix = "onec"
        if len(prefix) > 40:
            prefix = prefix[:40]
        existing = {item["mysql_database_name"] for item in state["databases"]}
        while True:
            suffix = "".join(secrets.choice(string.digits) for _ in range(6))
            candidate = f"{prefix}_{suffix}"
            if candidate not in existing:
                return candidate

    @staticmethod
    def _new_api_key() -> str:
        return f"gtsk_{secrets.token_urlsafe(24)}"

    @staticmethod
    def _calc_md5(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.md5(raw).hexdigest()  # noqa: S324 - required by technical spec

    @staticmethod
    def _find_or_create_md5_table(
        state: dict[str, Any],
        database_id: str,
        table_name: str,
    ) -> dict[str, Any]:
        for item in state["md5_tables"]:
            if item["database_id"] == database_id and item["table_name"] == table_name:
                return item

        created = {
            "id": f"tbl-{uuid4().hex[:10]}",
            "database_id": database_id,
            "table_name": table_name,
            "rows": [],
            "updated_at": datetime.now(UTC).isoformat(),
        }
        state["md5_tables"].append(created)
        return created

