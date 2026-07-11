#!/usr/bin/env bash
#
# Mycellium-Aegis — intro video generator (Higgsfield)
# ----------------------------------------------------
# Generates a ~36s cinematic promo: a title/hero card, six video shots,
# and an ambient score, using the Higgsfield CLI.
#
# Prerequisites (see SETUP.md):
#   1. npx skills add higgsfield-ai/skills      # skills (already in .agents/skills/)
#   2. install the higgsfield CLI, then: higgsfield auth login
#
# Usage:
#   bash higgsfield/generate_intro.sh            # 16:9 landscape (default)
#   ASPECT=9:16 bash higgsfield/generate_intro.sh # vertical social cut
#
# Notes:
#   - Every job uses --wait, so each command blocks and prints its result URL.
#   - Output URLs are also appended to higgsfield/output_urls.txt.
#   - Seedance 2.0 supports 4-15s clips; we use 6s per shot.

set -euo pipefail

ASPECT="${ASPECT:-16:9}"       # 16:9 (default) or 9:16
VIDEO_RES="${VIDEO_RES:-1080p}" # 1080p, or 4k for hero-grade output (slower/pricier)
DUR="${DUR:-6}"                # seconds per shot
OUT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$OUT_DIR/output_urls.txt"
STILLS_DIR="$OUT_DIR/stills"
mkdir -p "$STILLS_DIR"
: > "$LOG"

# --- guardrails -------------------------------------------------------------
if ! command -v higgsfield >/dev/null 2>&1; then
  echo "❌ higgsfield CLI not found. Install it and run 'higgsfield auth login' first (see SETUP.md)." >&2
  exit 1
fi
if ! higgsfield account status >/dev/null 2>&1; then
  echo "❌ Not authenticated. Run: higgsfield auth login" >&2
  exit 1
fi

say() { printf '\n\033[1;32m▶ %s\033[0m\n' "$*"; }
gen() { # gen <label> <command...>
  local label="$1"; shift
  say "$label"
  # Run, tee stdout to the log so result URLs are captured.
  "$@" | tee -a "$LOG"
}

# --- 0) Title / hero card (GPT Image 2) -------------------------------------
gen "Title card (GPT Image 2)" \
  higgsfield generate create gpt_image_2 \
    --prompt 'Minimal cinematic title card: the words "MYCELLIUM-AEGIS" in a clean modern sans-serif, subtitle "hearing the forest before it burns", dark forest-floor background with subtle glowing teal mycelium filaments forming a shield motif, elegant high-contrast premium tech-brand aesthetic' \
    --aspect_ratio "$ASPECT" \
    --resolution 2k \
    --wait

# --- Audio bed (Seed Audio 1.0) --------------------------------------------
gen "Ambient score (Seed Audio 1.0)" \
  higgsfield generate create seed_audio \
    --prompt 'Cinematic ambient score for a nature-tech product film: soft forest ambience, low warm drone, gentle rising strings building quiet tension then resolving to hopeful, subtle electronic pulses, about 36 seconds, no vocals' \
    --wait

# --- 1..6) Video shots (Seedance 2.0) --------------------------------------
gen "Shot 1 — The calm" \
  higgsfield generate create seedance_2_0 \
    --prompt 'Cinematic aerial descent over a vast Mediterranean pine forest at golden dusk, camera slowly craning down toward the forest floor, warm volumetric sunlight through the canopy, mist in the valleys, ultra-detailed, calm and majestic, 4K nature documentary look, slow graceful motion' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

gen "Shot 2 — The living network" \
  higgsfield generate create seedance_2_0 \
    --prompt 'Macro camera push into dark forest soil, revealing a vast glowing network of fungal mycelium threads 15 to 20 cm underground, bioluminescent teal-green filaments pulsing with faint electric signals travelling along the hyphae like a living neural web, tiny particles of light, cinematic, shallow depth of field, science meets nature' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

gen "Shot 3 — It feels the fire first" \
  higgsfield generate create seedance_2_0 \
    --prompt 'Underground cross-section: a small buried bio-hybrid sensor node with a rough mycelium-composite housing and fine electrodes nestled among roots and soil; a wave of heat and dryness approaches from above; surrounding mycelium threads flare from calm teal to urgent orange-red, electric spikes rippling outward from the node, tense dramatic lighting, macro cinematic' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

gen "Shot 4 — The mesh wakes up" \
  higgsfield generate create seedance_2_0 \
    --prompt 'Stylized wide shot across a forest floor at night, a dozen buried sensor nodes lighting up one after another and passing arcs of glowing data between them like a LoRa mesh network, streams of light converging toward a slim gateway antenna tower at the forest edge, cinematic, atmospheric fog, teal and amber light trails' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

gen "Shot 5 — Early warning" \
  higgsfield generate create seedance_2_0 \
    --prompt 'A modern emergency-operations dashboard glowing in a dark control room, a digital map of a forest with one node pulsing red and a bold alert reading FIRE ONSET DETECTED, clean data-visualization overlays of rising curves and waveforms, while a small live camera inset shows a forest with only the faintest wisp of smoke, cinematic sci-fi UI, blue and red glow' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

gen "Shot 6 — The forest saved" \
  higgsfield generate create seedance_2_0 \
    --prompt 'Sweeping golden-hour aerial rising up and away from a healthy green intact pine forest, sunlight bursting through, hopeful and triumphant, cinematic, the frame settling into calm negative space at the top for a title, 4K' \
    --aspect_ratio "$ASPECT" --duration "$DUR" --resolution "$VIDEO_RES" --wait

say "Done. All result URLs saved to: $LOG"
echo "Download each clip + the title card, then stitch in your editor (order: title → shots 1-6), lay the Seed Audio bed under it, and add the on-screen captions from STORYBOARD.md."
