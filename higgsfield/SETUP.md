# 🛠️ Higgsfield setup — Mycellium‑Aegis intro video

Three steps, matching the [Higgsfield "Skills for any AI"](https://higgsfield.ai) onboarding.

## 1 — Add the skills
Pulls the `generate`, `soul`, and `product‑photoshoot` skills into your agent.

```bash
npx skills add higgsfield-ai/skills
```

> ✅ Already done in this repo — the skills live under `.agents/skills/` (`higgsfield-generate`, `higgsfield-soul-id`, `higgsfield-product-photoshoot`, and more).

## 2 — Install the CLI and sign in
The `generate` skill drives the `higgsfield` CLI. Install it, then authenticate — **this step is interactive and needs your Higgsfield account**, so it can't be automated:

```bash
# install the CLI (downloads the released binary)
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh

# sign in (opens a browser / device-code flow)
higgsfield auth login

# verify
higgsfield account status
```

## 3 — Plug skills into your agent / generate
Inside your agent you can now invoke:

```
/higgsfield:generate
```

…or run the pre‑built pipeline for this project's intro video:

```bash
bash higgsfield/generate_intro.sh
# vertical social cut:
ASPECT=9:16 bash higgsfield/generate_intro.sh
# hero-grade 4K video (slower / more credits):
VIDEO_RES=4k bash higgsfield/generate_intro.sh
```

The script generates a title card, an ambient score, and six cinematic shots, printing a result URL for each and logging them to `higgsfield/output_urls.txt`. See `STORYBOARD.md` for the shot list, prompts, and edit notes.

---

### Models used
| Asset | Model | Why |
|:------|:------|:----|
| Title / hero card | `gpt_image_2` | High‑fidelity on‑image text & design |
| Six video shots | `seedance_2_0` | SOTA cinematic, multi‑shot, 4–15 s clips |
| Ambient score | `seed_audio` | Text‑to‑audio score/ambience |

Swap models freely — e.g. `marketing_studio_video` for an ad‑style cut, or `soul_location` stills for environment shots. Run `higgsfield model list --json` to see everything available on your account.
