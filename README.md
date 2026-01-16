# DocQA Case Engine Ver 1.0

**DocQA Case** is a lightweight, data-driven QA automation framework designed to bridge the gap between manual testing and full automation. It leverages Python and SQLite to generate, validate, and report test scenarios based on business requirements.

Instead of manually writing thousands of test cases in spreadsheets, this engine automates the logic generation (BVA, Edge Cases, Dependency Checks) while keeping a "Human-in-the-Loop" for quality assurance.

## Key Features

* **Instant Auto-Generation:** Transforms a single User Story into dozens of robust test cases (Positive, Negative, Boundary Values) in milliseconds.
* **Quality Curator Interface:** An interactive CLI that allows QA Engineers to review, approve, or reject generated scenarios before they enter the database.
* **Risk-Based Reporting:** Generates professional HTML dashboards that prioritize Critical and High-risk features for stakeholders.
* **Centralized Data:** Uses SQLite for structured, queryable, and scalable test case management (replacing flat Excel files).

## Project Structure

```text
DocQACase/
│
├── data/                      # Database storage (auto-generated)
│   └── docQA_case.db
│
├── src/                       # Source Code
│   ├── requirements_data.py   # The "Source of Truth" (Decomposition Table)
│   ├── setup_db.py            # Database & Schema Initialization
│   ├── generator_engine.py    # Core Logic (BVA & Dependency Algorithms)
│   ├── curator_cli.py         # Interactive Review Interface
│   ├── view_case.py           # Quick Terminal Viewer
│   └── generate_html_report.py# HTML Report Generator
│
├── requirements.txt           # Project Dependencies
└── README.md                  # Documentation


```

## Installation & Setup
1. Prerequisites:
- Python 3.8 or higher.
- pip (Python Package Installer).
2. Clone/Download the Repository.
3. Install Dependencies:
Bash
pip install -r requirements.txt


## Usage Workflow
Follow these steps to run the full QA cycle:

Step 1: Initialize Data Warehouse
Sets up the SQLite database and creates the necessary tables (features, test_scenarios).
Bash
python src/setup_db.py

Step 2: Generate Test Scenarios
The engine reads requirements_data.py, applies testing logic (BVA/Flow), and injects data into the DB with a Pending status.
Bash
python src/generator_engine.py

Step 3: Curator Review (Human-in-the-Loop)
Launch the interactive CLI to review high-risk scenarios.
- A = Approve
- R = Reject
- S = Skip
Bash
python src/curator_cli.py

Step 4: Generate Report
Creates a visual HTML report (test_report.html) summarizing coverage, risks, and approval status.
Bash
python src/generate_html_report.py


## Core Logic Explained
The engine uses three specific logic handlers found in generator_engine.py:
1. Input Validation: Automatically creates Boundary Value Analysis tests (Min, Max, Min-1, Max+1) for fields like Credit Cards or SWIFT codes.
2. Dependency Logic: Generates "If-This-Then-That" scenarios for features like Discount Stacking or Legal Checkboxes.
3. Functional Flow: Validates integration paths (e.g., PayPal Redirection) and simulates system failures (Timeouts).
