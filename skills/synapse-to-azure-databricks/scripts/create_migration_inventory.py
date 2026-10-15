from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


NAVY = "1F4E78"
WHITE = "FFFFFF"
LIFECYCLE_STATES = [
    "inventoried",
    "assessed",
    "fallback-required",
    "approved",
    "converted",
    "packaged",
    "deployed",
    "validated",
    "failed",
    "retained",
    "blocked",
    "cut-over",
    "rolled-back",
]
REQUIRED_COLUMNS = {
    "source_database",
    "source_schema",
    "source_object",
    "source_type",
    "definition_sha256",
    "dependencies",
    "source_identity",
    "classification",
    "disposition",
    "tool_route",
    "target_catalog",
    "target_schema",
    "target_object",
    "target_type",
    "owner",
    "validation_status",
    "notes",
}
SCENARIO_PROFILE = "staged-bronze-modernisation"
SCENARIO_REQUIRED_FIELDS = (
    "scenario_stage",
    "stage_gate_status",
    "writer_owner",
    "data_action",
    "original_location",
    "managed_target",
    "rollback_boundary",
    "retention_decision",
    "cleanup_decision",
)
SCENARIO_ENUMS = {
    "scenario_stage": {"1", "2", "3", "4"},
    "stage_gate_status": {
        "not-started",
        "blocked",
        "validation-pending",
        "approval-pending",
        "passed",
    },
    "writer_owner": {
        "synapse-owned",
        "adf-owned",
        "cutover-pending",
        "databricks-owned",
    },
    "data_action": {
        "register-existing",
        "convert",
        "copy",
        "ingest",
        "write-managed",
        "none",
    },
}
STATUS_HEADERS = [
    "Stable Source ID",
    "Source Database",
    "Source Schema",
    "Source Object",
    "Source Type",
    "Source Hash",
    "Definition File",
    "Workload Route",
    "Lakebridge Assessment Status",
    "Lakebridge Assessment Evidence",
    "Lakebridge Transpiler Status",
    "Lakebridge Transpiler Evidence",
    "Migration Inventory Status",
    "Classification",
    "Disposition",
    "Target Catalog",
    "Target Schema",
    "Target Object",
    "Target Type",
    "Lifecycle Status",
    "Review / Blocker Reason",
    "Deployment Evidence",
    "Validation Result",
    "Owner",
    "Next Action",
    "Last Updated UTC",
    "Scenario Profile",
    "Scenario Stage",
    "Stage Gate Status",
    "Writer Ownership",
    "Data Action",
    "Original Location",
    "Managed Target",
    "Rollback Boundary",
    "Retention Decision",
    "Cleanup Decision",
]
TARGET_HEADERS = [
    "Catalog",
    "Schema",
    "Object Name",
    "Object Type",
    "Source Identity / Path",
    "Deployment Status",
    "Deployment Statement ID",
    "Validation Status",
    "Validation Statement ID",
    "Row Count / Contract Metric",
    "Owner",
    "Rollback Boundary",
]
DEPENDENCY_HEADERS = [
    "Stable Source ID",
    "Dependency",
    "Dependency Type",
    "Resolution Status",
    "Evidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the governed Synapse-to-Databricks migration inventory."
    )
    parser.add_argument("--inventory-csv", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--lakebridge-workbook", type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Inventory CSV is missing required columns: " + ", ".join(sorted(missing))
            )
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    real_rows = [
        row
        for row in rows
        if not all(
            row.get(column, "").startswith("<") and row.get(column, "").endswith(">")
            for column in ("source_database", "source_schema", "source_object")
        )
    ]
    if not real_rows:
        raise ValueError(
            "Inventory CSV has no discovered source objects. Populate it before creating the workbook."
        )
    for index, row in enumerate(real_rows, start=2):
        if not re.fullmatch(r"[0-9a-fA-F]{64}", row["definition_sha256"]):
            raise ValueError(
                f"Inventory CSV row {index} has an invalid definition_sha256; expected 64 hexadecimal characters."
            )
        profile = row.get("scenario_profile", "")
        if profile and profile != SCENARIO_PROFILE:
            raise ValueError(
                f"Inventory CSV row {index} has an unsupported scenario_profile {profile!r}; "
                f"expected {SCENARIO_PROFILE!r} or blank."
            )
        if profile == SCENARIO_PROFILE:
            for field in SCENARIO_REQUIRED_FIELDS:
                value = row.get(field, "")
                if not value:
                    raise ValueError(
                        f"Inventory CSV row {index} is missing required {field} "
                        f"for {SCENARIO_PROFILE}."
                    )
                allowed_values = SCENARIO_ENUMS.get(field)
                if allowed_values and value not in allowed_values:
                    raise ValueError(
                        f"Inventory CSV row {index} has an invalid {field} {value!r}; "
                        f"expected one of {', '.join(sorted(allowed_values))}."
                    )
    return real_rows


