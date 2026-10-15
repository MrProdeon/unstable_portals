from dataclasses import dataclass, field

ATTENTION_LIMIT = 5


@dataclass
class Summary:
    total: int = 0
    open: int = 0
    critical: int = 0
    closed: int = 0
    attention_total: int = 0
    attention: list = field(default_factory=list)


def build_summary(portals):
    """Собирает сводку по списку порталов (работает и с пустым списком)."""
    portals = list(portals)
    open_portals = [p for p in portals if p.is_open]

    needing = [p for p in open_portals if p.risk.level in ("critical", "medium")]
    needing.sort(key=lambda p: (-p.risk.score, p.name))

    return Summary(
        total=len(portals),
        open=len(open_portals),
        critical=sum(1 for p in open_portals if p.risk.level == "critical"),
        closed=len(portals) - len(open_portals),
        attention_total=len(needing),
        attention=needing[:ATTENTION_LIMIT],
    )