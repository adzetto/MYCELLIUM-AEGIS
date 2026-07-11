# 🎬 Mycellium‑Aegis — Higgsfield Intro Video

Everything needed to produce the Mycellium‑Aegis promo video with **[Higgsfield](https://higgsfield.ai)** lives in this one file: setup, model choices, the full shot‑by‑shot storyboard, every prompt, the ready‑to‑run commands, and edit notes.

- **Concept:** a ~36‑second cinematic promo in six shots — *calm forest → living underground network → pre‑ignition detection → mesh alert → forest saved.*
- **Format:** 16:9 landscape (a 9:16 social cut is one flag change)
- **Look:** volumetric natural light meets bioluminescent teal/green "data‑glow"; grounded, hopeful, high‑tech‑nature
- **Voice line / tagline:** *"Mycellium‑Aegis — hearing the forest before it burns."*

---

## 1 · Setup (3 steps)

Matches the Higgsfield "Skills for any AI" onboarding.

### Step 1 — Add the skills
Pulls `generate`, `soul`, and `product‑photoshoot` (and more) into your agent.
```bash
npx skills add higgsfield-ai/skills
```
> ✅ Already done in this repo — the skills live under `.agents/skills/` and are symlinked into `.claude/skills/`. `skills-lock.json` records the install.

### Step 2 — Install the CLI and sign in
The `generate` skill drives the `higgsfield` CLI. **This step is interactive and needs your Higgsfield account, so it can't be automated.**
```bash
# install the CLI (downloads the released binary)
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh

# sign in (opens a browser / device-code flow)
higgsfield auth login

# verify you're authenticated
higgsfield account status
```

### Step 3 — Generate
Inside your agent, invoke `/higgsfield:generate`, or paste the [commands in §5](#5--ready-to-run-commands) into a terminal. Each job uses `--wait`, so it blocks and prints the finished asset's URL.

---

## 2 · Models used

| Asset | Model (`--model`/job type) | Why |
|:------|:---------------------------|:----|
| Title / hero card | `gpt_image_2` | High‑fidelity on‑image text & graphic design |
| Six video shots | `seedance_2_0` | SOTA cinematic, multi‑shot, 4–15 s clips, image‑to‑video |
| Ambient score | `seed_audio` | Text‑to‑audio score / ambience |

Swap freely — e.g. `marketing_studio_video` for an ad‑style cut, or `soul_location` stills for environment shots. Run `higgsfield model list --json` to see everything on your account.

> **Tip — shot consistency:** generating a **still first** (`gpt_image_2` / `nano_banana_2`) and feeding it to Seedance 2.0 as `--start-image` gives stronger shot‑to‑shot continuity. §5 shows the pure text‑to‑video path; §6 shows the still‑seeded variant.

---

## 3 · Storyboard & prompts

### Title / hero card — `gpt_image_2`
> Minimal cinematic title card: the words "MYCELLIUM‑AEGIS" in a clean modern sans‑serif, subtitle "hearing the forest before it burns", set against a dark forest‑floor background with subtle glowing teal mycelium filaments forming a shield motif, elegant, high‑contrast, 16:9, premium tech‑brand aesthetic.

### Ambient score — `seed_audio`
> Cinematic ambient score for a nature‑tech product film: soft forest ambience, low warm drone, gentle rising strings building quiet tension then resolving to hopeful, subtle electronic pulses, about 36 seconds, no vocals.

### Shot 1 — "The calm" (0–6 s) — `seedance_2_0`
> Cinematic aerial descent over a vast Mediterranean pine forest at golden dusk, camera slowly craning down toward the forest floor, warm volumetric sunlight through the canopy, mist in the valleys, ultra‑detailed, calm and majestic, 4K nature documentary look, slow graceful motion.

*Purpose: establish the thing we protect — peace before the threat.*

### Shot 2 — "The living network" (6–12 s) — `seedance_2_0`
> Macro camera push into dark forest soil, revealing a vast glowing network of fungal mycelium threads 15–20 cm underground, bioluminescent teal‑green filaments pulsing with faint electric signals travelling along the hyphae like a living neural web, tiny particles of light, cinematic, shallow depth of field, science‑meets‑nature.

*Purpose: reveal the core idea — the forest floor is already a sensor.*

### Shot 3 — "It feels the fire first" (12–18 s) — `seedance_2_0`
> Underground cross‑section: a small buried bio‑hybrid sensor node with a rough mycelium‑composite housing and fine electrodes nestled among roots and soil; a wave of heat and dryness approaches from above; the surrounding mycelium threads flare from calm teal to urgent orange‑red, electric spikes rippling outward from the node, tense dramatic lighting, macro cinematic.

*Purpose: pre‑ignition detection — heat/drying/spike stress before any flame.*

### Shot 4 — "The mesh wakes up" (18–24 s) — `seedance_2_0`
> Stylized wide shot across a forest floor at night, a dozen buried sensor nodes lighting up one after another and passing arcs of glowing data between them like a LoRa mesh network, streams of light converging toward a slim gateway antenna tower at the forest edge, cinematic, atmospheric fog, teal and amber light trails.

*Purpose: the P2P LoRa mesh relaying the alert.*

### Shot 5 — "Early warning" (24–30 s) — `seedance_2_0`
> A modern emergency‑operations dashboard glowing in a dark control room, a digital map of a forest with one node pulsing red and a bold alert reading "FIRE ONSET DETECTED", clean data‑visualization overlays of rising curves and waveforms, while a small live camera inset shows a forest with only the faintest wisp of smoke, cinematic sci‑fi UI, blue and red glow.

*Purpose: the payoff — humans alerted while the surface still looks fine.*

### Shot 6 — "The forest saved" (30–36 s) — `seedance_2_0`
> Sweeping golden‑hour aerial rising up and away from a healthy green intact pine forest, sunlight bursting through, hopeful and triumphant, cinematic, the frame settling into calm negative space at the top for a title, 4K.

*Purpose: resolution + room for the end title card.*

---

## 4 · On‑screen captions (add in edit)

| Time | Caption |
|-----:|:--------|
| 0–6 s | *Every year, forests burn.* |
| 6–12 s | *Beneath them lives a network that feels everything.* |
| 12–18 s | *Mycellium‑Aegis listens 15–20 cm underground —* |
| 18–24 s | *sensing a fire before the first flame.* |
| 24–30 s | *dT/dt · dR/dt · bioelectric spikes → early warning.* |
| 30–36 s | **Mycellium‑Aegis — hearing the forest before it burns.** |

---

## 5 · Ready‑to‑run commands

Copy‑paste after Step 2. Each job blocks (`--wait`) and prints the result URL. Save this block as `generate_intro.sh` if you prefer a script — but everything you need is right here.

```bash
#!/usr/bin/env bash
set -euo pipefail

ASPECT="${ASPECT:-16:9}"          # 16:9 (default) or 9:16 for a vertical cut
VIDEO_RES="${VIDEO_RES:-1080p}"    # 1080p, or 4k for hero-grade (slower/pricier)
DUR="${DUR:-6}"                    # seconds per shot (Seedance 2.0 supports 4-15)

# Guardrails
command -v higgsfield >/dev/null || { echo "Install the higgsfield CLI first (see Step 2)."; exit 1; }
higgsfield account status >/dev/null 2>&1 || { echo "Run: higgsfield auth login"; exit 1; }

# 0) Title / hero card
higgsfield generate create gpt_image_2 \
  --prompt 'Minimal cinematic title card: the words "MYCELLIUM-AEGIS" in a clean modern sans-serif, subtitle "hearing the forest before it burns", dark forest-floor background with subtle glowing teal mycelium filaments forming a shield motif, elegant high-contrast premium tech-brand aesthetic' \
  --aspect_ratio "$ASPECT" --resolution 2k --wait

# Ambient score
higgsfield generate create seed_audio \
  --prompt 'Cinematic ambient score for a nature-tech product film: soft forest ambience, low warm drone, gentle rising strings building quiet tension then resolving to hopeful, subtle electronic pulses, about 36 seconds, no vocals' \
  --wait

# 1) The calm
higgsfield generate create seedance_2_0 \
  --prompt 'Cinematic aerial descent over a vast Mediterranean pine forest at golden dusk, camera slowly craning down toward the forest floor, warm volumetric sunlight through the canopy, mist in the valleys, ultra-detailed, calm and majestic, 4K nature documentary look, slow graceful motion' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

# 2) The living network
higgsfield generate create seedance_2_0 \
  --prompt 'Macro camera push into dark forest soil, revealing a vast glowing network of fungal mycelium threads 15 to 20 cm underground, bioluminescent teal-green filaments pulsing with faint electric signals travelling along the hyphae like a living neural web, tiny particles of light, cinematic, shallow depth of field, science meets nature' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

# 3) It feels the fire first
higgsfield generate create seedance_2_0 \
  --prompt 'Underground cross-section: a small buried bio-hybrid sensor node with a rough mycelium-composite housing and fine electrodes nestled among roots and soil; a wave of heat and dryness approaches from above; surrounding mycelium threads flare from calm teal to urgent orange-red, electric spikes rippling outward from the node, tense dramatic lighting, macro cinematic' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

# 4) The mesh wakes up
higgsfield generate create seedance_2_0 \
  --prompt 'Stylized wide shot across a forest floor at night, a dozen buried sensor nodes lighting up one after another and passing arcs of glowing data between them like a LoRa mesh network, streams of light converging toward a slim gateway antenna tower at the forest edge, cinematic, atmospheric fog, teal and amber light trails' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

# 5) Early warning
higgsfield generate create seedance_2_0 \
  --prompt 'A modern emergency-operations dashboard glowing in a dark control room, a digital map of a forest with one node pulsing red and a bold alert reading FIRE ONSET DETECTED, clean data-visualization overlays of rising curves and waveforms, while a small live camera inset shows a forest with only the faintest wisp of smoke, cinematic sci-fi UI, blue and red glow' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

# 6) The forest saved
higgsfield generate create seedance_2_0 \
  --prompt 'Sweeping golden-hour aerial rising up and away from a healthy green intact pine forest, sunlight bursting through, hopeful and triumphant, cinematic, the frame settling into calm negative space at the top for a title, 4K' \
  --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait
```

Run variants:
```bash
# vertical social cut (Reels/Shorts/TikTok)
ASPECT=9:16 bash generate_intro.sh
# hero-grade 4K video (more credits, longer)
VIDEO_RES=4k bash generate_intro.sh
```

---

## 6 · Optional — still‑seeded shots (stronger continuity)

Generate a keyframe still, then animate it. Feed a local path or a previous job's UUID straight to `--start-image` (the CLI auto‑uploads/auto‑detects):

```bash
# 1) keyframe still for shot 2
higgsfield generate create gpt_image_2 \
  --prompt 'Macro underground forest soil with a glowing teal-green fungal mycelium network, bioluminescent filaments, cinematic, shallow depth of field' \
  --aspect_ratio 16:9 --resolution 2k --wait
#   -> note the returned image URL/id, save it locally as shot2_key.png

# 2) animate that exact still
higgsfield generate create seedance_2_0 \
  --prompt 'slow macro push-in, filaments pulse with faint electric light travelling along the hyphae' \
  --start-image ./shot2_key.png \
  --aspect_ratio 16:9 --duration 6 --resolution 1080p --wait
```

---

## 7 · Edit / delivery

1. Download the title card + the six clips + the audio bed from the printed URLs.
2. Stitch in your editor in order: **title → shots 1–6**.
3. Lay the Seed Audio score underneath; duck it slightly under any voiceover.
4. Add the on‑screen captions from §4.
5. Export 16:9 (H.264/H.265) for web/landing pages; re‑run with `ASPECT=9:16` for a vertical social cut.

---

## 8 · Troubleshooting

| Symptom | Fix |
|:--------|:----|
| `higgsfield: command not found` | Install the CLI (Step 2); ensure its bin dir is on `$PATH`. |
| `Session expired` / `Not authenticated` | `higgsfield auth login`. |
| `Missing required params: prompt` | Provide `--prompt`. |
| `Invalid values: aspect_ratio=…` | Use an allowed enum (`16:9`, `9:16`, `1:1`, …). |
| `Unknown params: foo` | That model's schema doesn't accept the flag — check `higgsfield model get <model> --json`. |
| Shot looks inconsistent with the others | Use the still‑seeded path in §6 with `--start-image`. |
