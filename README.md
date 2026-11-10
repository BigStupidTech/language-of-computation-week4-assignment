# Week 4 Assignment

This is my Module 4 assignment for MSAI-5523.

My partners are Ricky Wooten and John Dries.

## Tests and imports on my Windows computer

Open Start, type PowerShell, and open Windows PowerShell. Administrator mode is not needed. Go to this folder:

```powershell
cd "C:\Users\Admin\workspace\language-of-computation\week4-assignment"
```

Create a separate Python environment and install the team's pytest version. No activation command is needed:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --timeout 300 --retries 10 -r requirements-dev.txt
```

The tests were written independently from our shared rules.md. Each test uses a temporary folder and test.db, with cleanup after success or failure. The harness redirects the old script's hardcoded database filename without changing the script. It also checks that the real CSVs, rules, script, database and log did not change. The deterministic test compares book data, excluding internal IDs and run-history timestamps, rather than comparing raw SQLite bytes.

### Part 3: my first test run

Before changing ingest.py, run this myself and save the output:

```powershell
.\.venv\Scripts\python.exe -m pytest -v --tb=short 2>&1 | Tee-Object -FilePath test-results-before.txt
```

Wait until the final summary appears. Failures are expected because this is still my Module 3 script. My test count and failure count do not have to match a classmate's independently written suite. Do not repeat this command after fixing the script: that would replace the before-results file.

Then have the code updated to match the unchanged rules and tests. If an unresolved rule is found, discuss it with the team and update everyone's rules together. The brief harness checks done while preparing the tests are not my saved before run.

### Part 4: after the code is fixed

Run the tests myself again:

```powershell
.\.venv\Scripts\python.exe -m pytest -v --tb=short 2>&1 | Tee-Object -FilePath test-results.txt
```

Only after every test passes, remove the old week4 output files if present. These commands refer only to the current week4 folder:

```powershell
if (Test-Path -LiteralPath .\books.db) { Remove-Item -LiteralPath .\books.db }
if (Test-Path -LiteralPath .\ingestion-log.json) { Remove-Item -LiteralPath .\ingestion-log.json }
```

Run these three imports myself, one at a time, in this order:

```powershell
.\.venv\Scripts\python.exe ingest.py books.csv
.\.venv\Scripts\python.exe ingest.py books.csv
.\.venv\Scripts\python.exe ingest.py books-batch2.csv
```

Open the report:

```powershell
Start-Process .\report.html
```

Click Open ingestion-log.json and select the file in this week4 folder. Check all three runs, including rejections and warnings. The second run should not create duplicate books.

### Comparing with my two partners

After my final database is ready, compare separately with Ricky Wooten and John Dries. Save their databases as partner-1/books.db and partner-2/books.db, and the reports as comparison-1.md and comparison-2.md. First inspect the database columns and agree on their mapping, including which load-time fields to exclude. Each report needs a Why our data differs section. Share rules and final databases, not our independently written tests or ingestion code as development material.

Commit and push only when requested. Use the assignment branch, not main.

## If I am using Command Prompt instead of PowerShell

A prompt like `C:\Users\Admin\workspace\language-of-computation\week4-assignment>` is Command Prompt. `Tee-Object` does not work there. Use these commands instead. Output is saved to the file, so wait until the prompt returns before displaying it.

My before run has already been saved. For reference, the command used was:

```bat
.\.venv\Scripts\python.exe -m pytest -v --tb=short > test-results-before.txt 2>&1
type test-results-before.txt
```

Do not run that before command again after changing the code. Keep it as the original evidence.

Now run the fixed code's tests myself and save the final result:

```bat
cd /d C:\Users\Admin\workspace\language-of-computation\week4-assignment
.\.venv\Scripts\python.exe -m pytest -v --tb=short > test-results.txt 2>&1
type test-results.txt
```

Only after every test passes, start fresh in this week4 folder and run the three imports:

```bat
if exist books.db del books.db
if exist ingestion-log.json del ingestion-log.json
.\.venv\Scripts\python.exe ingest.py books.csv
.\.venv\Scripts\python.exe ingest.py books.csv
.\.venv\Scripts\python.exe ingest.py books-batch2.csv
start "" report.html
```

Choose ingestion-log.json in the report. The tests run by the coding assistant during development are separate from these personal saved runs.
