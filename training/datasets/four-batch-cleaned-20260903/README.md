# Four-batch cleaned training data

这是 A 文本拆分任务和 B-SAI 分类任务合并清洗后的公开训练数据，采用 ShareGPT `messages` 格式，包含 `train`、`validation`、`test` 三个划分。

- A：原始 16,725 条，去重后 16,507 条；train 10,619、validation 2,961、test 2,927。
- B-SAI：原始 8,618 条，去重后 8,580 条；train 6,042、validation 1,316、test 1,222。
- 重复内容按 Unicode NFKC 归一化并移除空白后判断；跨批次重复保留批次号较大的记录。
- A 的跨划分输入重叠为 0，B-SAI 的跨划分输入重叠为 0。
- B-SAI 标签为 `Specific -> 0`，`Ambiguous/Generic -> 1`。

去重明细和 SHA-256 校验文件位于同级的 `training/reports/four-batch-cleaned-20260903/`。
