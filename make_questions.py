#!/usr/bin/env python3
"""Hint pilot: draw MMLU questions (fetch) and choose hinted questions per batch (select).

Standard library only.
  python3 make_questions.py fetch            -> data/pool.jsonl
  python3 make_questions.py select --batch 1 -> data/batch1_items.jsonl
"""
import argparse, json, os, random, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261122
MMLU_TEST_ROWS = 14042  # four-option questions in the MMLU test split (cais/mmlu, config "all")
POOL_SIZE = 200
ROWS_API = ("https://datasets-server.huggingface.co/rows?dataset=cais%2Fmmlu"
            "&config=all&split=test&offset={i}&length=100")
BLOCKS = 30  # the rows API is rate limited, so fetch 30 random 100-row blocks, then sample
LETTERS = "ABCD"


def fetch_block(i):
    for attempt in range(12):
        try:
            with urllib.request.urlopen(ROWS_API.format(i=i), timeout=60) as r:
                return [(x["row_idx"], x["row"]) for x in json.load(r)["rows"]]
        except Exception as e:  # rate limit or network hiccup: wait and retry
            err = e
            print(f"block {i}: {e!r}; waiting 20s", flush=True)
            time.sleep(20)
    raise RuntimeError(f"block {i} failed: {err}")


def cmd_fetch(args):
    out = os.path.join(HERE, "data", "pool.jsonl")
    if os.path.exists(out):
        sys.exit("data/pool.jsonl already exists; not overwriting")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rng = random.Random(SEED)
    starts = rng.sample(range(MMLU_TEST_ROWS - 100), BLOCKS)
    seen = {}
    for n, s in enumerate(starts):
        for idx, row in fetch_block(s):
            if len(row["choices"]) == 4:
                seen[idx] = row
        print(f"block {n + 1}/{BLOCKS} ok, {len(seen)} rows", flush=True)
        time.sleep(1.5)
    rows = []
    for pos, i in enumerate(rng.sample(sorted(seen), POOL_SIZE)):
        row = seen[i]
        rows.append({"qid": i, "subject": row["subject"], "question": row["question"],
                     "choices": row["choices"], "answer": LETTERS[int(row["answer"])],
                     "pool_pos": pos})
    with open(out, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} questions, {len({r['subject'] for r in rows})} subjects -> {out}")


def cmd_select(args):
    b = args.batch
    pool = {}
    for line in open(os.path.join(HERE, "data", "pool.jsonl")):
        q = json.loads(line)
        pool[q["qid"]] = q
    out = os.path.join(HERE, "data", f"batch{b}_items.jsonl")
    if os.path.exists(out):
        sys.exit(f"{out} already exists; not overwriting")
    screen = {}
    for line in open(os.path.join(HERE, "runs", f"batch{b}", "calls.jsonl")):
        c = json.loads(line)
        if c["run"] == "nohint1" and c.get("status") == "ok":
            screen[c["qid"]] = c
    wrong = sorted(q for q, c in screen.items() if c["answer"] and c["answer"] != pool[q]["answer"])
    right = sorted(q for q, c in screen.items() if c["answer"] == pool[q]["answer"])
    rng = random.Random(SEED + b)
    rng.shuffle(wrong)
    rng.shuffle(right)
    n_correct = min(args.per_group, len(wrong))
    n_wrong = args.size - n_correct
    items = []
    for q in wrong[:n_correct]:  # model was wrong alone -> hint points to the correct answer
        items.append({"qid": q, "hint_type": "correct", "hint": pool[q]["answer"],
                      "screen_answer": screen[q]["answer"]})
    for q in right[:n_wrong]:    # model was right alone -> hint points to a wrong answer
        hint = rng.choice([l for l in LETTERS if l != pool[q]["answer"]])
        items.append({"qid": q, "hint_type": "wrong", "hint": hint,
                      "screen_answer": screen[q]["answer"]})
    with open(out, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    unread = len(screen) - len(wrong) - len(right)
    print(f"screen: {len(screen)} answered, {len(right)} right, {len(wrong)} wrong, {unread} unreadable")
    print(f"chosen: {n_correct} correct-hint + {len(items) - n_correct} wrong-hint -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    s = sub.add_parser("select")
    s.add_argument("--batch", type=int, required=True)
    s.add_argument("--size", type=int, default=20)
    s.add_argument("--per-group", type=int, default=10)
    a = p.parse_args()
    {"fetch": cmd_fetch, "select": cmd_select}[a.cmd](a)
