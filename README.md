# ESG

## 第 4 批次

`第4批次_解析结果.7z` 收录 50 份 2024 年中文 ESG、可持续发展或环境社会治理报告的完整 MinerU 解析目录。配套文件如下：

- `第4批次_清单.tsv`：公司、证券代码、报告标题、官方来源 URL、下载时间、页数、PDF SHA-256、规范化文本指纹和解析状态。
- `第4批次_校验报告.json`：50 份输入、50 个输出目录、唯一性、正文年份/类型、核心文件及 7z 测试结果。
- `第4批次_README.md`：采集准入、MinerU 命令、GPU 运行和使用说明。

本批次使用公司官网、CNINFO、上交所、深交所或港交所等正式披露来源；未启动模型训练、Arena 或分类评估。大型解析归档由 Git LFS 管理。

## 已发布的微调模型

当前发布的是基于 `Qwen2.5-1.5B-Instruct` 的两个独立 LoRA 适配器，不能单独替代底座模型：

- [`models/qwen2.5-1.5b/esg-split`](models/qwen2.5-1.5b/esg-split)：A 模型，将企业报告段落拆分为事实陈述，输出 `{"statements":["..."]}`。
- [`models/qwen2.5-1.5b/esg-sai`](models/qwen2.5-1.5b/esg-sai)：B-SAI 模型，判断单条 ESG 陈述是否 NonSpecific，输出 `{"non_specific":0}` 或 `{"non_specific":1}`。

模型训练配置、清洗后的四批次数据和审计报告分别位于 `training/configs/`、`training/datasets/` 和 `training/reports/`。发布内容不包含训练检查点、优化器状态或本地临时日志。

## 目录结构

```text
models/                         已训练模型及模型说明
training/configs/               可复现训练配置
training/datasets/              清洗后的训练、验证和测试 JSONL
training/reports/               去重规则、审计记录和校验文件
```

## 历史归档说明

仓库根目录中的 `第3批次_解析结果.7z`、`第4批次_解析结果.7z` 及其清单、校验报告属于既有发布路径，继续保留在根目录以兼容历史链接。它们不与当前训练发布物混用：

- 当前模型统一位于 `models/qwen2.5-1.5b/`。
- 当前训练配置、数据、脚本和审计材料统一位于 `training/`。
- 历史归档的分类和迁移约束见 [`archives/README.md`](archives/README.md)。

权重文件由 Git LFS 管理。使用模型前请先获取 Qwen 基础模型，并遵守基础模型与数据来源的适用许可。
