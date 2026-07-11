# 🎬 Mycellium‑Aegis — Intro Video Storyboard

A cinematic ~36‑second promo that explains the product in six shots: *calm forest → living underground network → pre‑ignition detection → mesh alert → forest saved.*

- **Format:** 16:9 landscape, cinematic (a 9:16 social cut is a one‑flag change — see `generate_intro.sh`)
- **Total length:** ~36 s (6 shots × ~6 s)
- **Look:** volumetric natural light meets bioluminescent teal/green data‑glow; grounded, hopeful, high‑tech‑nature
- **Models (Higgsfield):** Seedance 2.0 (video), GPT Image 2 (title/hero stills), Seed Audio 1.0 (score/ambience)

> Tip: generating a **still first** (GPT Image 2 / Nano Banana 2) and feeding it to Seedance 2.0 as `--start-image` gives stronger shot‑to‑shot consistency. `generate_intro.sh` includes both the pure text‑to‑video path and the still‑seeded path.

---

## Shot list

### Shot 1 — "The calm" (0–6 s)
**Prompt:** *Cinematic aerial descent over a vast Mediterranean pine forest at golden dusk, camera slowly craning down toward the forest floor, warm volumetric sunlight through the canopy, mist in the valleys, ultra‑detailed, calm and majestic, 4K nature documentary look, slow graceful motion.*
**Purpose:** Establish the thing we protect. Peace before the threat.

### Shot 2 — "The living network" (6–12 s)
**Prompt:** *Macro camera push into dark forest soil, revealing a vast glowing network of fungal mycelium threads 15–20 cm underground, bioluminescent teal‑green filaments pulsing with faint electric signals travelling along the hyphae like a living neural web, tiny particles of light, cinematic, shallow depth of field, science‑meets‑nature.*
**Purpose:** Reveal the core idea — the forest floor is already a sensor.

### Shot 3 — "It feels the fire first" (12–18 s)
**Prompt:** *Underground cross‑section: a small buried bio‑hybrid sensor node with a rough mycelium‑composite housing and fine electrodes nestled among roots and soil; a wave of heat and dryness approaches from above; the surrounding mycelium threads flare from calm teal to urgent orange‑red, electric spikes rippling outward from the node, tense dramatic lighting, macro cinematic.*
**Purpose:** Show pre‑ignition detection — heat/drying/spike stress before any flame.

### Shot 4 — "The mesh wakes up" (18–24 s)
**Prompt:** *Stylized wide shot across a forest floor at night, a dozen buried sensor nodes lighting up one after another and passing arcs of glowing data between them like a LoRa mesh network, streams of light converging toward a slim gateway antenna tower at the forest edge, cinematic, atmospheric fog, teal and amber light trails.*
**Purpose:** Show the P2P LoRa mesh relaying the alert.

### Shot 5 — "Early warning" (24–30 s)
**Prompt:** *A modern emergency‑operations dashboard glowing in a dark control room, a digital map of a forest with one node pulsing red and a bold alert reading "FIRE ONSET DETECTED", clean data‑visualization overlays of rising curves and waveforms, while a small live camera inset shows a forest with only the faintest wisp of smoke, cinematic sci‑fi UI, blue and red glow.*
**Purpose:** The payoff — humans alerted while the surface still looks fine.

### Shot 6 — "The forest saved" (30–36 s)
**Prompt:** *Sweeping golden‑hour aerial rising up and away from a healthy green intact pine forest, sunlight bursting through, hopeful and triumphant, cinematic, the frame settling into calm negative space at the top for a title, 4K.*
**Purpose:** Resolution + room for the end title card.

---

## Title / hero card (GPT Image 2)
**Prompt:** *Minimal cinematic title card: the words "MYCELLIUM‑AEGIS" in a clean modern sans‑serif, subtitle "hearing the forest before it burns", set against a dark forest‑floor background with subtle glowing teal mycelium filaments forming a shield motif, elegant, high‑contrast, 16:9, premium tech‑brand aesthetic.*

## Audio bed (Seed Audio 1.0)
**Prompt:** *Cinematic ambient score for a nature‑tech product film: soft forest ambience, low warm drone, gentle rising strings building quiet tension then resolving to hopeful, subtle electronic pulses, ~36 seconds, no vocals.*

---

## On‑screen text (optional overlay, add in edit)
| Time | Caption |
|-----:|:--------|
| 0–6 s | *Every year, forests burn.* |
| 6–12 s | *Beneath them lives a network that feels everything.* |
| 12–18 s | *Mycellium‑Aegis listens 15–20 cm underground —* |
| 18–24 s | *sensing a fire before the first flame.* |
| 24–30 s | *dT/dt · dR/dt · bioelectric spikes → early warning.* |
| 30–36 s | **Mycellium‑Aegis — hearing the forest before it burns.** |
