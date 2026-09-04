from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("ESG_WORKSPACE", Path(__file__).resolve().parents[2]))
DATA_ROOT = Path(os.environ.get(
    "ESG_FORMAL_DATA_ROOT",
    ROOT / "02_数据与解析" / "正式训练集" / "正式训练集",
))
OUT = Path(os.environ.get(
    "ESG_CLEAN_OUTPUT",
    ROOT / "90_环境与缓存" / "four_batch_cleaned_20260903",
))


A_SOURCES = [
    (1, "A1", DATA_ROOT / "Dataset-A_文本拆分" / "sft"),
    (2, "A2", DATA_ROOT / "Dataset-A_v2.2_Gold_第2批_闭环扩充_30报告_文本拆分" / "sft"),
    (3, "A3", DATA_ROOT / "第三次拆分集_Dataset-A_v3.3_SAI导向终态_20260901" / "sft"),
    (4, "A4", DATA_ROOT / "第四批次_Gold_拆分集_Dataset-A_v4.0_20260901" / "sft"),
]

B_SOURCES = [
    (1, "B1", DATA_ROOT / "Dataset-B_ESG分类" / "Dataset-B_v0.2_gold_plus_silver_all.jsonl", "raw"),
    (2, "B2", DATA_ROOT / "Dataset-B_v1.0_30报告_Luna双盲分类" / "Dataset-B_v1.0_Gold_all.jsonl", "raw"),
    (3, "B3", DATA_ROOT / "第三次分类集_Dataset-B_v3.2_SAI导向_Gold_Silver_20260901" / "sft" / "sai_binary", "sft"),
    (4, "B4", DATA_ROOT / "第四批次_Gold_Silver_分类集_Dataset-B_v4.0_20260901" / "sft" / "sai_binary", "sft"),
]

SPLIT_RANK = {"train": 1, "validation": 2, "test": 3}
SAI_LABELS = {"Specific", "Ambiguous", "Generic"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"JSONL 解析失败: {path}:{line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"JSONL 记录不是对象: {path}:{line_no}")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", "", text)


def key_for_text(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def canonical_json(text: str) -> str:
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return text.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assistant_content(row: dict[str, Any]) -> str:
    for message in reversed(row.get("messages", [])):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    return ""


def user_content(row: dict[str, Any]) -> str:
    for message in row.get("messages", []):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    return ""


def get_system_prompt(sft_dir: Path, split: str = "train") -> str:
    rows = read_jsonl(sft_dir / f"{split}.jsonl")
    for message in rows[0].get("messages", []):
        if message.get("role") == "system":
            return str(message.get("content", ""))
    raise RuntimeError(f"找不到 system prompt: {sft_dir}")


def candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "batch": candidate["batch"],
        "source_tag": candidate["source_tag"],
        "source_id": candidate["source_id"],
        "source_split": candidate["source_split"],
        "output_split": candidate["output_split"],
        "quality_tier": candidate.get("quality_tier"),
        "text_preview": candidate["text"][:160],
        "answer": candidate["answer_canonical"],
    }


