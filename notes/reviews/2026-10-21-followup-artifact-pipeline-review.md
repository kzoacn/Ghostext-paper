# Independent review of the follow-up artifact pipeline

Review date: 2026-10-21. I reviewed the export, verification, source-capture, materialization, and command-index extensions for `upstream-observable-replay-v1`, `upstream-budget-curve-v1`, and the Qwen2.5 profiles against the frozen observable follow-up plan. I found no correctness or reproducibility blocker in the inspected implementation and bounded checks. This is not a complete-archive sign-off: the Qwen replay and budget cohorts remain unfinished, and the final checks correctly reject them. No model inference was performed, no live experiment files were modified, and no prior review or overall recommendation was changed.

## Source profiles, input closure, and commands

I checked the exact source objects and input hashes for nine relevant profiles: the original GPT-2 main cohort and two pilot versions, Qwen2.5 main and pilot, and both models' observable replay and budget follow-ups. Each follow-up profile stages nine pinned source files and 162 input files: the original cohort manifest, all 160 original case records, and the frozen follow-up plan. The recorded sources match the generation manifests. All 78 entries in the current-source map also match the working-tree bytes at review time.

The Qwen2.5 main and pilot profiles stage the explicit follow-up plan and the recorded model-download pin. Their model-file digest declarations agree with that pin, including weight digest `88c142557820ccad55bb59756bfcfcf891de9cc6202816bd346445188a0ed342` and revision `060db6499f32faf8b98477b0a26969ef7d8b9987`. The protocol index chooses `<QWEN25_DIRECTORY>`, passes `--backend qwen25`, and selects the explicit study-plan path; the pilot command additionally passes `--pilot`. This is distinct from the earlier GGUF backend. I checked the pin and profile linkage without rehashing model weights or loading a model.

The old GPT-2 profiles correctly use archived-plan aliases. The first pilot restores its earlier plan, while the main cohort and second pilot restore their recorded later version. Materialization writes the alias from its hash-checked archived source after staging the ordinary inputs. It does not silently substitute the current prose plan for an older experiment.

I materialized all nine profiles into separate temporary trees using the real materializer. Every source object, cached source copy, input file, and alias matched its expected hash. Each indexed entry point accepted all recorded command-line flags in an offline `--help` check. A populated destination was rejected without overwriting it. In a separate bounded copy containing these profiles, I ran the real source-capture and protocol-index scripts; all nine reconstructed profile records and command records exactly matched the retained indexes. The live indexes were not rewritten.

## Complete observations and cohort checks

I independently reconstructed the public task and binding maps from each full original cohort. Both models retain 480 arm pairs and 960 output observations from 160 secret instances. Deduplication yields 482 distinct public inputs for GPT-2 and 492 for Qwen2.5; it does not reduce binding multiplicity. The reconstructed tasks and bindings exactly match the frozen replay manifests. I separately reconstructed all 160 budget assignments per model from the verified endpoint or the prescribed failure fallback, and these match the budget manifests.

The completed GPT-2 replay and budget profiles pass the actual verifier. In an isolated transformed copy, the verifier rejected a missing case, a duplicate case identity, a stale manifest reference, a missing analysis, and a changed persisted prefix. The budget checks compare every recorded generation block with its saved prefix and each completed block's receiver with its saved receiver stage.

Both live Qwen follow-up profiles failed final profile verification when checked. The observed snapshot had 99 of 492 replay cases and 28 of 160 budget cases; these are audit-time counts, not final results. The actual builder's final preflight also rejected `sp2027-observable-qwen25` before constructing an export. I placed a mandatory guard immediately after preflight in the separate review process, so this check could not overwrite an artifact even if the preflight unexpectedly passed. Draft verification accepts the available records while retaining the distinction from a final complete artifact.

Final export must still be performed after the planned Qwen records and analyses exist, followed by the full artifact verifier. The present review does not turn partial case files into a completed cohort or establish their eventual model results.

## Anonymization and preservation of scientific data

I exercised the actual sanitization and hash-reconnection functions on a bounded set of 2,406 real files, totaling 76,416,489 input bytes. It included the complete GPT-2 public replay and budget data, both complete original cohorts as frozen inputs, eight already persisted Qwen replay cases and thirteen Qwen budget cases, the associated prefix and receiver files, relevant source objects and aliases, and the new budget interruption record. The budget subset began with eight cases; five more were included because the interruption's preserved-file list referenced them. This was a component-level export reconstruction in a temporary tree, not a replacement of the live anonymous archive.

The metadata dependency graph converged after five passes; 997 files changed because of metadata redaction or updates to references to changed file hashes. All protected observations remained equal. Separate comparisons covered 860,155 protected-field occurrences and 276,359 CDF-observation rows, including repeated copies embedded in case and prefix records. These are integrity-check counts, not additional experimental samples. Published strings, prompts, token sequences, CDF boundaries, Decimal mass strings, statuses, scores, and numeric measurements were preserved. Upstream provenance, model digest declarations, and pinned Python source digests also remained unchanged.

I verified the transformed manifests' input links, profile manifest hashes, staged input hashes, and case/analysis references against the transformed bytes. The actual verifier passed both complete transformed GPT-2 profiles and both deliberately partial transformed Qwen profiles in draft mode. Public-input identities still recompute from the unchanged `(prompt, B, text)` tuples. The fixed file names and old-plan aliases remain coherent with the updated metadata hashes.

