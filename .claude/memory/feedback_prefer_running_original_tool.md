---
name: feedback-prefer-running-original-tool
description: "When reverse-engineering a proprietary format/tool is going poorly, check whether the original tool can just be run (even via a compatibility layer) before investing further in the from-scratch approach"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a374b143-cce1-46ef-8f09-e5e6a6aa97a1
  modified: 2026-09-08T15:35:53.306Z
---

When a from-scratch reverse-engineering effort (statistical inference, OCR, manual table
building, etc.) is fighting hard for marginal accuracy against a legacy proprietary tool's
output format, stop and check whether the *original tool* can just be run directly — even on
an unsupported platform via a compatibility layer (Wine, CrossOver, a VM) — before sinking more
effort into approximating it from scratch.

**Why:** in [[project-dedris-conversion]], two full approaches (frequency-rank statistical
matching, then OCR-based glyph recognition) were tried and abandoned trying to reverse-engineer
`udp.exe`'s Dedris-font keystroke mapping, before the user asked "can we just run the .exe" —
CrossOver's free trial ran it directly on the Mac, and it turned out to have its own real
conversion tables sitting in a trivially-parseable plain-text format the whole time. Both
earlier approaches were real effort that produced a worse answer than what was available for
free by just running the tool.

**How to apply:** when starting to reverse-engineer a legacy/proprietary format, surface "can
we just run the real tool via a compatibility layer" as an option early — ideally before, not
after, investing in a from-scratch approximation. This is especially worth raising when the
tool is a lightweight Windows GUI utility (cheap to try via Wine/CrossOver) rather than
something requiring a full OS/hardware environment.
