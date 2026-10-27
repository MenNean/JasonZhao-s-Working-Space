---
name: sap-exam
description: Answer SAP Emarsys open-book exam questions from screenshots or copied text, especially Chinese oral short-answer questions about implementation, account/user management, data onboarding, external data inputs, integrations, and configuration. Use the bundled Emarsys training knowledge base and examiner feedback first; use the QA file only as optional supporting memory for old multiple-choice questions.
---

# SAP Exam

## Purpose

Use this skill as a SAP Emarsys open-answer exam assistant. The expected output is usually a Chinese answer that the user can read aloud directly during an open-book exam.

The user prefers:

- Chinese answers by default.
- Clear, structured, practical wording.
- Not too long, but complete enough to score well.
- Simple language, with important SAP terms kept in English where useful.

## Source Priority

For open-answer questions, do not start with the QA file.

Use this order:

1. `references/exam-feedback.md`
   - Check whether the examiner already gave feedback on this topic.
   - Add the missing high-score details from that feedback.
2. `references/training-knowledge.md`
   - Search for the topic, feature names, setup steps, commands, roles, fields, or integration names.
   - Build the answer from the training content.
3. `references/qa.md`
   - Use only as supporting memory for old multiple-choice questions or when the user explicitly asks about a recorded QA item.

## Workflow

1. Read the screenshot or copied question.
2. Identify the topic, such as implementation, Account Owner, contact identification, data import, Web Extend, Smart Insight, External Events, External Content, Relational Data, Shopify, Adobe Commerce, SAP Commerce Cloud, CDC, CDP, Sales Cloud, or Account Engagement.
3. Search `exam-feedback.md` for the topic and collect examiner-required details.
4. Search `training-knowledge.md` for concrete steps and terminology.
5. Produce a Chinese answer that can be spoken directly.
6. If the question is actually multiple-choice, answer with option letters and correct text, and then optionally mention the QA match.

## Open-Answer Format

Default format:

```text
可以这样回答：

First paragraph: define the concept or goal.
Second paragraph: explain key steps, configuration, or examples.
Third paragraph: add monitoring, risks, rules, or best practices.
Final sentence: short summary.
```

Do not include source-search narration unless the user asks. Keep the final answer focused on what the user should say.

## High-Score Detail Checklist

Use these details when relevant.

### Contact Identification

- Use a stable, unique, long-term external identifier.
- Prefer IDs such as customer ID, member ID, CDP ID, or another generated external ID.
- Mention security rules: non-guessable, non-sequential, and avoid PII.
- Explain why email or phone can be risky as identifiers: duplicates, data fragmentation, unauthorized access, and privacy compliance issues.
- Mention that some SDKs, such as Mobile SDK and Web Push SDK, forbid PII as identifiers.

### Account Owner and Security

- Account Owner is the super admin for user management and security settings.
- Mention user creation, verification, deactivation, deletion, roles, and permissions.
- Include permitted login email domains, IP access control, SSO, API users, endpoint permissions, WebDAV users, and Keyring keys.
- Mention Keyring keys for SFTP auto-import, including 4096-bit RSA keys when detailed security is asked.
- Mention API credential types when relevant: OpenID Connect, OpenID Connect SAP Cloud Identity, and WSSE.
- Account Owner activation includes activation email, mandatory MFA, and phone verification by SMS or callback.

### Implementation Process

- Mention pre-implementation scoping:
  - use cases
  - single-account or multi-account design
  - multi-language and multi-currency
  - brands, regions, and future channels
  - user identification
  - data sources and architecture
  - APIs and real-time events
  - deliverability, DNS, IP warm-up, domains, and reply management
  - templates, HTML, images, fonts, and data export
- Mention milestones:
  - configure tenant/account
  - create Account Owner
  - activate channels
  - integrate data
  - activate email sending
  - migrate campaigns

### Web Extend

- Explain Web Extend as the website behavior data collection script.
- Mention concrete commands:
  - `setCustomerId`: identify a known or logged-in contact by customer ID.
  - `setEmail`: identify a contact by email when allowed by the implementation.
  - `view`: track product detail page views.
  - `category`: track category or listing page views.
  - `cart`: track products in the cart.
  - `purchase`: track completed purchases.
  - `go`: send the collected commands to SAP Emarsys.
- Mention correct page placement: login/identification pages, product pages, category pages, cart pages, checkout or thank-you pages.
- Mention that Web Extend fills standard `predict` fields and supports segmentation, Predict recommendations, Web Channel, Triggered Email, and Interactions.

### Smart Insight

- Explain Smart Insight as using product and sales data for lifecycle segmentation and analytics.
- For self-service setup, mention:
  - FTP account creation
  - contact field selection
  - product data configuration
  - sales data configuration by CSV upload or plug-in
  - store data configuration when needed
  - eRFM parameter setup
  - first data load and validation