def finalize_candidates(
    candidates: list[dict[str, Any]],
    domain: str,
    system_prompt: str,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate["text_key"]].append(candidate)

    selected: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    duplicate_audit: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    batch_selected = Counter()
    split_counts = Counter()
    conflict_groups = 0

    for text_key, group in groups.items():
        group_sorted = sorted(
            group,
            key=lambda item: (
                -item["batch"],
                -SPLIT_RANK.get(item["output_split"], 0),
                item["source_index"],
            ),
        )
        max_batch = group_sorted[0]["batch"]
        max_batch_rows = [item for item in group if item["batch"] == max_batch]
        max_answers = {item["answer_canonical"] for item in max_batch_rows}
        all_answers = {item["answer_canonical"] for item in group}

        if len(max_answers) > 1:
            conflict_groups += 1
            duplicate_audit.append(
                {
                    "text_key": text_key,
                    "domain": domain,
                    "decision": "excluded_same_highest_batch_conflict",
                    "highest_batch": max_batch,
                    "records": [candidate_summary(item) for item in group_sorted],
                }
            )
            for item in group_sorted:
                excluded.append(
                    {
                        "domain": domain,
                        "reason": "same_content_conflicting_answers_in_highest_batch",
                        "text_key": text_key,
                        **candidate_summary(item),
                    }
                )
            continue

        winner = group_sorted[0]
        if len(group) > 1:
            duplicate_audit.append(
                {
                    "text_key": text_key,
                    "domain": domain,
                    "decision": "keep_highest_batch",
                    "highest_batch": max_batch,
                    "answer_conflict_across_batches": len(all_answers) > 1,
                    "winner": candidate_summary(winner),
                    "records": [candidate_summary(item) for item in group_sorted],
                }
            )

        # Keep the training schema uniform across all four source versions.
        # Per-row provenance is retained in the audit JSONL, not in a variable
        # nested metadata struct that Apache Arrow cannot cast consistently.
        output_row = {
            "id": f"{domain}{winner['batch']}-{winner['source_id']}",
            "split": winner["output_split"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": winner["text"]},
                {"role": "assistant", "content": winner["assistant"]},
            ],
        }
        report_id = winner["row"].get("report_id") or (winner["row"].get("metadata") or {}).get("report_id")
        if report_id is not None:
            output_row["report_id"] = str(report_id)
        selected[winner["output_split"]].append(output_row)
        batch_selected[winner["batch"]] += 1
        split_counts[winner["output_split"]] += 1

    for split in selected:
        selected[split].sort(key=lambda row: row["id"])

    # A final invariant: after global dedup, no normalized input may occur in two splits.
    split_keys: dict[str, set[str]] = {
        split: {key_for_text(user_content(row)) for row in rows}
        for split, rows in selected.items()
    }
    split_overlap = {
        f"{left}_vs_{right}": sorted(split_keys[left] & split_keys[right])
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    }

    audit = {
        "domain": domain,
        "raw_rows": len(candidates),
        "unique_normalized_inputs": len(groups),
        "selected_rows": sum(len(rows) for rows in selected.values()),
        "selected_by_batch": dict(sorted(batch_selected.items())),
        "selected_by_split": dict(split_counts),
        "duplicate_groups": sum(len(group) > 1 for group in groups.values()),
        "duplicate_rows_removed": len(candidates) - len(groups),
        "same_highest_batch_conflict_groups_excluded": conflict_groups,
        "excluded_rows": len(excluded),
        "split_overlap_counts": {name: len(values) for name, values in split_overlap.items()},
        "split_overlap_keys": split_overlap,
        "duplicate_decisions": duplicate_audit,
        "excluded": excluded,
    }
    return selected, audit


def make_a_candidates() -> tuple[list[dict[str, Any]], str]:
    candidates: list[dict[str, Any]] = []
    for batch, source_tag, sft_dir in A_SOURCES:
        for split in ("train", "validation", "test"):
            path = sft_dir / f"{split}.jsonl"
            for source_index, row in enumerate(read_jsonl(path)):
                text = user_content(row)
                answer = assistant_content(row)
                if not text or not answer:
                    continue
                source_id = str(row.get("id") or (row.get("metadata") or {}).get("id") or f"row-{source_index}")
                metadata = row.get("metadata") or {}
                candidates.append(
                    {
                        "row": row,
                        "batch": batch,
                        "source_tag": source_tag,
                        "source_id": source_id,
                        "source_split": split,
                        "output_split": split,
                        "source_index": source_index,
                        "text": text,
                        "text_key": key_for_text(text),
                        "assistant": answer,
                        "answer_canonical": canonical_json(answer),
                        "quality_tier": metadata.get("quality_tier"),
                    }
                )
    latest_prompt = get_system_prompt(A_SOURCES[-1][2])
    return candidates, latest_prompt


