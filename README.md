# FlyingProbeMS — 飞针测试资料管理系统

> 🏷️ **鹏程工作室 出品** · 崇达电路（SUNTAK）内部工具

基于 PyQt5 + Oracle 的 PCB 飞针测试资料全流程管理平台，集成 ezCAM Genesis 自动化引擎，实现测试资料的自动输出、检查、转换、ERP 回写与多维报表分析。

---

## 📋 功能矩阵

| 模块 | 说明 |
|------|------|
| 🔐 用户系统 | 登录 / 注册 / 改密，记住密码，基于 Oracle 用户表 `INP_FLYPIN_USER` |
| 📋 任务管理 | 按工厂/状态/工序/日期搜索，20 条分页，全局行号，选中行详情面板 |
| 🔹 2W 资料 | 输出 / 检查 / 导入 / 转换 / 上传 ERP，输出路径实时展示 |
| 🔸 4W 资料 | 输出 / 检查 / 导入 / 转换，独立 Tab 操作区 |
| 📊 报表管理 | 数据明细（31列完整 2W/4W 字段）· 工厂汇总 · 日报统计 三视图，完成率/平均耗时统计卡片 |
| 🔄 自动调度 | `fp_auto_scheduler.py` 7×24 拉取 ERP 任务，批量执行，结果回写 |
| 📡 数据同步 | Oracle ERP（`cderpdb-scan`）↔ InPlan 双向交互 |
| 📧 通知告警 | 企业微信机器人 + 邮件双通道 |

---

## 🏭 支持工厂

| 工厂名称 | 代号 | ORG_ID |
|----------|------|--------|
| 江门一厂 | JM1  | 85     |
| 江门二厂 | JM2  | 107    |
| 珠海一厂 | ZH1  | 168    |
| 珠海二厂 | ZH2  | 228    |
| 大连电子 | DL   | 84     |

---

## 🔄 数据状态流

```
未运行 ──→ 未输出 ──→ 未检查 ──→ 未转换 ──→ 已转换 ──→ 已完成
  │                              │           │
  └─ ezFixtureII 输出 ──────────→│           │
                                 └─ TPG-E ──→│
                                             └─ 上传ERP ──→ ✅
```

---

## 🗄️ 数据库字段（飞针测试主表）

`INP.INP_FLYPIN_PROBE_TOOL_ALERT` 核心业务字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `OUTPUT_PATH_2W` | VARCHAR2 | 2W 输出路径 |
| `OUTPUT_BY_2W` | VARCHAR2 | 2W 输出人 |
| `OUTPUT_START_2W` | DATE | 2W 输出开始时间 |
| `OUTPUT_FINISH_TIME_2W` | DATE | 2W 输出完成时间 |
| `TOTAL_OUTPUT_MS_2W` | VARCHAR2 | 2W 输出总耗时 |
| `TEST_POINT_2W` | VARCHAR2 | 2W 测试点 |
| `CHECK_BY_2W` | VARCHAR2 | 2W 检查人 |
| `CHECK_START_2W` | DATE | 2W 检查开始时间 |
| `CHECK_FINISH_TIME_2W` | DATE | 2W 检查完成时间 |
| `TOTAL_CHECK_MS_2W` | VARCHAR2 | 2W 检查总耗时 |
| `OUTPUT_PATH_4W` | VARCHAR2 | 4W 输出路径 |
| `OUTPUT_BY_4W` | VARCHAR2 | 4W 输出人 |
| `OUTPUT_START_4W` | DATE | 4W 输出开始时间 |
| `OUTPUT_FINISH_TIME_4W` | DATE | 4W 输出完成时间 |
| `TOTAL_OUTPUT_MS_4W` | VARCHAR2 | 4W 输出总耗时 |
| `TEST_POINT_4W` | VARCHAR2 | 4W 测试点 |
| `CHECK_BY_4W` | VARCHAR2 | 4W 检查人 |
| `CHECK_START_4W` | DATE | 4W 检查开始时间 |
| `CHECK_FINISH_TIME_4W` | DATE | 4W 检查完成时间 |
| `TOTAL_CHECK_MS_4W` | VARCHAR2 | 4W 检查总耗时 |
| `STATUS` | VARCHAR2 | 状态 |
| `LAST_UPDATE_DATE_2W` | DATE | 2W 最后更新时间 |
| `LAST_UPDATED_BY_2W` | VARCHAR2 | 2W 最后更新人 |
| `LAST_UPDATE_DATE_4W` | DATE | 4W 最后更新时间 |
| `LAST_UPDATED_BY_4W` | VARCHAR2 | 4W 最后更新人 |

---

## 🏗️ 项目结构

