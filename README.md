# 健康管理与数据分析中心

一款电脑端健康管理软件：录入身高、体重、年龄、性别等个人数据后，自动计算并展示 BMI、基础代谢率（BMR）、每日总消耗（TDEE）、体脂率估算、健康体重区间等健康指标，并生成个性化的中文饮食 / 运动 / 作息建议报告。软件记录每次生成报告的时间，并每周自动对历史报告进行表格化汇总。

## 功能特性

- 个人信息录入（身高 / 体重 / 年龄 / 性别 / 活动水平）
- 健康指标计算（中国成人标准）
  - BMI 及分级（偏瘦 / 正常 / 超重 / 肥胖，配色徽章）
  - 基础代谢率 BMR（Mifflin-St Jeor 公式，分男女）
  - 每日总消耗 TDEE（按活动水平）
  - 体脂率估算（Deurenberg 公式）
  - 健康体重区间
- 指标仪表盘 + BMI 趋势折线图
- 个性化健康建议报告（Markdown 富文本）
- 历史报告记录（每次生成带时间戳，可查看往期详情）
- 每周自动表格化汇总（按自然周聚合，可导出 CSV）

## 目录结构

```
health_manager/
├── main.py              # 程序入口
├── calc.py              # 健康指标计算引擎（纯函数，可单测）
├── storage.py           # SQLite 持久化 + 自动周汇总
├── report_gen.py        # 个性化健康建议生成
├── ui/                  # PyQt6 界面（录入/结果/建议/历史/周汇总）
├── tests/test_calc.py   # 计算引擎单元测试
├── smoke_test.py        # 无显示环境冒烟测试
├── requirements.txt     # 运行依赖
├── pyproject.toml       # 项目元数据
├── run.bat              # Windows 启动脚本
├── run.sh               # Linux / macOS 启动脚本
└── .gitignore           # 排除本机数据与构建产物
```

## 运行方式

### Windows

- 已打包用户：直接双击 `dist/健康管理.exe`（无需安装 Python）。
- 源码用户：先安装依赖，再运行
  ```
  pip install -r requirements.txt
  run.bat
  ```
  或直接 `python main.py`。

### Linux / macOS

```
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

## 打包为可执行文件

使用 PyInstaller 构建单文件 exe（Windows 示例）：

```
pip install pyinstaller
pyinstaller --onefile --windowed --name 健康管理 --hidden-import PyQt6.QtCharts main.py
```

产物位于 `dist/`。macOS / Linux 用户请在本平台自行打包。

## 数据存储说明（重要）

- 每个用户各自持有一份**本地 SQLite 数据库**，数据**不出本机**，符合隐私预期。
- 默认存放位置（可通过环境变量覆盖）：
  - Windows：`%APPDATA%\健康管理\health.db`
  - macOS：`~/Library/Application Support/健康管理/health.db`
  - Linux：`~/.local/share/健康管理/health.db`
- 如需把数据库放到 U 盘或指定文件夹，设置环境变量后启动：
  ```
  set HEALTH_DB_PATH=D:\my_health.db    # Windows
  export HEALTH_DB_PATH=/mnt/usb/my_health.db   # Linux/macOS
  ```
- 卸载软件如需清除个人数据，删除上述目录 / 文件即可。
- 历史与周汇总均支持导出 CSV，便于数据携带与备份。

## 数据库演进

`health.db` 通过 `PRAGMA user_version` 记录 schema 版本（`storage.SCHEMA_VERSION`）。
日后若变更表结构，请在 `storage._apply_migrations` 中追加迁移步骤，老用户升级软件后数据库会自动平滑升级，不会损坏。

## 隐私与合规提示

健康数据属于敏感个人信息。本软件采用本地优先（local-first）设计，默认不联网、不收集任何用户数据。若将其改造为集中式（多用户 / 云端）部署，请注意遵守《个人信息保护法》等相关法规，落实告知同意、数据加密与最小收集原则。

## 许可证

本项目仅供学习与个人使用。
