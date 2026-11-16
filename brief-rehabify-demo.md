# Rehabify's hackathon demo experience

## Context
After a knee injury or surgery, most rehabilitation happens at home, between physiotherapy appointments. The patient is handed a short list of exercises (here: seated knee extensions) with targets for range, hold time and reps, and does them alone. Rehabify puts one motion sensor and a vibration motor on an ordinary knee brace, and a web dashboard shows each rep as it happens.

The people judging this build will receive a GitHub link. Most will read the README and run `python3 server.py --sim` on a laptop with no brace attached. The simulator is therefore the product they experience; the brace appears in photos and video.

## Gap
A rep counter tells you how many; it does not tell you whether each one was done well. At home the patient cannot see whether they reached the prescribed range, rushed the movement, or skipped the hold, and the physio only hears "I did them." Nothing in the current dashboard makes that difference felt within the first minute: it opens on a setup form, the simulated leg moves on its own, and every rep looks the same unless you find a dropdown in the header.

## Opportunity
The core mechanism works: the angle estimate tracks within a fraction of a degree in simulation, and each rep is graded on range, pace and hold. The opportunity is presentation. If a judge can perform a good rep, a short rep and a rushed rep themselves and watch Rehabify respond to each one differently, the product's claim proves itself without a word of pitch.

## Goals
- In 60 seconds a judge understands: Rehabify captures every rep and tells you whether the movement was efficient: full range, steady pace, held at the top.
- The experience feels warm and human: encouraging to someone recovering, never clinical scolding.
- One live visual carries the session at a glance, the way Apple's activity rings carry a day.
- A complete demo path runs on the simulator with no hardware, and the same screens run with the real brace.
- Every state on that path is designed: first run, not calibrated, calibrating, ready, exercising, rep feedback, set complete, brace disconnected, server offline, empty history.

## Constraints
- About four hours remain. The stack is fixed: a single static HTML page with vanilla JavaScript, served by a standard-library Python server. No build step, no framework, no new dependencies.
- Judges run it locally from a clone, on unknown laptops and browsers. It must also work on a phone held next to the patient.
- One exercise only: seated knee extension with the thigh supported. Walking analysis is the stated vision, not a feature.
- Rehabify measures and gives feedback; it does not diagnose or prescribe. Angles are an estimated movement range from the rest position, not an absolute knee angle.

## Guiding Principles
- **Feel it now, understand it after.** During a rep, the visual and the vibration carry the feedback; detail waits until the rep is done.
- **Encourage, never scold.** A short rep is "a little short of your target," not a red error.
- **Honest numbers.** Show what was measured (range, timing, hold), never an invented recovery score.
- **One glance.** A single live object tells you where you are in the rep and in the set.

## Key Assumptions & Open Questions
- Assumption: judges will run the simulator rather than only read the README. The README's first screen and screenshots still need to stand alone.
- Assumption: letting the judge trigger each simulated rep (good, short, rushed) is clearer than a simulator that moves on its own. To confirm with the team.
- Open: should a judge who clones the repo see sample history so the progress view isn't empty on first run? If so, it must be labelled as sample data.
- Open: Does the training-label control belong in the main flow, or in a secondary "record training data" mode?

## Proposed Scope (Phase 1)
In: one page that walks through calibrate, choose plan, exercise with live feedback, rep-by-rep results, set summary, and progress against previous sets; simulator controls designed into the page; all states above; phone, tablet and desktop layouts in light and dark mode; README hero.
Deferred: walking analysis, therapist accounts, multiple exercises, profile management beyond picking and adjusting a plan, the classifier's training workflow polish.
