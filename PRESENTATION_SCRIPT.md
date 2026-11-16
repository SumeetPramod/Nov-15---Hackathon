# Rehabify presentation script

About 3 minutes. **Bold** is what to click or show; normal text is what to say. Run the demo on the simulator (`python3 server.py --sim`) unless the brace is working reliably, and have the brace on camera or in hand either way.

---

## 1. The problem (0:00–0:20)

After a knee injury, most of your rehab happens at home, alone. Your physio gives you a sheet: straighten your knee, hold it, ten times. But nobody is there to tell you whether you actually reached the target, whether you rushed it, or whether you held it. A rep counter tells you how many. Nobody tells you how well.

## 2. What Rehabify is (0:20–0:40)

**Hold up the brace.**

Rehabify turns an ordinary knee brace into a rehab assistant. One motion sensor on the shin, a small vibration motor on the thigh, an Arduino, and a Raspberry Pi that runs everything and serves this page to any laptop or phone on the network.

## 3. Live demo (0:40–1:50)

**First screen.** The figure is drawn like a page from an anatomy atlas. It labels the two pieces of hardware: the motion sensor and the vibration motor.

**Click Set rest position.** First it learns where your leg rests. Every angle is measured from here.

**Today's plan appears.** The plan comes from the physio, in one sentence: straighten to 50 degrees, hold for 2 seconds, 5 times. The red line on the figure is the target.

**Press Good rep.** Watch the leg. When it passes the red line, the brace clicks. The ring around the knee fills while you hold. A double click when the hold is done.

**Press Stop short.** This one didn't reach the line. Rehabify says so, kindly: "just short of the red line, ease a little further next time." It never shows a poor rep in red. Someone in pain doesn't need to be scolded.

**Press Rush it.** This is the one I want you to look at. Those faint lines are the lift, drawn a quarter of a second apart, like old stop-motion photographs. A controlled rep leaves eight close lines. A rushed rep leaves two, far apart. You can see speed on the figure without reading a word.

**Finish the set.** At the end, every rep is drawn at its peak, and the summary says what went well and what to work on.

**Scroll to Your progress.** And between physio appointments, you can see your range improving day by day. The hollow points are clearly labelled sample data; your own sets follow them.

## 4. How we measure it (1:50–2:10)

The sensor gives us acceleration and rotation. Gravity tells us which way is down, the gyroscope tells us how fast the shin is turning, and we combine the two so the angle is both stable and quick. Because the thigh stays still, the shin's rotation is the knee's movement. In simulation the estimate stays within a quarter of a degree, even with the sensor mounted at an angle.

Every rep then gets three checks: did it pass the line, was the pace steady, did it hold.

## 5. Machine learning with scikit-learn (2:10–2:50)

Those three checks are rules we wrote. We also wanted to see whether a model could learn what a good rep looks like from examples, so we built a training pipeline with scikit-learn.

We defined three kinds of rep:

- **A good rep:** smooth and controlled. It passes the red line, takes at least a second on the way up and on the way down, and holds for the full hold time.
- **A mid rep:** controlled, but it stops partway. Steady pace, not enough range: it doesn't reach the line.
- **A bad, rushed rep:** jerked up and dropped. It might reach the line, but the lift takes well under a second and the hold barely happens.

**Show the plan step with `?train` in the address.** We recorded sets with the brace and tagged each one as good, mid or rushed. Every rep becomes six numbers: how far it went, how long the lift took, how long it held, how long the lowering took, and its peak and average speed.

We trained a random forest from scikit-learn on those numbers. And we were careful about one thing: we split the data by whole recording sessions, 80 percent for training and 20 percent for testing. Reps from the same recording look almost identical, so if they ended up on both sides, the score would look better than it really is.

> **If you recorded real sets, say:** On sessions it had never seen, the model classified **[XX] percent** of reps correctly. Its most useful clue was **[the top feature from train.py]**.
>
> **If you did not, say:** We've validated the pipeline end to end on the simulator; recording a proper set of real reps from several people is our next step, and we'd rather show you that number honestly than make one up.

**If a model is loaded, point at a rep result.** The model's opinion appears next to each rep, "Model: a bit quick", but the rules stay in charge. The model is a second opinion, not the judge.

## 6. Honest scope and what's next (2:50–3:10)

Rehabify doesn't diagnose anything, and it doesn't replace a physio. It reports an estimated range of movement from where you started, for one exercise, done seated. Next, we want to take the same sensor into walking, and give the physio a way to set targets remotely.

## 7. Close (3:10)

A rep counter tells you how many. Rehabify tells you how well, while you're doing it, through the brace itself. Thank you.

---

## Before you present

- [ ] Start the server and open the page at full screen. Do one practice run, then restart the server so the demo starts on the first screen.
- [ ] Brace charged, connected and visible on camera.
- [ ] If you want the model labels on screen, `model.pkl` must exist and the server must be restarted after training.

### The 15-minute training run (only if the brace works)

1. Open `http://rehabify.local:8000/?train` (or `localhost:8000/?train`).
2. On the plan step, open **Record training data** and pick a label. In the code, *good* is `controlled`, *mid* is `short` and *rushed* is `rushed`.
3. Record at least 2 sets of 5 reps for each label. More sets, and more than one person, make a more honest test.
4. Run `python3 train.py` (on the Pi: install scikit-learn with `sudo apt install python3-sklearn`).
5. Put its test accuracy and its top feature into section 5, then restart the server.

## Likely judge questions

- **How accurate is the angle?** Within a quarter of a degree in simulation; on the real brace, check it against a phone level app before the demo and quote what you see.
- **Why not just use the rules?** The rules work and stay in charge. The model is there to learn patterns that are hard to write as rules, such as a jerky lift that technically passes every threshold.
- **Why a random forest?** Small tabular data with six features. A random forest trains in seconds, needs no tuning to be reasonable, and tells us which features mattered.
- **What stops it overfitting?** The split is by whole session, not by rep, so the test set is recordings the model has never seen.
- **Does it work without the hardware?** Yes: the simulator runs the same measurement code, which is how anyone can try it from the GitHub link.
