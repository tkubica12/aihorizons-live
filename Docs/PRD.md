# Pizza company AI assistants - PRD (draft)

## Goal and success

- **Problem and target users:** Customers need a simple way to learn about pizzas and place or follow an order. Staff need to answer operational questions and coordinate preparation, delivery and complaints without switching between simulated back-office systems. The product consists of a Czech-speaking customer assistant embedded in a simulated e-shop and a Czech-speaking staff assistant in Microsoft Teams.
- **Desired outcome:** Demonstrate connected AI conversations over product knowledge and business processes, including a customer request that creates a record visible to staff and a staff action that changes what the customer can see. The focus is AI behavior and process orchestration, not building a production e-commerce or logistics platform.
- **Definition of done for milestone 1:** Using seeded demo data, a reviewer can ask the web assistant about ingredients, declared allergens, pizza stories and wine pairings, and the assistant distinguishes authoritative product records from editorial recommendations. It states when information is unavailable instead of guessing. Ordering, delivery and complaints are not required for this milestone.
- **Staff-agent technical slice (read-only):** A reviewer can query recent orders across all fictional customers through a separate staff MCP and a Python/LangGraph hosted agent in Foundry. The staff agent reuses catalog and knowledge tools in its own Foundry toolbox, not the customer toolbox. A second LangGraph demo agent says hello in Azure Container Apps and is registered in Foundry as external for trace monitoring. This slice does not implement the Teams channel or staff write operations.
- **Definition of done for the eventual end-to-end demo:** A reviewer can also place an order and obtain an order ID, see it in the staff workflow, assign an available simulated courier, check delivery status from the customer assistant and file a complaint that staff can assess and escalate. No assistant may invent a transaction or silently claim an unsuccessful action succeeded.
- **Out of scope:** Real authentication/OAuth, real payments, live courier tracking, route optimization, a full e-shop, integration with a real POS/ERP or carrier, and unsupervised financial or safety-critical decisions. Demo identities and back-office data are simulated; the solution must not be presented as suitable for real customer data or production use without further controls.

## Delivery milestones

- **Milestone 1 - product knowledge:** Seed a small catalog, structured recipes/allergens and editorial pizza data sheets; expose trustworthy Czech-language answers in the web assistant. Keep the content model reusable by later workflows. Teams and transactional back-office functions are not required yet.
- **Milestone 2 - ordering and staff operations:** Add simulated customer profiles, order creation/status, staff order queue and preparation updates in Teams.
- **Milestone 3 - delivery:** Add simulated courier availability, assignment, delivery status and exceptional handling across both assistants.
- **Milestone 4 - complaints:** Add customer complaint intake, policy-guided staff assessment, human escalation and decision traceability.
- These are proposed boundaries, not fixed dates; later milestones can be combined or narrowed after the preceding one is demonstrated.

## Business domain

- **Actors:** Customer; staff member handling orders and dispatch; kitchen staff; complaint reviewer or manager; simulated courier/carrier. One employee may play multiple roles in the demo.
- **Records:** Pizza catalog (name, description, price, size/options, availability), recipe and ingredients, declared allergens, editorial pizza data sheets (story, origin, wine pairing and rationale), demo customer profile, order and line items, delivery assignment and status, complaint and decision, and a versioned complaint policy. Profiles contain only fictional data and may include addresses, preferences and order history needed for the demo.
- **Source-of-truth rules:** Structured catalog/recipe/allergen and availability records determine transactional facts; the editorial knowledge base supplies narrative and pairing suggestions, never overrides allergens, price or availability. Orders, assignments and complaints have persistent IDs and traceable status changes. If records conflict or required facts are missing, the assistant states the uncertainty and routes the question to staff rather than guessing.
- **Order flow:** Draft -> confirmed -> preparing -> ready -> dispatched -> delivered; cancellation or failure are explicit exceptional outcomes. The customer confirms items, quantity, delivery address and shown total before the order becomes confirmed. Stock/availability is checked again at confirmation; a failed write must not return a confirmation or order ID.
- **Delivery flow:** An eligible simulated courier/carrier is selected or assigned by staff based on availability and service area; the assignment is visible with the order, and status changes are shared with the customer. Estimated times are labeled estimates, not live tracking. If no courier can be assigned, the order remains unassigned and staff receive an actionable exception.
- **Complaint flow:** A customer supplies an order reference, issue and requested resolution. A policy provides criteria, evidence requirements, possible outcomes and escalation limits. An assistant may summarize the case and recommend an outcome with reasons; final actions with financial impact or exceptions require staff approval. A configurable repeated-complaint threshold (e.g. five recent complaints by one demo customer) triggers human review rather than automatic rejection. The counting window and exact threshold remain product decisions.
- **Demo boundaries:** Customer identity is selected from seeded profiles rather than authenticated. Backend records must remain consistent across both assistants for a demo run; courier availability, dispatch and kitchen events may be simulated but must be labeled as such. The same seeded scenarios must support repeatable walkthroughs.

## Capabilities

