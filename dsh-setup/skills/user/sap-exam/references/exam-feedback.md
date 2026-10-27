# SAP Emarsys Exam Feedback

Use this feedback to improve future open-answer responses. The user wants concise Chinese answers that can be spoken during an open-book exam, but examiner feedback shows that higher scores require more concrete technical details.

## Data Overview and Contact Identification

Score: 4/5.

Strong points:

- The answer clearly described data import steps, core datasets, data management, and basic contact identification best practices.
- It correctly mentioned external identifiers should be stable, unique, long-term, and consistent across systems.

Add these details next time:

- External contact identifiers should follow security rules:
  - non-guessable
  - non-sequential
  - avoid sensitive personal information, or PII, such as email and phone number when possible
- Explain that using email as an identifier can create risk:
  - duplicate contacts
  - data fragmentation
  - unauthorized access risk
  - privacy compliance risk
- Mention that some functions, including Mobile SDK and Web Push SDK, explicitly forbid PII as identifiers.

## SAP Emarsys Implementation Process and Account and User Management

Score: 4/5.

Strong points:

- The answer accurately described the six implementation milestones, Account Owner responsibilities, preset roles, and main security settings.

Add these details next time:

- In security settings, explain that Account Owners manage:
  - permitted email domains for account login
  - IP access control
  - SSO configuration
  - API users and API endpoint permissions
  - WebDAV users
  - Keyring keys for SFTP auto-import, including 4096-bit RSA keys
- When discussing API credentials, mention the three credential types:
  - OpenID Connect
  - OpenID Connect SAP Cloud Identity
  - WSSE
- When discussing Account Owner activation, include:
  - activation email link
  - mandatory multi-factor authentication for Account Owners
  - phone number verification by SMS or callback

## Data Onboarding and Management in the SAP Emarsys System

Score: 3/5.

Strong points:

- The answer explained manual import, SFTP auto-import, API import, and plug-in import.
- It explained system fields, custom fields, field types, and suitable scenarios for different import methods.

Add these details next time:

### Web Extend configuration

When Web Extend is mentioned, include specific JavaScript commands and where they are used:

- `setCustomerId`: identify a logged-in or known contact using a customer ID.
- `setEmail`: identify a contact by email when this is allowed by the implementation design.
- `view`: track product detail page views.
- `category`: track category or listing page views.
- `cart`: track products currently in the cart.
- `purchase`: track completed purchase events.
- `go`: send collected commands to SAP Emarsys.

Explain that these commands must be placed on the correct page types: product pages, category pages, cart pages, checkout or thank-you pages, and pages where login or email identification happens.

### Smart Insight self-service configuration

When Smart Insight or sales data is discussed, include the configuration flow:

- create or configure the FTP account
- select contact fields
- configure product data
- configure sales data, either by CSV upload or plug-in
- configure store data where needed
- set eRFM parameters for engagement, recency, frequency, and monetary value
- validate data after the first load

### Data quality monitoring

Mention concrete monitoring tools:

- Predict Data Sources Dashboard:
  - green means healthy
  - orange means warnings or non-critical errors
  - red means urgent issue or broken integration
- Smart Insight:
  - Overview tab shows overall status and business/customer lifecycle views
  - Data Loads tab shows upload/load status, errors, and processing results

### Key import rules

Mention important rules:

- opt-in cannot normally be changed from false to true by file import.
- sales data files must follow naming rules and contain required fields.
- required sales fields usually include identifiers for contact/customer, item/product, order, purchase date, quantity, and price or revenue, depending on the configured schema.

## Managing External Data Inputs in SAP Emarsys

Score: 4/5.

Strong points:

- The answers explained External Events, External Content, and Relational Data clearly, with practical use cases.

Add these details next time:

### Relational Data supported databases

When talking about relational data connections, mention supported database types when relevant:

- Amazon Redshift
- Azure SQL
- Google BigQuery
- MySQL
- PostgreSQL
- Snowflake
- SAP HANA

### Relational Data security and connection details

Mention:

- SAP Emarsys uses TLS for encrypted server-side communication.
- Some database types, such as Microsoft SQL Server, MySQL, and PostgreSQL, require PEM-format CA certificates.
- Configure the CA certificate or full CA chain when needed.
- Mention connection timeout settings, such as a default 5 seconds and Amazon Redshift 15 seconds, when detailed configuration is requested.

## System Integration and Configuration with SAP Emarsys

Score: 3/5.

Strong points:

- The answer covered Shopify and Adobe Commerce installation, API configuration, data sync sequence, and Health Check monitoring.
- It showed basic understanding of SAP CX products.

Add these details next time:

### SAP Commerce Cloud connector

When SAP Commerce Cloud is mentioned, include the concrete configuration process:

- In SAP Emarsys, go to Add-ons and retrieve the automatically generated username and password or connector credentials.
- In SAP Commerce Backoffice, create an employee user.
- Assign the employee user to the `admin` group.
- Configure consent synchronization.
- Sync contacts first, then events, products, and other datasets.
- Enable Web Extend before product synchronization when required.

### SAP CX integrations and restrictions

Mention:

- SAP Commerce Cloud can sync customers, products, orders, and real-time events to SAP Emarsys.
- SAP Customer Data Cloud can sync profile data, consents, subscriptions, and communication topics.
- SAP Customer Data Platform can provide unified profile data, segments, indicators, and activities.
- SAP Customer Data Cloud and SAP Customer Data Platform cannot both connect directly to SAP Emarsys at the same time. If both are used, integrate CDC with CDP first, then connect CDP to SAP Emarsys.
- CDC custom fields follow naming prefixes such as:
  - `CD_C_` for consents
  - `CD_S_` for subscriptions
  - `CD_T_` for communication topics

### Account Engagement and B2B

When asked about SAP CX solutions or B2B use cases, include:

- SAP Account Engagement can support B2B marketing with SAP Emarsys.
- Mention Corporate Accounts management.
- Mention Sales Collaboration, for example sending emails on behalf of sales.
- Mention CDP usage in B2B scenarios for account and contact data enrichment.

