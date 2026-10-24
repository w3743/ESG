# ESG 发布仓库

本仓库发布 ESG 模型及企业报告的 MinerU 直接解析文字。模型入口见 [模型目录](models/README.md)，文字结果见 [pdf_text](pdf_text/README.md)。

## 模型

| 版本 | 交付形式 | 状态与入口 |
| --- | --- | --- |
| Qwen3.5-9B B09（2026-09-29） | 完整 GGUF，Q5_K_M，约 6.02 GiB | **实验候选**；[说明与下载](models/qwen3.5-9b/esg-split-classify-b09-20260929/README.md) · [预发布版](https://github.com/w3743/ESG/releases/tag/esg-qwen35-9b-b09-20260929-q5-k-m) |
| Qwen2.5-1.5B ESG Split / SAI | 两个独立 LoRA 适配器 | 历史版本；[加载说明](models/qwen2.5-1.5b/README.md) |
| ESG BERT Gold3x（2026-08-24） | 历史模型包 | 见 [模型目录](models/README.md) |

B09 权重以 Release 的 4 个分卷分发，目录内提供自动下载、逐卷校验和合并工具。完整 GGUF 无需额外加载基础模型或 LoRA；旧版 Qwen2.5 适配器需要对应底座。B09 保留实验候选状态，不代表已通过生产验收。

## PDF 解析文字

当前 batch-04 至 batch-10 共 7 批，每批 50 份，共 350 份报告文字。每份报告固定保存为 pdf_text/batch-<NN>/<ticker>/report.md；<ticker> 为保留市场后缀的证券代码。

原始 PDF、图片、表格清单和验收元数据在本地维护；仓库中只交付直接解析文字。

## 目录结构

`	ext
models/
  README.md
  qwen3.5-9b/esg-split-classify-b09-20260929/
    README.md           模型卡、历史指标与已知限制
    manifest.json       完整文件与分卷大小、SHA-256、下载 URL
    SHA256SUMS          校验表
    download_model.py   下载、验证并还原 GGUF
  qwen2.5-1.5b/         历史 LoRA 适配器
pdf_text/
  batch-04/ ... batch-10/
    <ticker>/report.md
`

## 发布约定

上传规则见 [UPLOAD_CONSTRAINTS.md](UPLOAD_CONSTRAINTS.md)。可提交的业务路径仅为 models/ 和 pdf_text/；根目录仅保留仓库说明与 Git 配置文件。

- 大权重与模型包使用 Git LFS；本版本 GGUF 使用 GitHub Release 分卷。说明、配置、分词器和清单使用普通 Git。
- 训练数据、训练脚本、训练状态、日志和缓存不进入发布仓库。
- 推送前按明确文件白名单检查，使用正常快进提交，不重写历史。
- 模型和原始报告的许可分别以对应来源为准；本仓库未新增第三方内容许可授权。
