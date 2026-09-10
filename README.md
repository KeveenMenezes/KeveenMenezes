<h1 align="center">Keveen Menezes</h1>

<p align="center">
  <b>.NET Specialist</b> · Distributed Systems · AWS<br>
  <sub>5+ years building software · Belo Horizonte, Brazil · open to remote, hybrid and on-site</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/.NET-512BD4?style=flat-square&logo=dotnet&logoColor=white" alt=".NET">
  <img src="https://img.shields.io/badge/C%23-239120?style=flat-square&logo=csharp&logoColor=white" alt="C#">
  <img src="https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=amazonwebservices&logoColor=white" alt="AWS">
  <img src="https://img.shields.io/badge/Apache%20Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white" alt="Kafka">
  <img src="https://img.shields.io/badge/2x%20AWS%20Certified-FF9900?style=flat-square&logo=amazonwebservices&logoColor=white" alt="2x AWS Certified">
</p>

---

### About

I've been building software for **5+ years** and I specialize in the **.NET platform**: C#, ASP.NET Core and .NET Aspire, running on AWS as event-driven, distributed systems.

What I actually get hired for is the decision *before* the code — choosing the pattern that fits the problem, and knowing what it costs to run. Kafka with one message per second isn't a distributed architecture; it's just Kafka. I care about the trade-off: scalability, cost, maintainability, and what the business actually needs.

Currently at **BMG Money** (credit fintech), owning the architecture of the company's centralized communications platform.

### Impact

| What I built | Result |
| --- | --- |
| Centralized multichannel communications platform on **Kafka + .NET Aspire** | **~50k messages/day**, absorbing 10k-in-2-minutes peaks without degradation |
| End-to-end message lifecycle tracking with **Lambda, SNS and SES** | Replaced a **$2k–$10k/month** vendor with the existing stack at ~**$400/month** |
| Async delivery with automated retries and **dead-letter queues** | Eliminated the silent message-loss failures of the previous sync model |
| **DocuSign** signing + storage integration | Document generation **2 min → 40 s (−66%)** |
| RPA orchestration platform migrated to **AWS Lambda** | **−40% infra cost**, execution **6 h → 40 min**, with horizontal scaling |
| Integration engine for **5 external vendors** (Strategy + Abstract Factory) | New partners onboard without touching core logic |

Technical reference on an 8-person team: code review, pattern definition, and the architecture conversation before the first line is written.

### Stack

**Core .NET** &nbsp;`C#` `.NET 8/10` `ASP.NET Core` `.NET Aspire` `Minimal APIs` `Entity Framework Core` `Dapper` `xUnit`

**Architecture** &nbsp;`DDD` `Clean Architecture` `Vertical Slice` `CQRS` `Event-Driven` `Microservices` `SOLID` `Design Patterns` `System Design`

**AWS** &nbsp;`Lambda (Native AOT)` `ECS` `EKS` `SQS` `SNS` `SES` `S3` `API Gateway` `AppSync` `Step Functions` `EventBridge` `DynamoDB` `Cognito` `CloudWatch` `X-Ray`

**Distributed & Data** &nbsp;`Apache Kafka` `RabbitMQ` `SQL Server` `PostgreSQL` `Redis` `DynamoDB`

**Platform & Quality** &nbsp;`Terraform` `AWS CDK` `CloudFormation` `Docker` `Kubernetes` `GitHub Actions` `Azure DevOps` `SonarQube` `OpenTelemetry` `Serilog` `Grafana`

**Front-end** &nbsp;`React` `Next.js` `Angular` `Blazor` `Razor` `ASP.NET MVC` `TypeScript`

### Featured — [DuckStore.AWS](https://github.com/KeveenMenezes/DuckStore.AWS)

A **serverless-first .NET e-commerce** built in public. It exists so my architectural reasoning is verifiable, not just claimed:

- **10 bounded contexts** modeled with DDD — own tables and events, no shared read model
- **CQRS** and event-driven communication; exactly **1 synchronous call** between services in the whole system, on purpose
- **AWS Lambda with Native AOT**, AppSync/GraphQL, Step Functions, EventBridge, DynamoDB
- Infrastructure as code with **AWS CDK**; CI/CD on GitHub Actions with **OIDC** — no static credentials
- **47 ADRs across 587 commits** — every decision has a written trade-off behind it

Live: [duckstore.dev.keveenmenezes.com](https://duckstore.dev.keveenmenezes.com)

Also: [CustomerFlow](https://github.com/KeveenMenezes/CustomerFlow) — event-driven + CQRS, writes through EF Core for consistency, reads through Dapper for speed · [DocStrategy](https://github.com/KeveenMenezes/DocStrategy)

### Certifications

<p>
  <img src="https://img.shields.io/badge/AWS%20Certified-Solutions%20Architect%20Associate-FF9900?style=flat-square&logo=amazonwebservices&logoColor=white" alt="AWS SAA">
  <img src="https://img.shields.io/badge/AWS%20Certified-Developer%20Associate-FF9900?style=flat-square&logo=amazonwebservices&logoColor=white" alt="AWS DVA">
</p>

B.S. in Information Systems — PUC Minas (2024)

### Writing

I publish architecture breakdowns on [LinkedIn](https://www.linkedin.com/in/keveen-menezes/) — serverless Next.js on AWS with OpenNext, replacing in-memory file processing with S3 pre-signed uploads and Step Functions Distributed Map, and why cloud cost is usually an architecture problem wearing a billing disguise.

### AI in the workflow

I use Claude Code as a development partner, not autocomplete. DuckStore was architected from day one for agent collaboration — the ADRs act as the contract that keeps an agent consistent across 10 bounded contexts.

### Contact


<p>
  <a href="https://www.linkedin.com/in/keveen-menezes/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="mailto:keveenprofissional@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>
  <a href="https://wa.me/5531984237807"><img src="https://img.shields.io/badge/WhatsApp-25D366?style=flat-square&logo=whatsapp&logoColor=white" alt="WhatsApp"></a>
</p>

---

<table style="border:none; width: 100%;">
  <tr>
    <td style="width: 56%; border: none;">
      <img align="center" style="width: 100%;" src="https://github-readme-stats.vercel.app/api?username=KeveenMenezes&hide=prs,issues,contribs&count_private=true&show_icons=true&theme=github_dark" alt="GitHub Stats" />
    </td>
    <td style="width: 42%; border: none;">
      <img align="center" style="width: 100%;" src="https://github-readme-stats.vercel.app/api/top-langs/?username=keveenmenezes&langs_count=4&layout=compact&theme=github_dark" alt="Top Languages" />
    </td>
  </tr>
</table>
