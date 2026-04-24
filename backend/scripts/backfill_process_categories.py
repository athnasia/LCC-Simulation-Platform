r"""为现有工艺补齐分类并初始化 PROCESS 资源分类。

执行方式：在 backend 目录下运行
    .\.venv\Scripts\python.exe scripts\backfill_process_categories.py
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.master_data import MdProcess, MdResourceCategory, ResourceType


PROCESS_CATEGORY_SEEDS = [
    {
        "name": "机加工",
        "code": "PROCESS_MACHINING",
        "description": "车削、铣削、钻孔、磨削等切削加工工艺",
    },
    {
        "name": "连接与装配",
        "code": "PROCESS_JOINING_ASSEMBLY",
        "description": "焊接与装配类工艺",
    },
    {
        "name": "热处理",
        "code": "PROCESS_HEAT_TREATMENT",
        "description": "热处理类工艺",
    },
    {
        "name": "表面处理",
        "code": "PROCESS_SURFACE_TREATMENT",
        "description": "表面处理类工艺",
    },
]


PROCESS_CATEGORY_BY_CODE = {
    "PROC_TURNING": "PROCESS_MACHINING",
    "PROC_MILLING": "PROCESS_MACHINING",
    "PROC_DRILLING": "PROCESS_MACHINING",
    "PROC_GRINDING": "PROCESS_MACHINING",
    "DRILL_01": "PROCESS_MACHINING",
    "PROC_WELDING": "PROCESS_JOINING_ASSEMBLY",
    "PROC_ASSEMBLY": "PROCESS_JOINING_ASSEMBLY",
    "PROC_HEAT_TREATMENT": "PROCESS_HEAT_TREATMENT",
    "PROC_SURFACE_TREATMENT": "PROCESS_SURFACE_TREATMENT",
}


def ensure_process_categories(db: Session) -> dict[str, MdResourceCategory]:
    categories: dict[str, MdResourceCategory] = {}

    for sort_order, seed in enumerate(PROCESS_CATEGORY_SEEDS, start=1):
        category = db.execute(
            select(MdResourceCategory).where(
                MdResourceCategory.code == seed["code"],
                MdResourceCategory.is_deleted == False,
            )
        ).scalar_one_or_none()

        if category is None:
            category = MdResourceCategory(
                name=seed["name"],
                code=seed["code"],
                resource_type=ResourceType.PROCESS,
                sort_order=sort_order,
                description=seed["description"],
                created_by="system",
                updated_by="system",
            )
            db.add(category)
            db.flush()
            print(f"[+] 创建工艺分类：{category.name}（{category.code}）")
        else:
            changed = False
            if category.name != seed["name"]:
                category.name = seed["name"]
                changed = True
            if category.resource_type != ResourceType.PROCESS:
                category.resource_type = ResourceType.PROCESS
                changed = True
            if category.sort_order != sort_order:
                category.sort_order = sort_order
                changed = True
            if category.description != seed["description"]:
                category.description = seed["description"]
                changed = True
            if changed:
                category.updated_by = "system"
                db.flush()
                print(f"[~] 更新工艺分类：{category.name}（{category.code}）")
            else:
                print(f"[=] 工艺分类已存在：{category.name}（{category.code}）")

        categories[category.code] = category

    return categories


def resolve_category_code(process: MdProcess) -> str | None:
    explicit_code = PROCESS_CATEGORY_BY_CODE.get(process.code.upper())
    if explicit_code:
        return explicit_code

    normalized_name = (process.name or "").strip().lower()
    normalized_code = process.code.strip().lower()
    haystack = f"{normalized_code} {normalized_name}"

    if any(keyword in haystack for keyword in ("turn", "mill", "drill", "grind", "车", "铣", "钻", "磨")):
        return "PROCESS_MACHINING"
    if any(keyword in haystack for keyword in ("weld", "assembly", "焊", "装配")):
        return "PROCESS_JOINING_ASSEMBLY"
    if any(keyword in haystack for keyword in ("heat", "热处理")):
        return "PROCESS_HEAT_TREATMENT"
    if any(keyword in haystack for keyword in ("surface", "表面")):
        return "PROCESS_SURFACE_TREATMENT"

    return None


def backfill_process_categories(db: Session) -> None:
    categories = ensure_process_categories(db)
    processes = db.execute(
        select(MdProcess).where(MdProcess.is_deleted == False).order_by(MdProcess.id)
    ).scalars().all()

    updated = 0
    skipped: list[str] = []

    for process in processes:
        category_code = resolve_category_code(process)
        if category_code is None:
            skipped.append(f"{process.code} / {process.name}")
            continue

        target_category = categories[category_code]
        if process.category_id == target_category.id:
            continue

        process.category_id = target_category.id
        process.updated_by = "system"
        updated += 1
        print(f"[~] 工艺归类：{process.code} -> {target_category.name}")

    db.commit()
    print(f"\n[OK] 已更新 {updated} 条工艺分类")

    if skipped:
        print("[!] 以下工艺未匹配到分类，请手工确认：")
        for item in skipped:
            print(f"    - {item}")


def main() -> None:
    db = SessionLocal()
    try:
        backfill_process_categories(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()