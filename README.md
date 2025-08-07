# MathReal

While Multimodal Large Language Models (MLLMs) have demonstrated remarkable capabilities in visual mathematical reasoning across various existing benchmarks, these benchmarks predominantly rely on clean or processed multimodal inputs, lacking the authentic complexity of real-world educational scenarios. To address this critical gap, we introduce **MathReal**, a meticulously curated dataset comprising 2,000 mathematical questions with images captured by handheld mobile devices in authentic Kindergarten through 12th grade (K–12) educational contexts. 

Unlike existing datasets, MathReal captures the true challenges that MLLMs face in realistic educational environments, where images suffer from quality degradation, perspective variations, and content interference. Through systematic classification and comprehensive evaluation across six experimental settings, MathReal reveals that the problem-solving abilities of state-of-the-art MLLMs are significantly challenged in authentic educational scenarios, providing crucial insights for future model improvements.

## Dataset Overview

MathReal provides mathematical problems across five key categories:
- **Plane Geometry (PG)**
- **Solid Geometry (SG)**
- **Logical Reasoning (LR)**
- **Function Graphs (FG)**
- **Statistical Charts (SC)**

## Dataset Structure

```
MathReal/
├── README.md
├── json/
│   └── testmini.json          # TestMini subset of MathReal dataset
├── img/
│   ├── clean/                 # Clean mathematical images (.png format)
│   └── real/                  # Real-world scenario images (.jpg format)
└── evaluate/                  # Evaluation pipeline scripts
    ├── extract_answer_1.py    # Step 1: Extract answers from model outputs
    ├── evaluation_answer_2.py # Step 2: Evaluate extracted answers
    └── calculate_answer_3.py  # Step 3: Calculate final scores
```

### Data Format

Each problem in `testmini.json` contains:
- `idx`: Unique identifier
- `ImgReal`: Path to real-world image (`.jpg`)
- `ImgClean`: Path to clean image (`.png`, may be null)
- `QuestionCN`/`QuestionEN`: Problem statement in Chinese/English
- `DescriptionCN`/`DescriptionEN`: Image description in Chinese/English
- `AnswerCN`/`AnswerEN`: Ground truth answer in Chinese/English
- `Category`: Problem category (PG, SG, LR, FG, SC)
- `Difficulty`: Problem difficulty level
- `EducationalStage`: Educational level (Primary, Middle, High.)
- `QuestionType`: Type of question (MultipleChoice, FillInTheBlankm, ConstructedResponse)
- Levels for image quality degradation, image perspective variation and

## Evaluation Pipeline

The evaluation process follows a three-step pipeline:

### Step 1: Extract Answers
```bash
python evaluate/extract_answer_1.py \
    --input <model_output.json> \
    --output <extracted_answers.json> \
    --timeout 10
```

**Purpose**: Extracts final answers from raw model outputs using OpenAI API

**Input**: JSON file containing model responses with `raw_output` field

**Output**: JSON file with extracted answers in `extracted_answer` field

### Step 2: Evaluate Answers
```bash
python evaluate/evaluation_answer_2.py \
    --gt_file <ground_truth.json> \
    --extract_file <extracted_answers.json> \
    --output_file <evaluation_results.json> 
```

**Purpose**: Compares extracted answers with ground truth using sophisticated evaluation criteria

**Features**:
- Mathematical equivalence checking (fractions vs decimals, algebraic expressions)
- Multi-part answer handling with partial credit
- Unit-aware comparison
- Multiple-choice question support

### Step 3: Calculate Final Scores
```bash
python evaluate/calculate_answer_3.py <evaluation_results.json>
```

**Purpose**: Computes category-wise and overall accuracy scores

**Output**: 
- Per-category accuracy (PG, SG, LR, FG, SC)
- Overall accuracy metrics
- Both strict and partial credit scoring

## Image Types

### Clean Images 
- **Format**: PNG
- **Description**: Clean, digitally rendered mathematical diagrams
- **Purpose**: Baseline evaluation without real-world visual challenges

### Real Images 
- **Format**: JPG  
- **Description**: Real-world mathematical problems captured in natural settings
- **Challenges**: Include blur, lighting variations, perspective distortions, and background interference
- **Purpose**: Evaluate model robustness under realistic conditions

## Real‑World Challenge Levels and Metrics

Each problem includes detailed real‑world challenges across three primary categories:

**Image Quality Degradation**:
- Blur
- Underexposure/overexposure
- Shadow coverage
- Glare

**Image Perspective Variation**:
- Rotation
- In-plane tilt
- Non-planar capture
- Background distortion

**Irrelevant Content Interference**:
- Handwritten questions
- Reverse side content
- Question marking
- Figure marking
- Handwritten answer for multiple-choice questions
- Handwritten process for constructed-response questions

## Requirements

- Python 3.7+
- OpenAI API access (for evaluation pipeline)
- Required packages: `openai`, `tqdm`, `json`, `argparse`