def make_b_raw_candidates(
    batch: int,
    source_tag: str,
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for source_index, row in enumerate(read_jsonl(path)):
        label = row.get("label")
        if label not in SAI_LABELS:
            continue
        source_split = str(row.get("split") or "train")
        quality_tier = str(row.get("quality_tier") or "")
        # Silver is admissible as training data, but never remains in validation/test.
        output_split = "train" if "silver" in quality_tier.lower() else source_split
        source_id = str(row.get("statement_id") or f"row-{source_index}")
        text = str(row.get("statement_text") or "")
        if not text:
            excluded.append({"domain": "B", "reason": "empty_statement_text", "source_tag": source_tag, "source_id": source_id})
            continue
        non_specific = 0 if label == "Specific" else 1
        assistant = json.dumps({"non_specific": non_specific}, ensure_ascii=False, separators=(",", ":"))
        candidates.append(
            {
                "row": row,
                "batch": batch,
                "source_tag": source_tag,
                "source_id": source_id,
                "source_split": source_split,
                "output_split": output_split,
                "split_reassigned": output_split != source_split,
                "source_index": source_index,
                "text": text,
                "text_key": key_for_text(text),
                "assistant": assistant,
                "answer_canonical": assistant,
                "quality_tier": quality_tier,
            }
        )
    return candidates, excluded


def make_b_sft_candidates(
    batch: int,
    source_tag: str,
    sft_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for split in ("train", "validation", "test"):
        path = sft_dir / f"{split}.jsonl"
        for source_index, row in enumerate(read_jsonl(path)):
            text = user_content(row)
            assistant = assistant_content(row)
            try:
                parsed = json.loads(assistant)
                non_specific = int(parsed["non_specific"])
                if non_specific not in (0, 1):
                    raise ValueError
            except (TypeError, ValueError, KeyError, json.JSONDecodeError):
                excluded.append(
                    {
                        "domain": "B",
                        "reason": "invalid_sai_assistant",
                        "source_tag": source_tag,
                        "source_id": row.get("id"),
                    }
                )
                continue
            metadata = row.get("metadata") or {}
            quality_tier = str(metadata.get("quality_tier") or "")
            source_split = split
            output_split = "train" if "silver" in quality_tier.lower() else source_split
            source_id = str(row.get("id") or metadata.get("statement_id") or f"row-{source_index}")
            if not text:
                excluded.append({"domain": "B", "reason": "empty_user_text", "source_tag": source_tag, "source_id": source_id})
                continue
            normalized_assistant = json.dumps({"non_specific": non_specific}, ensure_ascii=False, separators=(",", ":"))
            candidates.append(
                {
                    "row": row,
                    "batch": batch,
                    "source_tag": source_tag,
                    "source_id": source_id,
                    "source_split": source_split,
                    "output_split": output_split,
                    "split_reassigned": output_split != source_split,
                    "source_index": source_index,
                    "text": text,
                    "text_key": key_for_text(text),
                    "assistant": normalized_assistant,
                    "answer_canonical": normalized_assistant,
                    "quality_tier": quality_tier,
                }
            )
    return candidates, excluded


def build_b_candidates() -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    source_excluded: list[dict[str, Any]] = []
    for batch, source_tag, path, kind in B_SOURCES:
        if kind == "raw":
            rows, excluded = make_b_raw_candidates(batch, source_tag, path)
        else:
            rows, excluded = make_b_sft_candidates(batch, source_tag, path)
        candidates.extend(rows)
        source_excluded.extend(excluded)
    latest_prompt = get_system_prompt(B_SOURCES[-1][2])
    return candidates, latest_prompt, source_excluded


def source_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {"A": [], "B": []}
    for batch, source_tag, sft_dir in A_SOURCES:
        counts = {split: len(read_jsonl(sft_dir / f"{split}.jsonl")) for split in ("train", "validation", "test")}
        inventory["A"].append({"batch": batch, "source_tag": source_tag, "path": str(sft_dir), "counts": counts})
    for batch, source_tag, path, kind in B_SOURCES:
        if kind == "raw":
            rows = read_jsonl(path)
            counts = Counter(str(row.get("split") or "train") for row in rows)
        else:
            counts = Counter()
            for split in ("train", "validation", "test"):
                counts[split] = len(read_jsonl(path / f"{split}.jsonl"))
        inventory["B"].append({"batch": batch, "source_tag": source_tag, "path": str(path), "kind": kind, "counts": dict(counts)})
    return inventory


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a_candidates, a_prompt = make_a_candidates()
    b_candidates, b_prompt, b_source_excluded = build_b_candidates()

    a_selected, a_audit = finalize_candidates(a_candidates, "A", a_prompt)
    b_selected, b_audit = finalize_candidates(b_candidates, "B", b_prompt)
    b_audit["source_level_excluded"] = b_source_excluded
    b_audit["source_level_excluded_count"] = len(b_source_excluded)

    for split, rows in a_selected.items():
        write_jsonl(OUT / "dataset_a" / "sft" / f"{split}.jsonl", rows)
    for split, rows in b_selected.items():
        write_jsonl(OUT / "dataset_b_sai" / "sft" / f"{split}.jsonl", rows)

    write_jsonl(OUT / "audit" / "a_duplicate_decisions.jsonl", a_audit.pop("duplicate_decisions"))
    write_jsonl(OUT / "audit" / "a_excluded.jsonl", a_audit.pop("excluded"))
    write_jsonl(OUT / "audit" / "b_duplicate_decisions.jsonl", b_audit.pop("duplicate_decisions"))
    write_jsonl(OUT / "audit" / "b_excluded.jsonl", b_audit.pop("excluded") + b_source_excluded)

    dataset_info = {}
    for name, directory in (("four_batch_a_cleaned", "dataset_a"), ("four_batch_b_sai_cleaned", "dataset_b_sai")):
        for split in ("train", "validation", "test"):
            dataset_info[f"{name}_{split}"] = {
                "file_name": f"{directory}/sft/{split}.jsonl",
                "formatting": "sharegpt",
                "columns": {"messages": "messages"},
                "tags": {
                    "role_tag": "role",
                    "content_tag": "content",
                    "user_tag": "user",
                    "assistant_tag": "assistant",
                    "system_tag": "system",
                },
            }
    (OUT / "dataset_info.json").write_text(json.dumps(dataset_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "run_id": "four-batches-cleaned-20260903",
        "created_at": "2026-09-03",
        "rule": "Normalize Unicode NFKC and remove whitespace for content identity; when the same content occurs in multiple batches, keep the larger batch. Within one batch, prefer test over validation over train for identical duplicate rows. If the highest batch has conflicting answers, exclude the whole content group for review.",
        "batch_selection": {
            "A": {"1": "Dataset-A_文本拆分", "2": "Dataset-A_v2.2", "3": "Dataset-A_v3.3", "4": "Dataset-A_v4.0"},
            "B": {"1": "Dataset-B_v0.2_gold_plus_silver", "2": "Dataset-B_v1.0", "3": "Dataset-B_v3.2_sai_binary", "4": "Dataset-B_v4.0_sai_binary"},
        },
        "source_inventory": source_inventory(),
        "dataset_a": a_audit,
        "dataset_b_sai": b_audit,
        "invariants": {
            "a_train_validation_test_text_overlap": a_audit["split_overlap_counts"],
            "b_train_validation_test_text_overlap": b_audit["split_overlap_counts"],
            "original_data_overwritten": False,
            "silver_in_b_validation_or_test": False,
        },
    }
    (OUT / "cleaning_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "A": {"raw": a_audit["raw_rows"], "selected": a_audit["selected_rows"], "by_split": a_audit["selected_by_split"]},
        "B_SAI": {"raw": b_audit["raw_rows"], "selected": b_audit["selected_rows"], "by_split": b_audit["selected_by_split"]},
        "A_conflict_groups_excluded": a_audit["same_highest_batch_conflict_groups_excluded"],
        "B_conflict_groups_excluded": b_audit["same_highest_batch_conflict_groups_excluded"],
        "B_source_level_excluded": b_audit["source_level_excluded_count"],
        "split_overlaps": {"A": a_audit["split_overlap_counts"], "B": b_audit["split_overlap_counts"]},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