- Monitoring:
  - Overview tab for overall status and lifecycle/business views.
  - Data Loads tab for upload/load status, errors, and processing results.

### Data Import and Data Quality

- Mention manual import, SFTP auto-import, API import, plug-ins, Web Extend, forms, and Relational Data Service.
- Mention field mapping, unique identifier, cleansing, validation, and monitoring.
- Mention opt-in cannot normally be changed from false to true by file import.
- For sales data upload, mention file naming rules and required fields when detail is needed.
- Monitoring:
  - Predict Data Sources Dashboard uses green, orange, and red health states.
  - Green means healthy.
  - Orange means warnings or non-critical errors.
  - Red means urgent issue or broken integration.

### External Events

- External Events are events from outside SAP Emarsys that trigger automations, campaigns, or triggered messages.
- Mention event definition, event ID, API trigger, contact identifier, and payload.
- Endpoint to trigger an event: `POST /v3/event/{eventId}/trigger`.
- Examples: registration completed, order placed, password reset, booking confirmed, order cancelled.

### External Content

- External Content retrieves real-time content from external systems through API.
- Configuration logic:
  - create connection
  - configure endpoint URL and authentication
  - create reusable preset
  - create personalization token
  - insert token into content
- Supported authentication includes Basic HTTP authentication and OAuth2.
- SAML is not supported for External Content connections.

### Relational Data

- Relational Data connects external databases to SAP Emarsys for segmentation and personalization.
- Mention connections, tables and views, reference fields, personalization settings, segment templates, SQL, and parameters.
- Supported database examples:
  - Amazon Redshift
  - Azure SQL
  - Google BigQuery
  - MySQL
  - PostgreSQL
  - Snowflake
  - SAP HANA
- Security details:
  - server-side TLS encrypted communication
  - PEM-format CA certificates for some database types, such as Microsoft SQL Server, MySQL, and PostgreSQL
  - CA chain configuration when needed
  - timeout settings, such as default 5 seconds and Amazon Redshift 15 seconds when detailed configuration is asked

### Shopify Integration

- Install SAP Emarsys Shopify app or plug-in.
- Create SAP Emarsys API user and save username/secret.
- Enable required contact, event, field, and customer settings permissions.
- Connect Shopify using API credentials.
- Sync customer data first, then events, products, orders, and Web Extend or web behavior tracking.
- Do not sync orders to Smart Insight unless Smart Insight is enabled.
- Validate with contacts, Predict Data Sources, Live Events, event monitoring, and program reporting.

### Adobe Commerce Integration

- Install the latest Adobe Commerce extension.
- In Adobe Commerce admin, get the Connect token from Stores configuration under the Emarsys panel.
- In SAP Emarsys Add-ons for Adobe Commerce, paste the Connect token, fetch sites, and select the website/store view.
- Configure contacts, events, products, orders, and Web Extend.
- Product sync should include item, product name, price, availability, and optional custom fields.
- Use Health Check to inspect last sync time, status, warnings, and errors.

### SAP Commerce Cloud Integration

- In SAP Emarsys Add-ons, get the automatically generated connector username and password or credentials.
- In SAP Commerce Backoffice, create an employee user.
- Assign the employee user to the `admin` group.
- Configure consent synchronization.
- Sync contacts first, then real-time events, products, and other datasets.
- Enable Web Extend before product synchronization when required.

### SAP CX, CDC, CDP, Sales Cloud, and B2B

- SAP Commerce Cloud syncs customers, products, orders, and real-time events.
- SAP Customer Data Cloud syncs profile data, consents, subscriptions, and communication topics.
- SAP Customer Data Platform provides unified profiles, segments, indicators, and activities.
- SAP Customer Data Cloud and SAP Customer Data Platform cannot both connect directly to SAP Emarsys at the same time. If both are used, connect CDC to CDP first, then CDP to SAP Emarsys.
- CDC custom field prefixes:
  - `CD_C_` for consents
  - `CD_S_` for subscriptions
  - `CD_T_` for communication topics
- SAP Sales Cloud can connect through webhook node presets for sales follow-up use cases.
- SAP Account Engagement can support B2B marketing with Corporate Accounts, Sales Collaboration, sending emails on behalf of sales, and CDP-based account/contact data enrichment.

## References

- `references/exam-feedback.md`: examiner feedback and high-score details. Read this first for open-answer questions.
- `references/training-knowledge.md`: merged Emarsys training text. Use this as the main knowledge source.
- `references/qa.md`: old curated multiple-choice QA records. Use only as optional memory or when the user asks about a recorded QA item.

