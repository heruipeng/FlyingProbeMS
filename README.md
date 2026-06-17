# FlyingProbeMS — 飞针测试资料管理系统

> 🏷️ **鹏程工作室 出品**

**崇达电路（SUNTAK）飞针测试资料自动处理系统** — 集成 ezCAM Genesis 自动化引擎，实现 PCB 飞针测试资料的无人值守输出与管理。

---

## 📋 功能概览

| 模块 | 说明 |
|------|------|
| 🔐 用户系统 | 登录 / 注册 / 改密，支持记住密码，基于 Oracle 用户表 |
| 📊 任务管理 | PyQt5 可视化主界面，料号搜索、状态筛选、分页浏览、双击详情 |
| ⚙️ 核心引擎 | 11 步 ezCAM Genesis 自动化流程，无人值守输出飞针测试文件 |
| 🔄 自动调度 | 7×24 小时从 ERP 拉取待处理任务，批量执行，结果自动回写 |
| 📡 数据同步 | 与 Oracle ERP / InPlan 双向数据交互 |
| 📧 通知告警 | 企业微信机器人 + 邮件双通道异常通知 |

---

## 🏭 支持工厂

| 工厂 | 代码 |
|------|------|
| 江门一厂 | JM1 |
| 江门二厂 | JM2 |
| 珠海一厂 | ZH1 |
| 珠海二厂 | ZH2 |
| 大连电子 | DL |

---

## 🏗️ 项目结构

```
FlyingProbeMS/
├── login.py                  # 登录/注册/改密界面
├── main.py                   # PyQt5 主界面（1400×800）
├── fp_core_processor.py      # ★ 核心业务引擎（ezCAM 自动化）
├── fp_auto_scheduler.py      # ★ 无人值守批量调度器
├── fp_auto_scheduler.bat     # Windows 后台启动脚本
├── fp_config.py              # 工厂/路径/邮箱配置中心
├── update_tools.py           # 版本更新工具
├── update_version.ini        # 版本更新日志
├── icon_rc.py                # Qt 资源文件（图标/Logo）
├── config.ini                # 用户配置（工厂/状态/工序）
├── user_config.dat           # 登录凭证缓存（加密）
├── image/                    # UI 图标与提示图片
└── package/
    ├── Oracle_DB.py          # Oracle 数据库封装（cx_Oracle）
    ├── genCOM_36.py          # Genesis COM 通信层
    ├── gateway.py            # 网关通信模块
    ├── MessageBox.py         # 自定义弹窗组件
    ├── Ui_MessageBox.py      # 弹窗 UI
    └── wechat_robot.py       # 企业微信机器人通知
```

---

## 🔄 业务流程

```
ERP待处理任务
    │
    ▼
[自动调度器] ──→ 启动 ezFixtureII ──→ 执行核心脚本
    │
    ▼
① 读取 ezCAM UID，建立 Genesis 通信
② 导入 TGZ 工程文件
③ 清理无效图层（保留线路/阻焊/钻孔/外形）
④ 阻焊层完整性检查
⑤ 板型合法性校验（半孔/阴阳板/灯板）
⑥ 自动判断二线/四线测试模式
⑦ 工作稿 vs 原稿网络比对（短路/开路检测）
⑧ 自动导入原始 Gerber → 坐标对齐 → 覆盖还原
⑨ 阻焊小开窗去重清理
⑩ 生成飞针测试点 → 输出 356 测试文件
⑪ 结果自动回写 Oracle 数据库
    │
    ▼
状态更新 → 企业微信通知 → 完成
```

---

## 📊 数据状态流转

```
未运行 → 未输出 → 未检查 → 未转换 → 已转换 → 已完成
```

---

## 🚀 运行方式

### 手动模式（GUI 交互）

```bash
python login.py
```

登录后打开主界面，可手动搜索料号、查看详情、逐一处理。

### 全自动模式（无人值守）

```bash
fp_auto_scheduler.bat        # Windows 双击运行
# 或
python fp_auto_scheduler.py JM2   # 指定工厂代码
```

自动从 ERP 拉取待处理任务，逐个执行并上报结果。

---

## 🔧 环境依赖

| 依赖 | 说明 |
|------|------|
| **Windows** | 运行操作系统 |
| **Python 3.x** | 推荐 3.7+ |
| **PyQt5** | GUI 框架 |
| **ezFixtureII** | 盛鑫自动化飞针测试软件（`D:\eastek-server\ezFixtureII\`） |
| **Oracle Instant Client 19.21** | 需单独下载放入 `instantclient_19_21/` 目录 |
| **cx_Oracle** | Python Oracle 驱动 |
| **psutil** | 进程管理 |

### 安装 Oracle Instant Client

从 [Oracle 官网](https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html) 下载 **Version 19.21**，解压至项目根目录：

```
instantclient_19_21/
├── oci.dll
├── oraociei19.dll    ← 关键文件（~190MB）
└── ...
```

### 安装 Python 依赖

```bash
pip install PyQt5 cx_Oracle psutil
```

---

## ⚙️ 配置说明

### 数据库连接

- **ERP 数据库**：`cderpdb-scan.suntakpcb.com:1521/prod`（SID）
- **InPlan 数据库**：`inplan001:1521/inmind.fls`（Service Name）
- 连接配置在 `package/Oracle_DB.py` 中，可按需修改

### 工厂路径

各工厂 TGZ 路径、ORG 路径、输出路径在 `fp_config.py` 中配置，均为 UNC 网络路径。

---

## 📝 更新日志

| 版本   | 日期         | 变更                                                                                    |
|------|------------|---------------------------------------------------------------------------------------|
| V3.5 | 2026-06-17 | 上传报表筛查基表ERP数据时，过滤空格，并新增判断空字符串数据类型（非None）、核心业务引擎bug修复、检查兼容2w/4w模式 、启动软件速度优化、删除板外物件和外形线 |
| V3.4 | 2026-06-16 | 上传报表到旧表、修复拼板偏位异常、软硬结合板跑测试点                                                            |
| V3.3 | 2026-06-12 | 新增上传 ERP 数据、新增已转换状态                                                                   |
| V3.1 | 2026-06-11 | 四线测试删除无用层、取消时不传测试点数                                                                   |
| V3.0 | 2026-06-08 | 发布新版本                                                                                 |

---

## 👤 作者

- **开发者**：何瑞鹏 (rphe)
- **邮箱**：502614708@qq.com
- **出品**：鹏程工作室

---

## 📄 License

Copyright © SUNTAK SOFTWARE GROUP. All Rights Reserved.
