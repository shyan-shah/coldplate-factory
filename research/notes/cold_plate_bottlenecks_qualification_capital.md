# Cold Plates for AI Data Centres: Bottlenecks, Supplier Qualification, Capital Requirements and Key Risks for a New Entrant

Research date: 2026-11-19. Dates are given for every source where known. Several key DigiTimes articles are paywalled; for those only the lead paragraph was readable, and details come from secondary outlets that cite DigiTimes (flagged).

---

## 1. Manufacturing processes, equipment, cycle times, yields, and who holds capacity

### Takeaway
Standard cold-plate capacity (skived/CNC copper plus brazing) is held at very large scale by a few Taiwanese thermal makers. AVC is expanding about 5x in 2026. Whether standard plates are short is DISPUTED: AVC's chairman says capacity "still cannot meet client demand", while one Sept 2026 aggregator table relaying a single CLS investigation calls standard plates "relatively ample". Both agree that high-power custom (>1 kW) and microchannel (MLCP/MCL) plates, which need semiconductor-grade processes, are the tightest. Public data on process cycle times and yields is almost absent.

### Cited Findings
**Capacity holders and expansions (Taiwan / China / Vietnam)**
- AVC (Asia Vital Components) plans to lift cold-plate capacity 5x, from 200,000 units at end-2025 to 1 million units by end-2026. The article does not say whether this is per month. Manifold capacity goes from 1,000 to 7,000 units/month and chassis output from about 400k to 600,000 units/month. Capex is NT$15bn (US$472M) in 2026 and NT$17bn (US$534M) in 2027. The chairman says capacity "still cannot meet client demand" (TVBS World, released 2026-04-16, updated 2026-10-02) — [TVBS World / t.media](https://t.media/3179423). DigiTimes lead (2026-03-12): AVC will "significantly expand" cold plate, manifold and chassis output in 2026, the "liquid cooling era" — [DigiTimes](https://www.digitimes.com/news/a20260312PD226/avc-liquid-cooling-chassis.html)
- AVC is estimated to hold 40–50% of the cold-plate market for NVIDIA GB200/GB300. Its Q1 2026 revenue was NT$49.04bn (+110% YoY), and liquid cooling is about 30% of sales — [TVBS World / t.media](https://t.media/3179423)
- **Source-identity warning.** A third-party call-summary site (FinmoConf) labels this page "Auras Technology (3017.TW)", call dated 2026-05-14. But 3017.TW is AVC's ticker (Auras is 3324.TW), and the page's figures match AVC's exactly: capex NT$15bn (2026) / NT$17bn (2027), and module capacity from 200,000 to 1 million/month. This page is therefore likely AVC's call mislabelled, and should NOT be counted as an independent second 5x expansion. Its content: liquid-cooling module capacity "from 200,000 units a month to 1 million" (which suggests AVC's 200k→1M figure is per month); work on "all six tray designs" in NVIDIA's Vera Rubin/Blackwell family; work on "every US hyperscaler ASIC programme"; chassis/manifold expansion in Vietnam and China; ASIC revenue expected to overtake GPU revenue in 2027; Q1 2026 gross margin 29.77% (+3.94 pts YoY) — [FinmoConf call summary](https://finmoconf.diveinvest.net/en/auras/2026-q1)
- A separate search snippet (not fetched; URL unconfirmed) said Auras secured ASIC cold-plate orders from the four largest CSPs, with mass production from 2H26.
- **Source-dependence note:** the BigGo Finance table and the remio.ai summary below both appear to relay the same CLS (cls.cn) investigation of 2026-09-06. Both are low-grade aggregators and should be treated as ONE source, not two. That source conflicts with AVC's chairman (above) on whether standard plates are short.
- An industry table (BigGo Finance, 2026-09-06) rates standard cold plates "relatively ample", because "Taiwanese majors have monthly capacity in the millions". It rates high-power custom plates (>1,000 W) "tight" and MLCP microchannel plates the "largest gap", because they require "semiconductor-grade processes" and "Chinese players [are] still sampling". It also says "Traditional skived-fin processes have reached their limits" and cites "large-scale CNC and vacuum brazing capacity" as a China advantage — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- Another secondary summary of a CLS (cls.cn) investigation (2026-09-06) says customized plates above 1 kW remain constrained. It also says precision machining, vacuum bonding and customer certification take longer to expand than assembly. Several mainland Chinese suppliers were still sampling MLCPs, while Jentech, Auras and AVC hold an earlier position — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- Chinese contract makers are advertising large capacity. For example, one Chinese maker claims about 1,000,000 cold plates/year from a 30,000 m² facility, with prototypes in 4–6 weeks from 1 piece and production in 6–8 weeks (vendor claim) — [Tone Cooling](https://tonecooling.com/custom-liquid-cold-plate-design-order-guide/)
- KGI (2025-10-27) expects Jentech to be the "first and main supplier" of NVIDIA microchannel lids (MCL), with significant sales after 2H26/2027. MCL integrates heat spreader, TIM2 and cold plate. "Fluid reliability and manufacturing scalability" remain challenges — [KGI thermal sector report](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf)
- Jentech co-develops microchannel lids with NVIDIA and other chipmakers, citing Rubin packages of about 2,300 W. This is a search snippet only; the attribution to this URL is unconfirmed — [Jentech](https://www.jentech.com.tw/post/nvidia-ai-factory-mgx-ecosystem-jentech). KGI independently gives Rubin GPU TDP as 2.3 kW — [KGI](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf)

**Processes**
- A vendor blog says GB200-class microchannel cold plates are typically made by skiving thin fins directly from a copper base. It cites laminar flow (Re < 2000) and a target pressure drop under about 20 kPa (vendor claim) — [FiberMall](https://www.fibermall.com/blog/nvidia-gb200-liquid-cooling-plate.htm)
- An academic paper puts state-of-the-art copper fin structures at fin thickness and spacing of about 100–200 µm and fin height of about 1–2 mm (aspect ratio 10–20) — [Villanova/ASME paper via NSF PAR](https://par.nsf.gov/servlets/purl/10435523)
- Electrochemical additive manufacturing (ECAM, Fabric8Labs with U. Illinois) produced pure-copper cold plates with sub-100 µm features and up to 32% lower thermal resistance than pin-fin designs at a fixed flow rate — [UIUC MechSE](https://mechse.illinois.edu/news/82871)
- A trade-press piece says AVC and Auras invested heavily in ultra-precision CNC fly-cutting to finish brazed cold-plate surfaces to <15 µm flatness. This is a Substack source; low confidence — [Silicon Infra Alpha (Substack)](https://siliconinfraalpha.substack.com/p/why-gb200-delay-rumors-were-mathematically)
- Cold plates are CNC-machined to micron tolerances, often from copper billet. Fabrication adds about 30–50% on top of raw material cost — [The Cooling Report](https://thecoolingreport.com/intel/data-center-cooling-supply-chain-guide-2026.html)

### Inferences
- (Inference) Skiving, brazing and CNC capacity for standard plates is not the binding constraint. The Taiwanese majors are adding capacity faster than a startup could, with US$0.5bn/year capex at AVC alone. Scarcity sits in (a) >1 kW custom plates and (b) microchannel/MLCP/MCL processes, where process know-how and yield matter more than machine count.
- (Inference) The industry is moving from skived fins toward microchannel lids and etched or AM microstructures. Any new factory built around skiving/brazing for 2027+ NVIDIA platforms may target a process that is being superseded at the top end.

### Gaps
- No public cycle times or yields for skiving, vacuum brazing, diffusion bonding or FSW of cold plates were found. One Substack claims a "99.4% loop yield" for GB200, but it is unverified.
- No public data on US or Mexico cold-plate capacity or shortages was found. Vietnam appears only via Auras expansion; China via Chinese makers (Envicool, Tone Cooling).
- No source gave dedicated diffusion-bonding capacity or cost data.
- No metal fin-skiving machine price was found. The search returned only leather skiving machines and was not retried.

---

## 2. Reported supply-chain bottlenecks for liquid cooling, 2024–2026

### Takeaway
The bottlenecks cited are: (1) quick disconnects (UQDs), for both leaks and capacity; (2) CDUs; (3) high-power custom and microchannel cold plates; and (4) manifolds and pumps. The evidence base is thin. The explicit ranking comes from ONE CLS investigation (2026-09-06), relayed by two low-grade aggregators (BigGo, remio.ai). It is supported by a TrendForce QD-shortage forecast (Mar 2025), KGI QD part counts (Oct 2025), and DigiTimes-sourced reports of GB200 QD leaks. No source names cold-plate design as a bottleneck. AVC's chairman does say cold-plate capacity is short (section 1). GB200 leak problems centred on quick connectors, hoses and branch pipes, not the cold plate body.

### Cited Findings
**Leaks / reliability (GB200)**
- Late 2024 Taiwanese reporting attributed GB200 cabinet leaks to outsourced water-cooling parts: "branch pipe, quick connector, and hose" — [TweakTown](https://www.tweaktown.com/news/99446/nvidias-new-gb200-ai-server-cabinets-leaks-in-liquid-cooling-system-emergency-work-to-fix-it/index.html)
- Tom's Hardware, citing DigiTimes (mid-2025), reported that GB200 racks kept having liquid-cooling problems while shipping in volume. Quick-connect fittings were the main failure point, despite factory stress tests, and operators responded with localized shutdowns and extra leak testing. A commenter disputed whether DigiTimes actually said "widespread" leaks. Page body not retrievable; details from search summary — [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/large-scale-shipments-of-nvidia-gb300-servers-tipped-to-start-in-september-gb200-demand-remains-robust-despite-widespread-coolant-leak-reports)
- The Financial Times, via Tom's Hardware (May 2025), reported that suppliers spent "several months" fixing overheating and liquid-cooling leaks before the GB200 ramp — [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/nvidia-gb200-production-ramps-up-after-suppliers-tackle-ai-server-overheating-and-liquid-cooling-leaks)
- The Information, via TechSpot (Jan 2025), reported that Microsoft, AWS, Google and Meta delayed GB200 orders over overheating and other rack issues. It did not attribute these specifically to leaks — [TechSpot](https://www.techspot.com/news/106338-nvidia-best-customers-postponing-blackwell-chip-orders-due.html)

**Quick disconnects**
- TrendForce (2025-03-10) said GB300 may need about 4x the quick disconnects of GB200, so a QD shortage was expected. This is a forecast — [TrendForce](https://www.trendforce.com/news/2025/03/10/news-nvidia-to-unveil-gb300-at-gtc-with-shipment-reportedly-to-begin-in-may-driving-cooling-demands/)
- KGI (2025-10-27): GB300 has 27 cold plates per switch tray (vs 18 in GB200) and 180 QDs per switch tray (vs 0 in GB200), on top of 180 QDs in compute trays. Liquid-cooling content per GB300 rack is +10–20% vs GB200. AWS Trainium 2.5/3 racks are estimated at 99 cold-plate modules and 456 QDs per rack — [KGI](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf)
- A KGI survey (via a supply-chain analysis site) estimated that moving from GB200 to GB300 raises QD demand about 80.7% per 100 MW campus — [Energy Solutions](https://energy-solutions.co/supply-chain/ai-data-centers/data-center-liquid-cooling-cdu-heat-exchanger-coupling-supply)
- An industry table (2026-09-06) rates the UQD "tightest", with "Few qualified suppliers; capacity lags delivery schedules", and an expansion time of 1–2 years — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- OCP UQD v2.0.0 is reported effective 2026-09-22. It merges hand-mate and blind-mate specs, raises minimum Cv and requires cross-supplier verification. Vendor blog; not verified against OCP directly — [Apaltek](https://www.apaltek.com/liquid-cooling-quick-disconnect/)

**CDUs, manifolds, pumps**
- A CLS investigation (2026-09-06, via secondary summary) said CDUs were the tightest equipment category, with orders commonly running through end-2026 — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology). BigGo's table says standard CDUs are "gradually loosening" (pure assembly), but hyperscale high-redundancy CDUs are tight — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- Manifolds and high-end pumps/valves are rated "tight" because of "high engineering precision; concentrated supply". Pumps take 3–5 months from order to shipment for higher-power units — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- Lead times in normal conditions (2026): cold plates 12–16 weeks; CDUs 16–24 weeks; custom stainless manifolds 8–12 weeks; chillers 20–30 weeks — [The Cooling Report](https://thecoolingreport.com/intel/data-center-cooling-supply-chain-guide-2026.html)
- Coolant is also flagged: 3M's PFAS exit removed about 12,000 t of fluorinated fluid capacity, with a 2–3 year rebuild cycle. This mainly affects two-phase and immersion — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)

**Copper**
- LME 3-month copper hit a record of about US$14,533/t on 2026-09-08 (intraday reports up to about US$14,697). COMEX hit a record US$6.714/lb on 2026-08-12, carrying a US$400–600/t premium over LME in summer 2026, on US tariff uncertainty. A US copper tariff targeting 15% from 2027-01-01 and 30% from 2028 is reported — [DT Next](https://www.dtnext.in/news/business/copper-hits-record-high-above-14500-on-us-tariff-fears); [Skillings](https://www.skillings.net/copper-hits-record-14697-as-tariff-deadline-tightens-supply/); [Crux Investor](https://www.cruxinvestor.com/posts/us-copper-imports-hit-12-year-high-cutting-lme-stocks-14-raising-delivery-premiums)
- Forecasts conflict on supply: CRU sees a 639,000 t 2026 surplus, while ING projected a deficit of about 600,000 t — [Crux Investor](https://www.cruxinvestor.com/posts/coppers-record-run-masks-a-639-000-tonne-surplus-risk)

### Inferences
- (Inference) Tentative ranking, leaning heavily on the single CLS-derived table plus TrendForce/KGI/DigiTimes: QD/UQD capacity and leaks > CDUs > high-power/microchannel cold plates > manifolds/pumps > coolant chemistry > copper price. No source found names cold-plate design lead time as a bottleneck. This ranking needs corroboration from primary sources (supplier earnings calls, TrendForce/DigiTimes full text).
- (Inference) Copper is a cost and margin risk, not an availability bottleneck. At about US$14.5k/t, an ASSUMED 1–2 kg copper plate (plate mass is unsourced) carries roughly US$15–30 of metal, against an ASP of about US$300–500 (see section 5). Copper is meaningful for a US-based maker facing a COMEX premium and tariffs, but it is not decisive.

### Gaps
- The original The Information and DigiTimes articles on GB200 leaks were not retrievable (paywall/403). Fetch failures: the Tom's Hardware leak-article body was truncated, the Yahoo mirror (tech.yahoo.com) returned 403, and the Data Center Dynamics CoolTera article returned 403. There is no quantified leak rate or share of delays attributable to leaks.
- No primary statements from CPC/Dover, Stäubli, Parker or Danfoss on UQD capacity or lead times were found.

---

## 3. Who controls the spec and approved vendor lists

### Takeaway
For NVIDIA platforms, NVIDIA increasingly controls cold-plate selection directly. For Vera Rubin it centralised cold-plate procurement and named four suppliers (AVC, Cooler Master, Jentech, Delta). This removes ODM-level discretion. OCP provides the open test baseline (Cold Plate Test Spec v1.0.0, Sept 2026; UQD v2), but OCP specs set test methods, not vendor lists. Hyperscaler ASIC programmes (AWS Trainium, Google, Meta, Microsoft) are the main non-NVIDIA buyers, served so far by the same Taiwanese majors.

### Cited Findings
- DigiTimes (2025-11-17): NVIDIA is "tightening control over both assembly and key thermal components" for Vera Rubin as liquid cooling becomes mandatory — [DigiTimes](https://apps.digitimes.com/news/a20251117PD218/nvidia-rubin-supplier-liquid-cooling-supply-chain.html)
- DigiTimes (2026-03-18/19): NVIDIA is standardising Vera Rubin liquid cooling and named four cold-plate suppliers at GTC 2026 (lead only visible) — [DigiTimes](https://www.digitimes.com/news/a20260318PD231.html). The aggregator summary of the DigiTimes text says "The company will centralize procurement of cold plates" and names AVC, Cooler Master, Jentech and Delta Electronics — [Ground News](https://ground.news/article/nvidia-standardizes-vera-rubin-liquid-cooling-names-four-cold-plate-suppliers_797c41)
- Auras is not on that four-name list. A call-summary page labelled "Auras" claims work on "all six tray designs" for Vera Rubin/Blackwell, but that page is likely AVC's call mislabelled (ticker 3017.TW is AVC; see section 1). The claim fits AVC, which is on the list — [FinmoConf call summary](https://finmoconf.diveinvest.net/en/auras/2026-q1)
- DigiTimes (2026-05-15): design issues tied to a Rubin cooling-architecture change "have largely been resolved" (snippet) — [DigiTimes](https://digitimes.com/news/a20260515PD223/rubin-nvidia-cooling-hbm4-design.html). Rubin reportedly moved to a larger cold-plate design after a two-piece approach raised package-warping concerns — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- OCP Single-Phase D2C Cold Plate Test Specification v1.0.0 is effective 2026-09-03. Authors are from CoolIT Systems, PFX Group, Fabric8Labs and INFICON; Intel and ChemTreat gave feedback. It defines methods, not platform limits: "Future Product Specifications may reference these methods and tighten acceptance limits." It explicitly aims to let "operators … qualify alternate and second-source cold plates against one objective criterion" — [OCP spec PDF](https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Cold-Plate-Test-Specification-V1.0.0.pdf)
- KGI: AWS will liquid-cool Trainium 2.5/3, with higher cold-plate and QD content per rack than GB300. AMD MI400 Helios racks adopt liquid cooling — [KGI](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf)
- Jentech is reportedly targeting ASIC servers, with cold-plate revenue from 2H26. This is a search snippet only; the source URL is unconfirmed (it was not in the fetched remio.ai text). The FinmoConf call summary (likely AVC) says the company works on "every US hyperscaler ASIC programme" and expects ASIC revenue to overtake GPU revenue in 2027 — [FinmoConf call summary](https://finmoconf.diveinvest.net/en/auras/2026-q1)
- Hyperscalers and system vendors increasingly define reference racks in which the cold plate, socket, plumbing and controls are qualified together (market-research source) — [IndexBox](https://www.indexbox.io/blog/cold-plate-assemblies-market-forecast-points-higher-toward-2035-driven-by-hyperscale-liquid-cooling-adoption/)

### Inferences
- (Inference) For flagship NVIDIA GPUs, the door is effectively closed to a new entrant for Rubin-generation programmes: four named suppliers, centralised procurement, and volume and reliability as selection criteria. Plausible entry points are (a) non-NVIDIA silicon (custom ASICs, AMD, edge/inference accelerators), (b) second-source or aftermarket for operators using the OCP test baseline, and (c) adjacent markets (power electronics, EV, defence/HPC).
- (Inference) OCP standardisation cuts both ways. It lowers the qualification barrier for second sources, which helps an entrant. It also commoditises the plate, which hurts a design-speed differentiator.

### Gaps
- No public NVIDIA Recommended Vendor List (RVL) document for cold plates was found. The GB200/GB300 AVL composition beyond AVC's estimated 40–50% share is not public.
- Public OCP UQD v2 and the OCP "Liquid Cooling Cold Plate Requirements" document were not fetched directly.

---

## 4. Qualification and sales cycle for a new supplier

### Takeaway
No hyperscaler or NVIDIA publishes qualification durations. The best available evidence is secondary. It points to about 6–12 months for supplier qualification of mission-critical liquid-cooling parts, and about 1–2 years from R&D sampling to customer approval and certification for pumps and UQDs. Large Chinese makers were still sampling microchannel plates in late 2026. The OCP test array alone implies about 2–4 weeks of chamber time for one design pass, before customer-specific testing, iterations and production audits.

### Cited Findings
- Supplier qualification timelines of 6–12 months for mission-critical data-centre/semiconductor applications (market report) — [IndexBox](https://www.indexbox.io/blog/cold-plate-assemblies-market-forecast-points-higher-toward-2035-driven-by-hyperscale-liquid-cooling-adoption/). A substitute part that "starts a new six-month validation cycle is not an immediate substitute" — [The Cooling Report](https://thecoolingreport.com/intel/liquid-cooling-components-aftermarket-qualification-2035)
- About 1–2 years "from R&D sampling to customer approval and certification" (pumps, including UL). Chinese UQD precision capacity is expected to need 1–2 more years — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b). Pump products take 1–2 years from design to customer approval and safety certification (CLS via secondary) — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- Several mainland Chinese suppliers, with large CNC and brazing capacity, were still submitting samples or under test for MLCPs as of Sept 2026 — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- Glycol inhibitor and biocide packages must be qualified by each CDU vendor. Gaskets or fittings from a batch that fails qualification can stop production — [The Cooling Report](https://thecoolingreport.com/intel/data-center-cooling-supply-chain-guide-2026.html)
- **OCP Cold Plate Test Spec v1.0.0 (effective 2026-09-03), 18 mandatory tests for design qualification.** Conformance "does not constitute production acceptance". Key parameters — [OCP spec PDF](https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Cold-Plate-Test-Specification-V1.0.0.pdf):
  - Helium/hydrogen leak detection: 5–10 min dwell; e.g. < 0.6 SCCM "water-tight" per INFICON guidelines.
  - Gas pressure decay: 5–30 min; e.g. < 0.5% loss.
  - Hydrostatic: 5 min at max operating pressure, then 2 min at 3x max operating pressure, with no permanent deformation.
  - Burst (destructive): until rupture or 3x minimum proof pressure, rise 1–5 bar/min per ISO 18869; e.g. > 20 bar.
  - Thermal resistance on a TTV/processor stack at 45 ± 2 °C; pressure drop at ≥ 6 flow points (25–150% rated); flow up to < 1.5 m/s (erosion).
  - Mechanical: retention 30 N ± 10% for 5 s; flatness per ISO 12781-2; stiffness.
  - Operational temperature cycling: 10 °C for 72 h, then 65 °C for 72 h, under pressure in a loop.
  - Shipping cycling: −40 °C for 72 h, then +70 °C for 72 h, with helium leak before and after (≤ 1×10^? mbar·L/s). The exponent is lost in the PDF text layer and could not be recovered with pdftotext -raw.
  - Shock and vibration on a representative board; salt spray (ASTM B117, 5% NaCl, 35 °C, 8 h); humidity (40 °C/93% RH for 16 h, plus 40 °C/10% RH for 16 h).
  - Fluid compatibility: ASTM D8040 glassware corrosion and ICP/pH/reserve alkalinity/anion analysis; elastomers per ASTM D471, plastics per D543, brazing materials per ASTM D7933 stagnation test.
  - Cleanliness: ultrasonic flush, particulate < 50 µm.
- The OCP spec states its purpose is "shorter qualification cycles, lower cost to bring a cold plate design to market, and fewer redundant evaluations", and that a subset of tests can be used in early design iteration — [OCP spec PDF](https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Cold-Plate-Test-Specification-V1.0.0.pdf)
- A Dec 2025 OCP cold-plate sub-project call (AI-generated meeting summary; secondary) discussed UV-visible fluids for leak detection and standardising validation at about 40–45 °C — [pulse.bot summary](https://www.pulse.bot/hardware/video/ocp-ce-cp-cold-plate-base-specifications-project-call-dec-10-2025-b23d1d68-cc8e-441a-8b70-2a3a746b9183)

### Inferences
- (Inference) Chamber time for one OCP pass: the two 144-hour temperature-cycle regimes alone are about 12 days if run serially, plus fluid-compatibility tests (ASTM D8040 and D7933 are multi-day to multi-week), shock/vibration and burst. One design qualification pass is realistically 3–6 weeks of test time. Fixing failures and customer witness or re-testing pushes this toward the 6–12 month range reported for supplier qualification. Adding factory audits, PPAP-style process freeze and first-article runs at a hyperscaler or ODM plausibly gives 12–24 months to first volume PO for an unknown vendor. That figure is inferred, not sourced.
- (Inference) Qualification is a much bigger time sink than design. Even if an AI-agent design loop cut design from weeks to hours, qualification and the trust gap dominate time-to-revenue. Customers also requalify on any process change, which hurts a factory whose selling point is "every part is different".
- (Inference) Liability and warranty: an OCP-qualified design "does not leak … in service" is aspirational. A leak destroys a node or rack worth millions (a GB200 NVL72 rack is commonly put at about US$3M; not sourced here), so buyers will weight track record and balance sheet heavily.

### Gaps
- No primary hyperscaler, NVIDIA or ODM statement of qualification duration or cost was found.
- No published warranty terms or leak-liability clauses for cold plates were found.
- No cost estimate for running the full OCP test array at a third-party lab was found.

---

## 5. Capital to first revenue and a credible pilot

### Takeaway
Equipment for a credible small pilot line costs low single-digit millions of US dollars. That covers 2–3 five-axis CNCs, a vacuum brazing furnace, optionally FSW, a helium leak station, and a flow/thermal bench with TTVs. That is not the hard part. Venture-backed cold-plate entrants have raised US$30M–100M+ before or around scale-up, and most exits have been acquisitions by large incumbents.

### Cited Findings
**Equipment price indications (mostly marketplace or vendor; low precision)**
All equipment prices below are search-snippet only; none of the pages were fetched. URLs are the result-set pages where the figures appeared, but the exact page-to-figure attribution is unconfirmed.
- 5-axis machining centre: about US$150k–500k new for industrial machines. A US-focused 2026 guide gives US$250k–900k total upfront for a standard 5-axis milling centre (midpoint about US$420k). The results came from [Oturn Machinery](https://www.oturnmachinery.com/news/how-much-does-a-5-axis-cnc-machine-cost-in-2026-for-small-factories/), Australian buyer guides and others; a general cost/benefit discussion is at [MMS Online](https://mmsonline.com/articles/buying-a-five-axis-the-costs-and-benefits-of-a-complex-machine)
- Vacuum brazing furnace (aluminium, China marketplace listings): three listings of about US$70k, about US$170k and US$600k (horizontal high-vacuum). Only the US$600k listing is plausibly the linked page. No copper-specific or Western OEM pricing was found — [Made-in-China listing](https://www.madeinchina.com/mall/show-Acme-Heat-Treatment-Furnace-Brazing-Furnace-High-Vacuum-Aluminum-Brazing-Furnace-Quenching-Furnace_1368278.html)
- Friction stir welding: under €100k for a CNC-mounted head, €600k+ for a dedicated machine, up to seven figures for large gantries (vendor guides in the result set, including [Stirweld](https://stirweld.com/en/fsw-machine-choose-the-best-option/)). A water-cooled FSW machine was listed at about US$108k — [GetCostIdea](https://getcostidea.com/how-much-does-friction-stir-welding-equipment-cost/)
- Helium leak detection: no public prices ("price on request"). INFICON notes helium price and availability volatility and offers argon/air/forming-gas alternatives — [INFICON](https://www.inficon.com/en/news/helium-scarcity-and-industrial-leak-detection)

**Cold-plate economics**
- IDTechEx: cold-plate ASP about US$300–500/unit (CPU vs GPU). Server thermal content is about US$18,880/rack and in-rack CDU about US$23,000 — [IDTechEx via OnArtificialIntelligence](https://www.onartificialintelligence.com/articles/34213/two-phase-d2c-cooling-in-data-center-thermal-management-cost-analysis)
- Cooling system for one Blackwell Ultra NVL72 rack is about US$50,000, rising to about US$56,000 for NVL144 (Morgan Stanley via Tom's Hardware; body not retrievable). Search summary: about US$300 per CPU/GPU cold plate and about US$200 per NVSwitch plate — [Tom's Hardware](https://www.tomshardware.com/pc-components/cooling/cooling-system-for-a-single-nvidia-blackwell-ultra-nvl72-rack-costs-a-staggering-usd50-000-set-to-increase-to-usd56-000-with-next-generation-nvl144-racks)

**Startup funding and outcomes**
- Corintis (Switzerland, microfluidic copper cold plates): US$24M Series A (Sept 2025, led by BlueYard), total about US$33.4M, 55 staff. Target of >1M microfluidic cold plates/year by 2026; Microsoft collaboration — [Tech.eu](https://tech.eu/2025/09/25/corintis-lands-24m-and-microsoft-endorsement-for-chip-cooling-tech/); a valuation of about US$400M and a later US$25M Series A1 appeared in search snippets only (attribution to [Sacra](https://sacra.com/c/corintis) is unconfirmed; A1 timing unconfirmed)
- Accelsius (two-phase D2C): US$65M Series B closed 2026-01-12, led by Johnson Controls with Legrand, to expand its Austin production facility. Total raised conflicts across trackers (US$65M–115M) — [Business Wire](https://www.businesswire.com/news/home/20260112588650/en/Accelsius-Closes-65-Million-Series-B-Funding-Led-by-Johnson-Controls-Legrand-Joining-Round-to-Scale-Liquid-Cooling-for-Gigawatt-Class-AI-Factories)
- Fabric8Labs (ECAM copper cold plates): US$50M round (Nov 2025, NEA and Intel Capital) to expand US manufacturing; a prior US$50M Series B in Q1 2023 — [Intel Capital](https://www.intelcapital.com/fabric8labs-secures-50m-to-expand-u-s-advanced-manufacturing-capacity/); [3DPrint.com](https://3dprint.com/322134/50m-to-boost-fabric8labs-electrochemical-am-capacity-in-the-u-s/). Agreed to be acquired by TDK (announced 2026-06-10, value undisclosed) — [Converge Digest](https://convergedigest.com/tdk-acquires-fabric8labs-to-scale-advanced-cooling-for-ai-data-centers/)
- JetCool (founded 2019, Littleton MA, microconvective cold plates): acquired by Flex on 2024-11-14, terms undisclosed — [Flex IR](https://investors.flex.com/news/news-details/2024/Flex-Acquires-JetCool-to-Expand-Data-Center-and-Power-Portfolio/)

### Inferences
- (Inference, rough build-up) A credible cold-plate pilot (low thousands of units/year, OCP-test-capable) needs:
  - 3x 5-axis CNC: about US$1.0–1.5M.
  - Vacuum brazing furnace: about US$0.2–0.8M.
  - Optional FSW: about US$0.1–0.6M.
  - Helium leak station and flow/thermal bench with TTVs and environmental chambers: likely US$0.3–1.0M (unsourced; no public prices).
  - Metrology/CMM and cleaning: about US$0.2–0.5M.
  - Equipment subtotal: about US$2–4.5M.
  - Facility, staff and 18–24 months of qualification runway: plausibly US$8–20M before meaningful revenue. A robotics/autonomy layer adds more.
  - Benchmark: comparable startups raised about US$30–100M+ before scale.
- (Inference) At about US$300–500 ASP, 10,000 plates/year is only about US$3–5M revenue. A startup needs either high-value custom/low-volume niches or a hyperscale programme win to justify the capex.

### Gaps
- No public price for helium leak test systems, thermal test vehicles, or copper-capable vacuum brazing furnaces from Western OEMs (e.g., Ipsen, Seco/Warwick, ALD) was found.
- JetCool's pre-acquisition funding was not found. No pre-revenue spend data for small precision job shops entering cold plates was found.
- No copper-AM machine pricing was gathered.

---

## 6. Demand evidence for faster custom design

### Takeaway
There is real demand for more custom cold plates: custom ASICs at all four big CSPs, AMD Helios, >1 kW chips, and microchannel/MCL needs. Sources say this custom segment is supply-tight. But the tightness is attributed to process capability, precision machining and certification, not to design lead time. No source found buyers complaining specifically about cold-plate design turnaround.

### Cited Findings
- "High-power-density custom cold plates suited for chips above 1000W remain tight", while standard plates are ample — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- Customized >1 kW plates are constrained because "precision machining, vacuum bonding, and customer certification" take longer to expand than assembly — [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- ASIC programmes: AWS Trainium 2.5/3 liquid cooling with 99 cold-plate modules per rack (KGI) — [KGI](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf). Auras reports ASIC cold-plate orders from the top four CSPs, with mass production from 2H26 — [Auras call summary](https://finmoconf.diveinvest.net/en/auras/2026-q1)
- Taiwan's ecosystem advantage: cold-plate makers and power designers "can iterate with customers in days rather than weeks". This is a search snippet only; the URL is unconfirmed and it may be from any of several TVBS/DigiTimes results (candidate: [TVBS](https://news.tvbs.com.tw/english/3229366)). Treat as weak evidence.
- Chinese contract makers already advertise 1-piece prototypes in 4–6 weeks — [Tone Cooling](https://tonecooling.com/custom-liquid-cold-plate-design-order-guide/)
- Startups differentiate on novel geometry (Frore LiquidJet, Corintis microfluidics, Fabric8Labs ECAM, JetCool microconvective), not on design-cycle speed alone — [Tom's Hardware (Frore)](https://www.tomshardware.com/pc-components/liquid-cooling/frore-shows-off-liquidjet-nexus-coldplate-for-nvidia-vera-rubin-other-ai-accelerators-offers-up-claimed-10-percent-token-generation-boost-over-rival-liquid-cooling-solutions); [Tech.eu (Corintis)](https://tech.eu/2025/09/25/corintis-lands-24m-and-microsoft-endorsement-for-chip-cooling-tech/)

### Inferences
- (Inference) Incumbents already iterate designs in days and prototype in weeks. An "AI-agent design loop" compresses a step that is not the binding constraint. Its value would come only if it also produces geometries incumbents cannot make or validate, and only if that translates into faster qualification.
- (Inference) The best demand fit for "fast custom" is outside NVIDIA flagship racks: edge/inference accelerators, neocloud retrofits, power electronics, EV/defence. Volumes there are small and customers price-sensitive. This is unverified; no source quantified these segments.

### Gaps
- No survey or buyer-side evidence was found ranking design lead time against delivery capacity against price. This should be primary research (customer interviews) for the startup.
- No data was found on retrofit, neocloud or edge custom cold-plate demand volumes.

---

## 7. Biggest risks for a new entrant

### Takeaway
The dominant risks are: (1) NVIDIA's centralised control of cold-plate supply for flagship platforms; (2) scale and price pressure from Taiwanese majors spending about US$0.5bn/year on capacity and holding 40–50% share; (3) rapid consolidation by large strategics (US$0.85–9.5bn deals), which raises incumbents' balance sheets and service reach; (4) leak liability and reliability trust; (5) technology shifts (microchannel lids, chip-level cooling) that can strand process investments; and (6) AI capex cyclicality.

### Cited Findings
**Consolidation (dates/prices)**
- Vertiv acquired CoolTera (UK, CDUs/secondary fluid networks), announced Dec 2023 — [Business Wire](https://www.businesswire.com/news/home/20231203643358/en/Vertiv-Acquisition-of-CoolTera-Ltd.-Boosts-Liquid-Cooling-Portfolio) (not fetched; price not confirmed)
- Flex acquired JetCool, 2024-11-14 — [Flex IR](https://investors.flex.com/news/news-details/2024/Flex-Acquires-JetCool-to-Expand-Data-Center-and-Power-Portfolio/)
- Schneider Electric bought a 75% stake in Motivair (Buffalo NY; CDUs, cold plates) for about US$850M cash, with the remaining 25% by 2028 — [Capacity Media](https://capacitymedia.com/article/schneider-electric-850m-motivair-buyout)
- Eaton agreed to acquire Boyd Thermal for US$9.5bn (announced 2025-11-03; about 22.5x 2026E adjusted EBITDA). 2026E sales are US$1.7bn, of which US$1.5bn is liquid cooling — [Business Wire](https://secure.businesswire.com/news/home/20251103856036/en/Eaton-Signs-Agreement-to-Acquire-Boyd-Thermal-Expanding-Solutions-for-Data-Center-Customers-to-Include-Critical-Liquid-Cooling-Technology); [TT News](https://www.ttnews.com/articles/eaton-buy-boyd-thermal)
- Vertiv acquired PurgeRite (fluid management services) for about US$1.0bn plus up to US$250M earn-out (about 10x 2026E EBITDA), closed around Dec 2025 — [Data Centre Review](https://datacentrereview.com/2025/12/vertiv-completes-1bn-acquisition-of-purgerite-to-bolster-liquid-cooling-services/)
- Ecolab agreed to acquire CoolIT Systems (cold plates, CDUs; customers include NVIDIA and AMD) from KKR for about US$4.75bn (2026-03-20). CoolIT has about US$550M of next-12-month sales — [The Star / Reuters](https://www.thestar.com.my/tech/tech-news/2026/03/20/ecolab-to-buy-coolit-for-475-billion-to-tap-into-ai-data-center-boom)
- Trane/LiquidStack and Vertiv/ThermoKey are also reported among 2026 deals — [The Cooling Report](https://thecoolingreport.com/intel/data-center-cooling-supply-chain-guide-2026.html)
- TDK is acquiring Fabric8Labs (2026-06-10) — [Converge Digest](https://convergedigest.com/tdk-acquires-fabric8labs-to-scale-advanced-cooling-for-ai-data-centers/)

**Spec control / concentration**
- NVIDIA centralised Vera Rubin cold-plate procurement with four named suppliers — [Ground News (DigiTimes summary)](https://ground.news/article/nvidia-standardizes-vera-rubin-liquid-cooling-names-four-cold-plate-suppliers_797c41)
- AVC holds an estimated 40–50% GB200/GB300 cold-plate share, with US$472M capex in 2026 — [TVBS World / t.media](https://t.media/3179423)

**Technology shift**
- Rubin Ultra (>3 kW TDP) and the Kyber rack will likely need new chip-level solutions (MCL, microchannel cold plates). "Traditional liquid cooling technology will remain the mainstream … particularly inference servers, for the time being" — [KGI](https://www.kgi.com.hk/en/-/media/files/kgishk/research-reports/tw-reports/thermal-sector_27102025.pdf)
- "Traditional skived-fin processes have reached their limits" — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)

**Leak liability / reliability**
- GB200 leaks centred on QDs, hoses and branch pipes from outsourced suppliers, and triggered shutdowns and extra testing — [TweakTown](https://www.tweaktown.com/news/99446/nvidias-new-gb200-ai-server-cabinets-leaks-in-liquid-cooling-system-emergency-work-to-fix-it/index.html); [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/large-scale-shipments-of-nvidia-gb300-servers-tipped-to-start-in-september-gb200-demand-remains-robust-despite-widespread-coolant-leak-reports)

**Price / copper**
- Record copper and the US tariff schedule (15% from 2027, 30% from 2028, reported) — [Skillings](https://www.skillings.net/copper-hits-record-14697-as-tariff-deadline-tightens-supply/); [DT Next](https://www.dtnext.in/news/business/copper-hits-record-high-above-14500-on-us-tariff-fears)

### Inferences
- (Inference) The consolidation pattern (all liquid-cooling innovators acquired by Flex, Schneider, Eaton, Ecolab, TDK, Vertiv, Trane) suggests the realistic exit for a cold-plate startup is acquisition for technology. Strategics pay for proven, qualified revenue (Boyd US$1.5bn liquid-cooling sales; CoolIT about US$550M), not for factories.
- (Inference) Cyclicality: AVC and Auras are adding about 5x capacity in 2026. If AI capex slows, standard cold-plate capacity will be in surplus quickly and pricing will collapse first in commoditised segments. A US startup with higher cost structure would be most exposed.
- (Inference) Taiwanese thermal margins rose with liquid cooling (Auras record about 33% gross margin per search snippet, unverified), so incumbents have room to cut price against an entrant.

### Gaps
- No source quantified cold-plate price erosion or Chinese vs Taiwanese price differentials.
- AVC/Auras gross-margin figures appeared only in search snippets (AVC 33.86%, Auras about 33%) without a verified source URL. They conflict with the FinmoConf call summary (likely AVC), which gives a Q1 2026 gross margin of 29.77%.
- No evidence was found on how leak liability is allocated contractually (supplier vs ODM vs NVIDIA).

---

## 8. Evidence that would kill an "AI-agent + robot autonomous factory for custom cold plates" startup

### Takeaway
Current evidence leans against the premise that design is the bottleneck, though the evidence base is thin (one CLS-derived ranking plus forecasts and part counts). Capacity for standard plates is disputed: the CLS-derived table says "ample", while AVC's chairman says demand exceeds capacity. Either way it is expanding about 5x at AVC. The scarce items are UQDs, CDUs, microchannel process capability and certification. NVIDIA centralises vendor selection, and qualification (6–24 months) rather than design (days) sets time-to-revenue. The idea survives only if customer discovery shows a segment where design and iteration turnaround is the stated pain and qualification can be short.

### Cited Findings (evidence bearing on kill criteria)
- Standard cold-plate supply is "relatively ample"; Taiwanese majors have monthly capacity in the millions — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- AVC is going 5x on cold plates in 2026 with US$472M capex, yet its chairman says capacity still cannot meet demand (this counters the "ample" claim) — [TVBS World / t.media](https://t.media/3179423). The "Auras" 5x page is likely the same AVC figure mislabelled — [FinmoConf](https://finmoconf.diveinvest.net/en/auras/2026-q1)
- Most-cited bottlenecks are UQDs (1–2 year expansion), CDUs and manifolds/pumps, not plate design — [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b); [remio.ai](https://www.remio.ai/post/nvidia-makes-liquid-cooling-mandatory-turning-ai-infrastructure-into-technology)
- NVIDIA centralised cold-plate procurement for Vera Rubin to four incumbents — [Ground News](https://ground.news/article/nvidia-standardizes-vera-rubin-liquid-cooling-names-four-cold-plate-suppliers_797c41)
- Qualification takes 6–12 months (supplier) and 1–2 years sampling-to-certification for related components — [IndexBox](https://www.indexbox.io/blog/cold-plate-assemblies-market-forecast-points-higher-toward-2035-driven-by-hyperscale-liquid-cooling-adoption/); [BigGo Finance](https://finance.biggo.com/news/2a1183d2-e87c-4c48-95b9-8d3929f66b1b)
- Incumbents iterate in "days rather than weeks" (search snippet only, URL unconfirmed; weak). Chinese makers prototype in 4–6 weeks — [Tone Cooling](https://tonecooling.com/custom-liquid-cold-plate-design-order-guide/)
- The OCP test spec standardises validation methods, which could shorten qualification for second sources — [OCP spec PDF](https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Cold-Plate-Test-Specification-V1.0.0.pdf)

### Inferences (kill criteria to test; all inferences)
1. **Kill if** 10–20 buyer interviews (ASIC teams, ODM thermal leads, neoclouds, power-electronics OEMs) rank design turnaround below qualification, reliability or price, and below delivery capacity. Current secondary evidence already points this way.
2. **Kill if** the target segment's qualification time is ≥ 12 months regardless of design speed, so a faster design loop does not move time-to-PO. This holds for NVIDIA and hyperscaler flagship racks.
3. **Kill if** the custom segment's real scarcity is microchannel/MLCP process capability (semiconductor-grade etching, bonding, AM) that robots plus CNC cannot deliver, and incumbents (Jentech, AVC, Corintis, Fabric8Labs/TDK) already hold the processes.
4. **Kill if** unit economics fail: at about US$300–500 ASP and a pilot capex of about US$2–4.5M equipment plus US$8–20M runway, the startup cannot reach volumes that pay back without a hyperscale programme win, and such wins go to qualified incumbents.
5. **Kill if** leak liability or insurance requirements for a new vendor are prohibitive. For example, buyers demand a balance sheet or warranty indemnities a startup cannot provide.
6. **Kill if** the technology roadmap (MCL and chip-level cooling for >3 kW in 2027+) moves value into the package or lid, owned by chipmakers and their packaging partners. That would leave discrete cold plates as a commodity.
7. **Survival signals (would weaken the kill case):** buyers in non-NVIDIA niches report multi-week design and quote cycles as a pain; OCP-based second-source qualification measured in weeks; acquirers paying for design-automation IP; and evidence of shortages of US-domestic or tariff-free cold-plate supply after the 2027 copper tariffs.

### Gaps
- No primary buyer-side evidence was found on design-speed pain. This is the single most important unknown and requires customer discovery.
- No data on robotic or lights-out cold-plate manufacturing (yields, labour share of cost) was found. The labour share of cold-plate cost in Taiwan, China or Vietnam is unknown, so the cost advantage of automation is unquantified.
