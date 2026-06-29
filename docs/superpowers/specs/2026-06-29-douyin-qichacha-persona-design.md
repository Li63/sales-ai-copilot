# Douyin And Qichacha Persona Enrichment Design

## Goal

Add a practical customer persona enrichment workflow where sales users can paste or upload company research, Qichacha-style business material, Douyin profile links, Douyin home page notes, short-video summaries, comments, screenshots, PDFs, or Word files. The system should turn those materials into a more detailed customer profile and use that profile to improve reply suggestions, follow-up angles, and sales playbooks.

This version does not build automatic Douyin or Qichacha crawlers. Sales users provide the material manually, and the AI analyzes only the provided content. This keeps the feature stable, avoids login and anti-scraping fragility, and respects authorization boundaries.

## Product Scope

### In Scope

- Let sales save customer persona sources with explicit source types:
  - `douyin_profile`
  - `douyin_content`
  - `qichacha`
  - `website`
  - `manual`
- Let sales paste a source URL or original link when available.
- Let sales paste structured notes, upload screenshots, upload PDFs, or upload Word files.
- Summarize each source into actionable sales signals:
  - business stage and operating clues
  - content style and positioning
  - customer concerns and likely decision logic
  - communication preference
  - suggested opening angle
  - risk reminders
- Merge recent persona source summaries into the long-running `customer.persona_profile`.
- Feed richer persona context into:
  - `/api/analysis/realtime`
  - `/api/analysis/intent-reply`
- Upgrade the default shared sales playbook with Douyin-inspired sales content patterns:
  - hook first, then scene
  - pain point before product
  - evidence instead of hard claims
  - light conversion instead of pressure
  - private-domain handoff after content interest
- Update the software guide so sales know how to use Douyin and company research material.

### Out Of Scope

- Automatic Douyin crawling.
- Automatic Qichacha crawling.
- Ranking or verifying the public "top 10 Douyin sales creators".
- Storing videos or large media files.
- Guaranteeing that inferred persona signals are facts. The UI and prompt must present them as sales hypotheses grounded in uploaded material.

## Existing System Context

The current system already has useful foundation:

- `PersonaSource` stores customer-specific materials and `persona_summary`.
- `Customer.persona_profile` stores long-running persona memory.
- `LLMService.analyze_persona_source()` produces a compact sales-facing summary.
- `/api/persona/source/add` saves material and refreshes the profile.
- `ProfileTab.vue` has a customer persona material upload area.
- `SalesKnowledgeService.DEFAULT_SALES_PLAYBOOK` feeds shared sales technique guidance into realtime analysis.
- `CompanyMaterialPanel.vue` already handles product and company knowledge separately from customer persona material.

The improvement should extend these pieces instead of creating a parallel subsystem.

## Data Model

Add `source_url` to `PersonaSource`.

`PersonaSource.source_type` remains a string so this can ship without enum migrations. The API validates allowed values at the boundary and defaults unknown values to `manual`.

Source type meanings:

- `douyin_profile`: customer or company Douyin homepage, bio, positioning, follower-facing claims, pinned content summary.
- `douyin_content`: short-video titles, scripts, comments, interaction patterns, content themes.
- `qichacha`: company registration, business scope, risk clues, financing, legal, recruitment, or ownership notes copied from public/company research.
- `website`: official website, landing page, product page, media report, or other public web material.
- `manual`: sales user's own observation or offline research notes.

## Backend Design

### API Request

Extend `PersonaSourceRequest`:

```python
class PersonaSourceRequest(BaseModel):
    sales_userid: str
    external_userid: str
    content: str
    source_type: str = "manual"
    title: str | None = None
    source_url: str | None = None
```

Validation:

- Trim `content` to 7000 characters.
- Trim `source_url` to 500 characters.
- Allow only known source types; otherwise use `manual`.
- Reject empty `content` after trimming.

### LLM Prompt

Upgrade `PERSONA_ANALYSIS_PROMPT` so the model distinguishes source types. It should output JSON with these fields:

