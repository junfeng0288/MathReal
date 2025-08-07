import json
import sys
import os

category_map = {
    "Plane Geometry": "PG",
    "Solid Geometry": "SG",
    "Logical Reasoning": "LR",
    "Function Graphs": "FG",
    "Statistical Charts": "SC"
}
category_order = ["PG", "SG", "LR", "FG", "SC"]

def build_idx_category(gt_file):
    with open(gt_file, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    idx2cat = {}
    for item in gt_data:
        if "Category" in item and item["Category"] in category_map:
            idx2cat[item["idx"]] = category_map[item["Category"]]
    return idx2cat

def calc_model_score(score_file, idx2cat):
    with open(score_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cats = {cat: {"acc": 0, "acc_cnt": 0, "acc_str": 0, "acc_str_cnt": 0} for cat in category_map.values()}
    total_acc = 0
    total_acc_cnt = 0
    total_acc_str = 0
    total_acc_str_cnt = 0
    for item in data:
        idx = item["idx"]
        if idx not in idx2cat:
            continue
        cat = idx2cat[idx]
        if "acc" in item:
            cats[cat]["acc"] += item["acc"]
            cats[cat]["acc_cnt"] += 1
            total_acc += item["acc"]
            total_acc_cnt += 1
        if "acc_str" in item:
            cats[cat]["acc_str"] += item["acc_str"]
            cats[cat]["acc_str_cnt"] += 1
            total_acc_str += item["acc_str"]
            total_acc_str_cnt += 1
    acc_avg = {}
    acc_str_avg = {}
    for cat in category_order:
        acc_avg[cat] = cats[cat]["acc"] / cats[cat]["acc_cnt"] if cats[cat]["acc_cnt"] > 0 else 0
        acc_str_avg[cat] = cats[cat]["acc_str"] / cats[cat]["acc_str_cnt"] if cats[cat]["acc_str_cnt"] > 0 else 0
    overall_acc_str_avg = total_acc_str / total_acc_str_cnt if total_acc_str_cnt > 0 else 0
    overall_acc_avg = total_acc / total_acc_cnt if total_acc_cnt > 0 else 0
    return acc_avg, acc_str_avg, overall_acc_str_avg, overall_acc_avg

if __name__ == "__main__":
    gt_file = sys.argv[1]
    model_file = sys.argv[2]
    idx2cat = build_idx_category(gt_file)
    acc_avg, acc_str_avg, overall_acc_str_avg, overall_acc_avg = calc_model_score(model_file, idx2cat)
    out = []
    for cat in category_order:
        out.append(f"{acc_str_avg[cat]*100:.1f}")
    out.append(f"{overall_acc_str_avg*100:.1f}")
    for cat in category_order:
        out.append(f"{acc_avg[cat]*100:.1f}")
    out.append(f"{overall_acc_avg*100:.1f}")
    print(" & ".join(out))
