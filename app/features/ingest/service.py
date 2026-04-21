"""Service layer for ingest uploads."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException, Request, UploadFile, status

JOB_STORE = Path("volumes/ingest_jobs.json")
RAW_ROOT = Path("volumes/ingest/raw")
EXTRACTED_ROOT = Path("volumes/ingest/extracted")
SQL_OPERATION_PATTERN = re.compile(
    r"\b(insert|create|drop|delete|update|alter|truncate)\b", re.IGNORECASE
)


class IngestService:
    @staticmethod
    async def create_job_from_request(request: Request) -> dict:
        RAW_ROOT.mkdir(parents=True, exist_ok=True)
        EXTRACTED_ROOT.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        content_type = request.headers.get("content-type", "").lower()

        if "multipart/form-data" in content_type:
            form = await request.form()
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multipart request must include a file field named 'file'.",
                )

            payload = await upload.read()
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty.",
                )

            source_system = str(form.get("source_system") or "1C")
            company_name = IngestService._optional_str(form.get("company_name"))
            note = IngestService._optional_str(form.get("note"))
            original_filename = upload.filename or f"payload-{timestamp}.zip"
            payload_kind = IngestService._detect_payload_kind(original_filename)
            stored_name = f"{timestamp}_{IngestService._safe_filename(original_filename)}"
            stored_path = RAW_ROOT / stored_name
            stored_path.write_bytes(payload)
        elif "application/json" in content_type:
            body = await request.body()
            if not body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON request body is empty.",
                )
            try:
                payload_json = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON payload: {exc}",
                ) from exc

            source_system = "1C"
            company_name = None
            note = "JSON payload received directly."
            original_filename = f"payload-{timestamp}.json"
            payload_kind = "json"
            stored_path = RAW_ROOT / original_filename
            stored_path.write_text(
                json.dumps(payload_json, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            payload = stored_path.read_bytes()
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Use multipart/form-data with file or application/json.",
            )

        job = {
            "id": str(uuid4()),
            "source_system": source_system,
            "company_name": company_name,
            "note": note,
            "payload_kind": payload_kind,
            "status": "queued",
            "original_filename": original_filename,
            "stored_path": str(stored_path),
            "payload_size_bytes": len(payload),
            "extracted_file_count": 0,
            "sql_statement_count": 0,
            "sql_file_names": [],
            "preview_payload": [],
            "received_at": datetime.now(UTC).isoformat(),
            "processing_started_at": None,
            "processing_finished_at": None,
            "error_message": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        await IngestService._save_job(job)
        asyncio.create_task(IngestService.process_job(UUID(job["id"])))
        return job

    @staticmethod
    async def list_jobs(limit: int = 20) -> list[dict]:
        jobs = await IngestService._load_jobs()
        jobs.sort(key=lambda item: item.get("received_at", ""), reverse=True)
        return jobs[:limit]

    @staticmethod
    async def get_job(job_id: UUID) -> dict:
        for job in await IngestService._load_jobs():
            if job.get("id") == str(job_id):
                return job
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingest job not found.",
        )

    @staticmethod
    async def process_job(job_id: UUID) -> None:
        jobs = await IngestService._load_jobs()
        index = next((i for i, job in enumerate(jobs) if job.get("id") == str(job_id)), -1)
        if index < 0:
            return

        job = jobs[index]
        try:
            job["status"] = "processing"
            job["processing_started_at"] = datetime.now(UTC).isoformat()
            job["updated_at"] = datetime.now(UTC).isoformat()
            await IngestService._save_jobs(jobs)

            stored_path = Path(job["stored_path"])
            preview_payload: list[dict] = []
            sql_file_names: list[str] = []
            statement_count = 0
            extracted_count = 0

            if job["payload_kind"] == "zip":
                extracted_dir = EXTRACTED_ROOT / job["id"]
                extracted_dir.mkdir(parents=True, exist_ok=True)

                try:
                    with ZipFile(stored_path) as archive:
                        for member in archive.infolist():
                            if member.is_dir():
                                continue
                            member_name = Path(member.filename).name
                            if not member_name:
                                continue
                            safe_name = IngestService._safe_filename(member_name)
                            data = archive.read(member)
                            (extracted_dir / safe_name).write_bytes(data)
                            extracted_count += 1

                            text = IngestService._decode_bytes(data)
                            if Path(member_name).suffix.lower() in {".txt", ".sql", ".json"}:
                                operations = len(SQL_OPERATION_PATTERN.findall(text))
                                statement_count += operations
                                sql_file_names.append(member_name)
                                preview_payload.append(
                                    {
                                        "file_name": member_name,
                                        "operations_detected": operations,
                                        "preview_lines": IngestService._preview_lines(text),
                                    }
                                )
                except BadZipFile as exc:
                    raise ValueError("Uploaded archive is not a valid ZIP file.") from exc
            else:
                text = IngestService._decode_bytes(stored_path.read_bytes())
                operations = len(SQL_OPERATION_PATTERN.findall(text))
                statement_count = operations
                extracted_count = 1
                sql_file_names = [job["original_filename"]]
                preview_payload.append(
                    {
                        "file_name": job["original_filename"],
                        "operations_detected": operations,
                        "preview_lines": IngestService._preview_lines(text),
                    }
                )

            job["preview_payload"] = preview_payload
            job["sql_file_names"] = sql_file_names
            job["sql_statement_count"] = statement_count
            job["extracted_file_count"] = extracted_count
            job["status"] = "completed"
            job["processing_finished_at"] = datetime.now(UTC).isoformat()
            job["error_message"] = None
            job["updated_at"] = datetime.now(UTC).isoformat()
            await IngestService._save_jobs(jobs)
        except Exception as exc:
            job["status"] = "failed"
            job["error_message"] = str(exc)
            job["processing_finished_at"] = datetime.now(UTC).isoformat()
            job["updated_at"] = datetime.now(UTC).isoformat()
            await IngestService._save_jobs(jobs)

    @staticmethod
    async def _load_jobs() -> list[dict]:
        if not JOB_STORE.exists():
            return []
        try:
            return json.loads(JOB_STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    @staticmethod
    async def _save_job(job: dict) -> None:
        jobs = await IngestService._load_jobs()
        jobs.append(job)
        await IngestService._save_jobs(jobs)

    @staticmethod
    async def _save_jobs(jobs: list[dict]) -> None:
        JOB_STORE.parent.mkdir(parents=True, exist_ok=True)
        JOB_STORE.write_text(
            json.dumps(jobs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _optional_str(value: object | None) -> str | None:
        if value is None:
            return None
        prepared = str(value).strip()
        return prepared or None

    @staticmethod
    def _safe_filename(filename: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
        return safe or "payload.dat"

    @staticmethod
    def _detect_payload_kind(filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".zip":
            return "zip"
        if suffix == ".json":
            return "json"
        if suffix in {".txt", ".sql"}:
            return "sql"
        return "binary"

    @staticmethod
    def _decode_bytes(payload: bytes) -> str:
        for encoding in ("utf-8", "cp1251", "latin-1"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        return payload.decode("utf-8", errors="replace")

    @staticmethod
    def _preview_lines(text: str, max_lines: int = 4) -> list[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[:max_lines]
