"""
系统级数据字典 Pydantic Schema

提供：
  - 字典类型 CRUD 模型
  - 字典项 CRUD 模型
  - 前端缓存聚合响应模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SysDictTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="字典类型名称")
    code: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Z][A-Z0-9_]*$", description="字典类型编码")
    description: str | None = Field(None, max_length=256, description="字典类型描述")
    sort_order: int = Field(0, ge=0, description="排序值")
    is_active: bool = Field(True, description="是否启用")


class SysDictTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    description: str | None = Field(None, max_length=256)
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class SysDictTypeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    sort_order: int
    is_active: bool


class SysDictTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None


class SysDictItemCreate(BaseModel):
    dict_type_id: int = Field(..., description="所属字典类型 ID")
    value: str = Field(..., min_length=1, max_length=100, description="存储值")
    label: str = Field(..., min_length=1, max_length=100, description="展示标签")
    description: str | None = Field(None, max_length=256, description="字典项描述")
    sort_order: int = Field(0, ge=0, description="排序值")
    is_active: bool = Field(True, description="是否启用")
    extra_json: dict[str, Any] | None = Field(None, description="扩展元数据")


class SysDictItemUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=256)
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None
    extra_json: dict[str, Any] | None = None


class SysDictItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dict_type_id: int
    value: str
    label: str
    description: str | None
    sort_order: int
    is_active: bool
    extra_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None
    dict_type: SysDictTypeBrief


class SysDictCacheItemResponse(BaseModel):
    value: str
    label: str
    sort_order: int
    extra_json: dict[str, Any] | None


class SysDictCacheTypeResponse(BaseModel):
    name: str
    code: str
    items: list[SysDictCacheItemResponse]


class SysDictCacheResponse(BaseModel):
    dictionaries: list[SysDictCacheTypeResponse]