```
FlyingProbeMS/
├── login.py                  # 登录/注册/改密界面（含记住密码）
├── main.py                   # ★ PyQt5 主界面 V4.0（左侧导航 + StackedWidget 多页面）
├── fp_core_processor.py      # ★ 核心引擎（11步 ezCAM 自动化流程 + 邻近网络距离动态配置）
├── fp_auto_scheduler.py      # ★ 7×24 无人值守批量调度器
├── fp_auto_scheduler.bat     # Windows 双击启动调度器
├── fp_config.py              # 工厂路径/邮箱/通知配置
├── update_tools.py           # 版本更新检查与下载
├── update_version.ini        # 版本更新日志
├── delete_files.py           # 临时文件清理工具
├── config.ini                # 用户配置缓存（工厂/状态/工序）
├── flypin_data.log           # 运行日志
├── icon_rc.py                # Qt 资源编译文件（图标/Logo）
├── README.md                 # 本文件
├── image/                    # UI 图标素材
│   ├── logo.png / logo.ico   #   程序图标
│   ├── genesis.png / .ico    #   Genesis 图标
│   ├── finish.png            #   完成状态图
│   ├── error.png             #   错误状态图
│   ├── warning.png           #   警告图标
│   └── 提醒.png / 正确.png   #   提示图标
└── package/
    ├── Oracle_DB.py          # Oracle 数据库封装层（cx_Oracle）
    ├── genCOM_36.py          # Genesis COM 通信层
    ├── gateway.py            # 网关通信模块
    ├── MessageBox.py         # 自定义弹窗组件
    ├── Ui_MessageBox.py      # 弹窗 UI 定义
    └── wechat_robot.py       # 企业微信机器人通知
```

---

## ⚙️ 核心引擎流程（fp_core_processor.py）

```
① 建立 Genesis COM 连接（ezCAM UID）
    ↓
② 导入 TGZ 工程文件
    ↓
③ 清理无效图层（保留线路/阻焊/钻孔/外形）
    ↓
④ 阻焊层完整性检查
    ↓
⑤ 板型合法性校验（半孔 / 阴阳板 / 灯板）
    ↓
⑥ 自动判断二线(2W) / 四线(4W) 测试模式
    ↓
⑦ 邻近网络距离动态配置（江门二厂 JM2=50，其余 80）
    ↓
⑧ 工作稿 vs 原稿 网络比对（短路/开路检测）
    ↓
⑨ 自动导入原始 Gerber → 坐标对齐 → 覆盖还原
    ↓
⑩ 阻焊小开窗去重清理
    ↓
⑪ 生成飞针测试点 → 输出 356 测试文件
    ↓
⑫ 结果自动回写 Oracle 数据库 → 企业微信通知
```

---

## 🚀 运行方式

### 1. GUI 交互模式

```bash
python login.py
```

登录后进入主界面，左侧导航切换「任务管理」/「报表管理」，搜索料号、查看详情、逐一手动处理。

### 2. 全自动调度模式

```bash
# Windows 双击
fp_auto_scheduler.bat

# 或命令行指定工厂
python fp_auto_scheduler.py JM2
```

自动从 ERP 拉取待处理任务，逐个执行并上报。

---

## 🌿 分支策略

| 分支 | 用途 | 状态 |
|------|------|------|
| `master` | 生产稳定版 | V4.0（2026-06-22） |
| `master-20260620` | 2026年6月功能迭代分支（已合并） | 含 2W/4W 字段重构 |

```bash
git clone https://github.com/heruipeng/FlyingProbeMS.git
git checkout master
```

---

## 🔧 环境依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| Windows | 10/11/Server | 运行 OS |
| Python | 3.7+ | 推荐 3.8+ |
| PyQt5 | ≥5.15 | GUI 框架 |
| cx_Oracle | ≥8.0 | Oracle 数据库驱动 |
| psutil | ≥5.8 | 进程管理 |
| ezFixtureII | 1.1 | 盛鑫飞针测试软件 |
| TPG-E | — | 飞针数据转换工具 |
| Oracle Instant Client | 19.21 | 放入 `instantclient_19_21/` |

### 快速安装

```bash
pip install PyQt5 cx_Oracle psutil
```

---

## 📝 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| V4.0 | 2026-06-22 | 2W/4W 数据绑定重构（ATTRIBUTE→正式列名），详情面板 2W/4W Tab 独立控件，报表 31 列完整字段，邻近网络距离 JM2=50 动态配置，列宽自适应，报表数据明细自动拉伸 |
| V4.0 | 2026-06-19 | 新增报表管理系统（三视图 + 统计卡片 + CSV导出），左侧导航菜单，取消最小化窗口 |
| V3.6 | 2026-06-18 | 上传报表判断工具状态为空才上传，更新当前条目状态 |
| V3.5 | 2026-06-17 | 上传 ERP 空格过滤、核心引擎 bug 修复、2W/4W 检查兼容、启动加速、删除板外物件 |
| V3.4 | 2026-06-16 | 上传旧表、拼板偏位修复、软硬结合板测试 |
| V3.3 | 2026-06-12 | 新增上传 ERP 数据、新增已转换状态 |
| V3.1 | 2026-06-11 | 四线测试删无用层、取消时不上传点数 |
| V3.0 | 2026-06-08 | 新版本发布 |

---

## 📊 数据库表

| 表名 | Schema | 用途 |
|------|--------|------|
| `INP_FLYPIN_PROBE_TOOL_ALERT` | INP | 飞针测试任务主表 |
| `INP_FLYPIN_USER` | INP | 系统用户表 |
| `CUX_WIP_TOINP_V` | APPS | ERP 工单-飞针数据关联视图 |
| `CUX_MI_CHECKMT` | CUX | 治具检查基表 |
| `CUX_MI_CHECKMT_VQ` | APPS | 治具检查查询视图 |
| `BOM_OPERATION_SEQUENCES` | APPS | 工序序列 |
| `BOM_STANDARD_OPERATIONS` | APPS | 标准工序 |

---

## 👤 作者

- **开发者**：何瑞鹏 (rphe)
- **邮箱**：502614708@qq.com
- **出品**：鹏程工作室

---

## 📄 License

Copyright © SUNTAK SOFTWARE GROUP. All Rights Reserved.
