# Project Compliance Review Report

**Project name:** Qingteng Procurement—supplier due diligence and risk scoring  
**Business model:** B2B subscription; customers are procurement and compliance teams at manufacturing enterprises  
**Document version:** v0.2 draft  

---

## I. Background and scope of review

This review is based on the product team’s *Qingteng Procurement v1.0 Requirements Specification*. It covers collection of supplier entity information, third-party credit and public-sentiment API calls, user-uploaded due-diligence attachments, sanctions and export-control list screening, operation logs, and administrator permissions. The review is framed mainly around the Personal Information Protection Law of the People’s Republic of China, practice under the Measures for the Security Assessment of Outbound Data Transfers, obligations under the classified cybersecurity protection scheme, and industry practice under anti–commercial bribery compliance management guidance.

## II. Summary of findings by topic

### 2.1 Personal information of natural persons at suppliers

The system collects contact persons’ names, titles, work phones, and e-mail addresses in due-diligence questionnaires and allows buyers to upload attachments such as ID copies and signature pages. The specification states the data are “for contracting and compliance contact” but does not distinguish between “enterprise contact information” and “identifiable natural persons” for purposes of notice, consent, and retention periods. It also does not state what rules apply if the contact is not a resident of mainland China.

### 2.2 Third-party data and commissioned processing

Credit scores, public sentiment, and sanctions hits are returned by multiple external APIs. Some vendors appear in a contract appendix list, but the requirements document does not map each integration to “who processes which fields, whether responses are persisted, and for how long,” making it hard to verify that commissioned-processing agreements and filing obligations are closed.

### 2.3 Cross-border data flows

A pilot in which the customer group’s headquarters has a European entity is under discussion. The draft says the “core database is deployed in East China” but does not address whether access by European subsidiary users to attachments uploaded in China constitutes a cross-border scenario or triggers standard contractual clauses or a security assessment pathway.

### 2.4 Logs and classified protection

Administrators may export “full change history for a given supplier” to Excel, including operator accounts and timestamps. Whether this meets requirements for traceability of critical operations, tamper resistance, and typical audit-log expectations at Class 2 or above under the classified protection scheme is only stated in principle; specific retention periods and access approval are not tied to the design.

### 2.5 Anti-bribery and training records

The roadmap includes checkboxes for “related-party conflict-of-interest declarations” and markers for annual compliance training completion, but it does not describe how training records and declaration versions will be retained for evidentiary use in disputes or how this aligns with the group’s anti-bribery policy.

---
