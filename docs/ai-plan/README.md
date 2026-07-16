# AI & Signal-Intelligence Plan

This folder holds the artificial-intelligence plan for **Mycellium-Aegis** — how the
system turns three weakly informative sub-surface signals (heat-flux rate `dT/dt`,
substrate-drying rate `d(ln R)/dt`, and bioelectric spike frequency `f_spike`) into a
single, low-false-alarm fire-onset decision.

| File | What it is |
|:-----|:-----------|
| [`Mycellium-Aegis_AI_Plan_APA7.md`](./Mycellium-Aegis_AI_Plan_APA7.md) | The full plan, written in **APA 7th-edition** academic style (title page, abstract, headings, tables, in-text citations, references, and appendices). |

## What the plan covers

- **Objectives & success criteria** — headline target: false-positive rate **< 1%** while keeping recall ≥ 0.95.
- **Data foundation** — grounded in the project's two laboratory electrophysiology experiments (the ≈ 20 Hz → ≈ 5 Hz thermal-stress spectral shift), with labeling, provenance, and class-imbalance handling.
- **Signal processing & features** — linear-phase FIR denoising, Savitzky–Golay differentiation, spectral/statistical features.
- **Two-tier decision system** — an interpretable deterministic sensor-fusion **AND** rule (the safety floor) wrapped by a learned **LSTM** temporal classifier.
- **Model architecture & alternatives** — LSTM baseline vs. 1D-CNN, CNN-LSTM, TCN, Transformer, and gradient-boosted trees.
- **Training & evaluation** — grouped time-blocked cross-validation, focal/weighted loss, threshold selection under imbalance, per-regime metrics, lab + field validation.
- **Edge deployment** — INT8-quantized TinyML on the ESP32, event-driven inference within the solar/LiFePO₄ energy budget.
- **MLOps, governance & responsible AI** — versioning, drift monitoring, over-the-air updates, model cards, human oversight.
- **Risk register & roadmap mapping** — AI-specific risks and how every deliverable maps onto the funded 18-month work packages (WP-2, WP-3, WP-4, WP-5, WP-6).

## Rendering to a formatted APA 7 manuscript

The Markdown is written to convert cleanly to a Word/PDF APA 7 manuscript. A formatting
note at the top of the plan lists the exact conventions (running head, heading levels,
hanging indents, table/figure numbering). For example, with Pandoc:

```bash
pandoc "Mycellium-Aegis_AI_Plan_APA7.md" -o "Mycellium-Aegis_AI_Plan_APA7.docx"
```
