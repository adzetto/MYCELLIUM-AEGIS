<!--
APA 7th-edition (professional paper) formatting notes for anyone converting this
Markdown to Word/PDF:

  • Font/spacing: 12-pt Times New Roman (or 11-pt Calibri), double-spaced,
    1-in margins, 0.5-in first-line paragraph indents.
  • Running head: MYCELLIUM-AEGIS AI PLAN  (flush left, all caps, in the header),
    with the page number flush right on every page.
  • Headings map to APA levels as follows:
        #    → paper title (title page only)
        ##   → Level 1  (centered, bold, title case)
        ###  → Level 2  (flush left, bold, title case)
        #### → Level 3  (flush left, bold italic, title case)
        #####→ Level 4  (indented, bold, title case, ends with a period, run-in)
  • References use a hanging indent (0.5 in) once rendered.
  • Tables and figures follow APA style: number (bold), title (italic, on the
    next line), body, then a Note. In Markdown the italic title is rendered with
    asterisks and the number in bold.

This file is written to be readable as Markdown and faithfully convertible to an
APA 7 manuscript. Nothing below is auto-generated boilerplate; every claim is
tied to the project's own experimental record or to a cited source.
-->

# Artificial Intelligence and Signal-Intelligence Plan for the Mycellium-Aegis Sub-Surface Wildfire Early-Warning System

<div align="center">

**An LSTM Sensor-Fusion Approach to Pre-Ignition Fire Detection From Mycelial Bioelectric Activity**

Muhammet Yağcıoğlu¹, Mehmet Çetin¹, Ömer Ünal¹, and Mahmut Can Göçlü¹

¹ Mycellium-Aegis (in formation), İzmir Institute of Technology (İYTE) Technopark

<br>

Author Note

</div>

Muhammet Yağcıoğlu is Co-Founder and Chief Technology Officer of Mycellium-Aegis and leads the software and artificial-intelligence work stream described in this plan. Mehmet Çetin (Chief Executive Officer) leads system architecture; Ömer Ünal (Chief Operating Officer) leads embedded hardware and Internet-of-Things (IoT) systems; and Mahmut Can Göçlü (Chief Research Officer) leads biomaterials and electrode research. The work reported here was conducted within the İzmir Institute of Technology ecosystem and is prepared in support of an application to the TÜBİTAK 1812 Investment-Based Entrepreneurship Support Program (BİGG) under the Green Growth call. The authors have no known conflict of interest to disclose. Correspondence concerning this plan should be addressed to Muhammet Yağcıoğlu, Mycellium-Aegis, İYTE Teknopark, İzmir, Türkiye. Email: info@mycellium-aegis.org

<div align="center">

*Prepared 2026 · Aligned to the 18-month TÜBİTAK 1812 BİGG R&D roadmap*

</div>

---

## Abstract

Contemporary wildfire early-warning systems—satellite imaging, unmanned aerial vehicles, camera networks, and above-ground wireless sensor networks—share a structural limitation: they detect a fire only after flame, thermal radiation, or a smoke plume already exists. Mycellium-Aegis relocates the detection window to the *pre-ignition* phase by burying bio-hybrid sensors 15–20 cm deep and reading the electrical activity of the forest floor's fungal mycelium, which responds to abiotic stress with millivolt-scale voltage spikes. This document specifies the artificial-intelligence (AI) and signal-intelligence plan that converts three weakly informative raw channels—heat-flux rate (*dT/dt*), substrate-drying rate (*d*(ln *R*)/*dt*), and bioelectric spike frequency (*f*_spike)—into a single, low-false-alarm fire-onset decision. The plan is grounded in two laboratory electrophysiology experiments on *Pleurotus ostreatus* and a soil–mycelium network, which established a reproducible thermal-stress signature: a dominant-frequency shift from approximately 20 Hz at rest to approximately 5 Hz under heat stress, accompanied by amplitude change. We propose a two-tier decision system: (a) an interpretable deterministic sensor-fusion rule that requires all three derivative conditions to hold simultaneously (a logical AND), serving as a transparent safety baseline; and (b) a supervised long short-term memory (LSTM) recurrent classifier that learns the joint temporal signature and targets a false-positive rate below 1%. We detail the data foundation and labeling protocol, the feature-engineering and denoising pipeline (linear-phase finite-impulse-response filtering and Savitzky–Golay differentiation), the model architecture and alternatives considered (1D convolutional networks, convolutional-recurrent hybrids, temporal convolutional networks, and attention models), the training and evaluation methodology under severe class imbalance, and the constraints of on-device (edge) inference on an ESP32 microcontroller using 8-bit-quantized TinyML. Finally, we define the machine-learning operations (MLOps), data-governance, responsible-AI, and risk-mitigation practices and map every activity onto the project's funded 18-month work packages.

*Keywords:* wildfire early warning, mycelium biosensor, electrophysiology, sensor fusion, long short-term memory, edge AI, TinyML, false-positive minimization, time-series classification

---

## Introduction and Problem Statement

Wildfire frequency and severity are rising with climate-driven drought and heat waves, and fires damage not only vegetation but the physical, chemical, and biological structure of soil for years (Doerr et al., 2025). The prevailing early-warning stack—satellite imagery, unmanned aerial vehicles, camera towers, and above-ground sensor networks—detects fire only once combustion products (flame, radiated heat, smoke) already exist. By that point ignition has occurred and the intervention window has narrowed to minutes.

