# SOP CORP-001: Whistleblower Process (Hinweisgebersystem)

**Version:** 1.0
**Date:** 2026-07-18
**Status:** ACTIVE
**Owner:** Betriebsrat / Compliance Officer
**Classification:** INTERNAL - CONFIDENTIAL

---

## 1. Purpose & Legal Basis

This SOP establishes the **Whistleblower System (*Hinweisgebersystem*)** per the German Whistleblower Protection Act (*Hinweisgeberschutzgesetz - HinSchG*). It provides legally protected channels for reporting violations of law, regulatory breaches, and internal policy violations.

**Legal Basis:**
- *Hinweisgeberschutzgesetz (HinSchG)* §§ 1–46
- *EU Whistleblower Directive (EU) 2019/1937*
- *Betriebsverfassungsgesetz (BetrVG)* § 80(1) Nr. 2a

---

## 2. Scope of Reportable Violations

| Category | Examples |
|----------|----------|
| Criminal offenses | Fraud, theft, corruption, bribery, embezzlement |
| Regulatory violations | GDPR, financial regulations, environmental law, labor law |
| Health & safety | Workplace hazards, safety protocol violations |
| Discrimination & harassment | AGG violations, sexual harassment, bullying |
| Financial misconduct | Accounting fraud, insider trading, money laundering |
| Environmental violations | Illegal emissions, waste disposal, resource misuse |
| Data protection | Unauthorized access, data breaches, GDPR violations |
| Anti-competitive behavior | Cartels, price fixing, market abuse |

**Excluded:** Purely personal disputes, minor policy disagreements without legal relevance.

---

## 3. Reporting Channels

### 3.1 Mandatory Internal Channel (*Internes Meldesystem*)

| Requirement | Implementation |
|-------------|----------------|
| **Channel type** | Secure digital portal (encrypted) + dedicated phone hotline |
| **Availability** | 24/7/365, multilingual (DE/EN minimum) |
| **Anonymous reporting** | Fully supported — no metadata logging for anonymous reports |
| **Confidential reporting** | Identity known only to case handler; protected per § 8 HinSchG |
| **Operator** | Independent ombudsperson (*Vertrauensanwalt*) or external compliance lawyer |
| **Access control** | No IT admin access to report content; encryption keys held by ombudsperson |

### 3.2 External Reporting Channels (per HinSchG § 19)

- Federal Office of Justice (*Bundesamt für Justiz*)
- Federal Financial Supervisory Authority (*BaFin*)
- Federal Cartel Office (*Bundeskartellamt*)
- State data protection authorities
- Other sector-specific regulators

### 3.3 Public Disclosure (Last Resort)

Permitted only if:
1. Internal + external channels exhausted or no action taken within 3 months
2. Imminent danger to public interest
3. Risk of retaliation if reported internally/externally

---

## 4. Reporting Process

### 4.1 Submission

```
Reporter → Secure Portal / Hotline → Encrypted intake → Case ID assigned (BR-YYYYMMDD-HHMMSS-reporter)
```

**Required fields (anonymous optional):**
- Category of violation
- Description of facts (what, when, where, who)
- Evidence attachments (encrypted upload)
- Desired outcome (investigation, cessation, remediation)
- Contact preference (anonymous / confidential / open)

### 4.2 Acknowledgment & Assessment (≤ 7 Calendar Days)

| Step | Timeline | Responsible |
|------|----------|-------------|
| Receipt confirmation | ≤ 7 calendar days | Ombudsperson |
| Initial assessment (jurisdiction, credibility, urgency) | ≤ 7 calendar days | Ombudsperson + Compliance |
| Triage decision | ≤ 7 calendar days | Ombudsperson |
| Reporter notification | ≤ 7 calendar days | Ombudsperson |

**Triage outcomes:**
- **Accept** → Full investigation
- **Refer** → External authority (if outside scope)
- **Dismiss** → Insufficient evidence / not in scope (with written reasoning)

### 4.3 Investigation (≤ 30 Calendar Days from Acceptance)

| Phase | Activities | Timeline |
|-------|------------|----------|
| Planning | Scope definition, evidence preservation, interview list | Days 1–5 |
| Evidence gathering | Document review, system logs, witness interviews | Days 5–20 |
| Analysis | Legal assessment, root cause, impact evaluation | Days 20–25 |
| Draft findings | Preliminary report, recommended actions | Days 25–28 |
| Final report | Signed by ombudsperson, management response | Day 30 |

**Investigation principles:**
- Independence — no conflict of interest
- Confidentiality — need-to-know basis only
- Proportionality — depth matches severity
- Fairness — accused party heard before adverse findings

### 4.4 Outcome Communication

