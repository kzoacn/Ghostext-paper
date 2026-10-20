# Endpoint replay runtime correction

The first GPT-2 replay mistakenly used one CPU thread, whereas its generation
manifest specifies two. Replaying exactly the same visible tokens exposed
selected-frequency changes of one unit out of 4096 on some natural paths.
Several delivered texts consequently failed the intended endpoint property.
Those data are retained as a runtime-mismatch diagnostic. They do not measure
the same public source as the recorded delivery cohort.

The correction restores two threads, rejects a thread-count mismatch, and
replays the same 13 eligible pairs into a separate output directory. It does
not select new texts, change segment lengths, change the decision rule, or
change eligibility using outcomes. The natural-path selected masses are also
compared with their archived values after the text-only decision. Token-ID
agreement alone was insufficient to establish probability replay.

The Qwen replay already uses the original two-thread configuration. Its
selected masses can be checked against the original natural traces in the
independent analysis. CPU affinity is recorded in both cases; the relevant
numerical invariance is checked using the saved probabilities, not assumed
from model and source hashes alone.
