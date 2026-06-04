# Check gates — issue_13636

**Overall (gating): pass**

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C4 fix verified: test red pre-fix, green post-fix | pass | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | C4-verify: green-with-fix=PASS / red-without-fix=PASS | yes |
| T3 runtime: gramps core unit suite (whole-suite baseline) | fail | ./engine/scripts/ubuntu/run-unit.sh | T3-unit | Generated XML report: /workspace/gramps-testbed-v2/test-results/TEST-gramps.gen.merge.test.merge_ref_test.SourceSourceCh | no |
| C5 causal adequacy | none | reviewer + human sign-off | — | — | no |
| T5 judgment | none | reviewer + human sign-off | — | — | no |
| Validation act | none | human at sign-off | — | — | no |
