import os
import json
import argparse
import time
from tqdm import tqdm
from openai import OpenAI

BASE_URL = ""
API_KEY = ""
processing_timeout = 10

def extract_boxed_content(text):
    results = []
    i = 0
    while i < len(text):
        start = text.find(r'\boxed{', i)
        if start == -1:
            break
        brace_start = start + len(r'\boxed{') - 1
        stack = 0
        end = brace_start
        for j in range(brace_start, len(text)):
            if text[j] == '{':
                stack += 1
            elif text[j] == '}':
                stack -= 1
                if stack == 0:
                    end = j
                    break
        if stack == 0:
            content = text[brace_start+1:end].strip()
            results.append(content)
            i = end + 1
        else:
            i = brace_start + 1
    return results

def create_test_prompt(demo_prompt, response, inst):
    demo_prompt = demo_prompt.strip()
    test_prompt = f"Model's answer is: \n'{response}'\nPlease extract the final answer from the model's response according to the above requirements, and return only a string without any other content."
    full_prompt = f"{demo_prompt}\n\n{test_prompt}"
    return full_prompt

def api_call_simple(base_url, api_key, messages, timeout=8):
    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )
        completion = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0
        )
        return completion
    except Exception:
        return None

def extract_answer(response, inst):
    try:
        boxed_contents = extract_boxed_content(response)
        if boxed_contents:
            extracted = "; ".join(boxed_contents)
            return extracted

        demo_prompt = """You are a professional answer extraction expert. Please extract the final answer from the following text as accurately as possible, strictly following the priority strategy below:

Priority 1: Look for explicit answer keywords
- Search for the following keywords:
  * "final answer", "answer", "result"
  * "the answer is", "the result is"
  * Summary words such as "therefore", "so", "in conclusion" followed by the answer content
- Extract the content that immediately follows these keywords

Priority 2: Extract from the end of the text
- If no explicit answer is found in the previous step, try to extract the most likely answer from the last paragraph or last sentence of the text

Important Requirements:
1. Multiple answers should be separated by semicolons (;)
2. Return only the answer content itself, without extra explanations or formatting
3. If the answer cannot be determined, return null

Strictly follow the above priority order for extraction."""

        full_prompt = create_test_prompt(demo_prompt, response, inst)
        completion = api_call_simple(
            BASE_URL,
            API_KEY,
            [{"role": "user", "content": full_prompt}],
            timeout=8
        )
        if completion is None:
            return ""
        extraction = completion.choices[0].message.content.strip()
        return extraction
    except Exception:
        return ""

def process_single_item_simple(item, i):
    try:
        if 'raw_output' not in item:
            return ""
        raw_output = item.get('raw_output', '')
        if not raw_output:
            return ""
        answer = extract_answer(raw_output, item)
        return answer
    except Exception:
        return ""

def process_json_file(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read JSON file: {e}")
        return

    for i, item in enumerate(tqdm(data, desc="Processing progress")):
        answer = process_single_item_simple(item, i)
        item['extracted_answer'] = answer
        time.sleep(0.1)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Processing completed, results saved to {output_file}")
    except Exception as e:
        print(f"Failed to save final results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Extract answers from raw_output field in JSON file')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')
    parser.add_argument('--timeout', type=int, default=10, help='Processing timeout per item (seconds)')
    args = parser.parse_args()

    global processing_timeout
    processing_timeout = args.timeout

    process_json_file(args.input, args.output)

if __name__ == "__main__":
    main()