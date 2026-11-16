# Design

World: **Anatomy Plate.** A lithographic anatomical atlas plate: one finely drawn figure owns the page, and every measurement is named by a leader line. The patient's own leg is the figure; each rep is annotated live and then drawn as a record of how it moved. Warm and human through gentle line, humane type and encouraging copy, never through gore, muscle detail or clinical chrome.

This file describes the system as built in `static/index.html`. Tokens there are the source of truth.

## Colour

Strategy: **neutral plate plus an anatomical colour code.** Atlas paper and engraving ink carry the page; four anatomical colours each do one job and appear nowhere else.

| Token | Light | Dark | Job |
|---|---|---|---|
| `--paper` | `#EEF1EE` | `#121A1D` | page ground: cool atlas paper / engraving plate |
| `--sheet` | `#F7F9F7` | `#182226` | raised surfaces: inputs, notes, tray on narrow screens |
| `--ink` | `#1F2A2E` | `#E4EAE7` | text and figure line |
| `--ink-2` | `#56636A` | `#9AA8AE` | secondary text, leader lines, captions (5.4:1 / 7.2:1) |
| `--rule` / `--rule-soft` | `#C9D1CE` / `#DDE3E0` | `#2C393E` / `#222E33` | hairlines; hold-ring track |
| `--mark` | `#7A8783` | `#6B7A80` | meaningful non-text marks: input and step borders, "to come" dots (≥3:1) |
| `--chair` | `#9AA6A2` | `#4E5D63` | the chair drawing only (decorative) |
| `--vein` | `#2C4E9E` | `#8FAEF0` | the live limb, strobe lines, primary actions, focus ring, current step |
| `--artery` | `#C23B32` | `#F07A6E` | the red threshold line and the zone past it; error icons. Never a poor rep. |
| `--nerve` | `#A8750E` | `#F0C25A` | hold progress around the knee (3.5:1 on paper) |
| `--lymph` / `--lymph-ink` | `#3C8A5F` / `#2F7350` | `#6FC495` / `#7FD3A4` | a good rep: marker fill / text |

Light is primary: the scene is a home chair by daylight or a lamp, screen at arm's length. Dark mode is the same plate printed as a negative. Short or rushed reps are never red: the copy coaches, and the marker shape says what happened.

## Type

- **Spectral** (regular, italic, semibold, semibold italic): the plate's voice. Wordmark, headings, figure captions, leader-line tags (*a. rep*), the plan sentence and the first-screen lead.
- **Atkinson Hyperlegible** (regular, bold): everything a patient reads at a distance. Body, controls, readouts, tables. Designed for low vision; tabular numerals in all data.

Page text is set in rem so the browser's font-size preference applies: body 1.0625rem, results 1.25rem, h1 2.5rem (2rem on phones), h2 2.125rem. Figure text lives in SVG viewBox units (tags 23, values 52, last-rep verdict 40), scaled up between 901 and 1280 px where the plate shrinks. Headings track at -0.015em.

## Space and shape

4px base: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 (`--s1`…`--s8`). Radii: 8px controls, 12px notes, full for dots and step numbers. Elevation is a 1px hairline; no drop shadows.

## Layout

- **Above 1100 px:** header rule; the plate fills the left column with leader-line readouts at its right edge; a 440 px action panel on the right; "This set" and "Your progress" below.
- **901–1100 px:** single column; the plate keeps its leader labels; the simulator tray is fixed to the bottom.
- **900 px and below:** leader lines drop away and the readouts (rep, hold, range) sit in a row under the figure. On phones the figure shrinks on the first screen so the one action is above the fold; on every step change the page returns to the figure if it scrolled away.

## Signature moves

1. **The live atlas figure.** Fine-line thigh on a chair; the shin in vein blue follows the sensor with no easing; the red threshold line at target minus allowance with a faint zone past it; a nerve-coloured hold arc around the knee; one marker per rep arcing above it; leader lines to *a. rep*, *b. hold*, *c. range*. On the first screen the leaders name the vibration motor and the motion sensor instead.
2. **The Marey strobe.** After each rep, faint shin lines a quarter second apart show the lift (computed in `core.py`), with a dashed outline at the peak and a "last rep" verdict on the plate. A controlled lift leaves many close lines; a rushed one leaves two or three far apart. It stays until the next lift begins.
3. **The specimen sheet.** At the end of a set, every rep is drawn small at its peak, with its strobe and its verdict marker.

A caption beneath the plate (*Fig. 1–4*) always says in words what the figure shows.

## Verdict vocabulary

One shape per result, used on the figure, in the result line, in the table and on the specimen sheet:

| Result | Words | Marker | Icon |
|---|---|---|---|
| good | Full range, steady | filled lymph disc | check |
| short | A little short | ring, lower half filled | half-filled circle |
| rushed | A bit quick | ring with two bars | circle with two bars |
| short hold | Short hold | dashed ring | dashed circle |
| to come | To come | small mark dot | – |

## Motion

- The limb follows the sensor directly; nothing eases the angle.
- A haptic event shows as one ink ripple from the knee, the knee cap filling blue and arcs at the motor, at the instant the brace clicks.
- Rep markers pop in (350 ms); a finished rep's table row lands with a brief tint; the panel cross-fades with a 6 px rise (240 ms, exponential ease-out).
- `prefers-reduced-motion`: ripples and rises are removed; the 2 s calibration ring still fills because it is a progress signal; the limb still tracks.

## Components

Standard web controls drawn in the plate's language: vein-filled primary buttons (48–56 px), ink-outlined secondary buttons, underlined text buttons, native selects and number inputs on `--sheet` with `--mark` borders, disclosures for *Adjust targets*, a three-step indicator, a rep table whose columns never move, a simulator tray (Good rep / Stop short / Rush it, keys 1–3 with an on/off switch), and 1.75 px stroke SVG icons. No emoji or Unicode glyphs as icons.
