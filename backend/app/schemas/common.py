"""
通用 Pydantic 响应模型

提供：
  - PageResult[T]  : 泛型分页包装器，所有列表接口统一使用此结构返回
  - 使用方式：response_model=PageResult[SysUserResponse]
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    """
    通用分页响应体。

    字段：
        items   — 当前页数据列表
        total   — 符合过滤条件的总记录数
        page    — 当前页码（1 起始）
        size    — 每页条数
        pages   — 总页数（由 total 与 size 计算得出）
    """
    items: list[T]
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页条数")
    pages: int = Field(description="总页数")

    @classmethod
    def build(cls, *, items: list[T], total: int, page: int, size: int) -> "PageResult[T]":
        pages = max(1, (total + size - 1) // size) if total > 0 else 1
        return cls(items=items, total=total, page=page, size=size, pages=pages)