Mycellium-Aegis targets an earlier window. Underground mycelial networks transport water and nutrients and generate reproducible, directional voltage spikes in response to heat, moisture loss, and mechanical damage (Adamatzky, 2018, 2026a, 2026b; Phillips et al., 2023). At 15–20 cm depth the soil forms a thermal "safe zone" in which a surface fire arrives as a slow, damped wave of only 25–50 °C—cool enough for the mycelium to survive and keep signaling, yet coupled tightly enough to the surface that the onset of fire is detectable through electrical resistance and voltage change (Doerr et al., 2025). The engineering opportunity is therefore a *sensing* opportunity; the scientific and commercial risk is a *decision* problem. Raw sub-surface signals are individually ambiguous—a hot summer afternoon raises soil temperature, and a prolonged drought raises substrate resistance—so any single channel, thresholded naively, will produce false alarms that destroy operational trust and, in a public-safety deployment, waste scarce firefighting resources.

This plan addresses that decision problem. Its purpose is to specify, end to end, the AI and signal-intelligence system that transforms noisy, weakly informative, multi-rate sensor streams into a fire-onset decision with a controlled and auditable false-positive rate, and to do so within the compute, energy, and connectivity constraints of a buried, solar-powered, LoRa-networked node.

### Scope and Contributions

This document covers the full AI lifecycle for Mycellium-Aegis: the data foundation, the signal-processing and feature pipeline, the deterministic baseline, the learned classifier and the alternatives weighed against it, the training and evaluation protocol, on-device deployment, MLOps and governance, responsible-AI considerations, and AI-specific risk mitigation. It is deliberately explicit about what is *established* by the project's own experiments, what is *designed* but not yet validated, and what remains *open* and scheduled for the funded work packages. The plan does not specify the mechanical, biomaterial, or radio-frequency subsystems except where they constrain the AI (for example, the ESP32 compute budget or the LoRa payload size); those are covered in the project's engineering documentation.

### Relationship to the Funded Roadmap

The activities in this plan are not aspirational; they are mapped onto the project's 18-month TÜBİTAK 1812 BİGG work packages. Threshold and coefficient estimation belongs to Work Package 2 (climate-chamber characterization); denoising, event-driven inference, and edge deployment belong to Work Package 3 (signal processing and LoRa); and the trained LSTM classifier plus its intellectual-property protection belong to Work Package 5 (AI and patent). The "Integration With the R&D Roadmap" section makes this mapping concrete.

---

## Objectives and Success Criteria

The AI system has one primary objective and several supporting objectives, each stated with a measurable acceptance criterion so that progress is falsifiable rather than rhetorical.

### Primary Objective

Detect fire onset during the pre-ignition phase from sub-surface signals with a **false-positive rate below 1%** while retaining high sensitivity to genuine onset events. The 1% target is the project's headline AI commitment and the axis on which operational trust turns: at the network scale envisioned (hundreds to thousands of nodes reporting continuously), even a modest per-node false-alarm probability aggregates into frequent spurious alerts, so the false-positive constraint dominates the design.

### Supporting Objectives

Table 1 states the supporting objectives and their acceptance criteria.

**Table 1**

*AI System Objectives and Acceptance Criteria*

| Objective | Metric | Target / Acceptance criterion |
|:----------|:-------|:------------------------------|
| Minimize false alarms | False-positive rate (FPR) | < 1% on held-out field-representative data |
| Preserve sensitivity | Recall (true-positive rate) on onset events | ≥ 0.95 at the operating threshold |
| Balanced detection quality | Precision–recall area under curve (PR-AUC) | ≥ 0.98; F₁ ≥ 0.95 at the chosen operating point |
| Timeliness | Detection latency after onset signature | Alarm raised before surface flame in controlled burns |
| Edge feasibility | Peak RAM / model size on ESP32 | Model ≤ 128 KB; peak inference RAM ≤ 256 KB |
| Energy budget | Inference energy per decision | Compatible with 5 W solar + LiFePO₄, duty-cycled operation |
| Interpretability | Deterministic-baseline agreement | Learned model's alarms explainable against the AND rule |
| Robustness | Spatial cross-check confirmation | Neighboring-node corroboration for high-severity alerts |

*Note.* FPR = false-positive rate; PR-AUC = area under the precision–recall curve; RAM = random-access memory. The RAM and model-size budgets are engineering targets for the ESP32 (Xtensa LX6, 240 MHz) class of device and will be finalized in Work Package 3. "Field-representative data" denotes data that include seasonal and diurnal variation, drought episodes, and non-fire soil-heating events, so that the false-positive rate is measured against the confounders the system will actually face.

### Non-Goals

For clarity, the AI system is not intended to (a) localize a fire beyond the resolution of node spacing, (b) estimate fire intensity or spread rate as a certified output in the first product generation (directional information from star-electrode arrays is treated as a research signal, not a guaranteed feature), or (c) replace human authority over dispatch decisions. The system raises a corroborated alarm; a human institution acts on it.

---

## Data Foundation

An AI plan is only as credible as the data beneath it. Two escalating laboratory experiments conducted within the İYTE ecosystem (May 2026) established that mycelium answers thermal stress with a measurable, distinguishable bioelectric signature. These experiments constitute the seed dataset and, equally important, validate the founding hypothesis on which every downstream modeling choice depends.

### Experiment 1: Single-Channel Baseline (*Pleurotus ostreatus*)

