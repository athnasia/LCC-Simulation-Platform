import type { DictionaryOption } from '@/stores/dictionaries'

export type DictionaryTagType = '' | 'primary' | 'success' | 'warning' | 'info' | 'danger'

export const ATTR_DATA_TYPE_OPTIONS: DictionaryOption[] = [
  { value: 'STRING', label: '字符串', sort_order: 1, extra_json: { input_hint: '文本' } },
  { value: 'NUMBER', label: '数值', sort_order: 2, extra_json: { input_hint: '数字' } },
  { value: 'BOOLEAN', label: '布尔值', sort_order: 3, extra_json: { input_hint: 'true / false' } },
  { value: 'JSON', label: 'JSON 对象', sort_order: 4, extra_json: { input_hint: 'JSON 格式' } },
  { value: 'DATE', label: '日期', sort_order: 5, extra_json: { input_hint: '日期 (YYYY-MM-DD)' } },
  { value: 'ENUM', label: '枚举', sort_order: 6, extra_json: { input_hint: '枚举值' } },
]

export const PERMISSION_ACTION_OPTIONS: DictionaryOption[] = [
  { value: 'read', label: '读取', sort_order: 1, extra_json: { tag_type: 'success' } },
  { value: 'write', label: '维护', sort_order: 2, extra_json: { tag_type: '' } },
  { value: 'delete', label: '删除', sort_order: 3, extra_json: { tag_type: 'danger' } },
  { value: 'admin', label: '管理', sort_order: 4, extra_json: { tag_type: 'warning' } },
]

export const AUDIT_ACTION_OPTIONS: DictionaryOption[] = [
  { value: 'CREATE', label: '创建', sort_order: 1, extra_json: { tag_type: 'success' } },
  { value: 'UPDATE', label: '更新', sort_order: 2, extra_json: { tag_type: '' } },
  { value: 'DELETE', label: '删除', sort_order: 3, extra_json: { tag_type: 'danger' } },
  { value: 'RESET_PASSWORD', label: '重置密码', sort_order: 4, extra_json: { tag_type: 'warning' } },
  { value: 'CHANGE_PASSWORD', label: '修改密码', sort_order: 5, extra_json: { tag_type: 'warning' } },
]

export const AUDIT_RESOURCE_TYPE_OPTIONS: DictionaryOption[] = [
  { value: 'OrgDepartment', label: '部门', sort_order: 1, extra_json: null },
  { value: 'SysPermission', label: '权限', sort_order: 2, extra_json: null },
  { value: 'SysRole', label: '角色', sort_order: 3, extra_json: null },
  { value: 'SysUser', label: '用户', sort_order: 4, extra_json: null },
  { value: 'SysDictType', label: '字典类型', sort_order: 5, extra_json: null },
  { value: 'SysDictItem', label: '字典项', sort_order: 6, extra_json: null },
]

export const LABOR_SKILL_OPTIONS: DictionaryOption[] = [
  { value: 'JUNIOR', label: '初级', sort_order: 1, extra_json: null },
  { value: 'INTERMEDIATE', label: '中级', sort_order: 2, extra_json: null },
  { value: 'SENIOR', label: '高级', sort_order: 3, extra_json: null },
  { value: 'MASTER', label: '专家', sort_order: 4, extra_json: null },
]

export const ENERGY_TYPE_OPTIONS: DictionaryOption[] = [
  { value: 'ELECTRICITY', label: '电', sort_order: 1, extra_json: null },
  { value: 'WATER', label: '水', sort_order: 2, extra_json: null },
  { value: 'GAS', label: '气', sort_order: 3, extra_json: null },
  { value: 'STEAM', label: '蒸汽', sort_order: 4, extra_json: null },
  { value: 'COMPRESSED_AIR', label: '压缩空气', sort_order: 5, extra_json: null },
]