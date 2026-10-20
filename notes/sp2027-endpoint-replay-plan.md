# Post-hoc public endpoint replay

This diagnostic was specified on 2026-10-21, after observing the old delivery
cohort and deriving the public-stopping identity, and before replaying its
endpoint outcomes. It is retrospective, not a new confirmatory model study.

Use every previously primary-eligible complete, canonical, length-matched
guard-128 delivery pair in the two original repair cohorts. Preserve the old
interrupted-case exclusion. This selects 13 GPT-2 pairs and 37 Qwen pairs.
Do not change the selection using replay results. The source manifest lists
the disposition of every original record.

The observer knows the prompt, public source configuration, guard size, and
the chosen plaintext length of 16 bytes. Fixed framing therefore gives two
segments of 60 and 44 bytes. The detector takes visible text, retokenizes it,
and replays the original model, candidate source, and integer interval updates
from byte-exact saved sources. It uses no password, payload value, decrypted
header, saved token IDs, or delivery label. Saved IDs are compared only after
the decision to check replay fidelity. There is no tail in this cohort.

The positive event is first resolution of the second segment exactly at the
visible endpoint. Earlier resolution, unfinished resolution, and invalid
replay are distinct outcomes. This is a prefix-resolution support test; it
does not mirror all encoder abort predicates. Store the selected integer CDF
boundaries at every inspected token so a separate arithmetic-only analysis
can reproduce the decision without loading a model or calling the decoder.

Report all selected pairs and replay failures. TPR one, if confirmed, is the
structural property of delivered no-tail texts and not a discovery of an
unknown-general-purpose detector. Natural FPR is conditional on the original
eligibility slice. Give a prompt-family cluster interval and retain the full
per-pair table. Do not infer a deployment-wide low-FPR claim from this small
post-hoc sample or infer uniform authenticated packet bytes.