Experiment 1 recorded a single differential channel from oyster-mushroom tissue at a programmable-gain-amplifier setting of GAIN_SIXTEEN (±0.256 V full scale, 7.8125 µV per bit) at approximately 45 Hz, raw (no filtering, no offset calibration). The resting and heat-stressed conditions differed in both the amplitude and the frequency domain, as summarized in Table 2.

**Table 2**

*Experiment 1 — Amplitude- and Frequency-Domain Signatures of Thermal Stress*

| Metric | Resting (normal) | Fire stress |
|:-------|:-----------------|:------------|
| Voltage range | −29.4 mV to +0.1 mV | min −33.4 mV (Δ = −4.0 mV) |
| Mean voltage | −2.9 mV | −2.94 mV |
| Dominant frequency (FFT) | ≈ 20 Hz | ≈ 5 Hz (harmonic amplitude rises sharply) |
| Samples (*N*) | 1,048 | 1,085 |

*Note.* FFT = fast Fourier transform. Sampling rate *f*ₛ ≈ 45.0 Hz. The dominant-frequency shift from ≈ 20 Hz at rest to ≈ 5 Hz under heat stress is the single most important empirical result for the AI plan: it demonstrates that thermal stress increases ion-channel activity in a way that is legible in the spectral domain, which is precisely the kind of temporal-frequency structure a recurrent or spectro-temporal model is designed to learn. Data from the project's Experiment 1 electrophysiology record.

The mean voltage barely moves (−2.9 vs. −2.94 mV), which is exactly why a naive amplitude threshold would fail; the *distributional* and *spectral* changes carry the signal. This observation motivates feature engineering and sequence modeling over simple level detection.

### Experiment 2: Toward Field Realism (Soil–Mycelium Network)

Experiment 2 moved toward field conditions: an active mycelium network in a layered forest-floor mock-up (soil, rock, organics), measured from two differential channels simultaneously. Table 3 contrasts the two experiments and highlights the firmware and digital-signal-processing (DSP) upgrades that Experiment 2 introduced.

**Table 3**

*Experiment 1 Versus Experiment 2 — Measurement and DSP Configuration*

| Parameter | Experiment 1 | Experiment 2 |
|:----------|:-------------|:-------------|
| Subject | Single mushroom tissue | Active soil/mycelium network |
| Channels | 1 differential | 2 differential (network mapping) |
| PGA gain | GAIN_SIXTEEN (±0.256 V) | GAIN_TWOTHIRDS (±6.144 V, 24× range) |
| Resolution | 7.8 µV/bit | 187.5 µV/bit |
| Sample rate | ≈ 45 Hz | ≈ 100 Hz (Nyquist 50 Hz covers 5 Hz action potentials) |
| Filtering | None (raw) | 5-tap linear-phase FIR [0.1, 0.2, 0.4, 0.2, 0.1] |
| Offset calibration | None | Automatic (50-sample baseline) |

*Note.* PGA = programmable-gain amplifier; FIR = finite impulse response. The symmetric FIR kernel has unity DC gain (Σ*h*ₖ = 1.0) and linear phase, so it suppresses environmental and electromagnetic-interference noise without distorting the waveform's phase—a prerequisite for trustworthy derivative features. The wider PGA range absorbs the soil–electrode DC offset and impedance swings that saturated Experiment 1, and the two channels enable, for the first time, mapping thermal-stress propagation *across* the network rather than at a single point. Data from the project's Experiment 2 electrophysiology record.

### Data Pipeline and Provenance

Every recording is versioned with its full acquisition context—species/substrate, electrode geometry, PGA gain, sample rate, filter configuration, ambient temperature and humidity, and the stimulus protocol (rest vs. controlled radiant heat shock)—following the datasheets-for-datasets discipline (Gebru et al., 2021). Raw counts are retained alongside calibrated millivolt values so that any future recalibration is reproducible. The pipeline stages are: (a) acquisition on the ESP32/ADS1115 chain; (b) offset calibration against a rolling 50-sample baseline; (c) linear-phase FIR denoising; (d) windowing into fixed-length segments for feature extraction and model input; (e) label association; and (f) storage in a version-controlled dataset registry.

### Labeling Protocol

Because the deployed system must distinguish fire onset from benign confounders, labels are defined at the level of *physical regime*, not merely "alarm/no-alarm." Each window is labeled as one of: **normal** (diurnal/seasonal baseline), **drought** (slow capillary drying without heat inflow), **non-fire heating** (e.g., solar loading or a sub-surface heat source), or **fire onset** (concurrent heat inflow, rapid drying, and osmotic-stress spiking). In the laboratory phase, labels derive from the controlled stimulus schedule; in the field phase, labels derive from the synchronized controlled-burn logs specified in Work Package 4. This four-class scheme is what allows the model to learn the *difference* between drought and fire rather than merely detecting "something is happening."

### Class Imbalance and Data Augmentation

Fire onset is, by construction, extremely rare relative to normal operation, so the dataset is severely imbalanced. The plan addresses this at three levels: (a) collection—deliberately over-sampling controlled onset events in the chamber and field campaigns; (b) resampling—minority over-sampling in feature space, e.g., the Synthetic Minority Over-sampling Technique (SMOTE; Chawla et al., 2002), applied only to the training split to avoid leakage; and (c) physics-informed augmentation—time-warping, amplitude jitter within measured electrode-noise bounds, baseline-wander injection, and superposition of recorded environmental-noise segments, so that augmented onset examples remain physically plausible. Augmentation is never applied to validation or test data.

---

## Signal Processing and Feature Engineering

