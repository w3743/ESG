# ESG 发布仓库

本仓库只接受两类交付物：

- `models/`：可分发的模型文件及其最小运行元数据。
- `pdf_text/`：PDF 经 MinerU 解析后的文字结果；只放 Markdown、JSON、TXT 和清单，不放原始 PDF、图片或版面 PDF。

上传前必须阅读 [UPLOAD_CONSTRAINTS.md](UPLOAD_CONSTRAINTS.md)。本仓库采用“先解析、再验收、最后按白名单暂存”的发布流程。任何不属于 `models/` 或 `pdf_text/` 的业务文件都不得提交。

## 目录约定

```text
models/<model-id>/<variant>/
pdf_text/batch-<NN>/<ticker>/
pdf_text/manifests/batch-<NN>.tsv
```

当前 `pdf_text/batch-04/` 是已整理的第 4 批次文字结果。第 5 批次解析完成并验收后，放入 `pdf_text/batch-05/`。

## 版本策略

- 大文件由 Git LFS 管理；Git 历史不通过强制推送重写。
- 每次发布只允许一个明确范围的提交，并在推送前核对 `git diff --cached --name-only`。
- 原始 PDF 保留在本地数据目录，不进入本仓库。