def stable_source_id(row: dict[str, str]) -> str:
    if row["source_identity"]:
        return row["source_identity"]
    return ".".join(
        value
        for value in (
            row["source_database"],
            row["source_schema"],
            row["source_object"],
            row["source_type"],
        )
        if value
    )


def new_or_existing_workbook(lakebridge_workbook: Path | None) -> Workbook:
    if lakebridge_workbook:
        if not lakebridge_workbook.is_file():
            raise FileNotFoundError(
                f"Lakebridge workbook does not exist: {lakebridge_workbook}"
            )
        return load_workbook(lakebridge_workbook)
    workbook = Workbook()
    workbook.remove(workbook.active)
    return workbook


def add_sheet(
    workbook: Workbook,
    title: str,
    headers: list[str],
    rows: list[list[object]],
    table_name: str,
):
    if title in workbook.sheetnames:
        del workbook[title]
    sheet = workbook.create_sheet(title)
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A2"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    if not rows:
        sheet.append([""] * len(headers))
    for cell in sheet[1]:
        cell.font = Font(name="Arial", size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    for index, header in enumerate(headers, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = min(
            max(len(header) + 3, 16), 42
        )
    table = Table(
        displayName=table_name,
        ref=f"A1:{get_column_letter(len(headers))}{max(len(rows) + 1, 2)}",
    )
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    sheet.add_table(table)
    return sheet


def build_status_rows(
    rows: list[dict[str, str]], generated_at: str
) -> list[list[str]]:
    status_rows = []
    for row in rows:
        status_rows.append(
            [
                stable_source_id(row),
                row["source_database"],
                row["source_schema"],
                row["source_object"],
                row["source_type"],
                row["definition_sha256"],
                row.get("definition_file", ""),
                row["tool_route"],
                "not-run",
                "",
                "not-evaluated",
                "",
                "inventoried",
                row["classification"],
                row["disposition"],
                row["target_catalog"],
                row["target_schema"],
                row["target_object"],
                row["target_type"],
                "inventoried",
                row.get("fallback_reason", ""),
                "",
                row["validation_status"],
                row["owner"],
                row["notes"],
                generated_at,
                row.get("scenario_profile", ""),
                row.get("scenario_stage", ""),
                row.get("stage_gate_status", ""),
                row.get("writer_owner", ""),
                row.get("data_action", ""),
                row.get("original_location", ""),
                row.get("managed_target", ""),
                row.get("rollback_boundary", ""),
                row.get("retention_decision", ""),
                row.get("cleanup_decision", ""),
            ]
        )
    return status_rows


def build_target_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    return [
        [
            row["target_catalog"],
            row["target_schema"],
            row["target_object"],
            row["target_type"],
            stable_source_id(row),
            "not deployed",
            "",
            row["validation_status"],
            "",
            "",
            row["owner"],
            "",
        ]
        for row in rows
        if any(
            row[column]
            for column in ("target_catalog", "target_schema", "target_object", "target_type")
        )
    ]


def build_dependency_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    dependency_rows = []
    for row in rows:
        dependencies = [
            value.strip()
            for value in row["dependencies"].replace(";", ",").split(",")
            if value.strip()
        ]
        dependency_rows.extend(
            [
                stable_source_id(row),
                dependency,
                "source dependency",
                "unresolved",
                "",
            ]
            for dependency in dependencies
        )
    return dependency_rows


def add_summary(workbook: Workbook, object_count: int):
    if "Summary" in workbook.sheetnames:
        del workbook["Summary"]
    sheet = workbook.create_sheet("Summary", 0)
    sheet.sheet_view.showGridLines = False
    sheet.append(["Metric", "Value"])
    sheet.append(["Total approved-scope objects", object_count])
    for state in LIFECYCLE_STATES:
        sheet.append(
            [
                state,
                f'=COUNTIF(\'Migration Status\'!$P:$P,A{sheet.max_row + 1})',
            ]
        )
    for cell in sheet[1]:
        cell.font = Font(name="Arial", size=10, bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=NAVY)
    sheet.column_dimensions["A"].width = 34
    sheet.column_dimensions["B"].width = 18


def create_manifest(
    rows: list[dict[str, str]],
    inventory_csv: Path,
    generated_at: str,
) -> dict[str, object]:
    return {
        "schema_version": 2,
        "generated_at_utc": generated_at,
        "source_inventory": {
            "path": str(inventory_csv.resolve()),
            "sha256": sha256(inventory_csv),
        },
        "items": [
            {
                "stable_source_id": stable_source_id(row),
                "source_hash": row["definition_sha256"],
                "source_type": row["source_type"],
                "classification": row["classification"],
                "disposition": row["disposition"],
                "tool_route": row["tool_route"],
                "lakebridge_assessment_status": "not-run",
                "lakebridge_transpiler_status": "not-evaluated",
                "migration_inventory_status": "inventoried",
                "target": {
                    "catalog": row["target_catalog"],
                    "schema": row["target_schema"],
                    "object": row["target_object"],
                    "type": row["target_type"],
                },
                "lifecycle_status": "inventoried",
                "scenario": {
                    "profile": row.get("scenario_profile", ""),
                    "stage": row.get("scenario_stage", ""),
                    "stage_gate_status": row.get("stage_gate_status", ""),
                    "writer_ownership": row.get("writer_owner", ""),
                    "data_action": row.get("data_action", ""),
                    "original_location": row.get("original_location", ""),
                    "managed_target": row.get("managed_target", ""),
                    "rollback_boundary": row.get("rollback_boundary", ""),
                    "retention_decision": row.get("retention_decision", ""),
                    "cleanup_decision": row.get("cleanup_decision", ""),
                },
                "owner": row["owner"],
                "attempt_history": [],
                "evidence": [],
                "last_updated_utc": generated_at,
            }
            for row in rows
        ],
    }


def main() -> int:
    args = parse_args()
    rows = load_inventory(args.inventory_csv)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    workbook = new_or_existing_workbook(args.lakebridge_workbook)
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.properties.title = "Synapse to Azure Databricks migration inventory"
    workbook.properties.creator = "Skills for Databricks"

    add_sheet(
        workbook,
        "Migration Status",
        STATUS_HEADERS,
        build_status_rows(rows, generated_at),
        "MigrationStatus",
    )
    add_sheet(
        workbook,
        "Target Objects",
        TARGET_HEADERS,
        build_target_rows(rows),
        "TargetObjects",
    )
    add_sheet(
        workbook,
        "Dependencies",
        DEPENDENCY_HEADERS,
        build_dependency_rows(rows),
        "Dependencies",
    )
    add_sheet(
        workbook,
        "Decisions and Approvals",
        ["Decision ID", "Scope", "Decision", "Status", "Owner", "Evidence", "Updated UTC"],
        [],
        "DecisionsApprovals",
    )
    add_sheet(
        workbook,
        "Evidence",
        ["Evidence ID", "Stable Source ID", "Evidence Type", "Path / URI", "SHA-256", "Captured UTC"],
        [],
        "MigrationEvidence",
    )
    add_sheet(
        workbook,
        "Metadata and Lists",
        ["Key", "Value"],
        [
            ["Generated UTC", generated_at],
            ["Source inventory path", str(args.inventory_csv.resolve())],
            ["Source inventory SHA-256", sha256(args.inventory_csv)],
            ["Lakebridge workbook", str(args.lakebridge_workbook.resolve()) if args.lakebridge_workbook else ""],
            ["Lifecycle states", ", ".join(LIFECYCLE_STATES)],
        ],
        "InventoryMetadata",
    )
    add_summary(workbook, len(rows))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(args.output)

    manifest_path = args.manifest or args.output.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(create_manifest(rows, args.inventory_csv, generated_at), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created {args.output} with {len(rows)} source object(s).")
    print(f"Created {manifest_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
