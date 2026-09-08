from datetime import datetime, timezone
import pytest
from athena_procurement_arena.domain import (
    ActionDecision, CapitalProgram, CustomerAction, Organization, OrganizationRole,
    ProcurementEpisode, ProcurementForecast, ProcurementState, Project, ProjectPhase,
    ReadinessStatus, Site, Solicitation, TrailState,
)
from athena_procurement_arena.foundation import PowerScope

def test_domain_keeps_program_project_phase_episode_and_solicitation_distinct():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    org = Organization("o", "Buyer", (OrganizationRole.BUYER,))
    program = CapitalProgram("program", "Capital", org.organization_id)
    project = Project("project", program.program_id, org.organization_id, ("site",))
    phase = ProjectPhase("phase", project.project_id, "construction", t)
    episode = ProcurementEpisode("episode", project.project_id, org.organization_id, ProcurementState.FUNDED, t)
    solicitation = Solicitation("solicitation", episode.procurement_episode_id, "PUBLIC_RFP")
    assert len({program.program_id, project.project_id, phase.phase_id, episode.procurement_episode_id, solicitation.solicitation_id}) == 5
    assert Site("site", "Plant").site_id in project.site_ids

def test_readiness_mandatory_failure_cannot_be_averaged_away():
    decision = ActionDecision(CustomerAction.READY_FOR_AUTHORIZED_SUBMISSION,
                              readiness={"bonding": ReadinessStatus.FAIL, "technical_fit": ReadinessStatus.PASS})
    assert decision.has_mandatory_failure

def test_forecast_confidence_is_bounded():
    with pytest.raises(ValueError):
        ProcurementForecast(ProcurementState.FUNDED, 1.1)
