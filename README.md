# Hint pilot v2 (MentalAize)

Does explaining why beat a bare rule when a model is told how to treat hints?
A small prompting pilot on one local model. See PLAN.md for the frozen design.

Standard-library Python 3 only. Needs LM Studio's local server on port 1234 with
nvidia/nemotron-3-super loaded.

    python3 make_questions.py fetch              # draw 200 MMLU test questions (once)
    python3 run_pilot.py --batch 0 --phase smoke # 3 spare questions, all five runs
    python3 run_pilot.py --batch 1 --phase screen
    python3 make_questions.py select --batch 1
    python3 run_pilot.py --batch 1 --phase main
    python3 analyze.py --batch 1                 # results table -> runs/results_batch1.md

Batch 2 is the same with `--batch 2`; `python3 analyze.py --batch 1 2` pools both.
Every reply is saved whole in runs/batchN/calls.jsonl. A stopped run resumes.

MMLU: Hendrycks et al., 2021. Questions are fetched from the Hugging Face dataset cais/mmlu.