- `summary`
- `business_clues`
- `content_positioning`
- `communication_style`
- `decision_logic`
- `follow_angle`
- `risk_warning`
- `sales_tip`

The formatter should produce compact Markdown-style lines for the UI. If upstream parsing fails, the fallback should still mention the source type when possible.

### Persona Merge

Update `_refresh_customer_persona()` to group recent source summaries by source type. The merged profile should include:

- latest update date and source count
- a warning that these are hypotheses, not verified facts
- recent source highlights
- practical sales use guidance

The merged profile should remain capped at 3000 characters.

### Analysis Context

Update `_persona_sources()` to include `source_url`, `source_type`, `title`, and `persona_summary`. The realtime and intent-reply prompts already accept `persona_sources`, so no new endpoint is required.

## Frontend Design

Update `ProfileTab.vue` customer persona material area:

- Add a source type segmented control or select.
- Add source URL input.
- Update placeholders for Douyin and Qichacha use cases.
- Submit `source_type`, `source_url`, `title`, and `content`.
- In the source list, display a readable type label and URL when present.

The UI should stay compact because this is an enterprise WeChat sidebar. No large landing-page style redesign is needed.

Update `sidebar.ts`:

- Add `source_url` to `PersonaSource`.
- Add `source_url` to the `addPersonaSource` payload.
- Allow `extractFiles()` purpose to keep using the existing `persona` path.

## Sales Playbook Update

Upgrade the default sales playbook with a new section:

`## 抖音内容销售打法`

The section should teach sales how to learn from Douyin content without copying blindly:

- 3-second hook: name the customer's common stuck point.
- Scene first: speak from the customer's daily situation.
- Evidence chain: use cases, screenshots, numbers, process, comparison, or customer language.
- Soft conversion: invite a small next step instead of forcing a deal.
- Comment mining: collect customer objections from comments and turn them into follow-up questions.
- Private-domain handoff: after content interest, move to WeChat with a specific resource, checklist, or case.

Also add a short warning: do not fabricate rankings, data, or creator claims that have not been uploaded or verified.

## Product Manager Roadmap

Next requirements to consider after this MVP:

1. Source quality scoring: mark sources as strong, medium, or weak evidence.
2. Persona contradiction detection: warn when Douyin material and chat behavior conflict.
3. Follow-up task suggestions from source type: for example, Qichacha risk clue becomes "send compliance/after-sales proof".
4. Tenant-level approved research templates: admins define what sales should collect for each industry.
5. Douyin content library: sales save reusable content hooks and map them to customer objections.
6. Review queue for sensitive materials in regulated industries.

## Project Manager Plan

Implementation should be split into three small tasks:

1. Backend persona source type and URL support, including tests.
2. Prompt, persona merge, and sales playbook upgrade, including tests.
3. Frontend persona source form and display upgrade, including build verification.

Each task should be independently testable and committed separately where practical.

## Full-Stack Engineering Notes

- Keep the current `PersonaSource` table and endpoint.
- Avoid adding a scraping dependency or browser automation dependency.
- Avoid changing authentication behavior.
- Keep the feature useful even when the LLM call fails by improving fallbacks.
- Use UTF-8 for Chinese prompt and guide text.
- Preserve the existing compact sidebar information architecture.

## Testing

Backend tests should cover:

- request payload supports `source_url`
- unknown source type falls back to `manual`
- LLM persona payload includes source type and URL
- formatted persona analysis includes Douyin/Qichacha-specific fields
- sales playbook includes the Douyin content sales section

Frontend verification should cover:

- TypeScript build accepts new fields.
- Persona form can submit source type and URL.
- Existing file upload flow still appends extracted text.

## Success Criteria

- A sales user can add a Douyin profile/content or Qichacha material to a customer.
- The saved material appears in the customer persona source list with type and URL.
- The customer profile becomes more detailed and explicitly sales-actionable.
- Realtime reply suggestions use the enriched profile context.
- The shared sales playbook includes updated Douyin-inspired sales technique guidance.
- The app remains runnable through existing backend tests and frontend build.
