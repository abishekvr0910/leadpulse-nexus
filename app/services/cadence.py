from dataclasses import dataclass


@dataclass(frozen=True)
class EmailCadenceStep:
    stage: int
    day: int
    template_key: str
    resulting_email_stage: str


# These are the three real templates currently implemented by the MVP. The durable
# workflow can be extended to eight steps once stages 4-8 have approved copy.
EMAIL_CADENCE = (
    EmailCadenceStep(0, 0, "pl_initial_outreach", "INITIAL_SENT"),
    EmailCadenceStep(1, 3, "pl_follow_up_1", "FOLLOWUP1_SENT"),
    EmailCadenceStep(2, 7, "pl_follow_up_2", "FOLLOWUP2_SENT"),
)


def get_step(stage: int) -> EmailCadenceStep:
    return EMAIL_CADENCE[stage]