| Priority | Capability / user story | Acceptance criteria |
| --- | --- | --- |
| Must | As a customer, I can ask what a pizza contains and whether it includes a named allergen. | Answers use the current structured recipe/allergen declaration, name the relevant pizza and distinguish declared facts from missing or uncertain information; no unsupported "allergen-free" assurance is given. |
| Must | As a customer, I can ask about pizza history and wine pairings. | Answers use available editorial data, make the pairing a recommendation rather than a fact about safety, and say when there is no sourced pairing or story. |
| Must | As a customer, I can build and confirm a delivery order conversationally. | The assistant presents items, quantities, price/total and address for explicit confirmation, checks availability and creates one order with an ID; invalid inputs or failed creation yield an explicit error, not a success message. |
| Must | As a customer, I can check my order and delivery progress. | A known order ID returns its current recorded status and assignment/estimate where available; an unknown ID gives a clear not-found response. In the demo the selected customer profile determines which orders are visible. |
| Must | As staff in Teams, I can ask for open orders and update preparation status. | The assistant lists orders requiring action with IDs and timestamps; an authorized demo staff action records a valid transition that is visible to the customer assistant. Invalid transitions are rejected explicitly. |
| Must | As dispatch staff in Teams, I can see available simulated couriers and assign one to a ready order. | The assistant shows service area/availability, prevents incompatible or duplicate active assignments, records the assignment and exposes unassigned orders for manual follow-up. |
| Must | As a customer, I can submit a complaint about an order. | A complaint receives an ID linked to an order and issue; it is visible to staff, and the customer receives a truthful status without a promised refund or outcome. |
| Must | As complaint staff in Teams, I can review a complaint and the applicable policy. | The assistant presents order context, relevant criteria, complaint history and a reasoned recommendation; it flags threshold/exception cases for human review and records a staff decision separately from the recommendation. |
| Must | As an operator, I can maintain a small, consistent demo dataset. | Catalog, recipes, allergen declarations, editorial sheets, profiles, courier availability, orders and complaints have seeded fixtures; edits to transactional records are reflected in both assistant channels during the demo. |
| Should | As staff, I can ask operational questions about ingredients, pizza preparation and stock/availability. | Answers distinguish current structured facts from editorial guidance and identify unavailable or unknown stock instead of promising fulfillment. |
| Should | As staff, I can triage today's workload and exceptions. | The assistant summarizes open orders, unassigned deliveries and complaints needing a human decision, with IDs linking each item to its underlying record. |
| Could | As a customer, I can update or cancel an order before preparation passes a configured point. | The assistant states the eligibility rule, requests confirmation and records the change or explains why it is not allowed. |
| Could | As staff, I can inspect simple aggregate trends such as popular pizzas and complaint categories. | Counts come from seeded business records over a stated time range and exclude invented conclusions. |

## Non-functional requirements

- **Channel consistency:** Customer web chat and staff Teams chat use the same business records and policy version. Any action that changes state returns the updated ID/status or an explicit failure. Conversations remain understandable in Czech; internal prompts may be English.
- **Knowledge quality:** Every factual answer about ingredients, allergens, price and availability is grounded in an identified current record. Narrative answers and recommendations must be distinguishable from official product declarations. Changes to recipe/allergen data invalidate outdated answers in subsequent conversations.
- **Safety and oversight:** No assistant independently grants refunds, rejects a safety complaint or makes an unreviewed exception to policy. Allergy uncertainty and potential food-safety incidents are escalated to a person. Guidance is not a substitute for an official allergen declaration.
- **Privacy and access:** Only fictional profiles are seeded. The customer demo interface must not expose another selected profile's order or complaint records; Teams staff actions are limited to an explicitly configured demo staff context. Without real authentication, these are demo controls, not production security guarantees.
- **Staff access boundary in the technical slice:** Cross-customer order reads use a distinct read-only MCP endpoint, separate bearer credential, and staff-only Foundry toolbox. The customer agent and customer toolbox must not acquire these tools. The hosted agent is reachable through Foundry's authenticated agent endpoint; a Teams user identity or staff authorization policy is not yet implemented. Do not use real customer data.
- **Traceability:** Log each state-changing request with actor/channel, record ID, prior/new status, timestamp and outcome; retain the policy version and human decision for complaints. Avoid placing unnecessary personal data in conversational logs.
- **Reliability and UX:** A transactional failure is reported without fabricating success, and retrying a confirmation must not create duplicate orders. Provide a clear handoff path when the assistant cannot answer or act. Target an initial response within 5 seconds for at least 90% of seeded read-only demo queries under normal demo conditions; measure end-to-end write completion separately.
- **Accessibility:** Web chat must support keyboard interaction and readable status/error messages; Teams interaction should work in the familiar chat interface without requiring users to learn command syntax.

## Open questions

- Do customers only request delivery, or is pickup also in scope? Are price, tax, delivery fee, opening hours and service area required for a valid order?
- Which order transitions can customers initiate, and at what point are changes or cancellation disallowed?
- Who can approve a complaint outcome, what remedies are allowed, and what period defines "five complaints" for mandatory human review?
- Are food-safety complaints escalated immediately regardless of complaint count?
- What is the acceptable demo handoff when a courier is unavailable or an order cannot be fulfilled?
- Does the simulated web chat need a persistent customer-selected session, or is selecting a seeded profile at the start of each walkthrough sufficient?