| Recipient | Content | Timeline |
|-----------|---------|----------|
| Reporter | Outcome summary, actions taken, appeal rights | ≤ 30 days (or 3 months if complex) |
| Management (anonymized) | Findings, remediation plan, preventive measures | ≤ 30 days |
| Works Council (anonymized) | Pattern analysis, systemic issues | Quarterly |

---

## 5. Investigation Standards

### 5.1 Evidence Handling

| Requirement | Standard |
|-------------|----------|
| Collection | Chain of custody logged, hash-verified |
| Storage | Encrypted at rest (AES-256), access-controlled |
| Retention | 3 years after case closure (per HinSchG § 11) |
| Deletion | Secure wipe, certificate of destruction |

### 5.2 Interview Protocol

- Voluntary participation (no coercion)
- Right to be accompanied (works council rep, lawyer)
- Written summary signed by interviewee
- Recording only with explicit consent

### 5.3 Conflict of Interest

- Investigator must declare COI before case assignment
- Automatic recusal if COI exists
- Backup investigator pre-designated

---

## 6. Whistleblower Protection (HinSchG § 8–10, 13–15)

### 6.1 Protected Disclosures

Protection applies if reporter:
- Reasonably believes information is true at time of reporting
- Reports via internal or external channel
- Information falls within material scope (§ 2 HinSchG)

### 6.2 Prohibited Retaliation (HinSchG § 13)

| Prohibited Action | Protection |
|-------------------|------------|
| Termination | Null and void |
| Demotion / transfer | Reversible by Labor Court |
| Salary reduction | Recoverable + damages |
| Negative performance review | Inadmissible as evidence |
| Exclusion from training/projects | Discriminatory |
| Harassment / hostility | Criminal offense (§ 15 HinSchG) |
| Blacklisting | Prohibited |

### 6.3 Burden of Proof Shift (HinSchG § 13(3))

**If retaliation alleged within 1 year of report:**
- Employer must prove adverse action was **unrelated** to whistleblowing
- Presumption of retaliation if temporal proximity + no legitimate reason

### 6.4 Remedies

- Reinstatement / reversal of measure
- Compensation for material + non-material damage
- Injunctive relief (interim order possible)
- Legal costs reimbursed

---

## 7. Documentation & State Management

### 7.1 Case File Structure

```
.opencode-state/betriebsrat/grievances/
└── BR-YYYYMMDD-HHMMSS-reporter.json
```

**JSON Schema:**
```json
{
  "caseId": "BR-YYYYMMDD-HHMMSS-reporter",
  "receivedAt": "ISO8601",
  "channel": "portal|hotline|external",
  "anonymity": "anonymous|confidential|open",
  "category": "criminal|regulatory|safety|discrimination|financial|environmental|data|antitrust",
  "description": "string",
  "evidence": [{"filename": "string", "hash": "sha256", "encrypted": true}],
  "triage": {
    "decision": "accept|refer|dismiss",
    "reasoning": "string",
    "decidedAt": "ISO8601",
    "decidedBy": "ombudsperson-id"
  },
  "investigation": {
    "assignedTo": "investigator-id",
    "startedAt": "ISO8601",
    "completedAt": "ISO8601",
    "findings": "string",
    "recommendations": ["string"],
    "reportHash": "sha256"
  },
  "outcome": {
    "reporterNotifiedAt": "ISO8601",
    "managementResponse": "string",
    "remediationPlan": "string",
    "worksCouncilInformedAt": "ISO8601"
  },
  "status": "open|investigating|closed|referred",
  "retentionUntil": "ISO8601"
}
```

### 7.2 Race-Condition-Free Updates

- Single-writer per case file (ombudsperson owns investigation phase)
- Atomic writes: write to temp file → rename
- Status transitions logged with timestamp + actor

---

## 8. Reporting & Metrics

### 8.1 Quarterly Report to Works Council (Anonymized)

| Metric | Target |
|--------|--------|
| Reports received | Count by category |
| Anonymous vs. confidential | Ratio |
| Average triage time | ≤ 7 days |
| Average investigation time | ≤ 30 days |
| Substantiation rate | % accepted → substantiated |
| Retaliation claims | Count + outcome |
| Systemic issues identified | Count + themes |

### 8.2 Annual Report to Management Board

- Aggregated statistics (no case details)
- Trend analysis
- Policy/procedure improvements
- Resource adequacy assessment

---

## 9. Training & Awareness

| Audience | Frequency | Content |
|----------|-----------|---------|
| All employees | Annual + onboarding | Reporting channels, protections, examples |
| Managers | Annual + on promotion | Receiving reports, non-retaliation, escalation |
| Ombudsperson/Investigators | Annual + certification | Investigation techniques, legal updates, trauma-informed interviewing |
| Works Council | Semi-annual | System oversight, pattern recognition, co-determination rights |

---

## 10. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-18 | Betriebsrat Designer | Initial SOP |
