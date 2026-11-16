# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary: a person rehabilitating a knee at home.** After an injury or surgery, between physiotherapy appointments. Seated on a chair with the thigh supported, wearing the Rehabify brace, possibly sore or anxious about the knee. They glance at a laptop or a phone propped nearby while doing seated knee extensions; their hands and attention are on the movement.
- **Physiotherapist (assumed, not built).** Sets the exercise targets (range, hold time, pace, reps). There is no therapist interface; targets arrive as saved plans.
- **Hackathon judges.** Receive a GitHub link, read the README, and most run the simulator (`python3 server.py --sim`) on their own laptop without a brace.

## Product Purpose

Rehabify turns an ordinary knee brace into a rehabilitation assistant. One motion sensor on the shin measures each repetition of a seated knee extension; a vibration motor on the brace clicks when the leg reaches the target and when the hold is complete; the web page shows the movement live and grades every rep on range, pace and hold, then keeps a history of sets.

Success: the patient knows, rep by rep, whether the movement was efficient (full range, steady pace, held at the top), and can see progress between appointments. For the demo: within 60 seconds a judge understands that Rehabify captures every rep and checks its quality, not just its count.

## Positioning

A rep counter says how many. Rehabify says how well, in the moment, through the brace itself: tactile feedback at the target, and a per-rep account of range, timing and hold, from one inexpensive sensor on a brace the patient already wears.

## Operating Context

- A home chair, daylight or a lamp, a laptop on a table or a phone propped against something, often at arm's length or further.
- Single page served by a small Python server on the patient's laptop; the brace connects to it by USB.
- Sessions are short sets of 5 to 10 reps; a day may have several sets.
- The demo is judged from a GitHub repo, a README, and a local run of the simulator.

## Capabilities and Constraints

- One exercise: seated knee extension with the thigh supported and still.
- Angles are an **estimated movement range** from a calibrated rest position, not an absolute knee angle.
- Per rep: peak range, time up, hold time in the target band, time down, peak speed, and a result: good, short of target, rushed, or short hold. An optional trained classifier adds a second label per rep.
- Haptic events: target reached (click), hold complete (double click), set complete (buzz).
- Stack: one static HTML page with vanilla JavaScript, a standard-library Python server, live updates over Server-Sent Events. No build step, no framework.
- Rehabify does not diagnose, prescribe, or measure strength, joint load, ligament stability or walking. Walking analysis is the team's stated vision, not a capability.

## Brand Commitments

- Name: **Rehabify**.
- Voice: warm and human. Encouraging to someone in recovery; never clinical scolding, never hype.
- Craft reference (bar, not look): Apple Fitness activity rings, one iconic live visual that tells you where you stand at a glance.

## Evidence on Hand

- Working signal pipeline with a self-check (`core.py`), a simulator that produces good, short and rushed reps, and a serial path tested against a fake Arduino.
- No real patient data, clinical validation, testimonials or accuracy figures from real use yet. None may be implied. Simulated or sample data must be labelled as such.

## Product Principles

- Feel it now, understand it after: during a rep the leg and the vibration carry the feedback; detail waits until the rep ends.
- Encourage, never scold: a short rep is a little short of the target, not an error.
- Honest numbers: show what was measured; no recovery percentage or invented score.
- One glance: a single live object shows where you are in the rep and in the set.

## Accessibility & Inclusion

Users may be older, in pain, or viewing from a distance: large legible type for the live readouts, high contrast in both light and dark, nothing conveyed by colour alone, visible keyboard focus, reduced motion respected, and rep results announced to screen readers.