A synthetic observation containing personal-looking text and a home-directory substring stayed byte-for-byte equal as a string value, while corresponding metadata was sanitized. The later identity check still detects that text, so the implementation fails closed instead of silently editing an observation. A separate changed-CDF fixture was detected by the scientific-field preservation comparison. I found no path in the inspected export transformation that silently changes a retained scientific text or CDF value in these records.

## New Qwen budget interruption

The generic interruption checks in `verify_new_profile` apply to `upstream-budget-curve-v1` as well as the other new schemas. I independently checked the manifest link and all 60 hashes in `sp2027-budget-qwen25/interruptions/worker-2-01.json`. For `c4_0203_b512_r2`, those preserved inputs include all four prefixes at lengths 110, 138, 165, and 220, and the completed receivers at 110 and 138. The unfinished receiver at 165 is not represented as a completed stage.

The record explicitly preserves exit code 143 with an unknown cause, shard 2 of 6, and the move from logical CPU 2 to 10 on the same host. I verified that all nine current source hashes still match the frozen budget manifest and ran the actual draft-profile verifier successfully with the new interruption record present. The transformed-copy verifier also checked its preserved-file references after anonymization. This verifies the retained bytes and provenance; it does not infer an unrecorded cause or certify unfinished future receiver work.

## Reviewed identifiers and conclusion

| File | SHA-256 |
|---|---|
| `build_anonymous_artifact.py` | `37e09758fcccea96fc1cef68544c4dfd645cbf11d23fcb48872b0f05a99a5e79` |
| `verify_artifact.py` | `35e79b071bb0b08ecc56fc07db12b717aa969e88df208bef1df03d7ee4cf6ae3` |
| `capture_source_snapshots.py` | `1a6483fb3687193f4357b359daeb19be261640f83e29f3c7e0e225247e3ff89b` |
| `materialize_profile.py` | `33c5dbbd6eee5d7f5c01b87e2a2bf1bc22bf714820254449d5782ad496bf5348` |
| `build_protocol_index.py` | `227303e8f8aa39bcc433731cec19e6a17c8cc10d10f3a9845abbb7ea7eea75a2` |
| Frozen follow-up plan | `776778d862924f1b12bf77bac16fb1f2a31d6868fc7c7da62ba7facf4ece71f2` |

The reviewed extensions preserve the inspected scientific records and reconstruct the required frozen execution inputs. The incomplete Qwen cohorts remain blocked from final export and final profile verification, as required. No implementation change is requested by this review; the complete final archive still needs its own validation after those cohorts finish.

## Bounded persistence-recovery addendum

I reviewed the new saved-case assembler, its receipt checks in the updated verifier, the reproduction instructions, and recovery of `c4_0203_b128_r3`. The interruption record reports exit 1 with `OSError: [Errno 12] Cannot allocate memory` at `handle.write(encoded)` while writing the final case, after its four prefixes and four receiver records were saved. It distinguishes that reported failure from an unestablished underlying resource cause. I verified all 53 preserved-file hashes. The formerly empty temporary file is now absent: its zero-byte state and empty-file digest are recorded provenance, not something I independently reobserved after assembly.

The assembler reads the frozen budget manifest, the original case, four prefixes at lengths 38, 48, 57, and 76, and their four receivers. It validates the saved prefix records and completed ID receiver/source-probability checks, then constructs the same final dictionary as the runner. It does not require `recovery_match=True`, alter receiver outcomes, draw protocol randomness, or call a model. Its imported assembly dependencies still match the nine frozen budget source hashes. This new helper is separately pinned by the receipt; it is not represented as an originally recorded generation dependency.

An independent construction from those ten saved inputs exactly matches the reconstructed case bytes and SHA-256 `eef1e1853989462b0ae902edd12245ed4fab43be69ad7fef9ee94aa99ca38408`. The helper's own construction matches too. I additionally checked eight existing GPT-2/Qwen budget cases byte-for-byte; I did not repeat the parent's reported 209-case pre-use comparison. All ten receipt input hashes, its output hash, and its helper-source hash match. The empty write therefore does not require discarding or regenerating the scientific observations.

I limited the export check to 61 files totaling 1,682,797 bytes. Metadata redaction and hash reconnection converged in five passes, preserved the scientific fields, and left a case that both independent assembly and the helper reproduced exactly from the redacted inputs. The updated draft verifier accepted the transformed receipt and interruption links. In that isolated copy it rejected corrupted output, source, and input hashes, as well as either receipt flag falsely claiming model inference or new randomness.

The newly reviewed assembler hash is `680f3489b088c8daee022502506e776fb0d8dbaccef7745302114a6d65f5a0a9`; the updated verifier hash is `db2bb5af8c5a3de41f33d94aa4dab33fde9b294d3a1916b684ae92ef5149df83`. The current-source map still reflected the preceding verifier version during this check. The parent confirmed that source capture and command indexes will be refreshed before the next artifact build; the live generation dependencies were unchanged.

No persistence-recovery correctness blocker was found. This addendum checks the saved-input assembly and its evidence, not future work on the pending shard or a complete final artifact. I made no model calls, runner or plan edits, inference-data changes, or recommendation change.
