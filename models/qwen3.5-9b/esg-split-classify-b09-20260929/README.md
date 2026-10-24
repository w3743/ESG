# ESG Split Classify · Qwen3.5-9B · B09

此版本为 **实验候选，尚未晋级正式模型**。基于 `Qwen/Qwen3.5-9B`，从既有 `update1350` 适配器继续训练，再合并并导出为完整 GGUF 权重；使用此 GGUF 不需要额外加载 LoRA 或基础模型。

| 项目 | 值 |
| --- | --- |
| 模型检查点 | B09，2026-09-29 |
| LM Studio 登记日期 | 2026-10-13 |
| 格式 / 量化 | GGUF / Q5_K_M |
| 文件大小 | 6,467,969,664 字节（约 6.02 GiB） |
| 基座修订 | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| 导出工具 | llama.cpp `b11026` |
| 完整文件 SHA-256 | `ab6da373a48b84807201948e250446fbcbf2143eb3ea69c31be6f629c44a8334` |

## 下载与还原

权重位于 [GitHub 预发布版](https://github.com/w3743/ESG/releases/tag/esg-qwen35-9b-b09-20260929-q5-k-m)。受 GitHub Release 单附件大小限制，原始文件按字节顺序分成 4 卷；这些分卷不是可单独加载的 GGUF，也不是压缩包。

先克隆仓库，在仓库根目录执行（Python 3.10+，仅使用标准库）：

```sh
python models/qwen3.5-9b/esg-split-classify-b09-20260929/download_model.py --output-dir ./downloaded-models
```

脚本逐卷下载、核对大小和 SHA-256，按顺序合并，并再次验证完整模型 SHA-256。已完成且校验通过的分卷会跳过；下载中断时重新执行即可。请预留至少 13 GB 可用磁盘空间用于分卷和合并后的文件。

也可以手动下载 Release 内的 `.part001` 至 `.part004`，全部放到同一个目录，再执行：

```sh
python models/qwen3.5-9b/esg-split-classify-b09-20260929/download_model.py --output-dir ./downloaded-models --merge-only
```

还原结果：`ESG-Split-Classify-Qwen3.5-9B-B09-20260929-Q5_K_M.gguf`。分卷详情见 [manifest.json](manifest.json)，校验表见 [SHA256SUMS](SHA256SUMS)。仓库源码 ZIP 不包含本版本 GGUF 权重。

## 加载与适用范围

将还原后的 `.gguf` 导入支持 Qwen3.5 `qwen35` 架构的 LM Studio，或通过兼容的 llama.cpp 加载。导出工具版本记录在上表；本次发布验证了文件完整性，未重新执行推理性能或业务验收测试。模型面向中文企业 ESG 报告陈述拆分和分类；分类历史标签为 `Non-ESG`、`Specific`、`Ambiguous`、`Generic`。不能套用旧版 Qwen2.5 SAI 的二分类输出约定。

本交付未附完整训练提示词和原始任务协议；实际使用应沿用该训练版本对应的提示词，并由应用校验结构化输出。不要将普通聊天示例当作已验证的业务协议。

## 已知评测与限制

导出凭据记录：B09 使用 274 条训练样本、18 次参数更新，训练批次自身无验证集或测试集。在历史 211 条分类开发集上，与 `update1350` 配对比较：

| 历史分类指标 | update1350 | B09 |
| --- | ---: | ---: |
| 联合完全正确 | 122 / 211（57.82%） | 132 / 211（62.56%） |
| Macro F1 | 0.5485 | 0.5833 |

以上为源适配器的历史开发集结果，不能代表本次 GGUF 的独立测试结果。Ambiguous 改善，但 Non-ESG 和 Generic 召回下降；该 211 条结果不覆盖完整拆分任务。仍需未见来源的最终测试，因此保持实验候选状态。

基础模型许可见 [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)。本发布不新增训练数据或第三方材料的许可授权。
