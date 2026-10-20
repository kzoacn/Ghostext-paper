# Full-support integration and budget-recovery scheduling review

This is a focused independent review of the integrated full-support corollary and the operational recovery of Qwen budget shard 5 of 6. I made no model calls, scientific-source edits, changes to retained observations, or overall recommendation change. The operational snapshot below was captured at 2026-10-20 23:32:17 UTC, while further scheduled cases were still running.

## Manuscript consistency

The corollary in `paper/sections/04-stopping-security.tex`, the first subsection of `paper/sections/17-proofs.tex`, and the corresponding introduction and limitation statements agree with the previously reviewed proof. The assumptions are a fixed finite alphabet of at least two tokens, a time-homogeneous finite-order kernel, and positive probability for every token from every context. The kernel and context order remain fixed as the payload grows.

The context-chain proof handles a memoryless source by its one-symbol-context representation, so it does not incorrectly replace symbol rewards with the transition reward of a one-state chain. Irreducibility and aperiodicity follow from the full context graph. The Poisson-equation signs and martingale decomposition are correct. Its bounded endpoint contribution changes variance by only `o(n)`, including from a fixed initial context. Zero asymptotic variance makes every allowed-edge square vanish; normalization over the `d`-step continuations then forces the potential to be constant and all token probabilities to be `1/V`. The structural zeros of the lifted context matrix are correctly distinguished from missing token support.

The introduction and limitations retain the asymptotic fixed-source scope. The ideal fixed-window softmax example is explicitly conditional on the distribution depending only on that window, and supplies neither a practical neural-model constant nor a transfer to masked, rounded, or stateful software. The existing restricted-support negative control is not presented as a counterexample to this corollary. The added Kontoyiannis 1998 reference has the title, journal, volume, issue, pages, DOI, and primary author-hosted URL previously checked in the separate corollary review. I found no mathematical or citation mismatch in this integration.

Reviewed manuscript SHA-256 values:

| File | SHA-256 |
|---|---|
| `04-stopping-security.tex` | `2661107f5f4db78810de7f07ad54c868bf7e7ed94108d3650864380badc0526d` |
| `17-proofs.tex` | `52730c583f51c54336fa73e3bc9eda6bd6cf97e86d3e6b524604c657128659f2` |
| `01-introduction.tex` | `62ff7fb53f615a71d2dd58327b9f495522186ad52e809ff724cf79b549c6c6c9` |
| `13-limitations-and-conclusion.tex` | `dacf31dd2e9074ed085e12d91cbd9e6b08e0f089163924a2c163a397df12d21b` |
| `refs.bib` | `537660714988c2eb71509a5799b73cb9ccbb2fd50cc81cff47aaf85960afc44d` |

## Actual recovery records

The recovery schedule has SHA-256 `322f786dacb3a5ab15879e93ce2a74a422d189dc5563816aa51e4e165e1706ac`. Its manifest link matches `89714e4b55d10234036048fb3b2c55f2480c135e5435c58d7183bc8a4aba22f2`, and all nine current scientific dependency hashes still match that manifest. I rechecked all 53 preserved-file hashes in `interruptions/worker-5-01.json`, all ten saved-case assembly input hashes, and the assembled output hash. None changed.

The original shard consists of exactly 26 manifest indices congruent to 5 modulo 6. The interruption's five saved final cases plus its subsequently assembled failed-write case account for exactly indices `{5,11,17,23,29,35}`. The schedule contains every remaining index exactly once, with no extra task. Its 20 tasks are ordered by descending preassigned `reference_N`, then original manifest index. Every entry has the original case identity and `reference_N`, and its new shard selector is `index / 160`. Since the manifest has 160 tasks, each such invocation selects exactly that original task. The live original shards 0 through 4 cannot select any of them.

The 13 captured launch records cover exactly the first 13 scheduled entries without repetition. Each command, shard pair, task identity, reference length, CPU declaration, schedule hash, source map, and manifest hash agrees. Their event journals begin after their respective launch records and after the schedule; there is one budget-stream begin per captured task, with the declared CPU affinity. The six preserved original tasks' journals precede the schedule. The other scheduled tasks have no event preceding the schedule. This supports the claimed partition between retained work and previously unstarted work in the inspected records.

Three captured launches use completed-single-task vacancy evidence: `95 -> 149`, `53 -> 101`, and `47 -> 137`. Each referenced launch and final case has the stated hash. The earlier final case has the correct manifest and task identity and contains completed generations; its recorded receiver work predates the later launch. None of those launch records asserts an exit code. Other captured launches record a tool session and an observed zero exit code; I checked the consistency and uniqueness of those declarations, not an independent external attestation of the tool observation.

A persisted final case establishes that the assigned generation and receiver work finished. It does not establish process exit or release of model memory. The no-exit-code wording is therefore accurate. The value seven is the recorded scheduling limit; this review does not infer an independently measured maximum number of resident model processes. The frozen runner performs no further assigned inference after saving a single selected task's final case; it prints its result and leaves the loop.

Two pairs dispatched together have opposite JSON-creation timestamp order to their queue order by 0.000200 and 0.000169 seconds. This is consistent with concurrent dispatch of the next pair and does not change the assigned task set. A verifier should not demand strict descending-`N` timestamps within such a dispatch wave.

