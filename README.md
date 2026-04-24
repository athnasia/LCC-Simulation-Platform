# 工业互联网平台：基于数字孪生的成本建模与仿真优化系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.5+-green.svg)](https://vuejs.org/)

## 📋 项目简介

基于数字孪生的全生命周期成本（LCC）建模、仿真与优化系统，为制造业企业提供从产品设计到报废的成本决策支持。

**核心业务流**：基础数据定义 → 动态组合建模 → LCC全生命周期仿真计算

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI (REST API)
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **异步任务**: Celery
- **认证**: JWT + RBAC

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **可视化**: ECharts

### 架构风格
- 模块化单体架构（API层 → 应用层 → 领域层 → 基础设施层）
- 领域驱动设计（DDD）
- 预留微服务拆分空间

## 📦 核心模块

1. **全景视界** - 2D/3D数字孪生与宏观成本驾驶舱
2. **主数据与资源中心** - 材料、设备、工艺、人员、能源日历管理
3. **工程建模与协同** - BOM拆解与工艺路线编排
4. **成本核算与仿真优化** - 静态台账核算与动态LCC仿真
5. **物联网与现场采集** - 设备数据接入（OPC-UA/MQTT）
6. **系统与平台管理** - RBAC权限与审计日志

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- pnpm 8+
- MySQL 8.0+
- Redis 6.0+

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和Redis连接信息

# 运行数据库迁移
.\.venv\Scripts\alembic.exe upgrade head

# 初始化种子数据
.\.venv\Scripts\python.exe -m app.core.init_db

# 启动开发服务器
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 访问应用

- 前端地址: http://localhost:5173
- API文档: http://localhost:8001/api/docs
- 默认账号: admin / 123456

### Worker 重启规则

- 凡是修改 `backend/app/services/simulation_service.py` 或 `backend/app/worker/tasks.py`，完成代码变更后都必须重启 Celery Worker 容器 `lcc-app-worker-1`。
- 原因：本地开发环境中 API 运行在宿主机，而异步仿真实际由 Docker 中的 Worker 执行；若不重启 Worker，可能出现 API 已是新逻辑、但仿真结果仍由旧 Worker 代码产出的情况。
- 推荐命令：`docker compose restart worker`

## 📁 项目结构

```
lcc-app/
├── backend/                # 后端代码
│   ├── app/
│   │   ├── api/           # API路由层
│   │   ├── core/          # 核心配置
│   │   ├── models/        # ORM模型
│   │   ├── schemas/       # Pydantic模型
│   │   ├── services/      # 业务逻辑层
│   │   ├── repositories/  # 数据访问层
│   │   ├── domain/        # 领域规则
│   │   └── tasks/         # Celery任务
│   ├── alembic/           # 数据库迁移
│   ├── storage/           # 文件存储
│   └── logs/              # 日志文件
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API封装
│   │   ├── views/        # 页面组件
│   │   ├── components/   # 业务组件
│   │   ├── layouts/      # 布局组件
│   │   ├── stores/       # 状态管理
│   │   └── router/       # 路由配置
│   └── public/           # 静态资源
├── docs/                  # 文档
│   ├── 规划.md           # 功能规划
│   ├── 总体架构设计.md   # 架构设计
│   └── TECH_DEBT.md      # 技术债务清单
├── AGENTS.md             # Agent指令文档
└── README.md             # 项目说明
```

## 🔐 安全说明

- **敏感信息**: 所有敏感配置（数据库密码、JWT密钥等）存储在 `.env` 文件中，已添加到 `.gitignore`
- **权限控制**: 基于RBAC的细粒度权限控制
- **审计日志**: 完整的操作审计记录

## 📝 开发规范

详细的开发规范请参考 [AGENTS.md](AGENTS.md)，包括：
- 代码生成规范
- 数据库设计准则
- 业务规则约束
- 技术栈要求

## 🐛 技术债务

已知的技术债务记录在 [docs/TECH_DEBT.md](docs/TECH_DEBT.md)，包括：
- TD-001: 单位换算链路图算法缺失
- TD-002: 权限资源路径魔法字符串

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

**注意**: 本项目目前处于 MVP 开发阶段，部分功能仍在迭代中。
