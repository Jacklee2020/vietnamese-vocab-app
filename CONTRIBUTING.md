# 贡献指南（Contributing）

感谢你有兴趣为「越南语千词斩」贡献！任何形式的帮助都欢迎：提 issue、修 bug、完善词库、改进文档。

## 项目结构速览

- `pwa/`：应用本体（`index.html` 内嵌全部词库，整个目录即完整应用）
- `词库_合并版.csv`：词库源数据（`序号, 分类, 越南语, 中文`）
- `scripts/validate_dict.py`：词库校验脚本（CI 会自动运行）
- `merge_data.py` / `make_pwa.py`：词库合并与构建脚本

## 如何贡献

### 报告问题

1. 先搜索已有 issue，避免重复；
2. 新建 issue 时说明：设备与浏览器、操作步骤、实际结果、期望结果，尽量附截图。

### 修改词库

1. 用 Excel / 表格软件打开 `词库_合并版.csv`（UTF-8 编码）编辑；
2. 本地运行校验：`python3 scripts/validate_dict.py 词库_合并版.csv`；
3. 校验通过后再提交（或直接提 issue 说明想增删的单词）。

### 修改代码

1. Fork 本仓库并 clone；
2. 创建分支：`git checkout -b feature/你的改动`；
3. 提交前跑一遍校验：
   ```bash
   python3 scripts/validate_dict.py 词库_合并版.csv
   ```
4. 提交并发起 Pull Request，描述改动目的。

## 约定

- 词库数据**保留所有权利**（见 LICENSE），贡献词条即视为授权本项目使用；
- 代码风格保持简洁，遵循现有写法，不引入第三方依赖。
