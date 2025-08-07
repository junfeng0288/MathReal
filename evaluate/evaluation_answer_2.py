import os
import json
import argparse
from tqdm import tqdm
from openai import OpenAI
import re

BASE_URL = ""
API_KEY = ""

def create_eval_prompt(gt_answer, model_answer, question_type):
    prompt = f"""You are a top-tier mathematics evaluation expert, tasked with rigorously and precisely determining the correctness of model-generated answers.
### Core Task
Determine whether the "Model Answer" below is mathematically and option-wise completely equivalent to the "Reference Answer", and assign a **partial credit score** based on the proportion of correct components.
### Evaluation Principles
1.  **Numerical Core Priority**:
    - Focus solely on the final numerical values, expressions, options, or conclusions.
    - Ignore solution processes, explanatory text (e.g., "the answer is:", "therefore the result is:"), variable names (e.g., D, E, Q1), and irrelevant descriptions.
    - Only retain mathematical content that directly corresponds to the reference answer for comparison.
2.  **Mathematical Equivalence (Strict Judgment)**:
    - Fractions and decimals: 1/2 is equivalent to 0.5; 1/2 is equivalent to 5/10.
    - Numerical formats: 10 is equivalent to 10.0; 1,887,800 is equivalent to 1887800 (ignore thousand separators).
    - Special symbols: π is equivalent to 3.14 (only when the problem explicitly allows approximation).
    - Algebraic expressions: x^2 + y is equivalent to y + x^2; however, `18+6√3` and `18-6√3` are **not equivalent**.
    - Formatting: (√3 + 3)/2 is equivalent to √3/2 + 3/2.
    - Range notation: x∈[0, 1] is equivalent to 0<=x<=1.
    - **Operator Sensitivity**: +, -, ×, ÷, ^, etc., must be strictly consistent; any symbol error renders the expressions non-equivalent.
    - **Coordinate Points**: (x,y) values must be numerically identical. Treat x and y as **two sub-components**. If one is correct and the other wrong, assign 0.5 for that point.
    - **Whitespace-induced formatting differences**: "y=2x+3" and "y = 2 x + 3" are equivalent; ignore the impact of spaces within expressions.
3.  **Unit Handling**:
    - Reference answer has no unit: if the model answer includes a correct and reasonable unit (e.g., 15 vs 15m), it is considered correct.
    - Reference answer has a unit: incorrect units are considered wrong (e.g., 15m vs 15cm); if the model answer lacks a unit but the numerical value is correct, it is considered correct.
    - Ignore unit formatting differences: "180 \\text{{ dm}}^2" and "180dm^2" are equivalent; correctly extract the content.
4.  **Handling Multi-Part Answers (Critical!)**:
    - You must **split the reference answer into all sub-answers (blanks)** based on its structure.
    - Each newline `\
`, semicolon `;`, or major section `(1)`, `(2)` indicates a separate blank.
    - For each blank, further decompose it if it contains multiple components:
        - **Multiple-choice selections**: e.g., "②;③" → two sub-answers. If model answers "②", give 0.5.
        - **"Or"-connected answers**: e.g., "5 or -75" → two valid solutions. If model answers only "5", give 0.5 for that blank.
        - **Coordinate pairs**: e.g., (5,0) → treat as two values. If model says (5,1), give 0.5.
        - **Multiple points**: e.g., (1,0),(9,8),(-1,9) → three points. Each correct point gives 1/3.
    - Total score = sum of all correct sub-components / total number of sub-components.
    - Always allow **proportional partial credit** unless explicitly stated otherwise.
5.  **Special Rules for Multiple-Choice Questions**:
    - If the reference answer is a single option (e.g., "B"), then as long as the model answer contains that option letter (e.g., "B", "B.", "Option B", "B. f'(x₀) > g'(x₀)") and no other options, it is considered correct → 1.0.
    - If multiple options appear or an incorrect option is selected, it is considered wrong → 0.0.
6.  **Semantic Equivalence**:
    - Even if the phrasing differs, as long as the mathematical meaning is the same, it is considered correct.
    - For example: "materials ② and ③" is equivalent to "②;③"; "you selected B" is equivalent to "B".
7.  **Proof or Graphing Questions**:
    - If the question type is a proof or graphing question, treat the model answer as acceptable by default; do not score it, and directly return <score>1.0</score>.
### Scoring Criteria
- **1.0**: All components are correct.
- **0.0–1.0**: Assign partial credit **proportionally** based on the number of correct sub-components.
- **0.0**: No component is correct.
- Round to **two decimal places** (e.g., 0.83, 0.67, 0.50).
### Output Format
You must strictly return only the XML tag containing the score, with no additional text or explanation.
<score>score</score>
Examples:
<score>1.0</score>
<score>0.5</score>
<score>0.33</score>
### Example1 (Or-connected answers)
**Question Type**: Problem-solving  
**Reference Answer**:  
"(1)①(5,0);
②(15,0)or(-5,0);
(2)5or-75."  
**Model Answer**:  
"D(5, 0); E(15, 0) \\text{{ or }} E(-5, 0); 5"  
**Analysis**:  
- Blank ①: (5,0) → one point → correct → 1.0 for this sub-blank → 1/3
- Blank ②: two solutions: (15,0), (-5,0) → model gives both → correct → 1/3
- Blank (2): two solutions: 5, -75 → model only gives 5 → covers 1 out of 2 → 0.5 credit → 0.5 * (1/3) = 1/6
- Total score: 1/3 + 1/3 + 1/6 = 5/6 ≈ 0.83
<score>0.83</score>
### Example2 (Multiple selections)
**Question Type**: Problem-solving  
**Reference Answer**:  
"②;③;⑤"  
**Model Answer**:  
"② and ⑤"  
**Analysis**:
- Total of 3 correct selections.
- Model selects ② (correct), ⑤ (correct), misses ③ → 2 out of 3 correct → score = 2/3 ≈ 0.67
<score>0.67</score>

### Evaluation Content  
**Question Type**: {question_type}  
**Reference Answer**:  
"{gt_answer}"  
**Model Answer**:  
"{model_answer}"  
"""
    return prompt

