# CCS 2026 Submission Requirements (Working Notes)

Source of truth:

- CFP page: `notes/policies/ccs2026_cfp.html`
- Template sample: `notes/policies/sample-ccs2026.tex`

This note summarizes submission-critical items for this repository workflow.

## 1. Format Constraints

- Must use ACM `sigconf` 2-column format.
- Main content limit: 12 pages.
- Bibliography, appendices, and supplementary material are excluded from the 12-page limit.
- Must not alter margins, font defaults, or whitespace behavior.
- Must retain ACM metadata blocks (CCS concepts, keywords, rights-management info placeholders in submission format).
- Non-conforming format can be desk-rejected.

## 2. Anonymization Constraints

- Submission must be properly anonymized.
- No author-identifying content in main text or appendices.
- Self-citation should be third-person.
- No deanonymizing links (including repositories/artifact pages with identifying traces).

## 3. Mandatory Appendices

Appendices must be after main content + bibliography.

- `Open Science` appendix is mandatory.
- `Ethical Considerations` appendix is mandatory when ethical concerns may exist; when in doubt, include it.
- If AI tools were used to generate/substantially rewrite content, include `Generative AI Usage` section after main content + bibliography (per CFP policy text).

## 4. Open Science Policy (Submission-Time)

- Must list artifacts needed to evaluate core contributions.
- Must provide anonymous artifact URL in both paper and HotCRP (if online artifacts exist).
- Must explain any unavailable artifacts and justify constraints.
- If no artifact is needed, state this explicitly in Open Science appendix.

## 5. Artifact Hosting Constraints

- Prefer anonymous hosting services suitable for double-blind review.
- Avoid self-managed/modifiable hosting that can deanonymize reviewers or allow post-deadline changes.
- Artifact contents should remain fixed after the artifact deadline.

## 6. Writing Policy Implications For Ghostext-paper

- Keep security framing primary; avoid unsupported broad AI benchmark claims.
- Tie each major claim to: code/test evidence and literature positioning.
- Claims about detector resistance, robustness under edits, or cross-model compatibility must be caveated unless directly evaluated.

## 7. Local Checklist Before Submission

- [ ] Compiles with `acmart` `sigconf`.
- [ ] <= 12 pages main content.
- [ ] Open Science appendix present and concrete.
- [ ] Ethical Considerations appendix present (or explicit rationale for omission).
- [ ] Anonymization pass complete (text, metadata, artifacts, links).
- [ ] Bibliography entries verified (no hallucinated references).
