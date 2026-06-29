# Customer Intelligence Core Redesign

## Problem

The current customer persona workflow looks like a form, but the core intelligence loop is broken:

- Uploaded screenshots were reduced to OCR/extracted text before persona analysis, losing page layout, account context, comment structure, and visual evidence.
- Douyin links are stored as `source_url`, but the system does not turn Douyin share text into structured evidence.
- Different sources are mixed together, even though Douyin, Moments, Qichacha, website, and chat records represent different levels of truth.
- Long source records take space from the core analysis.

## Product Direction

Rename this area conceptually to "客户情报中枢". Its job is not to store files; its job is to turn scattered customer evidence into an actionable sales battle view.

## Source Layers

- Douyin profile: account positioning, boss IP, product selling points, trust-building style.
- Douyin content: video title, tags, product scene, comment pain points, demand clues.
- Moments/manual observation: personality, values, relationship warmth, communication preference.
- Qichacha: enterprise reality, business scope, operating stage, risk, scale, recruitment, credibility.
- Website/public material: product line, cases, service objects, delivery capability.
- Chat records: verified demand, budget, objection, decision stage.

## UX Changes

- One intake card: paste link/share text, upload files, or paste notes.
- System infers source type from link/text where possible.
- Screenshot upload saves and analyzes automatically through a direct multimodal endpoint; Word/PDF/text files still use text extraction.
- Douyin share text is parsed into evidence sections before LLM analysis.
- Source records are hidden by default; show only compact source coverage.

## Analysis Output

The top output becomes "企业全方位解析":

- Enterprise positioning
- Strength and credibility
- Account/personality clues
- Purchase motivation
- Deal opportunity
- Risk warnings
- Follow-up strategy
- Copyable icebreaker script

## Constraints

- Keep the existing Vue 3 + Vant frontend stack.
- Keep the existing `/api/persona/source/add` API path compatible.
- Do not claim Douyin page contents were fetched when only share text/link was parsed.
- Do not collapse screenshots into OCR-only text when a vision model is available; screenshots are the primary source for most sales users.
- Server deployment may only touch `/data/sales-ai/app`.