def evaluate_answer_score_openai(model_answer, gt_answer, question_type):
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )
    prompt = create_eval_prompt(gt_answer, model_answer, question_type)
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = completion.choices[0].message.content.strip()
        score_match = re.search(r"<score>([\d.]+)</score>", content)
        if score_match:
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))
            return score, {"raw_output": content}
        else:
            numbers = re.findall(r'\b0\.\d+\b|\b1\.0+\b|\b[01]\b', content)
            if numbers:
                score = float(numbers[-1])
                score = max(0.0, min(1.0, score))
                return score, {"raw_output": content, "warning": "Score tag not found, using regex extraction"}
            else:
                return 0.0, {"error": "Unable to extract score", "raw_output": content}
    except Exception as e:
        return 0.0, {"error": str(e)}

def load_json_data(file_path, key_by_field=None, default_if_error=None):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if key_by_field:
            if isinstance(data, list) and all(key_by_field in item for item in data if isinstance(item, dict)):
                return {item[key_by_field]: item for item in data if isinstance(item, dict) and key_by_field in item}
            else:
                return default_if_error if default_if_error is not None else data
        return data
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return default_if_error

def main():
    parser = argparse.ArgumentParser(description='Evaluate extracted answers using OpenAI API for full and partial credit scoring.')
    parser.add_argument('--gt_file', type=str, required=True, help='Path to GT question data file (containing idx and answer_gt fields)')
    parser.add_argument('--extract_file', type=str, required=True, help='Path to extracted answer JSON file (containing idx and extracted_answer fields)')
    parser.add_argument('--output_file', type=str, required=True, help='Output file path')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of data entries to process')
    args = parser.parse_args()

    gt_data_map = load_json_data(args.gt_file, key_by_field="idx", default_if_error={})
    extract_data_map = load_json_data(args.extract_file, key_by_field="idx", default_if_error={})

    if not gt_data_map:
        print(f"Error: Failed to load GT question data file '{args.gt_file}'. Program terminated.")
        return
    if not extract_data_map:
        print(f"Error: Failed to load extracted answer file '{args.extract_file}'. Program terminated.")
        return

    common_indices = set(gt_data_map.keys()) & set(extract_data_map.keys())
    if args.limit:
        common_indices = list(common_indices)[:args.limit]

    results = []
    total_score = 0.0
    total_binary_score = 0.0
    total_count = 0

    print(f"\n--- Starting Evaluation ({len(common_indices)} data entries) ---")
    for idx in tqdm(common_indices, desc="Evaluating", ncols=100):
        gt_item = gt_data_map[idx]
        ext_item = extract_data_map[idx]
        gt_answer = gt_item.get("AnswerCN", "")
        model_answer = ext_item.get("extracted_answer", "")
        question_type = gt_item.get("QuestionType", "")

        score, full_info = evaluate_answer_score_openai(model_answer, gt_answer, question_type)
        binary_score = 1.0 if score == 1.0 else 0.0
        total_score += score
        total_binary_score += binary_score
        total_count += 1
        print(f"  idx: {idx}, Score: {score:.4f}, Binary Score: {binary_score:.1f}")

        results.append({
            "idx": idx,
            "AnswerCN": gt_answer,
            "answer_model": model_answer,
            "acc": score,
            "acc_str": binary_score,
            "full_info": full_info
        })

    avg_score = total_score / total_count if total_count > 0 else 0.0
    avg_binary_score = total_binary_score / total_count if total_count > 0 else 0.0

    print(f"\n--- Evaluation Complete ---")
    print(f"Total Entries: {total_count}")
    print(f"Average Score: {avg_score:.5f}")
    print(f"Average Binary Score: {avg_binary_score:.5f}")

    try:
        with open(args.output_file, 'w', encoding='utf-8') as f_out:
            json.dump(results, f_out, ensure_ascii=False, indent=2)
        print(f"Results saved to: {args.output_file}")
    except Exception as e:
        print(f"Error saving results to JSON file: {e}")

if __name__ == "__main__":
    main()