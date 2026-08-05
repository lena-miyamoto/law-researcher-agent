---
name: ask-law
description: >
  Answer a free-form legal question about Austrian or EU law: research the question,
  provide a source-backed answer with authority assessment and risk analysis, then
  answer follow-up questions interactively. Delegates deep research to the law-researcher agent.
argument-hint: "<free-form legal question about Austrian or EU law>"
user-invocable: true
---

# ask-law

Answer free-form Austrian and EU legal questions interactively. Delegates deep
research to the law-researcher agent.

## When to Use

User asks an open-ended legal question: "Is it legal to…?", "What are my rights if…?",
"How does liability work for…?", "What is the statute of limitations for…?",
"Does Austrian law require…?", "Can I be held liable for…?"

Not for: "Explain law X" (use explain-law), "Look up this document" (use law-db).

## Procedure

### Step 1: Validate the Question

- **Is it a legal question?** If purely factual or non-legal, clarify scope: "I can help
  with Austrian and EU legal questions. Is there a legal dimension you'd like me to focus on?"
- **Is it about Austrian or EU law?** If another jurisdiction, note the limitation. Offer
  an AT/EU perspective only if a comparable framework exists, with a jurisdictional caveat.
- **Is it vague?** Ask clarifying questions before researching: what area of law, what
  context, what jurisdiction. Do not guess the user's intent.

### Step 2: Classify Complexity

**Answer inline** (general legal knowledge, no authoritative sources required):

- Definitional questions about legal terms and concepts
- Structural questions about the Austrian or EU legal system
- Common-knowledge legal facts not requiring source verification
- Clarifying follow-ups about an answer already provided

For inline answers, include: "This is based on general legal knowledge. I can research
this with full sourcing — just ask."

**Delegate to law-researcher** (requires authoritative sources):

- Questions requiring statutory interpretation or specific legal provisions
- Questions about rights, obligations, procedures, or remedies
- Scenario-based questions with practical implications
- Regulatory compliance questions
- Any question whose answer could affect a legal decision

Dispatch pattern:

```text
Agent(subagent_type="law-researcher", prompt="Research question: {question}
Context: Free-form legal question from user.
Jurisdiction: {AT/EU/AT+EU}.
Required: Supporting authority, counter-authority, legal risk assessment.")
```

When in doubt: **delegate**. A false inline answer risks incompleteness; a false
delegation is only a minor delay.

### Step 3: Present the Answer

- **Delegated research**: summarize the law-researcher's findings in plain language.
  Include the authority quality rating. Flag legal uncertainty.
- **Inline answers**: state the answer clearly with the general-knowledge caveat.
- Include: "This is legal information, not legal advice. For advice about your specific
  situation, consult a qualified lawyer."

### Step 4: Interactive Follow-Up

After the answer, prompt: "Do you have any follow-up questions about this topic?"

- **Related question** (same topic, deeper detail): re-enter Step 2. When delegating,
  pass existing research context to the law-researcher agent.
- **Unrelated question**: treat as a fresh invocation, start from Step 1.
- Continue the loop until the user indicates they are done.

## Delegation Rules

### Answer Inline

- Definitional questions about legal terms
- Structural questions about the legal system
- Common-knowledge legal facts
- Clarifying questions about an answer already provided

### Delegate to law-researcher

- Statutory interpretation questions
- Case law questions
- Rights, obligations, and remedies questions
- Scenario-based questions with practical implications
- Regulatory compliance questions
- Any question where the answer could have legal consequences

**Dispatch context:** Include the original question, clarifying context from the user,
jurisdiction (AT/EU/AT+EU), and any relevant legal framework or statutes identified.

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Non-legal question | Clarify scope. Offer to help if there is a legal dimension. |
| Non-AT/EU jurisdiction | Note limitation. Offer AT/EU perspective with jurisdictional caveat if comparable law exists. |
| Vague question | Ask clarifying questions: area of law, context, jurisdiction. Do not guess. |
| Question needs a specific law identified first | Suggest using explain-law for that law, then returning with a targeted question. |
| Multiple distinct questions | Address each separately. Flag overlapping areas. |
| Question outside legal expertise | Defer to competent authority or qualified practitioner. |
| User asks for personal legal advice | Include disclaimer: information, not advice. |
| Question better suited for explain-law | Offer to switch skills or answer with available knowledge. |
| No authority found | Report per law-researcher standards: "No adequate authority found." |

## Integration Pointers

| What | How |
|------|-----|
| Deep legal research | `Agent(subagent_type="law-researcher", ...)` |
| Check local archive for context | `uv run law-db-query --search-keyword "..."` |
| Refer to explain-law | Suggest user invoke `Skill: "explain-law"` for specific law lookups |
