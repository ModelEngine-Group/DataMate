## 🚀 快速开始

```
npm install       # 安装依赖
npm run dev       # 启动项目
npm run mock      # 启动后台Mock服务（可选）
```

## 📁 项目结构

```
frontend/
├── public/                               # 📖 文档中心
│   ├── huawei-logo.webp/                 # logo
│   └── xxx/         # 标注工作台（可分离部署）
│
├── src/                                # 🎨 前端应用
│   ├── apps/                          # 多前端应用
│   │   ├── console/                   # 数据工作台&运营控制台
│   │   │   ├── next.config.js
│   │   │   ├── package.json
│   │   │   └── src/
│   │   └── annotation-studio/         # 标注工作台（可分离部署）
│   │
│   ├── assets/                      # 共享UI组件/SDK
│   │   ├── xxx/                   # 数据工作台&运营控制台
│   │   │   ├── next.config.js
│   │   │   └── src/
│   │   │
│   │   │
│   │   └── xxx/                   # 数据工作台&运营控制台
│   │       ├── package.json
│   │       └── src/
│   │
│   ├── components/                        # 构建与环境配置
│   │   ├── CardView.tsx                  # 数据工作台&运营控制台
│   │   ├── DetailHeader.tsx                   # 数据工作台&运营控制台
│   │   ├── RadioCard.tsx                   # 数据工作台&运营控制台
│   │   ├── SearchControls                   # 数据工作台&运营控制台
│   │   ├── TagList         # 标注工作台（可分离部署）
│   │   └── TaskPopover         # 标注工作台（可分离部署）
│   │
│   ├── hooks/                        # 构建与环境配置
│   │   ├── console/                   # 数据工作台&运营控制台
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   └── annotation-studio/         # 标注工作台（可分离部署）
│   │
│   ├── mock/                        # 构建与环境配置
│   │   ├── console/                   # 数据工作台&运营控制台
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   └── annotation-studio/         # 标注工作台（可分离部署）
│   │
│   ├── pages/                        # 构建与环境配置
│   │   ├── console/                   # 数据工作台&运营控制台
│   │   │   ├── next.config.js
│   │   │   ├── package.json
│   │   │   └── src/
│   │   └── annotation-studio/         # 标注工作台（可分离部署）
│   │
│   ├── providers/                        # 构建与环境配置
│   │   ├── console/                   # 数据工作台&运营控制台
│   │   │   ├── next.config.js
│   │   │   ├── package.json
│   │   │   └── src/
│   │   └── annotation-studio/         # 标注工作台（可分离部署）
│   │
│   ├── routes/                        # 构建与环境配置
│   │   └── next.config.js
│   │
│   ├── types/                        # 构建与环境配置
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   ├── next.config.js
│   │   └──  next.config.js
│   │
│   └── utils/                        # 构建与环境配置
│       ├── next.config.js
│       ├── next.config.js
│       └── next.config.js
│
├── eslint.config.js/                            # 🔧 后端服务架构
├── index.html/                            # 🔧 后端服务架构
├── package.json/                            # 🔧 后端服务架构
├── README.md                           # 项目说明
├── tailwind.config.ts                        # 更新日志
├── vite.config.ts                             # 开源协议
└── pom.xml                            # Maven根配置
```

## 开发新功能
- 安装开发依赖：

```bash
npm install xxx
```