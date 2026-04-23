/**
 * 基础组件入口文件
 * 
 * 统一导出所有基础组件，支持全局注册
 */

import type { App } from 'vue'
import PageContainer from './PageContainer.vue'
import BaseTable from './BaseTable.vue'
import BaseDialog from './BaseDialog.vue'

export { PageContainer, BaseTable, BaseDialog }

export const baseComponents = {
  PageContainer,
  BaseTable,
  BaseDialog,
}

export function installBaseComponents(app: App) {
  Object.entries(baseComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}
