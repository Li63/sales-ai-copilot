# Sales AI OS Product UI Design

## Goal

Redesign the frontend into a sellable, premium B2B SaaS product experience. The system should feel like a professional "销冠 AI 作战 OS", not an internal demo, not a generic CRM, and not a decorative AI showcase.

The first impression must communicate:

- This is a serious sales operating system.
- AI is producing concrete sales judgment, not generic chat.
- Customer intelligence is structured, traceable, and action-oriented.
- A sales team can use this every day to improve conversion, follow-up discipline, and sales playbook quality.

## Product Positioning

### Product Name

Primary product concept: **销冠 AI 作战 OS**

Supporting names inside the product:

- 作战台: the daily command center.
- 客户情报中枢: the intake and evidence layer.
- AI 作战卡: the structured customer analysis output.
- 话术引擎: the sales-script generation area.
- 跟进指挥: the task and next-action area.
- 复盘训练场: the feedback and playbook learning area.

### Target Users

- Frontline sales who need fast customer judgment before and after conversations.
- Sales managers who want standardized follow-up and repeatable sales playbooks.
- New salespeople who need a guided process instead of relying on intuition.
- Business owners who want to see that AI can turn scattered customer materials into practical sales actions.

### Job To Be Done

When a salesperson has a potential customer, they need to quickly understand the customer's real business, intent, pain points, and communication angle, so they can say the right thing, follow up at the right time, and continuously improve the team playbook.

## Core Product Loop

```text
客户资料进入系统
→ AI 识别资料来源和可信度
→ 形成客户画像和企业全方位解析
→ 输出成交机会、痛点、跟进策略、破冰话术
→ 销售执行并记录结果
→ 复盘反馈反哺客户判断和话术库
```

Every primary screen should make one part of this loop obvious.

## Design Principles

1. **Action before explanation**
   The UI should show the next sales action before long analysis text.

2. **Evidence before conclusion**
   AI judgment should be paired with source coverage, confidence, and evidence type.

3. **Sales workflow before data display**
   The interface should follow how salespeople work: identify customer, collect intelligence, judge opportunity, speak, follow up, review.

4. **Premium but restrained**
   The product should feel expensive through clarity, spacing, hierarchy, and confidence, not through noisy gradients or flashy decoration.

5. **Desktop as command center, mobile as action companion**
   Desktop should feel like a serious workstation. Mobile should prioritize copying scripts, uploading screenshots, and quick follow-up.

6. **AI as copilot, not chatbot**
   AI should appear as a decision and execution layer, not as a generic message box.

## Visual Direction

### Brand Mood

- Professional
- Sharp
- Trustworthy
- Intelligent
- Premium
- Calm under pressure

### Avoid

- Cute colors or playful illustrations.
- Marketing landing-page style hero sections inside the app.
- Generic purple AI SaaS styling.
- Too many floating cards without workflow meaning.
- Long AI text walls.
- Dashboard charts that do not directly support sales action.

### Recommended Look

The visual style should combine:

- Enterprise SaaS precision.
- Sales command-center confidence.
- AI intelligence signals.
- Clean Chinese B2B product credibility.

Suggested visual references by feel:

- Linear-like spacing discipline.
- Retool-like operational density.
- Notion-like content clarity.
- Modern CRM command center, but with stronger AI intelligence output.

## Design System Direction

### Color Tokens

Primitive palette:

- Ink Navy: main navigation and authority.
- Arctic Gray: app background and workspace canvas.
- Porcelain White: main panel surfaces.
- Signal Blue: primary AI/action color.
- Deal Green: positive customer opportunity and completion.
- Amber: risk, missing evidence, and attention.
- Slate: secondary metadata and inactive states.

Semantic usage:

- Primary action: Signal Blue.
- Sales success: Deal Green.
- Warning or evidence gap: Amber.
- Navigation background: Ink Navy.
- Workspace background: Arctic Gray.
- Main panels: Porcelain White.
- Borders: cool gray with high clarity.

### Typography

Use a mature Chinese SaaS typography direction:

- Display/title: strong weight, compact letter spacing.
- Body: high readability, no decorative font.
- Metrics: tabular, bold, concise.
- AI conclusions: slightly larger and higher contrast than metadata.

Do not overuse huge title text inside the product. Make the product feel operational, not promotional.

### Shape And Surface

- Desktop panels use small to medium radius, not large mobile-card radius.
- Use crisp borders and subtle shadows.
- Important AI output can use a stronger left accent line or status rail.
- Workflow sections should use step rails, timelines, and source coverage bars.

### Motion

Use motion only when it increases trust:

- AI analyzing material.
- Workflows progressing from evidence to conclusion.
- Action copied successfully.
- Task completed.

Avoid looping decorative animation.

## Information Architecture

### Primary Navigation

Recommended navigation:

1. 作战台
2. 客户情报
3. 画像拆解
4. AI 话术
5. 跟进任务
6. 复盘学习
7. 知识库
8. 设置

The current navigation can be remapped without changing backend APIs:

