# 608 Sparta Project — Academy & Talent Data Pipeline

This repo pulls Sparta's Academy and Talent data out of S3, cleans it, and pushes
the cleaned results to a second S3 bucket — automatically, every night, via
GitHub Actions.

It's part of a larger group project split across three teams (Storage,
Transformation, Visualisation). This repo covers **Extract, Transform, and
Load**, owned by the Transformation team.

## Pipeline stages

```
Raw S3 bucket → extract → transform (clean) → load → Cleaned S3 bucket
(data608-final-project-...)                          (data-608-clean-data)
```

1. **Extract** (`src/extract/s3_reader.py`) — pulls raw files from S3 and
   saves them locally as `raw_*.csv`.
2. **Transform** (`src/transform/*.py`) — one script per data source, each
   reads a `raw_*.csv`, cleans it, and writes a `cleaned_*.csv` /
   `clean_*.csv`.
3. **Load** (`src/load/*.py`) — uploads the cleaned CSVs to the clean-data
   S3 bucket, ready for the Storage team to pick up.

All of this runs automatically overnight via
[`.github/workflows/nightly_pipeline.yml`](.github/workflows/nightly_pipeline.yml).

## Repo structure

```
src/
  extract/
    s3_reader.py          - pulls raw data from S3 (see "Extract" below)
  transform/
    clean_academy.py            - cleans Academy weekly scores
    clean_talent_json.py        - cleans Talent JSON profiles (coding self-scores etc.)
    clean_talent_csv.py         - cleans Talent application CSVs (name/grade standardisation)
    talent_txt_clean.py         - parses Sparta Day .txt assessment files
  load/
    Pierce-data_uplaod.py       - uploads cleaned CSVs to the clean-data S3 bucket (used by the workflow)
    upload_data.py              - uisng boto3 to upload to S3
  validation/
    academy_validate.py, validate_academy.py, validate_talent.py
                                 - standalone validation checks (not yet wired into the automated pipeline)
  match/                        - placeholder for a future matching stage (not yet implemented)
  Audit.py                      - one-off script to inspect what's actually in the raw S3 bucket

.github/workflows/nightly_pipeline.yml   - the scheduled pipeline (see below)
requirements.txt                         - Python dependencies
.env                                     - local AWS credentials (gitignored, never committed)
files_seen.txt                           - bookmark file, see "Incremental loading" below
```

## Extract: `src/extract/s3_reader.py`

Reads from the raw bucket (`BUCKET` constant at the top of the file) and
handles four file types, one loader function each:

| Function | Reads | Feeds into |
|---|---|---|
| `load_all_academy_data` | `Academy/*.csv` | `clean_academy.py` |
| `load_all_talent_data` | `Talent/*.json` | `clean_talent_json.py` |
| `load_all_applicant_talent_data` | `Talent/*Applicants.csv` | `clean_talent_csv.py` |
| `load_all_sparta_day_data` | `Talent/*.txt` | `talent_txt_clean.py` |

**Incremental loading**: every S3 key that's successfully processed gets
appended to `files_seen.txt`. Each loader filters the file list against
this before downloading anything, so subsequent runs only pull *new*
files instead of re-downloading everything every night. New rows get
*appended* to the local `raw_*.csv` files (not overwritten), so the raw
data accumulates over time rather than resetting each run.

**Error handling**: each loader runs its downloads through
`_run_with_error_handling`, which uses a thread pool but catches
per-file exceptions instead of letting one bad file kill the whole
batch. Only files that succeed get bookmarked in `files_seen.txt` — a
file that errors stays un-bookmarked so it's automatically retried on
the next run.

## Transform: `src/transform/*.py`

Four independent scripts, one per data source. Each follows the same
shape: read a `raw_*.csv`, run it through a small pipeline of cleaning
functions, write out a `cleaned_*.csv` / `clean_*.csv`, and — as of the
error-handling work — wrap the whole `__main__` body in `try`/`except`
so a failure prints a clear message and exits with a specific non-zero
code instead of crashing with a raw traceback:

| Script | Exit code on failure |
|---|---|
| `clean_academy.py` | 1 |
| `clean_talent_json.py` | 2 |
| `clean_talent_csv.py` | 3 |
| `talent_txt_clean.py` | 4 |

In the GitHub Actions workflow, each of these runs as its own step with
`continue-on-error: true`, so one script failing does **not** stop the
others from running. Each step's outcome is written to a "Cleaning step
results" table in the run's summary tab, and a final step at the very
end of the job checks all four outcomes — if any of them failed, the
overall run is marked as failed (red ✗) even though every step still
got a chance to run. So a green run genuinely means every cleaning
script succeeded; a red one means check the summary table to see which
one didn't, without that failure having blocked the others.

## Load: `src/load/Pierce-data_uplaod.py`

Uploads whichever cleaned CSVs exist locally to the `data-608-clean-data`
S3 bucket, under a `data/` prefix. Skips any file that isn't present
locally and keeps going if one individual upload fails, rather than
stopping the whole batch.

## The nightly workflow

[`.github/workflows/nightly_pipeline.yml`](.github/workflows/nightly_pipeline.yml)
runs on a schedule (`cron: '0 20 * * *'` — 20:00 UTC daily) and can also
be triggered manually from the **Actions** tab (**"Run workflow"**
button — use this, not "Re-run failed jobs" on an old run, which
replays the old commit instead of picking up new changes).

Steps, in order:

1. Check out the repo, set up Python, `pip install -r requirements.txt`
2. Run the extract step (needs AWS secrets — see below)
3. Run each of the four transform scripts as its own step
   (`continue-on-error: true`)
4. Upload cleaned data to S3 (needs AWS secrets)
5. Commit and push any new/updated local data files (`raw_*.csv`,
   `cleaned_*.csv`, `files_seen.txt`) back to the repo, so there's a
   local history of what's been processed

**Required repo secrets** (Settings → Secrets and variables → Actions):
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

**Required repo setting**: the workflow needs write access to push its
own commits back, which the job requests via a `permissions: contents:
write` block — if pushes ever start failing with a 403, check
Settings → Actions → General → Workflow permissions is set to allow
this.

## Running it locally

```bash
pip install -r requirements.txt
```

Create a `.env` file (gitignored, never commit this) in the project
root with:

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-central-1
```

Then run each stage from the **project root** (not from inside `src/`),
using `-m` so Python can resolve the `src.` package imports correctly:

```bash
python3 -m src.extract.s3_reader
python3 src/transform/clean_academy.py
python3 src/transform/clean_talent_json.py
python3 src/transform/clean_talent_csv.py
python3 src/transform/talent_txt_clean.py
python3 "src/load/Pierce-data_uplaod.py"
```

## Known gaps

- **Two upload scripts exist** in `src/load/` — `Pierce-data_uplaod.py`
  (used by the workflow, uploads all four cleaned files) and
  `upload_data.py` (older, mostly commented out, only handles Sparta Day
  data, not currently used anywhere).
- **Validation (`src/validation/`) and matching (`src/match/`) aren't
  wired into the automated pipeline yet** — they exist as standalone
  scripts you run manually.
