# Cleaning and audit reports

- `cleaning_report.json`：四批次来源、去重统计、划分重叠检查和不覆盖原始数据的记录。
- `checksums.sha256`：清洗后 JSONL 文件校验值。
- `audit/`：重复决策及排除记录。

本目录只记录数据清洗和训练前审计证据；模型权重与训练指标位于 `models/qwen2.5-1.5b/`。
