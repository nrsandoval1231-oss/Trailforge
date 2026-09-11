# Construction and commissioning power for large generation projects

## Finding

The claim that a 300 MW permanent-generation facility may need about 3 MW for
commissioning is plausible as a project-specific planning case, but the
research does not support it as a universal 1% rule. Temporary power is driven
by construction sequence, auxiliary systems, cranes and welding, water and
wastewater systems, HVAC, controls, battery charging, testing loads, and the
point at which permanent power becomes available.

The defensible ICP rule is therefore: screen large generation, industrial, and
data-center projects for a separately stated temporary construction or
commissioning-power requirement; do not estimate that requirement from the
permanent plant MW alone.

## Evidence

1. The U.S. Department of Energy Hanford WTP interface document describes a
   primary temporary construction supply of 7 MW and a separate intermittent
   requirement of up to 2 MW for aggregate mining. It also states that
   permanent plant power is provided before startup and commissioning. This
   demonstrates that temporary construction load can be multi-megawatt and
   separately scoped from permanent operating power, but it does not imply a
   fixed ratio to plant nameplate.
2. A public data-center construction-power provider describes gas and diesel
   generators from 100 kW to 1.5 MW and load-on-demand packages using multiple
   generators. This supports the multi-unit rental pattern and staged load
   growth, but is vendor capability evidence rather than an RFP requirement.
3. The 178th Wing Base Microgrid solicitation requires natural-gas generators
   and microgrid controls for critical 24/7 operations. Its public Q&A asks for
   proof that two 500 kW generators can operate simultaneously at full load,
   confirming that gas capacity and site integration are gating facts in this
   class of project. Current status and rental scope require the latest
   official solicitation and amendments; older notice dates are insufficient.
4. The JBMDL microgrid presolicitation describes two 500 kW natural-gas
   generators alongside PV, BESS, and a microgrid controller. This is a direct
   equipment-size pattern for Aura 412-class units, not proof of rental demand
   or current solicitation status.

## Aura sizing translation

For a stated 3 MW temporary requirement, before derating or redundancy:

| Configuration | Gross unit count | Practical planning note |
| --- | ---: | --- |
| Aura 412 R at 500 kW natural gas | 6 | 7 if one-unit N+1 redundancy is required |
| Aura 408 R at 310 kW natural gas | 10 | 11 if one-unit N+1 redundancy is required |
| Hypothetical usable output of 246 kW/unit | 13 | 14 for one-unit N+1; not validated Aura sizing |

The Aura workbook's cached example at 875 m altitude, 45 C, and MTZ 80 shows
approximately 246 kW electrical output and approximately 222 kW island output
for an Aura 408. Formulas and model applicability were not validated; the
246 kW table row is arithmetic, not an island-mode guarantee. Site conditions,
operating mode, step loading,
gas pressure, and redundancy must be requested before converting a project
requirement into unit count.

The companion `commissioning-power-market-evidence-2026-09-11.md` adds a
specific commissioning case at the 350 MW Azure Sky facility and corrected
procurement classifications. It does not establish a universal sizing ratio.

## ICP update

Add these terms and signals to discovery: `temporary construction power`,
`commissioning power`, `energization`, `startup power`, `construction utility`,
`temporary generation`, `gas capacity study`, `natural gas generator`, and
`N+1`. A large permanent facility is not itself a lead; it becomes a candidate
only when a temporary-power scope, gas feasibility, timing, and responsible
buyer or EPC path are evidenced.

## Sources

- U.S. Department of Energy, *ICD-11 Electricity*, Hanford WTP, pp. 6-7,
  https://emcbc.doe.gov/SEB/Files/HanfordITDC/DocLib/ICD-11%20Electricity.pdf
- Aggreko, *Data center construction power and temperature control solutions*,
  https://www.aggreko.com/en-us/Sectors/Data-centres/Data-centre-construction
- SAM.gov, *178th Wing Base Microgrid Construction*, Notice
  W50S8Q-26-B-A001, https://sam.gov/opp/c935ca4506e444b58b1a1a00d32d2b4a/view
- SAM.gov, *Construction of the Power Generation with Microgrid at Joint Base
  McGuire-Dix-Lakehurst*, Notice W912DS26BA032,
  https://sam.gov/workspace/contract/opp/400488be8f204749b1d5f9289f378866/view