The inspected launcher, `tmp/launch_budget_recovery.py`, has SHA-256 `4a19c4a566e658ecee71e624cb979f591e1ef512e4c60e0c6684a3ab2ee9af52`. It checks membership, absence of existing work for its new task, source hashes, and the chosen vacancy branch, then records the unchanged runner command before executing it. I did not execute the launcher. It is presently outside the builder's exported `scripts/*.py` set. The recorded commands reconstruct the scientific invocations; if the artifact is intended to preserve the launcher's own prelaunch-check provenance, that helper needs a separate retained source pin.

## Artifact-verifier gap requiring correction

At the reviewed verifier hash `db2bb5af8c5a3de41f33d94aa4dab33fde9b294d3a1916b684ae92ef5149df83`, the generic launch checks bind the manifest, source dictionary, task case ID, and arithmetic shard selection. They do not validate the recovery schedule or the new vacancy dependencies.

I imported the actual `verify_new_profile` function and called it on an isolated partial profile under `/tmp`. The unmodified baseline passed. It also accepted each of these separately malformed fixtures:

- A wrong schedule hash, or a schedule with one assigned task removed.
- A wrong vacated-case hash or wrong vacated-launch hash.
- A duplicate launch record assigning the same task again.
- A wrong launch `reference_N`, a command using a different shard index, or a maximum-worker declaration of 99.
- An added zero-exit-code assertion on a record whose vacancy evidence explicitly says that no exit code is asserted.

These checks used draft mode to avoid representing the live incomplete cohort as final. The missing dependency checks are also absent from the non-draft branch; a final file index would protect the resulting bytes without establishing their operational semantics. This is a verification-coverage defect, not evidence that the inspected live scientific observations were changed.

Before final export, validate the schedule's original-shard complement and entry bindings, every recovery launch's schedule/command/worker links, uniqueness, and mutually exclusive vacancy evidence. The completed-task branch must bind the earlier single-task launch and final case, check chronology and task identity, and retain the absence of an asserted exit code. The session branch must require its explicit observed-exit declaration while distinguishing that declaration from an independent process audit. Final mode should require the complete scheduled launch/task set; draft mode may permit a valid partial set. Reusing a vacancy evidence identifier should fail. Preserve interruption and assembly receipts and recheck the new links after export hash reconnection.

The independent audit harness is `/tmp/review_budget_recovery_schedule.py`; its captured records and result are in `/tmp/reviewer-budget-schedule-j7r39olf/AUDIT-SUMMARY.json`. I notified the parent of the concrete gap. The correction and its subsequent verification are recorded below.

## Verifier correction and completed recovery check

The parent added `verify_recovery_schedule` and addressed the follow-up omissions identified during its review. The final reviewed verifier has SHA-256 `74033d56af0f93fbf8a03a3b35e7371b03a6bed315ff3660ceac534d7b80085b`. It requires a schedule for every budget launch, checks the precise task partition and queue order, and binds every launch's record kind, manifest, sources, schedule, task, reference length, worker limit, CPU, and complete recorded command. Both the cohort selector and model directory are checked. It enforces the distinct vacancy branches and their dependencies, rejects repeated task or vacancy assignments, and checks recovery-journal identities, timing, and stage uniqueness. A completed case requires a nonempty journal. Final mode requires all scheduled launches and final cases.

I reran the actual verifier in a temporary copy containing 353 real files, 32 budget cases, and all 20 launch records. The baseline and live draft-profile checks passed. All 20 malformed fixtures failed: the nine originally reported mutations, changed cohort/model commands, absent schedule bindings including an otherwise hidden duplicate, wrong record kind, contradictory or self-referential vacancy branches, reused vacancy evidence, missing completed-case journals, duplicate stage records, and an event predating its launch. The check results are retained in `/tmp/reviewer-budget-verifier-02c_l13r/AUDIT-SUMMARY.json`.

At 23:37:20 UTC all 20 scheduled recovery cases were present. I independently reran the actual-record checks, including the original 53 preserved-file hashes, ten assembly inputs, nine scientific source hashes, task complement, all launch commands, and the three completed-task vacancy chains. Every recovery journal contained 14 unique expected records. The complete-record snapshot is `/tmp/reviewer-budget-recovery-complete-records.json`. This establishes completion of the rescheduled population; it does not by itself establish completion or analysis of the other original shards.

I then exercised the actual export sanitizer and hash-reconnection functions on the 353-file recovery closure, totaling 9,185,591 input bytes. The graph converged in four passes, changing 57 metadata or hash-dependent files and preserving the scientific fields. The transformed partial profile passed, and the transformed complete 20-task recovery schedule passed its non-draft check. All three completed-task vacancy chains remained valid after redaction. Separate missing-final-case and missing-final-launch mutations were rejected by the final schedule check. This is a component check of the recovery dependencies, not a claim that the partial copy is a complete anonymous artifact. Its result is `/tmp/reviewer-budget-recovery-export-4k4l4qc1/AUDIT-SUMMARY.json`.

No blocker remains in the reviewed corollary integration, inspected recovery records, or corrected recovery-provenance verification. The parent accepts the distinction between the recorded seven-worker scheduling limit and an independently measured resident-process count, and does not claim that the temporary launcher is included in the artifact. The complete cohort analyses, refreshed source capture, and whole final archive still require their own validation. No scientific runner, frozen plan, retained inference result, or overall recommendation was changed by this review.
