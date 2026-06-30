# Sales Battle UI Workflow Design

## Context

The current product is a Vue 3 + Vant mobile-first sales copilot. The user asked for a better looking UI after the first "sales war room" refresh, plus two concrete product upgrades:

- Turn customer material upload, Douyin homepage links, and Qichacha material into a clearer workflow form.
- Turn AI persona output into stronger sales battle cards: deal opportunity, customer pain, follow-up strategy, and icebreaker script.

## UI References

GitHub research pointed to four relevant directions:

- `vue-vben-admin`: mature Vue admin architecture and dense dashboard layout.
- `Soybean Admin` / `Vue Naive Admin`: cleaner Vue admin visual language with light cards and refined spacing.
- `shadcn-vue`: modern component feel, strong tokens, simple cards, direct hierarchy.
- `Vuestic Admin`: complete dashboard structure but heavier visual and dependency footprint.

The project should not replace Vant right now. A full UI framework migration would add dependency risk and slow product iteration. This slice borrows the visual patterns: clean cards, light background, clearer hierarchy, step indicators, and action-first panels.

## Product Decision

The "customer panorama" tab becomes the core customer intelligence workflow:

1. Select material source: Douyin homepage, Douyin content, Qichacha, website, or sales observation.
2. Add source URL and upload images, Word, or PDF.
3. AI analyzes the material and stores source summaries.
4. The customer profile renders actionable battle cards.

## Battle Cards

The AI output is structured into:

- Deal opportunity: why this customer may be worth approaching now.
- Customer pain: what the customer likely cares about or fears, expressed as a sales hypothesis.
- Follow-up strategy: next conversational angle and cadence.
- Icebreaker script: low-pressure wording the salesperson can copy.

The UI must support old persona data by extracting matching labels from existing text and falling back to realtime analysis fields.

## Engineering Scope

- Keep Vue 3, Vant, and existing API contracts.
- Update frontend profile UI only where the workflow and cards live.
- Update LLM persona prompt and fallback formatting so future analyses include battle-card labels.
- Keep server deployment safety rule: only touch `/data/sales-ai/app` for this project.

## Acceptance

- `npm run build` passes.
- Persona and LLM tests pass.
- Mobile layout has no horizontal overflow.
- User can save source URL, source type, uploaded text, and pasted material in one workflow panel.
