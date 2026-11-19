# Y Combinator Requests for Startups and Portfolio: hardware, manufacturing, robotics, energy, data centres, industrial AI, defence

Research date: 2026-11-19.

**Method note.** YC's RFS page (https://www.ycombinator.com/rfs) server-renders only the current edition, Winter 2027. Every previous edition is stored in the page's JavaScript bundle, `RequestsForStartupsPage-JoCjuwdt.js` on bookface-static.ycombinator.com, which the RFS page loads. I parsed that bundle locally. It yielded all 9 editions, with full text, authors and coauthors. Text quoted in these notes is verbatim from that bundle or from the rendered page, and I cite it as [YC RFS](https://www.ycombinator.com/rfs) plus the edition tab.

- **Anchors:** only Winter 2027 items have HTML anchor ids, for example `#data-center-supply-chain`. Older items are reachable only through the edition tabs on /rfs.
- **Dates:** the page gives **no per-item publication dates**. Edition labels such as "Fall 2026" appear to name the target application batch, not the publication date.
- **Edition counts:** my counts (W27 11, F26 13, S26 16, Sp26 10, F25 6, Su25 14, Sp25 12, W25 9, Su24 16) match the third-party [Superframeworks RFS tracker](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026) for every edition it covers. This is independent cross-validation.

---

## Q1. Current RFS edition (Winter 2027): every request, with the relevant ones marked

### Takeaway
The current edition, fetched 2026-11-19, is **Winter 2027**, not Fall 2026. It has 11 requests. Its intro explicitly targets "hardware, infrastructure... from factories and data centers". **"Data Center Supply Chain" (Jared Friedman)** names liquid cooling equipment as "sold out", which is the most direct YC endorsement of a cold-plate or cooling-hardware business found anywhere in the RFS archive. "Robots Made in America" (Diana Hu) and "Vertical Foundation Models" (Diana Hu, naming manufacturing and energy) are also relevant.

### Cited Findings
- **Edition intro (Winter 2027):** "AI's biggest bottlenecks are moving beyond the models. We're excited about a new wave of startups building the hardware, infrastructure, financial systems, and specialized software needed to bring intelligence into the real economy, from factories and data centers to government and space." — [YC RFS, Winter 2027](https://www.ycombinator.com/rfs)
- **Full list of Winter 2027 requests** (R = relevant to hardware, manufacturing, robotics, energy, data centres, industrial AI or defence). Source for all: [YC RFS, Winter 2027](https://www.ycombinator.com/rfs).
  1. **Startups in a World of Abundant Space Access**, Ankit Gupta (R, space hardware): "What business models maybe don't quite work today but could work when launch costs fall 100x or more".
  2. **The $15-an-Hour Expert**, Brad Flora (not relevant): AI turning uncredentialed workers into experts in benefits, tax, claims and billing.
  3. **Robots Made in America**, Diana Hu (**R, robotics and manufacturing**). See detail below.
  4. **LLMs That Write Well**, Jared Friedman (not relevant).
  5. **Plaid for Government Benefits**, Gustaf Alströmer (not relevant).
  6. **Wall Street for the Physical Buildout**, Brad Flora (**R, capital for robots and data centres**). See detail below.
  7. **Vertical Foundation Models**, Diana Hu (**R, industrial AI**). See detail below.
  8. **AI for City Hall**, Gustaf Alströmer (marginal: construction permitting).
  9. **Data Center Supply Chain**, Jared Friedman (**R, data centres, cooling and power**). See detail below.
  10. **AI for the Air-Gapped Economy**, Brad Flora (**R, defence and nuclear**). See detail below.
  11. **Own Your Intelligence**, Jon Xu (marginal: specialised or owned models for regulated industries).
- **Data Center Supply Chain (Jared Friedman), verbatim:**
  - "The AI data center buildout is the largest capital investment project in American history - bigger than the railroads, the highways, and the Manhattan Project - combined."
  - "Large power transformers have a three-year lead time. Switchgear, circuit breakers, and liquid cooling equipment are all sold out. Even raw materials are under pressure: the grain-oriented electrical steel that's used in transformer cores is made in only a single plant in the US, and they're unable to keep up."
  - "We're interested in funding companies that are enabling every aspect of the data center supply chain."
  - Source: [YC RFS #data-center-supply-chain](https://www.ycombinator.com/rfs#data-center-supply-chain). The lead-time and single-plant figures are the author's claims; I did not verify them.
- **Robots Made in America (Diana Hu):**
  - "The best robot foundation models are starting to transfer skills from one robot to another, and I think the bottleneck is moving to the hardware."
  - It cites 38,400 US industrial robot installs in 2025 (+12%), China making 94% of sintered rare-earth magnets in 2024, and an FCC rule under which connected mobile robots need "more than 65 percent" of component cost to be domestic, "rising to 75 percent in 2029". These are author claims; I did not verify them.
  - "Assembling imported parts won't get you there."
  - "We want to fund founders building robots and their supply chain here: rare-earth magnets, motors, strain-wave gears, encoders, force sensors, grippers, chips, battery packs, and the machines that make them."
  - Source: [YC RFS #robots-made-in-america](https://www.ycombinator.com/rfs#robots-made-in-america)
- **Wall Street for the Physical Buildout (Brad Flora):**
  - "Software is cheap to start. Robots, GPU clusters, and data centers aren't."
  - "Today, banks underwrite a robot like a forklift."
  - Wants "lenders, leasing companies, securitization, and hedges for the physical AI economy."
  - Source: [YC RFS #wall-street-for-the-physical-buildout](https://www.ycombinator.com/rfs#wall-street-for-the-physical-buildout)
- **Vertical Foundation Models (Diana Hu):**
  - "I'd like to see more research labs build specialized foundation models for manufacturing, energy, and biology that work zero-shot or from a handful of examples."
  - "The hard part is getting high-quality, vertical-specific, verifiable rewards."
  - It references a model called "Jev" and Google's "TimesFM-3", 330M parameters. These are author claims; I did not verify them.
  - Source: [YC RFS #vertical-foundation-models](https://www.ycombinator.com/rfs#vertical-foundation-models)
- **AI for the Air-Gapped Economy (Brad Flora):**
  - "Defense contractors, banks, hospitals, and nuclear plants keep it behind walls."
  - Wants "on-prem models, deployment tooling, security accreditation, and hardware."
  - "It's slower and harder to sell. It's also where the largest budgets and the most defensible companies are."
  - Source: [YC RFS #ai-for-the-air-gapped-economy](https://www.ycombinator.com/rfs#ai-for-the-air-gapped-economy)
- **Short videos:** each RFS item has a YouTube Shorts video id in the bundle, for example data-center-supply-chain = `9EJM4LNMK0I` and robots-made-in-america = `7adYEc1XkEs`. URLs such as https://www.youtube.com/shorts/9EJM4LNMK0I are **constructed from the ids and were not fetched**. — [YC RFS bundle](https://www.ycombinator.com/rfs)
- **Application deadline:** a third party reports that Winter 2027 applications were due 2026-11-02, 8pm PT. — [Superframeworks](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)
- **Superseded edition:** the user brief assumed the current edition was "as of November 2026". Third-party articles from October 2026 still called Fall 2026 the latest edition. — [StartupIdeasDB, 2026-10-19](https://startupideasdb.com/blog/yc-requests-for-startups-fall-2026); [Superframeworks, updated 2026-10-10](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)

### Inferences
- *Inference:* Winter 2027 was probably published between late October and mid-November 2026. Third-party sources still showed Fall 2026 as latest on 10 and 19 October 2026.
- *Inference:* "Data Center Supply Chain" is the strongest RFS fit for the cold-plate factory idea. It names liquid cooling equipment as a sold-out bottleneck and asks for "every aspect" of the supply chain.
  - "Robots Made in America" supports the robotics side only if the company *makes* robot components. It does not cover using imported robots in a factory.
  - "Wall Street for the Physical Buildout" signals YC awareness that capex-heavy factory models need financing innovation.
- *Inference:* No Winter 2027 request uses the phrase "autonomous factory" or "agent-run factory". The fit is thematic, through supply chain plus physical AI, not literal.

### Gaps
- No per-item publication dates are shown, and the exact Winter 2027 publication date was not found.
- The FCC 65%/75% rule, the "Jev" model and TimesFM-3 were not independently verified. They are reported as the RFS author's claims.

---

## Q2. Previous editions (Fall 2026 back to Summer 2024): relevant requests per edition

### Takeaway
YC's RFS has moved steadily toward atoms. The arc runs as follows:
- Summer 2024: "New Defense Technology", "ML for Robotics", "ML to Simulate the Physical World".
- Winter 2025: "Manufacture in the USA", "AI-Aided Engineering Tools".
- Spring 2025: "Datacenters", which includes a "lights out" robot-run vision and names cooling.
- Summer 2025: "Full-stack AI Companies".
- Spring 2026: "Modern Metal Mills", a software-defined mill.
- Summer 2026: "Hardware Supply Chain", "Counter-Swarm Defense", "Supply Chain 2.0 for Semiconductors".
- Fall 2026: "Future of American Defense", written by the US Army Secretary, plus "Compute at Sea" and "New Operating Systems for the Physical World".

Source for every item: [YC RFS, edition tabs](https://www.ycombinator.com/rfs), parsed from the page bundle. Only Winter 2027 items have direct anchors.

### Cited Findings

**Edition dating evidence** (YC shows no per-item dates):

| Edition | Items | Date evidence |
|---|---|---|
| Winter 2027 | 11 | Live on /rfs when fetched 2026-11-19 ([YC RFS](https://www.ycombinator.com/rfs)). Not yet listed by third parties on 2026-10-19 ([StartupIdeasDB](https://startupideasdb.com/blog/yc-requests-for-startups-fall-2026)). *Inference:* published late Oct to mid-Nov 2026. |
| Fall 2026 | 13 | Described as the latest edition on 2026-10-10 ([Superframeworks](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)) and 2026-10-19 ([StartupIdeasDB](https://startupideasdb.com/blog/yc-requests-for-startups-fall-2026)). |
| Summer 2026 | 16 | No publication date found. |
| Spring 2026 | 10 | Third-party coverage first published 2026-02-03 ([Superframeworks](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)). |
| Fall 2025 | 6 | No publication date found. |
| Summer 2025 | 14 | No publication date found. |
| Spring 2025 | 12 | YC intro says it was published "just 3 months after our last one" ([YC RFS](https://www.ycombinator.com/rfs)). |
| Winter 2025 | 9 | No publication date found. |
| Summer 2024 | 16 | YC: "published in the summer of 2024" ([YC RFS](https://www.ycombinator.com/rfs)). Extruct says February 2024 with 20 categories ([Extruct](https://www.extruct.ai/research/industrial-tech-thesis/)). The sources conflict. |

**Fall 2026 (13 requests).** Intro: "AI is moving into the physical world... include, for the first time, one from the sitting U.S. Secretary of the Army." — [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)
- All titles and authors:
  - The Primer (Andrew Miklas)
  - **The Future of American Defense (Daniel P. Driscoll)**
  - A Cloud for Small Software (Pete Koomen)
  - Multiplayer AI (Aaron Epstein)
  - **Compute at Sea (Francois Chaubard)**
  - AI-Powered Consumer Products for 1 Billion People (Raphael Schaad)
  - AI for the Aging Population (Max Kolysh): includes home robotics
  - **New Operating Systems for the Physical World (Charlie Warren)**
  - The Best Time to Build in Crypto (Nemil Dalal)
  - **Data for the Real World (Austin Tindle, coauthor Diana Hu)**
  - Proving You're Human (Max Kolysh)
  - AI-Native Compliance Infrastructure (Daivik Goel)
  - Self-Maintaining APIs (Harsha Gaddipati)
  - Source: [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)
- **The Future of American Defense:**
  - "We are actively funding low-cost interceptors or any component that helps us lower the cost per kill."
  - "We need next-gen sensors, software, payloads, and other hardware that plugs directly into our open system architecture. We need cutting-edge drones, resilient logistics, and advanced manufacturing..."
  - "Bring us your ideas, and we will give you the capital and the proving ground to scale."
  - Source: [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)
  - A third party notes that Military Times reported Driscoll's resignation on 2026-08-31, so the request reflects a mid-2026 signal. I did not verify this. — [Superframeworks](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)
- **Compute at Sea:** "the ocean... is an enormous natural heat sink"; "compute flotillas: many standardized, modular vessels". — [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)
- **New Operating Systems for the Physical World:**
  - Lists "three kinds of workers: AI agents that can quote complex work and schedule teams. Robots actually deployed in the field. And humans who increasingly use wearables."
  - "How do you route a job between an agent, a robot, and a person?"
  - "these industries spend 10 to 100x more on labor than software."
  - Source: [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)
- **Data for the Real World:** dense physical-world data collection for "energy, agriculture, logistics, and construction". Cites Gecko Robotics and Sorcerer. — [YC RFS, Fall 2026](https://www.ycombinator.com/rfs)

**Summer 2026 (16 requests).** Intro: "rebuilding software, services, and silicon — and pushing AI into the physical world." — [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- All titles and authors:
  - AI for Low-Pesticide Agriculture (Garry Tan)
  - AI-Native Discovery Engines (Jon Xu)
  - **AI-Native Service Companies (Gustaf Alströmer)**
  - AI Personalized Medicine (Ankit Gupta)
  - Company Brain (Tom Blomfield)
  - **Counter-Swarm Defense (Tyler Bosmeny)**
  - Dynamic Software Interfaces (Ankit Gupta)
  - **Electronics in Space (Philip Johnston)**
  - **Hardware Supply Chain (Nicolas Dessaigne)**
  - **Industrial Capabilities in Space (Adi Oltean)**
  - **Inference Chips for Agent Workflows (Diana Hu)**
  - SaaS Challengers (Jared Friedman): includes "ERPs, industrial control systems, supply chain management" as targets
  - Software for Agents (Aaron Epstein)
  - Startups That Want to Sell to Huge Companies (Harshita Arora, coauthor Brad Flora)
  - **Supply Chain 2.0 for Semiconductors (Diana Hu)**
  - The AI Operating System for Companies (Diana Hu)
  - Source: [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- **Hardware Supply Chain (Nicolas Dessaigne).** (*Inference:* the closest RFS to "agent-run contract manufacturing".)
  - "In Shenzhen, a team can go from design to a new physical part in a day. In the US, that same loop often takes weeks."
  - "The problem isn't just the supply chain. It's iteration speed."
  - Names Hlabs (W26, actuators) and Prototyping.io (P26, "helps turn designs into mechanical parts in days").
  - Wants startups that "produce parts dramatically faster", "enable rapid hardware iteration" and "tightly integrate design, manufacturing, and logistics".
  - Source: [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- **Counter-Swarm Defense (Tyler Bosmeny):**
  - Claims "a swarm of cheap Iranian drones took out an AWS data center". This is the author's claim; I did not verify it.
  - "A Patriot missile costs three million dollars. An FPV drone? Five hundred bucks."
  - Wants "high-capacity interceptors", sensor-fusion software and non-kinetic defences.
  - "The winning companies will look more like Cloudflare than Raytheon."
  - Source: [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- **AI-Native Service Companies (Gustaf Alströmer):** "AI-native companies that don't sell software—they sell the service. Instead of giving you a tool, they just do the work." Example areas are insurance, accounting, compliance and healthcare admin, not manufacturing. — [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- **Supply Chain 2.0 for Semiconductors (Diana Hu):** "A single advanced AI chip goes through about 1,400 process steps... managed with spreadsheets, SAP, and phone calls." Wants allocation tracking, multi-tier risk monitoring and export compliance. — [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)
- **Inference Chips for Agent Workflows (Diana Hu):** purpose-built silicon for agent loops. Also **Electronics in Space**, which covers mass-, thermal- and radiation-optimised inference chips, and **Industrial Capabilities in Space**, which covers lunar electrolysis and 3D printing. — [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)

**Spring 2026 (10 requests).** Intro: "...AI-native workflows, new financial primitives, modernized industrial systems, and more." — [YC RFS, Spring 2026](https://www.ycombinator.com/rfs)
- All titles and authors:
  - Cursor for Product Managers (Andrew Miklas)
  - AI-Native Hedge Funds (Charlie Holtz)
  - AI-Native Agencies (Aaron Epstein)
  - Stablecoin Financial Services (Daivik Goel)
  - AI for Government (Tom Blomfield)
  - **Modern Metal Mills (Zane Hengsperger)**
  - **AI Guidance for Physical Work (David Lieb)**
  - **Large Spatial Models (Ryan McLinko)**
  - Infra for Government Fraud Hunters (Garry Tan)
  - Make LLMs Easy to Train (Gabriel Birnbaum)
  - Source: [YC RFS, Spring 2026](https://www.ycombinator.com/rfs)
- **Modern Metal Mills.** (*Inference:* the most explicit "reindustrialisation / software-defined factory" request in the archive.)
  - "When people talk about reindustrializing America... a bigger problem is hiding in plain sight: American metal mills are slow by design."
  - Cites lead times of "8 to 30 weeks".
  - "Material handling, changeovers, inspection, and quality control still rely on tribal knowledge."
  - "AI-driven planning, real-time MES, and modern automation can compress lead times and raise margins at the same time."
  - "modern, software-defined American mills—especially in aluminum rolling and steel tube".
  - Source: [YC RFS, Spring 2026](https://www.ycombinator.com/rfs)
- **AI Guidance for Physical Work:** real-time camera-based AI coaching for field services, manufacturing and healthcare. Suggests you "pick a vertical, like HVAC repair or nursing, and build a full-stack superpowered workforce." — [YC RFS, Spring 2026](https://www.ycombinator.com/rfs)
- **Large Spatial Models:** "models that treat geometry and physical structure as first-class primitives... enable AI systems to reason about and design real-world objects". (*Inference:* relevant to agentic CAD and thermal design.) — [YC RFS, Spring 2026](https://www.ycombinator.com/rfs)
- **Third-party date and correction:** Spring 2026 coverage was originally published 2026-02-03. The tracker says the February version listed 8 categories and that three official ideas were added later. — [Superframeworks](https://superframeworks.com/articles/yc-rfs-startup-ideas-indie-hackers-2026)

**Fall 2025 (6 requests).** Intro: "ideas that treat AI not as a feature, but as a foundation." — [YC RFS, Fall 2025](https://www.ycombinator.com/rfs)
- All titles and authors:
  - **Retraining Workers for the AI Economy (Harj Taggar)**
  - Video Generation as a Primitive (David Lieb)
  - **The First 10-person, $100B Company (Aaron Epstein)**
  - Infrastructure for Multi-Agent Systems (Pete Koomen)
  - AI Native Enterprise Software (Andrew Miklas)
  - Using LLMs Instead of Government Consulting (Gustaf Alströmer)
  - Source: [YC RFS, Fall 2025](https://www.ycombinator.com/rfs)
- **Retraining Workers:** "there needs to be a huge buildout of physical infrastructure like data centers and semiconductor fabs... we also have a shortage of skilled tradespeople—the electricians, the HVAC technicians, the welders". — [YC RFS, Fall 2025](https://www.ycombinator.com/rfs)
- **10-person $100B company:** "the best high-agency startups of the future will all optimize for one metric: revenue per employee." — [YC RFS, Fall 2025](https://www.ycombinator.com/rfs)

**Summer 2025 (14 requests).** Intro: "2025 is indeed shaping up to be the 'year of AI agents'." — [YC RFS, Summer 2025](https://www.ycombinator.com/rfs)
- Relevant requests:
  - **Full-stack AI Companies (Jared Friedman):** "you could start your own law firm, staff it with AI agents, and compete with the existing law firms... You could do this for any industry, especially one dominated by slow-moving incumbents. Instead of selling to the dinosaurs, you could make them extinct."
  - **Software Tools To Make Robots (Diana Hu):** B2B industrial focus, citing Gecko Robotics inspection robots.
  - **AI for Scientific Advancement (Diana Hu):** "use AI to transform how physical things are made faster and more efficiently".
  - **AI Research Labs (Jared Friedman).**
  - Source: [YC RFS, Summer 2025](https://www.ycombinator.com/rfs)
- Other Summer 2025 requests, not relevant:
  - More Design Founders
  - Voice AI
  - AI Personal Assistant
  - Healthcare AI
  - AI Personal Tutor
  - Future of Education
  - AI Residential Security
  - Internal Agent Builder
  - AI Voice Assistants for Email
  - AI for Personal Finance
  - Source: [YC RFS, Summer 2025](https://www.ycombinator.com/rfs)

**Spring 2025 (12 requests).** — [YC RFS, Spring 2025](https://www.ycombinator.com/rfs)
- **Datacenters (Diana Hu):**
  - "we need new companies and more innovative solutions to accelerate this buildout—whether in power infrastructure, cooling, material procurement, or project management."
  - "software will handle every aspect of planning and constructing new datacenters... These applications will be 'lights out,' with robots operating autonomously 24/7 without human intervention."
- **AI Coding Agents for Hardware-Optimized Code (Diana Hu):** AI-generated kernels.
- **Inference AI Infrastructure in the World of Test-Time Compute (Diana Hu).**
- **Vertical AI Agents (Jared Friedman):** "The value prop of vertical AI agents is to automate the work entirely."
- Others, not relevant: Secure AI App Store, Compliance and Audit, Browser & Computer Automation, AI Personal Staff, Devtools for AI Agents, Future of Software Engineering, AICOSS, B2A Software.

**Winter 2025 (9 requests).** Intro: "We just watched giant robotic chopsticks pluck a falling skyscraper out of the sky... It feels like we are entering a golden age of building." — [YC RFS, Winter 2025](https://www.ycombinator.com/rfs)
- **Manufacture in the USA (Jared Friedman):**
  - "New ML-based robotics systems will make it possible to automate far more, which will reduce the cost-of-labor arbitrage that pushed manufacturing to other countries in the first place."
  - Cites Astranis (W16), Gecko Robotics (W16) and Solugen (W17).
- **AI-Aided Engineering Tools (Diana Hu):** "The CAD/CAM software... EDA tools... and the CFD tools for fluid and thermal analysis... All still rely on complex numerical solvers". Wants "the new generation of Computer-aided Engineering". (*Inference:* this covers AI thermal design.)
- **LLMs for Chip Design (Garry Tan).**
- **New Space Companies (Jared Friedman, coauthor Dalton Caldwell).**
- **Public Safety Technology (Garry Tan).**
- Others: Government Software, Stablecoins 2.0, Fintech 2.0, One Million Jobs 2.0.

**Summer 2024 (16 requests).** Intro: "the requests for startups we published in the summer of 2024, our first big list since the start of the new AI wave." — [YC RFS, Summer 2024](https://www.ycombinator.com/rfs)
- **Using Machine Learning to Simulate the Physical World (Diana Hu, coauthor Jared Friedman):** ML replacing CFD and physics simulation.
- **New Defense Technology (Jared Friedman, coauthor Gustaf Alströmer):** "the defense contractors it depends on have grown slow and inefficient, bloated by decades of cost-plus contracts... This decade is the time to return Silicon Valley to these roots."
- **Applying Machine Learning to Robotics (Diana Hu, coauthor Jared Friedman):** "industrial use-cases like Gecko Robotics (W16)... funding people building software tools to help other people to make robots, along with people building the robots themselves."
- **New ERP Software (Dalton Caldwell).**
- **Spatial Computing (Diana Hu).**
- **Small Fine-tuned Models (Nicolas Dessaigne).**
- Others: Commercial Open Source, Internal Dev Tools, LLMs for Back Office, AI to Build Enterprise Software, Stablecoin Finance, A Way to End Cancer, Foundation Models for Biology, MSO for Healthcare, Eliminating Healthcare Middlemen, Explainable AI.
- **Conflicting date and count:** Extruct says YC published this list in **February 2024** as "its first RFS update since 2018" with **20 categories**. YC's page labels it **Summer 2024** with **16 items**. — [Extruct, 2026-02-24](https://www.extruct.ai/research/industrial-tech-thesis/), contradicted by [YC RFS](https://www.ycombinator.com/rfs)

### Inferences
- *Inference:* hardware, physical-world and defence requests grew from about 3 of 16 in Summer 2024 to about 6 of 11 in Winter 2027. This tracks YC's reported shift in batch mix (see Q5).
- *Inference:* the "autonomous factory" thesis is assembled from several requests. None of them states it on its own. The pieces are:
  - Datacenters (Sp25): lights-out, robots 24/7, cooling.
  - Full-stack AI (Su25): do the work, don't sell tools.
  - Modern Metal Mills (Sp26): software-defined factory with AI planning and MES.
  - Hardware Supply Chain (Su26): parts in days, design, manufacturing and logistics integrated.
  - Data Center Supply Chain (W27): liquid cooling sold out.
  - AI-Aided Engineering (W25): AI CFD and thermal tools.

### Gaps
- **Wayback Machine:** web.archive.org could not be fetched ("unable to fetch from web.archive.org"). I could not independently check historical snapshots or original publication dates. The YC bundle stands in for archive text.
- **Pre-2024 editions:** editions before Summer 2024 are not on the current page and were not researched.
- **Bundle vs original wording:** I could not determine whether the bundle text is identical to each edition's original wording at publication, since YC may have edited it.

---

## Q3. Theme cross-index: which YC requests explicitly cover each theme

### Takeaway
Every theme in the brief has at least one explicit YC request. The densest coverage is data-centre and compute infrastructure (requests in 4 editions: Sp25, Su26, F26, W27; Fall 2025 touches it indirectly via trades retraining) and defence (requests in 4 editions: Su24, Su26, F26, W27; plus Public Safety in W25). "Autonomous factory" as a phrase never appears. The nearest wording is "lights out" (Datacenters, Spring 2025, applied to datacenters and warehouses, not factories) and "software-defined American mills" (Spring 2026).

### Cited Findings
Source for all rows: [YC RFS](https://www.ycombinator.com/rfs), edition tabs, from a keyword scan of the full bundle text.

- **AI-native, autonomous or lights-out factories:**
  - Datacenters (Sp25, Hu): software for "planning and constructing new datacenters or warehouses... These applications will be 'lights out,' with robots operating autonomously 24/7". The "lights out" wording refers to building and operating data centres or warehouses, not factories.
  - Modern Metal Mills (Sp26, Hengsperger): "software-defined American mills".
  - Hardware Supply Chain (Su26, Dessaigne): parts in a day, "tightly integrate design, manufacturing, and logistics".
  - Keyword search: the phrase "autonomous factory" or "dark factory" is absent from all 107 RFS items across the 9 editions.
- **Reindustrialisation and American manufacturing:**
  - Manufacture in the USA (W25, Friedman).
  - Modern Metal Mills (Sp26).
  - Hardware Supply Chain (Su26).
  - Robots Made in America (W27, Hu).
  - The Future of American Defense (F26) asks for "advanced manufacturing".
- **Robotics:**
  - Applying ML to Robotics (Su24).
  - Software Tools To Make Robots (Su25).
  - Datacenters (Sp25): robots.
  - AI for the Aging Population (F26): home robotics.
  - New Operating Systems for the Physical World (F26): field robots.
  - Robots Made in America (W27).
- **Full-stack companies that do the work:**
  - Full-stack AI Companies (Su25, Friedman).
  - Vertical AI Agents (Sp25, Friedman): "automate the work entirely".
  - AI-Native Agencies (Sp26, Epstein).
  - AI-Native Service Companies (Su26, Alströmer): "they just do the work".
  - AI Guidance for Physical Work (Sp26): "full-stack superpowered workforce".
- **Data-centre and compute infrastructure:**
  - Datacenters (Sp25).
  - Inference AI Infrastructure (Sp25).
  - Inference Chips for Agent Workflows (Su26).
  - Electronics in Space (Su26).
  - Compute at Sea (F26).
  - Data Center Supply Chain (W27): "liquid cooling equipment... sold out".
  - Wall Street for the Physical Buildout (W27).
- **Energy and power:**
  - Datacenters (Sp25): "power infrastructure".
  - Modern Metal Mills (Sp26): on-site generation and "next-generation nuclear".
  - Data for the Real World (F26): energy data.
  - Data Center Supply Chain (W27): transformers, switchgear, electrical steel.
  - Vertical Foundation Models (W27): energy.
  - AI for the Air-Gapped Economy (W27): nuclear plants.
- **Defence and dual-use:**
  - New Defense Technology (Su24).
  - Public Safety Technology (W25).
  - Counter-Swarm Defense (Su26).
  - The Future of American Defense (F26, US Army Secretary).
  - AI for the Air-Gapped Economy (W27): defence contractors.
- **Supply chain:**
  - Supply Chain 2.0 for Semiconductors (Su26).
  - Hardware Supply Chain (Su26).
  - SaaS Challengers (Su26): "supply chain management".
  - Robots Made in America (W27): component supply chain.
  - Data Center Supply Chain (W27).
- **Industrial AI and engineering software:**
  - ML to Simulate the Physical World (Su24).
  - New ERP Software (Su24).
  - AI-Aided Engineering Tools (W25): CAD, CAM, CFD and thermal.
  - LLMs for Chip Design (W25).
  - AI for Scientific Advancement (Su25).
  - Large Spatial Models (Sp26).
  - Vertical Foundation Models (W27).
- **Trades labour for the buildout:**
  - Retraining Workers for the AI Economy (F25): "electricians, the HVAC technicians, the welders".

### Inferences
- *Inference:* the cold-plate autonomous factory maps onto at least five requests: W27 Data Center Supply Chain, Su26 Hardware Supply Chain, Sp25 Datacenters, Su25 Full-stack AI and W25 AI-Aided Engineering Tools. That is unusually broad support.
  - The weakest link is that YC partners frame liquid cooling as a supply *bottleneck*. They do not specifically frame it as a manufacturing-automation opportunity.
- *Inference:* each alternative idea maps to a different request:
  - Robotic machine-tending cells: Su24 ML Robotics and W25 Manufacture in USA. Su26 Hardware Supply Chain applies only if the company sells parts and not just cells.
  - Agent-run contract manufacturing: Su26 Hardware Supply Chain and Su25 Full-stack AI.
  - Data-centre install and service robotics: Sp25 Datacenters ("lights out") and F26 New OS for the Physical World.
  - Test and inspection robotics: Su24/Su25 Gecko examples and F26 Data for the Real World.
  - Defence and drone components: F26 Future of American Defense, Su26 Counter-Swarm and W27 Robots Made in America (motors and magnets).
  - Energy hardware: W27 Data Center Supply Chain (transformers and switchgear).

### Gaps
- No RFS explicitly discusses CNC, machine tending, cold plates or thermal hardware manufacturing. A local grep of all 107 items for "CNC", "cold plate", "dark factor", "machining" and "machine shop" returned zero matches. "Liquid cooling equipment" (W27) and "cooling" (Sp25) are the only cooling references.

---

## Q4. Recent YC companies (2024–2026 batches) in the target spaces

### Takeaway
YC has funded a dense cluster of directly overlapping companies, mostly in **Fall 2026 (F26)** and **Summer 2026 (S26)**. Part of that skew comes from the method: the directory listings showed only the newest ~50 companies per industry, so 2024–2025 companies are under-represented. Three groups stand out:
- **Autonomous CNC and contract manufacturing:** **twentyfour26 (F26)**, whose tagline is "Building Autonomous Factories in America, Starting with On-Demand CNC", **Antropi Robotics (F26)**, which runs "autonomous CNC dark factories", and **Forge Automation (W25)**.
- **AI-native data-centre equipment manufacturing:** **Applied Kinetics (F26)**, which makes transformers, switchgear, generators and cooling, with AI agents doing coordination.
- **Data-centre robotics:** **Nines (F26)**, **Proprio Robotics (S26)**, **Shepherd Robotics (F26)** and **Boost Robotics (Spring 2025)**.

**In the searches I ran I found no YC company that specifically makes liquid-cooling cold plates or CDUs.** The nearest are Ferveret (S21, immersion), Madrone (Spring 2026, dew-point cooling), Kara (S26, diamond heat spreaders), Pacific (S26, diamond-cooled modular data-centre pods) and Applied Kinetics (F26, "cooling systems" among its products).

**Notation.**
- ✓ means I fetched the YC company page directly.
- † means the description comes from a YC directory industry-listing page (paraphrased by the fetch tool), and the company URL is constructed from the slug and was not fetched.
- Descriptions are paraphrases, not quotes.
- Batch codes: F = Fall, S = Summer, W = Winter, P or X = Spring. The directory showed "P2026" for Madrone while its page said "Spring 2026". Extruct uses "X25" for Spring 2025.

### Cited Findings

**A. Autonomous, agent-run or software-defined factories and CNC automation**
- **twentyfour26 (F26) ✓:**
  - Tagline: "Building Autonomous Factories in America, Starting with On-Demand CNC…".
  - Builds standardised cells combining machines, tooling, workholding and inspection.
  - Its models are being built to read CAD, plan machining, select tooling and setups, and run the machines.
  - Already makes parts for Bay Area hardware companies, with turnaround as fast as about 48 hours.
  - Long-term goal is to expose manufacturing via an API.
  - Team of 2; site twentyfour26.com. The launch post targets space, defence and robotics hardware teams.
  - Source: [YC page](https://www.ycombinator.com/companies/twentyfour26)
- **Antropi Robotics (F26) ✓:**
  - Tagline: "Autonomous CNC factories for faster hardware".
  - Runs 24/7 "dark factories" through a Factory OS linking planning, CNC machines, robots and inspection.
  - Customers upload CAD and receive inspected parts with a report. It also offers agent ordering via an MCP server.
  - Claims its first factory is live with lead times under 7 days. The goal is US microfactories delivering in about 24 hours.
  - Targets Series B+ teams in compute infrastructure, robotics, medtech and energy.
  - Primary partner: Nicolas Dessaigne, who also wrote the Su26 Hardware Supply Chain RFS.
  - Source: [YC page](https://www.ycombinator.com/companies/antropi-robotics)
- **Forge Automation (W25) ✓:** "Software Enabled CNC Parts Supplier", based in Toronto. Custom metal parts in about 4 days via CAD upload, plus dedicated reserved CNC machines. Reports thousands of parts shipped. — [YC page](https://www.ycombinator.com/companies/forge-automation)
- **Daedalus (W20, older than the 2024–2026 window):** automated CNC machining for high-mix low-volume parts, $21M Series A. This is per a secondary source and was not fetched. — [Extruct](https://www.extruct.ai/research/industrial-tech-thesis/)
- **horizontal. (F26) ✓:** "AI agents that run factory operations end-to-end". Agents replan production, check material availability, investigate quality issues and sequence order releases inside existing plant systems. — [YC page](https://www.ycombinator.com/companies/horizontal)
- **GUILD (S26) ✓:**
  - Calls itself an "AI-native defense prime" for aerospace precision metals (engine components, brackets, housings).
  - Wins government contracts directly, uses a "company brain" knowledge graph and sells the GUILD Forge planning tool.
  - It appears to rely on partner factories rather than its own machining.
  - Source: [YC page](https://www.ycombinator.com/companies/guild)
- **Nox Metals (S25) ✓:** "Supplying America's Industrial Base". An AI-powered metals supplier with automated, vertically integrated factories converting raw metal to production-ready aluminium plate and block. Steel, tube and sheet are planned. (*Inference:* this matches the Sp26 Modern Metal Mills RFS.) — [YC page](https://www.ycombinator.com/companies/nox-metals)
- **Inflection Space Systems (F26 on one listing; no batch on another) †:** factory capacity for tens of thousands of spacecraft a year. [https://www.ycombinator.com/companies/inflection-space-systems](https://www.ycombinator.com/companies/inflection-space-systems) (constructed) — [YC Industrials listing](https://www.ycombinator.com/companies/industry/industrials); [Manufacturing listing](https://www.ycombinator.com/companies/industry/manufacturing)
- **Further companies from the [Manufacturing listing](https://www.ycombinator.com/companies/industry/manufacturing) †:**
  - **Tenet Industries (P26):** AI and robotics electronics-assembly factory in Munich. [https://www.ycombinator.com/companies/tenet-industries](https://www.ycombinator.com/companies/tenet-industries) (constructed)
  - **ProvenMetal (S26):** US circuit-board manufacturing with automated procurement, design-for-manufacture (DFM) review and assembly, in days. [https://www.ycombinator.com/companies/provenmetal](https://www.ycombinator.com/companies/provenmetal) (constructed)
  - **Resin Technologies (F26):** designs and manufactures validated electronics boards from specs. [https://www.ycombinator.com/companies/resin-technologies](https://www.ycombinator.com/companies/resin-technologies) (constructed) Source: [Hardware listing](https://www.ycombinator.com/companies/industry/hardware).
  - **Sinter (F26):** plastics from prototype to production. [https://www.ycombinator.com/companies/sinter-systems](https://www.ycombinator.com/companies/sinter-systems) (constructed)
  - **Ultrasonium (S26):** new metal-part process claimed to be 15x faster and 75% cheaper. [https://www.ycombinator.com/companies/ultrasonium](https://www.ycombinator.com/companies/ultrasonium) (constructed)
  - **Sidekick (S26):** text-based AI agent running custom-manufacturing shop operations. [https://www.ycombinator.com/companies/textsidekick](https://www.ycombinator.com/companies/textsidekick) (constructed)
  - **Bizmark (S26):** an agent called "Otto" for manufacturer procurement, quoting and production planning. [https://www.ycombinator.com/companies/bizmark](https://www.ycombinator.com/companies/bizmark) (constructed)
  - **Organizely (F26):** AI-native ERP for US manufacturers. [https://www.ycombinator.com/companies/organizely](https://www.ycombinator.com/companies/organizely) (constructed)
  - **OpEra (F26):** AI production planning and scheduling. [https://www.ycombinator.com/companies/opera](https://www.ycombinator.com/companies/opera) (constructed)
  - **Neuron Industries (S26):** AI industrial controller to replace PLCs. [https://www.ycombinator.com/companies/neuron-industries](https://www.ycombinator.com/companies/neuron-industries) (constructed)
  - **Allus AI (F25):** vision models for factory monitoring. [https://www.ycombinator.com/companies/allus-ai](https://www.ycombinator.com/companies/allus-ai) (constructed)
  - **MOVEdot (F25):** agents for hardware test analysis and reporting. [https://www.ycombinator.com/companies/movedot](https://www.ycombinator.com/companies/movedot) (constructed)
  - **Axial (F25):** GPU-native geometry, simulation and manufacturing compute. [https://www.ycombinator.com/companies/axial](https://www.ycombinator.com/companies/axial) (constructed)
  - **HERA (S26):** physical AI design tools for heavy engineering. [https://www.ycombinator.com/companies/manufacturingintelligence](https://www.ycombinator.com/companies/manufacturingintelligence) (constructed)
  - **Normal (S25):** industrial hardware and AI. [https://www.ycombinator.com/companies/normal](https://www.ycombinator.com/companies/normal) (constructed)
  - **Paloma (S25):** software for supply chain and manufacturing operations. [https://www.ycombinator.com/companies/paloma](https://www.ycombinator.com/companies/paloma) (constructed)
- **Prototyping.io (P26) and Hlabs (W26):** cited by name inside the Su26 Hardware Supply Chain RFS. Prototyping.io "helps turn designs into mechanical parts in days" and Hlabs is "building actuators". — [YC RFS, Summer 2026](https://www.ycombinator.com/rfs)

**B. Robotic manufacturing, machine tending, welding and finishing**
- **Odin Robotics (F26) ✓:**
  - "Robot arms that do repetitive manual work in existing factories".
  - The launch demo shows a robot fully tending a CNC mill (load, cycle, unload).
  - Combines deterministic control with learned skills for variable parts and frequent changeovers.
  - Delivers a turnkey cell (robot, end effector, sensors, integration). Team of 2.
  - Source: [YC page](https://www.ycombinator.com/companies/odin-robotics)
- **Pivot Robotics (W24) ✓:** "AI for Robot Arms in Factories". Its first product, Proteus, automates metal grinding using foundation vision models. It is piloting more than 10 systems at a cast-iron foundry and plans to expand to material handling and assembly for high-mix manufacturers. — [YC page](https://www.ycombinator.com/companies/pivot-robotics)
- **Forge Robotics (F25) ✓:** "A robotics intelligence system for metal fabrication". Gives welding robots a live 3D map for real-time seam finding. Later plans modular autonomous factory units from cut parts to welded assemblies. — [YC page](https://www.ycombinator.com/companies/forge-robotics)
- **Shiraz AI (S26) †:** factory robots that learn tasks from a single human demonstration. [https://www.ycombinator.com/companies/shiraz-ai](https://www.ycombinator.com/companies/shiraz-ai) (constructed) — [Manufacturing listing](https://www.ycombinator.com/companies/industry/manufacturing)
- **Advanced Metal Research (P26) †:** robotic welding cells with vision seam tracking and inspection. [https://www.ycombinator.com/companies/advanced-metal-research](https://www.ycombinator.com/companies/advanced-metal-research) (constructed) — [Manufacturing listing](https://www.ycombinator.com/companies/industry/manufacturing)
- **HIRO Industries (W27) †:** two-armed robot for sorting, packing and assembly, using teleoperation plus AI. [https://www.ycombinator.com/companies/hiro-industries](https://www.ycombinator.com/companies/hiro-industries) (constructed) — [Industrials listing](https://www.ycombinator.com/companies/industry/industrials)
- **Robot component makers (match the W27 Robots Made in America RFS) †:**
  - **Silica (F26):** low-cost force-sensing actuators. [https://www.ycombinator.com/companies/silica](https://www.ycombinator.com/companies/silica) (constructed)
  - **Open Actuation (F26):** high-mix drone motors and robot actuators made in Los Angeles. [https://www.ycombinator.com/companies/open-actuation](https://www.ycombinator.com/companies/open-actuation) (constructed)
  - **Mass Magnetics (S26):** US permanent magnets from recycled rare-earth scrap, including DFARS-compliant magnets. [https://www.ycombinator.com/companies/mass-magnetics](https://www.ycombinator.com/companies/mass-magnetics) (constructed)
  - Sources: [Manufacturing listing](https://www.ycombinator.com/companies/industry/manufacturing); [Defense listing](https://www.ycombinator.com/companies/industry/defense)
- **Older companies, per a secondary source (not individually verified):**
  - Maihem (W24): adaptive AI robots for industrial tasks.
  - Verne Robotics (S25).
  - Bucket Robotics (S24): AI defect detection.
  - Autumn Labs (S24): factory equipment monitoring.
  - GroundControl (X25): automation for first-article inspection (FAI), PPAP and AS9102 quality-compliance paperwork.
  - Vendra (S24): marketplace of US manufacturers.
  - Kyten Technologies (W26): aerospace-grade battery-pack manufacturing.
  - Revise Robotics (W25): automated electronics refurbishment.
  - Source: [Extruct, 2026-02-24](https://www.extruct.ai/research/industrial-tech-thesis/). No YC page URLs were captured for these Extruct-only companies.

**C. Data-centre hardware, power and cooling**
- **Applied Kinetics (F26) ✓:**
  - Tagline: "AI-native manufacturing for data center and energy projects".
  - An end-to-end manufacturer of **transformers, switchgear, generators and cooling systems** built to project specs, through a manufacturing network in the US, Europe, LatAm and APAC.
  - AI agents review specs, schedule production, track orders and flag delays. Humans handle design approval, QA and freight.
  - Claims a pad-mount transformer in 7 weeks versus up to 65 weeks on the open market.
  - The page does not mention liquid cooling, cold plates or CDUs. Team of 2; founded 2026; primary partner Harj Taggar.
  - Source: [YC page](https://www.ycombinator.com/companies/applied-kinetics)
- **Pacific (S26) ✓:** "Robotic factories to mass produce data centers". Factory-built modular pods deployed on stalled sites. Claims diamond wafers in its cooling system and plans to vertically integrate transformers and switchgear. Pods are financed "like aircraft". — [YC page](https://www.ycombinator.com/companies/pacific)
- **Madrone (Spring 2026, shown as P2026 in the directory) ✓:** "Hyper-efficient coolers for data centers". Dew-point modular cooling claiming up to 30% power and water savings in Texas; also chiller-less desert cooling. Not cold plates. — [YC page](https://www.ycombinator.com/companies/madrone)
- **Kara (S26) ✓:** "Making Diamond Semiconductors". Ultra-pure diamond wafers and diamond thermal parts, including heat spreaders for AI and HPC and diamond-metal composites. — [YC page](https://www.ycombinator.com/companies/kara)
- **Ferveret (S21, outside the window):** liquid cooling inspired by nuclear-plant cooling. Its Lambert unit is immersion, not cold plate. — [YC page](https://www.ycombinator.com/companies/ferveret-inc); [DCD](https://www.datacenterdynamics.com/en/analysis/ferveret-liquid-cooling-immersion-cooling-data-center/)
- **From the [Energy listing](https://www.ycombinator.com/companies/industry/energy) and [Industrials listing](https://www.ycombinator.com/companies/industry/industrials) †:**
  - **Aikido Technologies (F26):** offshore ocean-cooled data centres on wind platforms. [https://www.ycombinator.com/companies/aikido-technologies](https://www.ycombinator.com/companies/aikido-technologies) (constructed)
  - **Liquid Energy (F26):** modular "NanoDC" units. [https://www.ycombinator.com/companies/liquid-energy](https://www.ycombinator.com/companies/liquid-energy) (constructed)
  - **Atomarine (S26):** nuclear power ships for floating compute. [https://www.ycombinator.com/companies/atomarine](https://www.ycombinator.com/companies/atomarine) (constructed)
  - **Rewbi (S24):** 1–10MW distributed data centres in industrial buildings. [https://www.ycombinator.com/companies/rewbi](https://www.ycombinator.com/companies/rewbi) (constructed)
  - **Voxel Energy (W26):** on-site generation and storage using second-life EV batteries. [https://www.ycombinator.com/companies/voxel-energy](https://www.ycombinator.com/companies/voxel-energy) (constructed)
  - **NODI Energy (P25):** edge batteries for data-centre grid congestion. [https://www.ycombinator.com/companies/nodi-energy](https://www.ycombinator.com/companies/nodi-energy) (constructed)
  - **Talos (F26):** predictive maintenance for power transformers. [https://www.ycombinator.com/companies/talos-us](https://www.ycombinator.com/companies/talos-us) (constructed)
  - **Viraj Aero (F26 on one listing):** gas turbines that also supply data-centre cooling water. [https://www.ycombinator.com/companies/viraj-aero](https://www.ycombinator.com/companies/viraj-aero) (constructed)
  - **Marengo (S26):** AI engineering design automation, starting with data centres. [https://www.ycombinator.com/companies/marengo](https://www.ycombinator.com/companies/marengo) (constructed)
  - **Maingen (S26):** industrial simulations for plants and data centres. [https://www.ycombinator.com/companies/maingen](https://www.ycombinator.com/companies/maingen) (constructed)
  - **Astro (W25):** finds power-ready land. [https://www.ycombinator.com/companies/astro](https://www.ycombinator.com/companies/astro) (constructed)
- **Dipole Labs (Summer 2026 batch):** optical networking hardware that keeps data as light to cut power and heat. **Lamb Labs (S26):** inference chips with model weights in silicon. Both were among the "9 buzziest" companies at the Sept 2026 Demo Day. — [TechCrunch, 2026-09-13](https://techcrunch.com/2026/09/13/the-9-buzziest-startups-from-y-combinators-latest-demo-day-according-to-vcs/)
- **Archgen Labs (F26) †:** AI 3D-chip design tools, including LayerTherm thermal analysis. [https://www.ycombinator.com/companies/archgen-labs](https://www.ycombinator.com/companies/archgen-labs) (constructed) — [Hardware listing](https://www.ycombinator.com/companies/industry/hardware)
- **Stoa (S26) †:** GPU pricing and trading infrastructure. [https://www.ycombinator.com/companies/stoa](https://www.ycombinator.com/companies/stoa) (constructed) — [Hardware listing](https://www.ycombinator.com/companies/industry/hardware)

**D. Data-centre robotics (install, service, commissioning)**
- **Nines (F26) ✓:** "Robot pit crew for AI data centers". During construction its robots match, insert and verify thousands of fibre connections per GPU rack. On live sites they swap drives, transceivers and fans. — [YC page](https://www.ycombinator.com/companies/nines)
- **Proprio Robotics (S26) ✓:** "Robots to maintain and assemble data centers". Covers onshore server assembly, 24/7 maintenance and dismantling for GPU and memory recovery. Plans maintenance-robot deployment in Q1 2027. — [YC page](https://www.ycombinator.com/companies/proprio-robotics)
- **Shepherd Robotics (F26) ✓:** "Robots for high skilled labor powering AI infrastructure". Uses general-purpose robots on robot foundation models. First applications are data-centre commissioning and inspection, plus electrical assembly (wire routing, terminal insertion). Electronics manufacturing and test are also targets, with human supervision. — [YC page](https://www.ycombinator.com/companies/shepherd-robotics)
- **Boost Robotics (Spring 2025) ✓:** "Robots for the inspection and maintenance of data centers". Mobile manipulators doing hands-on work without an on-site technician, based in Boston. — [YC page](https://www.ycombinator.com/companies/boost-robotics)
- **DeepAware AI (Summer 2025):** AI control for data-centre facilities. This comes from a search summary only and was not fetched. — [YC page (search result)](https://ycombinator.com/companies/deepaware-ai)
- **Cosmic Robotics (S26):** a 10,000-lb heavy-lift robot installing solar. The data-centre construction claim comes from a search snippet; the Runtimewire article was not fetched. — [Runtimewire](https://runtimewire.com/article/cosmic-robotics-yc-s26-solar-data-center-construction-robot); [TechCrunch](https://techcrunch.com/2026/09/13/the-9-buzziest-startups-from-y-combinators-latest-demo-day-according-to-vcs/)
- **Mantle (F26) †:** field-service company that deploys, fixes and maintains machines for manufacturers. This is general machine field service, not specifically data-centre robotics. [https://www.ycombinator.com/companies/mantle-2](https://www.ycombinator.com/companies/mantle-2) (constructed) — [Robotics listing](https://www.ycombinator.com/companies/industry/robotics)

**E. Test and inspection**
- **Hundred (F26) †:** automated optical inspection catching sub-100µm defects in device components. [https://www.ycombinator.com/companies/hundred](https://www.ycombinator.com/companies/hundred) (constructed) — [Hardware listing](https://www.ycombinator.com/companies/industry/hardware)
- **Hilstart (S26) †:** physical agent harnesses that let AI debug and validate hardware. **Hardware Intelligence (S26) †:** WaveZip waveform capture for test failures. **Evident Machines (F26) †:** RL environments for AI electrical engineering, validated in a physical lab. Constructed URLs: https://www.ycombinator.com/companies/hilstart, https://www.ycombinator.com/companies/hardware-intelligence, https://www.ycombinator.com/companies/evident-machines. — [Hardware listing](https://www.ycombinator.com/companies/industry/hardware)
- **Salem Robotics (S26) †:** robot software for hazardous-site inspections and compliance records. **Kanopy (F26) †:** video risk detection for power lines and pipelines. Constructed URLs: https://www.ycombinator.com/companies/salem-robotics-inc, https://www.ycombinator.com/companies/kanopy. — [Robotics listing](https://www.ycombinator.com/companies/industry/robotics); [Industrials listing](https://www.ycombinator.com/companies/industry/industrials)
- **Gecko Robotics (W16, outside the window):** inspection robots. It is repeatedly cited by YC partners in the RFS (Su24, W25, Su25, F26). — [YC RFS](https://www.ycombinator.com/rfs)

**F. Defence hardware ([Defense listing](https://www.ycombinator.com/companies/industry/defense) †, unless noted)**
- **F26:**
  - Keres: reusable unmanned jet interceptors.
  - Polemos Industries: AI-guided ballistic missiles and compact launchers.
  - Caladh: maritime counter-drone.
  - Kairox Systems: amphibious drone.
  - Streamline Systems: GPS-independent navigation modules.
  - Super Powers Mobility: high-voltage battery packs and power electronics.
  - ChemPilot.ai: AI and an automated wet lab for defence materials.
- **S26:**
  - IMPACT Drones: containerised interceptor drones as a service.
  - Vernius Systems: low-cost radar seekers for interceptors.
  - Earendil Robotics: small-unit counter-drone.
  - Greypoint Industries: emitter-hunting drone swarm.
  - Isengard Industries: allied-nation production of strike and counter-drone systems, also a TechCrunch "buzziest" pick.
  - Hop Aero: rocket cargo.
  - Edgerun: military exoskeletons.
  - GUILD ✓: described in group A.
  - Mass Magnetics: described in group B.
- **P26 (Spring 2026):**
  - Arlo Industries: passive sensor mesh.
  - Surtr Defense Systems: counter-UAS sensor-fusion OS.
  - AICE: marine drone swarms.
  - 9 Mothers: low-cost counter-drone, already selling to the Department of War.
  - BayMachines: air-gapped GPU containers for defence.
- **Earlier batches:**
  - W26: Seeing Systems (strike drones), DAIVIN!.
  - F25: Null Labs (defence simulation), Icarus (solar high-altitude aircraft), Prox (ramjet weapon, "scalable production").
  - S25: Albacore (mass-producible underwater drones), Perseus Defense (mass-manufactured counter-UAS missile).
  - W25: Conntour.
  - W24: Deepnight (AI night vision).
- **Further defence companies, per a secondary source:** Ares Industries (S24, low-cost cruise missiles), Splash Industries (W25, autonomous patrol boats), SalesPatriot (W25), Usul (S24). — [Extruct](https://www.extruct.ai/research/industrial-tech-thesis/)

- **Constructed YC URLs for the defence companies above** (prefix https://www.ycombinator.com/companies/): keres, polemos-industries, caladh, kairox-systems, streamline-systems, super-powers-mobility-spm, chempilotai, impact-drones, vernius-systems-inc, earendil-robotics, greypoint-industries, isengard-industries-inc, hop-aero, edgerun, arlo-industries, surtr-defense-systems, aice, 9-mothers-corporation, baymachines, seeing-systems, daivin, null-labs, icarus, prox, albacore-inc, perseus-defense, conntour, deepnight. Ares Industries, Splash Industries, SalesPatriot and Usul are Extruct-only; no URL was captured.

**G. Energy hardware ([Energy listing](https://www.ycombinator.com/companies/industry/energy) †)**
- **F26:**
  - Ailit: battery wagons for diesel locomotives.
  - Micora: palletised solar plus robots that deploy it.
  - Invertix: AI for autonomously operating power plants.
- **S26:** Atomarine (nuclear power ships), Cosmic Robotics (solar install robots).
- **W25:** Maritime Fusion.
- **F25:** Zephyr Fusion.
- **S24:** Ionworks (battery simulation).
- **Older:** Steinmetz Motors (W25, EV motor controllers), per [Extruct](https://www.extruct.ai/research/industrial-tech-thesis/).

- **Constructed YC URLs for the energy companies above** (prefix https://www.ycombinator.com/companies/): ailit, micora, invertix, atomarine, cosmic-robotics, maritime-fusion, zephyr-fusion, ionworks. Steinmetz Motors is Extruct-only; no URL was captured.

**Context stats (secondary)**
- YC industrial companies per year, per Extruct: 18 (2021), 3 (2023), 21 (2024), 24 (2025), 21 (W26). — [Extruct, 2026-02-24](https://www.extruct.ai/research/industrial-tech-thesis/)

### Inferences
- *Inference:* **twentyfour26, Antropi and Forge Automation are direct competitors** to the "robotic machine-tending / agent-run CNC contract manufacturing" alternative.
  - The two F26 companies use near-identical language ("autonomous factories", "dark factories", CAD-to-part agents).
  - YC has therefore already funded at least two versions of that idea in the same batch.
  - Odin Robotics covers the "sell machine-tending cells to shops" variant.
- *Inference:* **Applied Kinetics is the closest YC analogue to the cold-plate idea's business model.** It is an AI-native, agent-coordinated manufacturer of sold-out data-centre equipment, cooling included.
  - However, it appears to coordinate a *network* of existing factories rather than run a robotic factory itself.
  - A cold-plate company would differ in having a narrower product, owned automated production and in-house thermal design.
- *Inference:* data-centre install and service robotics is crowded inside YC: Nines, Proprio, Shepherd, Boost and arguably Pacific and Cosmic. That is four or more companies across Spring 2025 to F26.
- *Inference:* the absence of a YC cold-plate or CDU manufacturer is a white space. It may also suggest YC has not yet seen a strong team there. Either reading is speculative.

### Gaps
- **Directory coverage:** YC directory industry pages returned only the first ~50 companies, newest first ("Loading more companies..."). W24–W25 coverage therefore rests mainly on Extruct (a vendor-research secondary source) and individual fetches. Older 2024–2025 companies in these spaces are likely missing.
- **Directory API:** the companies directory's search API could not be used (the access attempt was blocked), so keyword searches such as "CNC", "cold plate" or "thermal" were not run against it.
- **Cold-plate search:** a web search restricted to ycombinator.com for "cold plate / direct-to-chip / liquid cooling" returned only Ferveret. I found no YC cold-plate manufacturer in the searches I ran. That does not establish that none exists. — [search result: Ferveret](https://www.ycombinator.com/companies/ferveret-inc)
- **Inconsistent batches:** batch labels for Inflection Space Systems and Viraj Aero differ between directory pages.
- **Unverified claims:** funding amounts and company performance claims (lead times, parts shipped) are self-reported and were not verified.

---

## Q5. YC partner essays, podcasts and Lightcone episodes on hard tech, manufacturing and robotics

### Takeaway
YC's most recent public framing, from a YC podcast episode in September 2026 (probably the "State of Startups 2026" episode; the identification is an inference), is that "startups are moving from bits to atoms". Hard tech reportedly rose from 8% to 20% of accepted companies in 12 months, and "full-stack" companies from 10% to over 25%. The RFS texts themselves are the main partner essays, each with a short video.

### Cited Findings
- **YC on X:** "startups are moving from bits to atoms, nearly one in five YC companies has a solo founder, and companies are reaching meaningful revenue…" — [Y Combinator on X](https://x.com/ycombinator/status/2100653734326092236). Text is from a search snippet; the post itself was not fetched.
- **Episode metadata:** the episode is titled "The State of Startups 2026: bits to atoms, solo founders and hard tech", dated September 2026. It describes the shift from software toward physical hard tech and defence, and AI compute becoming physical infrastructure. — [Dealroom listing](https://dealroom.co/news/talk-yslXlV2BP_Y-the-state-of-startups-2026-bits-to-atoms-solo-founders-and-hard-tech/)
  - The YouTube id yslXlV2BP_Y gives https://www.youtube.com/watch?v=yslXlV2BP_Y. That URL is constructed and was not fetched.
  - Reported chapters include "Defense, Manufacturing, and the Return of Hard Tech" and "Robotics Is Approaching Its ChatGPT Moment" (12:34). — [search summary of YC post](https://x.com/ycombinator/status/2100653734326092236); [Digg](https://digg.com/ai/t6kaco4i)
- **Episode stats** (podcast dated 2026-09-18, per a secondary write-up of YC's analysis of the prior 12 months of accepted companies). Scuttlebutt gives no episode title. Matching these stats to the Dealroom-titled "State of Startups 2026" episode is an *inference* from matching dates and topics:

  | Category | Before | After |
  |---|---|---|
  | Hard tech | 8% | 20% |
  | Industrial manufacturing | ~4% | ~10% |
  | Robotics | ~1% | ~6–7% |
  | Defence | ~1.5% | ~5% |
  | Semiconductors / photonics | ~1% | ~4% |
  | Power infrastructure | ~1% | ~3% |
  | "Full-stack or end-to-end" companies | 10% | >25% |
  | Solo founders | ~5% | >18% |
  | Median end-of-batch revenue | ~$8K/month | ~$20K/month |

  - Quote: hard tech means "Things that actually touch atoms and not just bits."
  - Several figures are host estimates.
  - Source: [Scuttlebutt, 2026-09-19](https://daily.scuttlebutt.co/p/hard-tech-went-from-8-to-20-of-the)
- **TechCrunch on Demo Day (2026-09-13):** the summer 2026 batch skewed "far more toward deep tech than in past years". The 9 VC-favoured picks included Atomarine, Dipole Labs, Isengard Industries, Lamb Labs, Nori, Cosmic Robotics and Waddle Labs. — [TechCrunch](https://techcrunch.com/2026/09/13/the-9-buzziest-startups-from-y-combinators-latest-demo-day-according-to-vcs/)
- **Lightcone Ep. 5, "Inside The Hard Tech Startups Turning Sci-Fi Into Reality" (April 2024):** covers YC companies building satellites, rockets and electric planes. — [YC Startup Library](https://www.ycombinator.com/library/Kq-inside-the-hard-tech-startups-turning-sci-fi-into-reality-lightcone-podcast-ep-5); [Spotify](https://creators.spotify.com/pod/profile/lightconepodcast/episodes/Inside-The-Hard-Tech-Startups-Turning-Sci-Fi-Into-Reality-e2j26n2)
- **Robotics episode with Physical Intelligence:** a search summary mentions a Lightcone episode with Physical Intelligence co-founder Quan Vuong on robotics' scaling moment and vertical robotics companies. Title, date and URL were not confirmed. — [Lightcone on Apple Podcasts](https://podcasts.apple.com/us/podcast/lightcone-podcast/id1743860177)
- **Partner theses inside the RFS** (verbatim, [YC RFS](https://www.ycombinator.com/rfs)):
  - Diana Hu authored or coauthored ML Simulation and ML Robotics (Su24), AI-Aided Engineering (W25), Datacenters, AI Coding Agents for Hardware-Optimized Code and Inference AI Infrastructure (Sp25), AI for Scientific Advancement and Software Tools To Make Robots (Su25), Inference Chips and Semiconductor Supply Chain (Su26), Data for the Real World (F26, coauthor), and Robots Made in America and Vertical Foundation Models (W27). That is 13 by my own tally of the bundle. (*Inference:* she is the most relevant YC partner for this space.)
  - Jared Friedman authored Manufacture in the USA (W25), New Defense Technology (Su24), Full-stack AI (Su25) and Data Center Supply Chain (W27).
  - Nicolas Dessaigne authored Hardware Supply Chain (Su26) and is listed as primary partner for Antropi Robotics. — [Antropi YC page](https://www.ycombinator.com/companies/antropi-robotics)
  - Harj Taggar authored Retraining Workers (F25) and is primary partner for Applied Kinetics. — [Applied Kinetics YC page](https://www.ycombinator.com/companies/applied-kinetics)

### Inferences
- *Inference:* YC's stated batch mix (hard tech 20%, full-stack >25%, industrial manufacturing ~10%) suggests a cold-plate autonomous factory fits squarely within what YC is currently accepting.
  - It also means competition for "hard tech" slots and partner attention is now much greater than in 2024.
  - Partners will likely compare it with twentyfour26, Antropi and Applied Kinetics.
- *Inference:* Diana Hu, Jared Friedman, Nicolas Dessaigne and Harj Taggar are the partners whose published theses or portfolio most overlap the idea. Friedman wrote the liquid-cooling bottleneck request; Dessaigne is partner to an autonomous-CNC company; Taggar is partner to an AI-native data-centre equipment maker.

### Gaps
- **Unfetched primary:** the YC primary page or video for the September 2026 "State of Startups 2026" episode was not fetched. The statistics come from Scuttlebutt and Dealroom (secondary), and some are host estimates.
- **Physical Intelligence episode:** no confirmed title, date or URL.
- **Blog search:** no YC blog essays specifically on reindustrialisation or manufacturing were found in the time available. The YC blog (ycombinator.com/blog) was not systematically searched.
- **YC Library:** the YC Startup Library was not searched for other hard-tech talks, such as Demo Day or batch-analysis posts.
