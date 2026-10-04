---
name: feedback-tibetan-review-format
description: "When asking the user to review/correct Tibetan Unicode strings, use a table document, not inline chat questions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9ea9e228-eb1f-4f7a-aada-2d55d6901962
  modified: 2026-09-07T17:08:44.228Z
---

Never use inline chat multiple-choice questions (e.g. AskUserQuestion) to ask the user to
confirm or correct Tibetan Unicode text. Instead, create an RTF or LibreOffice/Word document
with a table: one column showing the item being reviewed (e.g. a Dedris font key + the current
best-guess Tibetan), and a second blank column for the user to type the correct Tibetan into.

**Why:** the terminal's multiple-choice question UI garbles/overwrites itself when the choices
contain Tibetan text, discovered while reviewing [[project_kama_pipeline_state]]'s Dedris
vowel-mapping corrections — the user had to explicitly redirect away from chat-based review
partway through.

**How to apply:** any review step involving Tibetan strings in this repo (`tibetan_text_scripts`)
should default to a document-with-a-fill-in-column workflow. This likely generalizes to any
non-Latin/complex-script text the user needs to review character-by-character, not just Tibetan
specifically — be alert for the same garbling risk with other scripts too.