- 作战 -> 作战台
- 客户 -> 客户情报 or 客户库
- 画像 -> 画像拆解
- 跟进 -> 跟进任务
- 复盘 -> 复盘学习
- 内容 -> 知识库 / 内容增长
- 我的 -> 设置

## Global App Shell

### Desktop Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Left Navigation │ Top Search + Status + Create               │
│                 ├──────────────────────────────┬─────────────┤
│                 │ Main Workspace               │ AI Copilot  │
│                 │                              │ Panel       │
│                 │                              │             │
└──────────────────────────────────────────────────────────────┘
```

Desktop should feel like a real web application:

- Persistent left navigation.
- Top search and action bar.
- Main workspace with strong page hierarchy.
- Right AI panel for context, reasoning, and next action.
- No centered phone-like shell on desktop.

### Tablet Layout

- Navigation can collapse into a left icon rail or top segment.
- AI Copilot panel becomes a collapsible drawer.
- Main content uses two columns where useful.

### Mobile Layout

- Bottom navigation remains.
- Current customer action card comes first.
- AI next action and copyable scripts stay close to thumb reach.
- Upload screenshot / paste material should be a primary action, not buried.

## Core Screens

## 1. 作战台

Purpose: Give the salesperson today's operating plan.

Primary question answered:

> 今天我应该先跟谁，为什么，怎么开口？

Recommended modules:

- 今日优先客户
- 当前重点客户作战卡
- AI 今日建议
- 待补资料
- 待复盘沟通
- 高意向客户预警
- 一键复制破冰话术

Main content order:

1. Today's top recommendation.
2. Current customer battle summary.
3. Next action and copyable script.
4. Tasks grouped by urgency.
5. Recent learning from feedback.

Acceptance criteria:

- A salesperson can identify the first customer to follow up within 5 seconds.
- The page always exposes at least one next action when analysis exists.
- Metrics do not dominate the page unless they directly change today's action.

## 2. 客户情报

Purpose: Turn scattered customer material into structured evidence.

Primary question answered:

> 我还缺哪些资料，上传后系统会怎么看？

Source types must be explicit:

- 抖音主页: account positioning, persona, trust-building style.
- 抖音作品: product scene, copy angle, comment demand, viral content signals.
- 企查查: business reality, scope, risk, scale, credibility.
- 官网/产品页: product line, cases, service objects, delivery capability.
- 朋友圈/截图: personality, trust preference, relationship warmth.
- 聊天记录: verified demand, objection, budget, decision stage.
- 销售观察: offline judgment and relationship context.

Recommended UI:

```text
资料源选择
→ 粘贴链接/上传截图/输入观察
→ AI 识别来源类型
→ 资料覆盖度
→ 进入作战卡生成
```

Important behavior:

- Screenshot upload should feel first-class.
- Douyin share text should be accepted directly.
- Source coverage should be compact and visual.
- Raw source records should be hidden by default.

Acceptance criteria:

- Users can understand what each source type contributes.
- Upload/paste flow feels like a workflow, not a plain form.
- System never claims a source was fetched if it was only pasted or partially resolved.

## 3. 画像拆解

Purpose: Convert evidence into an AI Battle Card.

Primary question answered:

> 这个客户是谁，机会在哪里，我该怎么推进？

Recommended AI Battle Card sections:

1. 企业定位
2. 真实实力
3. 经营阶段
4. 账号/persona
5. 采购动机
6. 成交机会
7. 客户痛点
8. 跟进策略
9. 破冰话术
10. 风险提醒

Each section should include:

- AI judgment.
- Evidence source.
- Confidence or evidence strength.
- Recommended action.
- Copy button where applicable.

Acceptance criteria:

- AI output is scannable without reading a long report.
- Sales can copy a useful sentence directly.
- Weak evidence is visually differentiated from strong evidence.

## 4. AI 话术

Purpose: Generate sales scripts by intent.

Primary question answered:

> 我现在想推进某个动作，怎么说最合适？

Recommended intent categories:

- 破冰
- 催回复
- 约时间
- 询问预算
- 报价解释
- 处理价格异议
- 让客户拉老板
- 推进成交
- 沉默客户唤醒

Output format:

- 推荐话术
- 为什么这样说
- 适用客户类型
- 风险提醒
- 下一句怎么接

Acceptance criteria:

- The user starts from sales intent, not a blank prompt.
- Each script is copyable.
- Explanations are short and operational.

## 5. 跟进任务

Purpose: Make follow-up visible and executable.

Primary question answered:

> 哪些客户不能拖，下一步做什么？

Recommended task groups:

- 今天必须跟
- 高意向待推进
- 资料待补齐
- 沉默客户唤醒
- 已成交待复盘

Task row/card should include:

- Customer name.
- Intent level.
- Last contact.
- AI next action.
- Copy script.
- Mark followed.

Acceptance criteria:

- Tasks are grouped by urgency.
- Each task has one clear action.
- Completing a task updates visible state.

## 6. 复盘学习

Purpose: Turn sales outcomes into a better playbook.

Primary question answered:

> 这句话有没有用，下次系统应该怎么改？

Recommended flow:

```text
选择使用过的话术
→ 记录客户反馈
→ 标记效果
→ 输入销售判断
→ AI 总结经验
→ 反哺话术库和客户判断
```

Acceptance criteria:

- Feedback entry is lightweight.
- Good and bad outcomes both produce learning.
- Lessons are visible in future recommendations.

## 7. 知识库

Purpose: Keep company, industry, product, and sales guidance available to AI.

Recommended groups:

- 公司资料
- 产品资料
- 成功案例
- 行业销售指南
- 基础话术库
- 内容/IP 素材

Acceptance criteria:

- Sales can see which knowledge is active.
- Admin can manage company-level material.
- AI recommendation clearly benefits from this context.

## Role-Based Experience

### Sales User

Default experience:

- 作战台
- 当前客户
- 情报上传
- 话术复制
- 跟进记录
- 复盘学习

### Tenant Admin

Default experience:

- Sales account management.
- Company material management.
- Approval and knowledge-base status.
- Team overview.

Tenant admin UI should look like an admin console, not the sales battle interface.

### Platform Admin

Default experience:

- Tenant management.
- Tenant admin creation.
- Tenant status and system-level governance.

Platform admin UI can remain operational and simple, but should share the same design tokens.

## Right AI Copilot Panel

The right panel should become a stable product signature.

Recommended structure:

- AI conclusion.
- Why this matters.
- Evidence used.
- Missing evidence.
- Recommended next action.
- Copyable script.

Panel states:

- No customer selected.
- Material missing.
- Analysis ready.
- AI processing.
- Risk/low confidence.

The panel should never feel like a generic chat sidebar. It is a decision assistant.

## Empty States

Empty states must sell the workflow:

- No customer: "先创建或选择客户，系统会生成客户作战卡。"
- No source: "上传抖音主页、企查查或聊天截图，AI 会判断客户机会。"
- No analysis: "导入聊天记录或客户资料后生成第一版判断。"
- No follow-up: "保存一次跟进后，系统会帮你安排下一次动作。"
- No feedback: "记录客户反馈后，话术会越来越贴近你的行业。"

Empty states should include a primary action.

## Commercial First Impression

The product should feel valuable in screenshots and demos.

Demo-ready first screen should show:

- A named customer.
- A high-value AI conclusion.
- Evidence coverage.
- Deal opportunity.
- One copyable script.
- One next follow-up action.

Avoid showing a blank system in sales demos.

## Success Metrics

Product success:

- Sales can generate a useful next action faster.
- Sales uploads more customer evidence.
- Follow-up completion rate improves.
- More customer feedback is recorded.
- Reply suggestions become more specific over time.

UI success:

- First-time users understand the system's core value within 10 seconds.
- Desktop no longer looks like a stretched mobile app.
- The customer intelligence workflow is discoverable without explanation.
- Users can copy an AI-generated sales script in under 3 clicks.
- Uploaded screenshots and pasted links clearly lead to analysis output.

Guardrails:

- Do not hide core sales actions behind decorative visuals.
- Do not make desktop too sparse.
- Do not make mobile too dense.
- Do not claim AI evidence that the backend did not actually retrieve or analyze.
- Do not disrupt existing backend APIs during the UI redesign.

## Implementation Strategy

### Phase 1: Design System Reset

- Define global design tokens in `frontend/src/styles/base.css`.
- Establish desktop shell, mobile shell, panels, buttons, badges, source coverage, AI conclusion blocks.
- Remove inconsistent one-off styling where possible.

### Phase 2: App Shell And Navigation

- Redesign `App.vue` into a stable Sales AI OS shell.
- Rename navigation labels conceptually.
- Make right AI Copilot panel a reusable layout pattern.
- Keep existing Vue state and store methods.

### Phase 3: Core Sales Screens

Prioritize:

1. 作战台 / RecommendationTab
2. 客户情报 + 画像拆解 / ProfileTab
3. 跟进任务 / FollowTab
4. 复盘学习 / feedback area

### Phase 4: Admin And Knowledge Areas

- Align tenant admin, platform admin, and knowledge panels with the same design system.
- Keep admin pages clear and less dramatic than the sales command center.

## Technical Constraints

- Keep Vue 3 + Vant + custom CSS for now.
- Do not introduce a large UI framework unless separately approved.
- Keep existing backend APIs compatible.
- Keep mobile support.
- Server deployment must only touch `/data/sales-ai/app`.
- Do not recreate MySQL or Redis during deployment.

## Acceptance Criteria For The Redesign

- Desktop at 1440px and 1920px feels like a polished commercial SaaS product.
- Mobile at 390px remains easy for salespeople to copy scripts and upload screenshots.
- Customer intelligence flow is visually central and easy to explain in a demo.
- AI Battle Card is stronger than raw AI text output.
- Right AI Copilot panel consistently shows conclusion, evidence, missing context, and next action.
- Build passes with `npm run build`.
- Browser screenshots are checked for desktop, tablet, and mobile.
- Deployment preserves `.env`, `certs`, `outputs`, `work`, `.agents`, `.codex`.
- Deployment does not change MySQL/Redis container IDs.