The AI system does not consume raw voltage directly; it consumes physically meaningful features whose behavior is understood. This choice improves data efficiency (critical given a small seed dataset), interpretability, and edge feasibility.

### Denoising and Differentiation

The 5-tap linear-phase FIR filter validated in Experiment 2 is the first stage: it removes high-frequency environmental and electromagnetic noise while preserving waveform phase, so that derivatives computed downstream are not corrupted by filter-induced phase distortion. For the derivative features—*dT/dt* and *d*(ln *R*)/*dt*—naive finite differencing amplifies noise; the plan therefore uses Savitzky–Golay filtering, which fits a local low-order polynomial by least squares and yields smoothed estimates of both the signal and its derivatives in a single pass (Savitzky & Golay, 1964). Work Package 3 will additionally evaluate a Savitzky–Golay hardware/firmware filter for on-node execution.

### Core Feature Set

The three fusion channels defined by the project's detection algorithm form the backbone of the feature set:

1. **Heat-flux rate,** *dT/dt.* At 20 cm the natural rate is on the order of 0.05 °C per hour; an abnormal inflow (illustratively, > 1.5 °C per 10 min) indicates heat pressure from above. Absolute temperature is a weak feature at this depth and is used only contextually.
2. **Drying rate,** *d*(ln *R*)/*dt.* Substrate resistance is inversely and exponentially related to capillary water content; fire-driven drying produces a conductivity drop over minutes rather than the days that natural drought takes.
3. **Bioelectric spiking,** *f*_spike. Spike-burst rate rising above baseline + 3σ over a window Δ*t* signals osmotic stress; star-electrode geometries additionally resolve the *direction* of the incoming stress front.

### Spectral and Statistical Features

Because Experiment 1 established a diagnostic spectral shift (≈ 20 Hz → ≈ 5 Hz), the feature set includes band-power ratios (e.g., low-band/high-band energy), spectral centroid, and dominant-frequency estimates per window, computed with a short-time FFT. Complementary time-domain statistics—windowed variance, skewness, kurtosis, zero-crossing rate, and Hjorth mobility/complexity—capture the distributional change that mean voltage misses. This hand-crafted set gives the deterministic baseline something interpretable to threshold and gives the learned model a compact, physically grounded input representation.

### Learned Versus Engineered Features

The plan preserves both paths deliberately. The engineered features feed the deterministic baseline and the first-generation LSTM. In parallel, a research track evaluates end-to-end learning directly from denoised, windowed waveforms (a 1D convolutional front end that learns its own filters), which may recover structure the hand-crafted set omits. The production model is whichever meets the acceptance criteria in Table 1 at the lowest edge cost; interpretability is a tie-breaker in favor of the engineered-feature model.

---

## Detection Approach: A Two-Tier Decision System

The plan uses two decision layers that operate together: a transparent deterministic rule and a learned classifier. Each compensates for the other's weakness.

### Tier 1: Deterministic Sensor-Fusion Baseline

The baseline is the project's fixed AND rule over rates of change:

```
Alarm = (dT/dt > β)  AND  (d(ln R)/dt > γ)  AND  (spike_active = TRUE)
```

Fixed absolute thresholds ("alarm if temperature > 30 °C") fail in a forest, where seasonal and diurnal swings are normal; watching *rates of change* and requiring all three conditions simultaneously is a combination that natural drought or a hot summer day cannot produce (Phillips et al., 2023). Drying alone is classified as **drought**; all three together are classified as **fire onset**. The coefficients β and γ are not guessed—they are estimated empirically from the maximum variance of a site's historical warming and drying rates, and Work Package 2 fixes them at 98% confidence in a climate chamber. This tier is fully interpretable, requires negligible compute, runs even if the learned model is unavailable, and provides a safety floor and an audit reference for every learned-model decision.

### Tier 2: Learned Temporal Classifier

The deterministic AND rule is robust but rigid: it treats the three channels as independent binary conditions and ignores the *temporal shape* and *joint evolution* of the signature—precisely the information that Experiment 1's spectral shift showed to be diagnostic. Tier 2 is a supervised sequence classifier that learns the joint spatio-temporal signature of fire onset and outputs a calibrated probability, enabling a tunable operating point that meets the < 1% false-positive target while preserving recall. The two tiers are combined conservatively for high-severity alerts: an alarm is escalated when the learned model's probability exceeds the operating threshold *and* the deterministic rule corroborates, with neighboring-node cross-checking for the highest-severity notifications. This design keeps the interpretable rule in the loop while letting the model reduce false alarms that a rigid threshold would raise.

---

## Model Architecture

### Rationale for a Recurrent Model

Fire onset is a *temporal* phenomenon: it is defined by how *dT/dt*, *d*(ln *R*)/*dt*, and spike dynamics evolve and co-occur over seconds to minutes, and by the spectral migration from higher to lower dominant frequencies. Long short-term memory (LSTM) networks were designed to learn dependencies across time while mitigating the vanishing-gradient problem of vanilla recurrent networks (Hochreiter & Schmidhuber, 1997), which makes them a natural first choice for this multivariate, multi-rate time series. The project's headline model is therefore an LSTM sensor-fusion classifier.

### Reference Architecture

The first-generation model is a compact, bidirectional-optional LSTM over windowed multichannel features:

- **Input.** A sliding window of the engineered feature vector (the three fusion channels plus spectral and statistical features) at a fixed stride, optionally augmented with the two raw differential channels for the end-to-end variant.
- **Recurrent core.** One or two LSTM layers (hidden size on the order of 32–64 units), sized against the ESP32 memory budget rather than maximal accuracy. Dropout between layers regularizes the small-data regime (Srivastava et al., 2014).
- **Head.** A fully connected layer to a four-way softmax (normal, drought, non-fire heating, fire onset), with the fire-onset probability driving the alarm decision.
- **Calibration.** Post-hoc probability calibration (temperature scaling) so that the operating threshold corresponds to a meaningful confidence and the false-positive rate is controllable.

### Alternatives Considered

The LSTM is the baseline, not a foregone conclusion. Table 4 records the alternatives evaluated and the trade-offs that inform model selection. The production choice is made empirically against the Table 1 criteria, with edge cost and interpretability as tie-breakers.

**Table 4**

*Candidate Model Families and Trade-Offs for Edge Time-Series Classification*

| Model family | Strengths | Weaknesses / risks | Fit for Mycellium-Aegis |
|:-------------|:----------|:-------------------|:------------------------|
| LSTM (baseline) | Learns long-range temporal dependencies; mature; small variants deployable | Sequential inference; can overfit tiny datasets | Primary; strong temporal fit |
| 1D CNN | Cheap, parallel, learns local spectral motifs; excellent on MCUs | Limited long-range memory | Strong front-end / end-to-end candidate |
| CNN-LSTM hybrid | CNN extracts motifs, LSTM models their evolution | Larger; more tuning | Promising if CNN or LSTM alone underfits |
| Temporal convolutional network (TCN) | Long receptive field via dilations; parallel; stable gradients (Bai et al., 2018) | Newer tooling for MCU export | Serious alternative to LSTM |
| Transformer / attention | Flexible global context (Vaswani et al., 2017) | Data-hungry; heavy for MCUs | Deferred; revisit with a larger corpus |
| Gradient-boosted trees on features | Robust on tabular features; interpretable | No native temporal modeling | Useful strong baseline for benchmarking |

*Note.* CNN = convolutional neural network; MCU = microcontroller unit; TCN = temporal convolutional network. All learned candidates are benchmarked against the deterministic AND rule and a gradient-boosted-trees baseline so that the added value of sequence modeling is measured, not assumed.

---

## Training Methodology

### Data Splits and Cross-Validation

To avoid optimistic bias from temporal autocorrelation, splits respect time and source: windows from the same recording session, electrode, or node never straddle the train/validation/test boundary. The plan uses grouped, time-blocked cross-validation (leave-one-session-out during the laboratory phase, leave-one-site-out during the field phase) so that reported performance estimates generalization to unseen sessions and sites rather than to unseen windows of a seen session.

### Loss, Imbalance, and Thresholding

Given severe class imbalance, training minimizes a class-weighted cross-entropy or focal loss, which down-weights easy negatives and focuses learning on hard, rare positives (Lin et al., 2017). Crucially, the < 1% false-positive constraint is enforced at *threshold-selection* time, not by the loss alone: the operating threshold on the calibrated fire-onset probability is chosen on the validation split to satisfy FPR < 1% while maximizing recall, and is then frozen and evaluated once on the held-out test set. Precision–recall AUC—not accuracy—is the headline selection metric, because accuracy is meaningless under extreme imbalance.

### Optimization and Regularization

Models are trained with the Adam optimizer (Kingma & Ba, 2015) under early stopping on validation PR-AUC, with dropout (Srivastava et al., 2014), weight decay, and gradient clipping. Hyperparameters (window length and stride, hidden size, number of layers, dropout rate, learning rate, class weights) are searched with grouped cross-validation; the search space is bounded by the edge budget so that no configuration is considered that cannot ship. Every run is tracked with its data version, code commit, random seed, and full configuration for reproducibility.

### Reproducibility

All training is deterministic to the extent the framework allows (fixed seeds, pinned library versions), and each model artifact is stored with a model card (Mitchell et al., 2019) recording its training data, intended use, metrics by subgroup/regime, and known limitations. The reference implementation targets PyTorch for research and exports to an edge runtime for deployment.

---

## Evaluation and Validation

### Metrics

Reflecting the false-positive-dominated objective, the evaluation suite is: false-positive rate (primary constraint), recall/true-positive rate at the operating point, precision, F₁, PR-AUC, and ROC-AUC (secondary). Detection latency—time from onset signature to alarm—is reported for every controlled-burn event. Because a single scalar hides failure modes, metrics are reported *per regime* (normal, drought, non-fire heating, fire onset) and *per confounder*, so that a model that achieves headline numbers by failing on drought discrimination is caught.

### Laboratory Validation

Work Package 2 validates the model in a climate chamber that simulates 15–20 cm soil depth with radiant heat shock, logging *dT/dt* and *d*(ln *R*)/*dt* on a 24-bit ADC. This phase fixes the deterministic β and γ coefficients at 98% confidence and produces the labeled onset events needed to train and stress-test the classifier against controlled, repeatable stimuli.

### Field Validation

Work Package 4 buries sensors in an authorized forest plot and runs a small, controlled burn with synchronous logging, providing the first field-labeled onset events and the acid test of the primary objective: the alarm must be raised *before* surface flame. Field data also drive leave-one-site-out evaluation, exposing dataset shift between chamber and forest.

### Spatial Corroboration

Individual-node decisions are cross-checked against neighboring nodes over the LoRa mesh. A localized, single-node anomaly is treated with lower confidence than a spatially coherent anomaly propagating across adjacent nodes, which both suppresses idiosyncratic false positives and provides coarse directional information consistent with the anisotropic spiking observed in star-electrode recordings (Adamatzky, 2026b).

---

## Edge Deployment and On-Device Inference

### Constraints

Inference runs on a buried, solar-powered node built around an ESP32 (Xtensa LX6, 240 MHz) with an ADS1115 16-bit ADC and a low-noise MCP6022 preamplifier, communicating over LoRa at 868 MHz—a long-range, low-power radio choice consistent with prior LoRa-based wildfire early-warning designs (Makdee et al., 2026). The node is energy- and memory-constrained and must operate maintenance-free for long periods on a 5 W solar panel and LiFePO₄ storage. This rules out cloud-only inference for the hot path: connectivity is intermittent and energy-expensive, so the fire-onset decision must be made *on the node*, with only confirmed events forwarded over the mesh.

### Model Compression

The learned model is compressed for the ESP32 via 8-bit integer (INT8) post-training quantization and, if needed, structured pruning, targeting the model-size and RAM budgets in Table 1. Deployment uses a microcontroller inference runtime (e.g., TensorFlow Lite for Microcontrollers), consistent with established TinyML practice for ultra-low-power devices (Warden & Situnayake, 2019). Quantization is validated by measuring the post-quantization false-positive and recall figures against the floating-point model; any regression beyond a set tolerance blocks release.

### Event-Driven Inference

To conserve energy, the node runs a cheap always-on gate—the deterministic derivative checks plus lightweight spike detection—and only wakes the LSTM when the gate indicates a plausible anomaly. This event-driven design (also a Work Package 3 deliverable) keeps average power within the harvesting budget while ensuring the more expensive learned model runs exactly when it matters. Confirmed events are transmitted as compact LoRa payloads; raw waveforms are retained locally and uploaded opportunistically for retraining.

---

## MLOps, Data Governance, and Model Lifecycle

### Versioning and Traceability

Data, features, code, and models are versioned together. Every deployed model is traceable to the exact dataset snapshot, feature-pipeline version, training configuration, and evaluation report that produced it, and carries a model card (Mitchell et al., 2019) and the dataset's datasheet (Gebru et al., 2021). This traceability is also a prerequisite for the patent and public-tender compliance documentation in Work Package 5.

### Drift Monitoring and Retraining

Buried biosensors face non-stationarity: electrodes age and corrode, mycelium networks grow and self-heal, and soil chemistry shifts after rain or fire. The plan monitors input-distribution drift (feature statistics vs. training baselines) and, where ground truth is later available, prediction drift. Detected drift triggers a review and, if warranted, retraining on augmented data, followed by staged re-release. Field nodes receive validated models through controlled over-the-air updates, with the deterministic Tier-1 rule always available as a fallback if an update must be rolled back.

### Human Oversight

The system is decision-support, not autonomous dispatch. Every high-severity alarm carries its evidence (the contributing features, the deterministic-rule status, and neighboring-node corroboration) so that a human institution can audit and act. This keeps a person accountable for consequential decisions and provides a feedback channel—confirmed and disconfirmed alarms—that feeds the retraining loop.

---

## Responsible AI and Ethical Considerations

Because Mycellium-Aegis informs public-safety decisions, the plan treats responsible-AI practice as a requirement, not an add-on. Four commitments are load-bearing. First, **false-positive discipline**: the system's dominant design constraint is minimizing false alarms, precisely because false alarms erode institutional trust and waste emergency resources; the interpretable Tier-1 rule and spatial corroboration exist to bound this. Second, **transparency and auditability**: model cards, versioned data, and evidence-carrying alarms make each decision explainable and reviewable. Third, **human authority**: the AI raises corroborated alarms but never commands a response. Fourth, **environmental integrity**: the AI plan is consistent with the project's Green Growth positioning—edge inference minimizes energy and transmission, and the sensing substrate is a biodegradable, fire-resistant biocomposite (Zhang et al., 2022) hosting pyrophilic fungi that are activated rather than killed by the survivable temperature rise at depth and that metabolize pyrogenic organic matter, contributing to post-fire soil restoration rather than becoming electronic waste (Duong et al., 2025; Fischer et al., 2021). These commitments align the AI system with the TÜBİTAK 1812 BİGG Green Growth call's climate, smart-infrastructure, and circular-economy themes (TÜBİTAK, 2023).

---

## AI-Specific Risk Assessment

Table 5 enumerates the risks that are specific to the AI subsystem, distinct from the project's hardware and biological risks, together with their mitigations.

**Table 5**

*AI-Specific Risks and Mitigations*

| Risk | Description | Mitigation |
|:-----|:------------|:-----------|
| False positives | Summer drought or non-fire sub-surface heating mistaken for fire | Three-signal AND fusion; four-class regime labeling; threshold set to FPR < 1%; neighbor cross-check |
| Missed onset (false negatives) | Model fails to flag a genuine onset | Recall-preserving thresholding; focal loss; conservative escalation; deterministic Tier-1 floor |
| Small-data overfitting | Seed dataset is small and imbalanced | Physics-informed augmentation; dropout/weight decay; grouped CV; compact models |
| Dataset shift (lab → field) | Chamber data differ from forest data | Leave-one-site-out validation; drift monitoring; field-data retraining in WP-4/WP-5 |
| Quantization regression | INT8 model degrades vs. float | Post-quantization metric gate; block release on regression beyond tolerance |
| Sensor degradation / noise | Electrode corrosion and biotic damage shift signals | Drift detection; differential Ag/AgCl or Pt-coated electrodes to preserve SNR; retraining |
| Label noise | Imperfect onset timing in field labels | Synchronized controlled-burn logs; tolerant labeling windows; label audits |
| Automation over-reliance | Operators defer uncritically to the model | Evidence-carrying alarms; human authority retained; interpretable baseline |

*Note.* CV = cross-validation; SNR = signal-to-noise ratio; INT8 = 8-bit integer quantization; WP = work package. These AI risks complement, and do not replace, the project's hardware and biological risk register (false alarms, biotic/abiotic damage, electrode corrosion).

---

## Integration With the 18-Month R&D Roadmap

The AI activities are scheduled inside the funded work packages so that the plan is executable rather than aspirational. Table 6 maps AI deliverables onto the roadmap.

**Table 6**

*Mapping of AI Deliverables to TÜBİTAK 1812 BİGG Work Packages*

| Work package | Window | AI/signal-intelligence deliverable |
|:-------------|:-------|:-----------------------------------|
| WP-2: Climate chamber & thresholds | M4–M7 | Fix β, γ at 98% confidence; build labeled onset dataset; train and stress-test first LSTM; per-regime evaluation |
| WP-3: Signal processing & LoRa | M6–M9 | Denoising (linear-phase FIR + Savitzky–Golay); event-driven inference gate; INT8 edge deployment on ESP32; compact-payload alerting |
| WP-4: Field prototype | M9–M11 | Field-labeled onset events; leave-one-site-out validation; latency-before-flame validation; drift measurement |
| WP-5: AI & patent | M11–M15 | Production LSTM classifier at FPR < 1%; model cards & compliance docs; TÜRKPATENT filing for the algorithm/electrode |
| WP-6: Commercial MVP | M15–M18 | Reference deployment; MLOps for OTA model updates and monitoring at a live B2B/B2G site |

*Note.* OTA = over the air; B2B/B2G = business-to-business / business-to-government. Months are relative to "Month 0" (Excellence Seal obtained after the BİGG Stage-1 accelerator). WP-1 (biocomposite and culture, M1–M3) produces the sensor housings that generate the data this plan consumes.

---

## Conclusion

Mycellium-Aegis reframes wildfire early warning from an above-ground *imaging* problem into a sub-surface *inference* problem. The scientific premise is established by the project's own electrophysiology: mycelium answers thermal stress with a reproducible signature that is legible in both amplitude and, decisively, frequency—the dominant band migrating from approximately 20 Hz at rest to approximately 5 Hz under heat stress. The engineering premise—burial at 15–20 cm, where fire arrives as a survivable 25–50 °C wave—makes that signature measurable in the field. What remains is the *decision* problem, and this plan specifies how to solve it responsibly: an interpretable deterministic sensor-fusion baseline that no drought or hot afternoon can trip, wrapped by an LSTM temporal classifier that learns the joint onset signature and is tuned to a false-positive rate below 1%, all executed on-device within a buried node's energy and memory budget, and governed by versioning, drift monitoring, human oversight, and per-regime evaluation. Each element is mapped onto a funded work package, so the path from the current laboratory evidence (TRL 3→4) to a field-validated prototype (TRL 6→7) is concrete and auditable. The result is an AI system whose central commitment—earning operational trust by not crying wolf—is designed in from the first line, not bolted on at the end.

---

## References

Adamatzky, A. (2018). Towards fungal computer. *Interface Focus, 8*(6), Article 20180029. https://doi.org/10.1098/rsfs.2018.0029

Adamatzky, A. (2026a). *Fungal systems for security and resilience* (arXiv:2602.10543) [Preprint]. arXiv. https://arxiv.org/abs/2602.10543

Adamatzky, A. (2026b). *Directional electrical spiking, bursting, and information propagation in oyster mycelium recorded with a star-shaped electrode array* (arXiv:2601.08099) [Preprint]. arXiv. https://arxiv.org/abs/2601.08099

Bai, S., Kolter, J. Z., & Koltun, V. (2018). *An empirical evaluation of generic convolutional and recurrent networks for sequence modeling* (arXiv:1803.01271) [Preprint]. arXiv. https://arxiv.org/abs/1803.01271

Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: Synthetic minority over-sampling technique. *Journal of Artificial Intelligence Research, 16*, 321–357. https://doi.org/10.1613/jair.953

Doerr, S. H., Girona-García, A., Sánchez-García, C., Badía-Villas, D., Bryant, R., Dickinson, M. B., Hsieh, R., Mataix-Solera, J., Miesel, J. R., Robichaud, P. R., Stoof, C. R., & Santín, C. (2025). Soil heating during wildfires and prescribed burns: A global evaluation. *International Journal of Wildland Fire, 34*(12), Article WF25103. https://doi.org/10.1071/WF25103

Fischer, M. S., Stark, F. G., Berry, T. D., Zeba, N., Whitman, T., & Traxler, M. F. (2021). Pyrolyzed substrates induce aromatic compound metabolism in the post-fire fungus, *Pyronema domesticum*. *Frontiers in Microbiology, 12*, Article 729289. https://doi.org/10.3389/fmicb.2021.729289

Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). Datasheets for datasets. *Communications of the ACM, 64*(12), 86–92. https://doi.org/10.1145/3458723

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation, 9*(8), 1735–1780. https://doi.org/10.1162/neco.1997.9.8.1735

Kingma, D. P., & Ba, J. (2015). *Adam: A method for stochastic optimization* (arXiv:1412.6980) [Preprint]. arXiv. https://arxiv.org/abs/1412.6980

Lin, T.-Y., Goyal, P., Girshick, R., He, K., & Dollár, P. (2017). Focal loss for dense object detection. In *Proceedings of the IEEE International Conference on Computer Vision (ICCV)* (pp. 2980–2988). IEEE. https://doi.org/10.1109/ICCV.2017.324

Makdee, S., Sangkaphet, P., Boonprasom, C., Chaleamwong, B., & Chansiri, N. (2026). The development of a wildfire early warning system using LoRa technology. *Computers, 15*(2), Article 105. https://doi.org/10.3390/computers15020105

Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model cards for model reporting. In *Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT\* '19)* (pp. 220–229). Association for Computing Machinery. https://doi.org/10.1145/3287560.3287596

Phillips, N., Gandia, A., & Adamatzky, A. (2023). Electrical response of fungi to changing moisture content. *Fungal Biology and Biotechnology, 10*(1), Article 8. https://doi.org/10.1186/s40694-023-00155-0

Savitzky, A., & Golay, M. J. E. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry, 36*(8), 1627–1639. https://doi.org/10.1021/ac60214a047

Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I., & Salakhutdinov, R. (2014). Dropout: A simple way to prevent neural networks from overfitting. *Journal of Machine Learning Research, 15*(1), 1929–1958.

TÜBİTAK. (2023). *TÜBİTAK BiGG ekosisteminde büyük değişiklik* [TÜBİTAK BiGG ecosystem major change]. Türkiye Bilimsel ve Teknolojik Araştırma Kurumu. https://tubitak.gov.tr/tr/haber/tubitak-bigg-ekosisteminde-buyuk-degisiklik

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. In *Advances in Neural Information Processing Systems* (Vol. 30, pp. 5998–6008). Curran Associates. https://doi.org/10.48550/arXiv.1706.03762

Warden, P., & Situnayake, D. (2019). *TinyML: Machine learning with TensorFlow Lite on Arduino and ultra-low-power microcontrollers*. O'Reilly Media.

Zhang, X., Li, Y., Fan, X., Wnek, G., Liao, Y.-T. T., & Yu, X. (2022). Development and characterization of novelly grown fire-resistant fungal fibers. *Scientific Reports, 12*, Article 10836. https://doi.org/10.1038/s41598-022-14806-6

---

## Appendix A: Model Card Template

The following template is completed for every released model, following Mitchell et al. (2019).

- **Model details.** Name, version, date, owner (Mycellium-Aegis AI team), architecture, training framework, and the exact data snapshot and code commit used.
- **Intended use.** Pre-ignition fire-onset detection from sub-surface mycelial bioelectric and environmental signals at 15–20 cm depth; decision-support only, not autonomous dispatch.
- **Factors.** Regime (normal, drought, non-fire heating, fire onset), substrate/species, electrode type and age, season, and site.
- **Metrics.** FPR (primary), recall, precision, F₁, PR-AUC, ROC-AUC, and detection latency, each reported per regime and per site.
- **Training data.** Dataset version, class balance, augmentation applied, and provenance.
- **Evaluation data.** Held-out sessions/sites; leave-one-site-out protocol.
- **Ethical considerations.** False-positive impact on emergency resources; human oversight; environmental footprint.
- **Caveats and recommendations.** Known dataset-shift limits; retraining cadence; conditions under which Tier-1 fallback should be used.

## Appendix B: Data Dictionary (Core Fields)

- **timestamp** — acquisition time (UTC), per sample.
- **node_id / channel** — node identifier and differential channel index.
- **v_raw_counts** — raw ADC counts (integer), retained for recalibration.
- **v_mv** — calibrated voltage (mV) after offset calibration and FIR denoising.
- **pga_gain** — programmable-gain-amplifier setting (e.g., GAIN_SIXTEEN, GAIN_TWOTHIRDS).
- **fs_hz** — sample rate (Hz).
- **dT_dt** — heat-flux rate feature (°C · time⁻¹).
- **dlnR_dt** — drying-rate feature (d ln R · time⁻¹).
- **f_spike** — spike-burst frequency feature (relative to baseline + 3σ).
- **band_power_ratio / spectral_centroid / dom_freq** — short-time spectral features (Hz and dimensionless).
- **regime_label** — normal | drought | non_fire_heating | fire_onset.
- **stimulus** — laboratory/field stimulus protocol reference.
- **env_temp / env_rh** — ambient temperature (°C) and relative humidity (%).
- **dataset_version / code_commit** — provenance keys for reproducibility.

## Appendix C: Reference Hyperparameter Space

- **Window length:** 5–60 s (grouped-CV selected).
- **Window stride:** 25%–100% of window length.
- **LSTM layers / hidden units:** 1–2 layers; 32–64 units (edge-bounded).
- **Dropout:** 0.2–0.5.
- **Optimizer:** Adam; learning rate 1e-4 to 1e-2 (log-scale search).
- **Loss:** class-weighted cross-entropy or focal loss (γ_focal ∈ {1, 2, 3}).
- **Class weighting / resampling:** inverse-frequency weights and/or SMOTE on the training split only.
- **Regularization:** weight decay 1e-5 to 1e-3; gradient clipping at a fixed norm; early stopping on validation PR-AUC.
- **Quantization:** INT8 post-training; release gated on post-quantization FPR/recall tolerance.
