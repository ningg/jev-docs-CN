# jev-docs-CN
Jev 模型 官方说明（TypeSafe），中文文档，中英文，最新版本，持续迭代


## 1.背景

* 为了掌握 Jev 的所有关键点，决定详细阅读[官网资料](https://docs.typesafe.ai/)
* 过程中，为了记录一些业内基础知识，需要在文档上批注
* 决定用 AI 将其做一份 `中英文版本`，同时加上批注，以此加深理解
* 另一方面，也希望统一 中英文术语，避免翻译出不同名称，引入额外的理解成本



## 2.几个事项

| 事项 | 内容 | 状态 |
| --- | --- | --- |
| 获取原文 | 原始的官网文档，下载到本地 | DONE |
| 获取原文 | 调整格式，减少乱码，并且，样式尽可能跟官网一致 | DOING 80% |
| 中文批注 | 阅读一遍后，添加关键批注 | |
| 中文批注 | 打磨细节，校正一遍要点 | |
| 传播形式 | 前期，尽可能每周产出 1 份 pdf 文档 | |
| 传播形式 | 独立网站上，内容实时更新 | DONE |
| 共同建设 | 利用 SEO 等，对外宣传当前工作和计划，吸引更多相同志趣的人，一起建设 | |


## 3.本地预览

侧边栏由 `mkdocs.yml` 里的 `nav` 手写维护，**无需单独生成**。

但 `docs/` 不入库（见 `.gitignore`），需从 `documentation/en/` 转换生成后再预览。

```bash
# 1. 首次：创建虚拟环境并安装依赖
python3 -m venv .venv-docs
source .venv-docs/bin/activate
pip install -r requirements-docs.txt

# 2. 每次改了 documentation/en/ 之后：生成 MkDocs 输入目录 docs/
python scripts/prepare-mkdocs-docs.py

# 3. 启动本地预览（热更新；监听 docs/ 与 mkdocs.yml）
mkdocs serve -a 127.0.0.1:8000
```

浏览器打开：http://127.0.0.1:8000/jev-docs-CN/

可选：

```bash
# 重新从官网拉取英文原文到 documentation/en/（一般不需要）
bash scripts/download-en-docs.sh

# 仅构建静态站点到 site/（不启服务）
mkdocs build
```

| 命令 | 何时需要 |
| --- | --- |
| `pip install -r requirements-docs.txt` | 首次 / 依赖变更 |
| `python scripts/prepare-mkdocs-docs.py` | 改了 `documentation/en/` 或刚 clone |
| `mkdocs serve` | 日常预览 |
| `bash scripts/download-en-docs.sh` | 可选，重新拉官网英文原文 |
| `mkdocs build` | 可选，只构建到 `site/` |




