"""Freeze the public Stibnite sources used by the Stibnite mining import.

Content is the Firecrawl markdown article body retrieved 2026-10-21, keeping
whole source paragraphs verbatim (PDF line breaks joined) and omitting site
navigation, cookie banners, unrelated sections and legal boilerplate. Run from the repository
root: python scenarios/fixtures/mining/stibnite/build_captures.py
"""
from datetime import UTC, datetime
from pathlib import Path

from athena_procurement_arena.public_capture import capture_markdown, write_capture

HERE = Path(__file__).parent
CAPTURED_AT = datetime(2026, 10, 21, 1, 30, tzinfo=UTC)
CAPTURED_BY = "Claude Code for Nick Sandoval"

SOURCES = {
    "perpetua-sept-2026-update": (
        "https://perpetuaresources.com/wp-content/uploads/2026/09/Sept-2026-Construction-Update.pdf",
        "01a15c1d-0ac8-7595-ada3-6d8be299bfbd",
        """## NEWS RELEASE

September 28, 2026

# Perpetua Resources Provides Construction & Exploration Update

*Access Road, Worker Housing, Powerline and Drilling Programs Advance*

BOISE, ID – Perpetua Resources Corp. (Nasdaq: PPTA / TSX: PPTA) (“Perpetua Resources,” “Perpetua,” or the “Company”) today provided an update on construction and exploration progress at its Stibnite Gold Project (the “Project”) in central Idaho. With federal approvals secured in 2025 and early works and critical path construction activities continuing through the summer and into the fall, the Company is pleased to share recent progress with stakeholders.

## Permanent Worker Housing Continues to Ramp Up

In late August, the Worker Housing Facility civil works were completed, and foundation installation began in preparation for placement and erection of the camp modules.

Treated wood foundations are currently being installed to support the kitchen, dining, and recreation modules, while the Triodetic™ metal foundation will support the dormitory buildings and the arctic corridor connecting the facility.

## Powerline Equipment Deliveries Continue

Powerline upgrades are important for project development, as the upgraded line will deliver the required grid power needed to run the Project’s processing facility and site operations. Working closely with its partners at Idaho Power Co., Perpetua is well advanced in procuring key equipment and materials. Long-lead power items such as substations and transformers have also been ordered to ensure timely delivery. Essential items such as power poles and ancillary equipment have been procured and delivered to Perpetua’s laydown areas in Donnelly and Cascade, Idaho.

## Momentum Continues into the Fall

Looking ahead, Perpetua will continue to advance critical path work through the fall, including bridge deliveries for Burntlog Route, installation of the Worker Housing Facility, and ongoing powerline procurement. Drilling will continue with four rigs before ramping down into the winter months, and the Company expects to report additional assay results from the exploration program as they become available.

## About Perpetua Resources and the Stibnite Gold Project

Perpetua Resources Corp., through its wholly owned subsidiaries, is focused on the exploration, site restoration, and redevelopment of gold-antimony-silver deposits in the Stibnite-Yellow Pine district of central Idaho. The Stibnite Gold Project is one of the highestgrade, open-pit gold deposits in the United States and holds the only identified domestic reserve of the critical mineral antimony, which is essential to the defense, energy, and manufacturing sectors. The Project is designed to apply a modern, responsible mining approach to restore a historic mine site and provide uplift to water quality, improve fish habitat access, and invest in river restoration while supporting local economic development in rural Idaho.
""",
    ),
    "atco-housing-award": (
        "https://www.atco.com/en-ca/about-us/news/2025/123051-atco-structures-accelerates-u-s-expansion-with-179m-worker-housi.html",
        "01a15c1d-0a74-703a-b004-005cd3daee29",
        """October 27, 2025

## ATCO Structures Accelerates U.S. Expansion with $179M Worker Housing Contract for Perpetua Resources

CALGARY, AB, Oct. 27, 2025 /CNW/ - **ATCO Ltd.**(TSX: ACO.X) (TSX: ACO.Y) ATCO Structures today announced that its U.S. division, ATCO Structures & Logistics (USA) Inc., has been awarded a contract to design, supply and install a worker housing facility for Perpetua Resources Corp.'s Stibnite Gold Project located near Yellow Pine, Idaho. The $179M CAD ($130M USD) contract includes plans for a 1,052-person dormitory lodge and office facilities, which will be operational in Q1 2027 and enable gold, silver and antimony mining operations and associated restoration activities at the site. Initial work in 2025 will be focused on site preparation for construction of the facility, which will commence in 2026.

"Delivering the Stibnite Gold Project requires world-class partners," said Michael Wright, Vice President, Projects for Perpetua Resources. "ATCO brings proven expertise in safely delivering the high-quality housing needed for our remote on-site workforce. This contract marks a significant milestone in mobilizing our construction team and underscores our disciplined approach to project execution. Together, we are laying the foundation to deliver one of America's most important critical mineral projects."
""",
    ),
    "hatch-epcm": (
        "https://www.hatch.com/About-Us/News-And-Media/2025/12/Perpetua-Resources-selects-Hatch-as-EPCM-for-Stibnite-Gold-Project",
        "01a15c1d-0a79-747e-aace-02547b7a2d84",
        """# Perpetua Resources selects Hatch as EPCM for Stibnite Gold Project

12 17, 2025

**Boise, Idaho** – Perpetua Resources Corp. (Nasdaq: PPTA / TSX: PPTA) (“Perpetua Resources” or “Perpetua” or the “Company”) today announced that it has selected Hatch Ltd. (“Hatch”) as the Engineering, Procurement, and Construction Management (“EPCM”) contractor for the Stibnite Gold Project (“SGP” or “Project”). The appointment of Hatch follows a highly competitive review process and marks a major milestone in Perpetua’s transition from planning to development, ahead of a final investment decision expected in the spring of 2026. The EPCM selection strengthens Perpetua’s readiness to responsibly deliver one of the most strategically important mining projects in the United States.

Under the EPCM model, Hatch will be responsible for:

- Comprehensive process plant and infrastructure engineering and design
- Procurement management for all major equipment and systems
- Construction management across the full process facility scope
- Integrated project controls, reporting, and performance management standard
""",
    ),
    "idaho-power-contract": (
        "https://perpetuaresources.com/perpetua-resources-commences-detailed-engineering-and-signs-procurement-contract/",
        "01a15c1d-0ac2-731f-8317-feea1cc37e76",
        """**BOISE, ID** – Perpetua Resources Corp. (Nasdaq: PPTA / TSX: PPTA) (“Perpetua Resources” or “Perpetua” or the “Company”), announced today that following the successful completion of basic engineering for the Stibnite Gold Project (“Project”) along with the release of its 2024 Financial Update (“Financial Update”), the Company has approved commencement of detailed engineering studies with Ausenco Engineering USA South Inc. (“Ausenco”) and signed a procurement contract with Idaho Power Company (“Idaho Power”) for powerline materials. The Financial Update reconfirms the robust economics of the Project, indicating a $3.7 billion after-tax net present value (“NPV”) (5%) and an after-tax internal rate of return (“IRR”) in excess of 27% at spot prices2 and is resilient at lower prices including a $1.4 billion after-tax NPV (5%) and 15.4% after-tax IRR at long-term consensus prices3, driven by industry leading1 operating costs.

As Perpetua advances towards a construction decision later this year, the Company has signed a procurement contract with Idaho Power to begin down payments on several critical long-lead power line items.
""",
    ),
}

if __name__ == "__main__":
    for capture_id, (url, job, content) in SOURCES.items():
        capture = capture_markdown(url, content, capture_id=capture_id, captured_by=CAPTURED_BY,
                                   captured_at=CAPTURED_AT, provider="firecrawl", provider_job_id=job)
        write_capture(capture, HERE / f"{capture_id}.json")
        print(capture_id, capture.capture_hash[:12])
