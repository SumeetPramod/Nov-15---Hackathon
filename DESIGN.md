# Design

World: **Anatomy Plate.** A lithographic anatomical atlas plate: one finely drawn figure owns the page, and every measurement is named by a leader line. The patient's own leg is the figure; each rep is annotated live. Warm and human through gentle line, humane type and encouraging copy, never through gore, muscle detail or clinical chrome.

This file records the direction chosen before the build. It is refreshed from the built system at the finish.

## Colour

Strategy: **full palette with an anatomical colour code.** Neutral atlas paper and engraving ink carry the page; four anatomical colours do real jobs and appear nowhere else.

| Token | Light | Dark | Job |
|---|---|---|---|
| `--paper` | `#EEF1EE` | `#121A1D` | page ground: cool atlas paper / engraving plate |
| `--sheet` | `#F7F9F7` | `#182226` | raised surfaces: panel, table, inputs |
| `--ink` | `#1F2A2E` | `#E4EAE7` | text, figure line |
| `--ink-2` | `#56636A` | `#9AA8AE` | secondary text, leader lines, captions |
| `--rule` | `#C9D1CE` | `#2C393E` | hairlines, borders |
| `--vein` | `#2C4E9E` | `#8FAEF0` | the live limb, primary actions, focus, selection |
| `--artery` | `#C23B32` | `#F07A6E` | the target zone; never for errors on movement |
| `--nerve` | `#E2AE38` | `#F0C25A` | hold progress (fill only, never text) |
| `--lymph` | `#3C8A5F` | `#6FC495` | a good rep (fill); text uses `--lymph-ink` `#2F7350` / `#7FD3A4` |

Light is primary: the scene is a home chair by daylight or a lamp, screen at arm's length. Dark mode is the same plate printed as a negative. Short or rushed reps are never shown in red; the copy carries the coaching and the rep marker stays hollow or partial.

## Type

- **Spectral** (Production Type), regular, italic, semibold: the plate's voice. Wordmark, headings, figure captions, leader-line letters (*a. range*).
- **Atkinson Hyperlegible** (Braille Institute), regular and bold: everything a patient must read at a distance. Body, controls, readouts, tables. Designed for low vision; numerals are unambiguous. Tabular numerals in all data.

Scale (px): 13 · 15 · 17 (body) · 20 · 26 · 34 · 44 · 64 (live readout). Tracking -0.015em on headings, 0 elsewhere. Body measure stays under 70ch. Body copy works at one size; hierarchy comes from weight and position.

## Space and shape

4px base: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64. Radii: 8px on controls, 12px on the few raised surfaces, full on status dots. Elevation is a 1px `--rule` hairline; no shadows except the active rep row's focus.

## Layout

- Laptop: header rule; the plate figure fills the left column, a single action panel (440px) on the right; below, the set table and progress. The figure owns the field: no cards around it.
- Phone: figure on top at about 45% of the viewport, panel below, simulator controls in a sticky bottom tray within thumb reach.

## Signature move

The live leg drawn as an atlas figure: fine-line thigh on a chair, the shin in vein blue rotating with the real knee, the target zone hatched in artery red, a nerve-yellow hold arc filling around the knee, rep markers arcing above it, and leader lines that carry the live readouts (*a. range*, *b. hold*, *c. rep*). A caption beneath (*Fig. 3*) says in words what the figure shows. The set summary repeats the figure small, once per rep, frozen at its peak: a specimen sheet of the set.

## Motion

- The limb follows the sensor with no easing: it must feel attached to the body.
- Haptic events show as a single ink ripple from the knee, at the instant the brace clicks.
- Rep markers fill with a short ease-out (200ms); a finished rep lands in its table row with a brief paper-tint highlight.
- Step changes in the panel cross-fade with a 6px rise over 240ms, exponential ease-out.
- `prefers-reduced-motion`: ripples, rises and fills become instant; the limb still tracks.

## Components

Standard web controls drawn in the plate's language: buttons (vein-filled primary, ink-outlined secondary, text-only tertiary), native select and number inputs on `--sheet`, a disclosure for adjusting targets, a step indicator for the three steps, a rep table whose columns never move, and SVG line icons at 1.75px stroke. No emoji or Unicode glyphs as icons.
