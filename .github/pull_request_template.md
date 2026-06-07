<!--
Rx Entry Simulator — pull request template.
Fill in every section; keep it concise. You may delete these HTML comments.
Before requesting review, run `python run_checks.py` and confirm it exits 0.
See "Verifying changes" in README.md and the guidance in AGENTS.md / CLAUDE.md.
-->

## 1. Summary

<!-- One or two sentences: what this PR does and why. -->

## 2. What changed

<!-- Bullet the concrete changes (files, functions, behavior). -->

-

## 3. What did not change / protected areas

<!-- Call out what you deliberately left alone. Check the ones that hold true. -->

- [ ] No change to scoring / field-validation logic (`checker.py`)
- [ ] No change to prescription **case data** or **scenario data** (`cases.py`, `SCENARIOS` in `app.py`)
- [ ] No change to the Streamlit app flow / UI
- Other notes:

## 4. Verification commands run

<!-- Paste the exact commands and their results, e.g. "Ran 26 tests ... OK (exit 0)". -->

```
python run_checks.py
```

## 5. Product review / screenshots (if UI changed)

<!-- If the UI changed: attach before/after screenshots OR describe the visual difference
     against AGENTS.md design tokens. If nothing visual changed, write "No UI change." -->

## 6. Risk level

<!-- Low / Medium / High, plus one line of justification. -->

## 7. Rollback plan

<!-- How to revert safely if needed (usually: revert this PR's merge commit; note any
     data/migration considerations, or "none"). -->

## 8. Checklist before merge

- [ ] I ran `python run_checks.py` and it exited `0` (all tests pass).
- [ ] **Did checker / scoring logic change?** If yes, explain why:
- [ ] **Did case data or scenario data change?** If yes, explain why:
- [ ] **Did the UI change?** If yes, before/after screenshots or a visual-diff description are in section 5.
- [ ] I preserved the existing Streamlit app flow (the three sections; the seven entry
      fields and their order; Check Entry → Try Again → Next Case / See Example).
- [ ] I did **not** rewrite history or force-push.
- [ ] I did **not** add AI co-author trailers (unless intentionally wanted).
- [ ] Changes follow the design + architecture guidance in `AGENTS.md` / `CLAUDE.md`.
