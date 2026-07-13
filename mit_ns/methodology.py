"""12-step design methodology navigator (Ch.5) + digitized constraints."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from mit_ns.data import load_design_constraints, load_system_labels, load_table_9_1


@dataclass
class MethodologyStep:
    number: int
    title: str
    thesis_ref: str
    description: str
    ai_assist: str
    status_in_repo: str
    checklist: list[str]


STEPS: list[MethodologyStep] = [
    MethodologyStep(
        1,
        "Division of Nuclear / Non-Nuclear Buildings",
        "5.2.2 / 6.2.2",
        "Split site layout along nuclear vs non-nuclear QA/labor boundaries.",
        "LLM can classify buildings/systems from FSAR text into nuclear vs non-nuclear.",
        "constraints digitized in data/design_constraints.json",
        ["Tag each building nuclear/non-nuclear", "Separate QA/QC labor pools"],
    ),
    MethodologyStep(
        2,
        "System Assignments to Buildings",
        "5.2.3 / 6.2.3 / Table 6-1",
        "Assign systems (RCS, CVCS, MS, …) to RB/RAB/CB/FHB/WPB/TB.",
        "LLM extracts system→building maps from plant descriptions / P&IDs captions.",
        "system_labels.csv includes building_hint",
        ["Produce system list per building", "Flag multi-building systems"],
    ),
    MethodologyStep(
        3,
        "Matrix Analysis of Power Plant Systems",
        "5.2.4 / 6.2.4 / Fig 6-1",
        "Build cost-penalty interaction matrix and reorder/cluster systems.",
        "Modern optimizers (GA+LS etc.) replace 1989 BEA heuristic on the DSM.",
        "DONE — core benchmark in repo",
        ["Digitize interface matrix", "Run clustering / partition", "Review clusters with engineers"],
    ),
    MethodologyStep(
        4,
        "Designation of Safety and Non-Safety Regions",
        "5.2.5 / 6.2.5 / Table 6-3",
        "Define safety / non-safety / train A-B regions before placement.",
        "LLM extracts separation criteria; optimizer applies soft/hard constraints.",
        "safety tags in system_labels.csv + mixing penalties",
        ["Mark safety systems", "Encode train separation as constraints"],
    ),
    MethodologyStep(
        5,
        "System Placement",
        "5.2.6 / 6.2.6",
        "Place clustered systems into plant regions using matrix priorities.",
        "AI proposes placement candidates; engineers approve.",
        "partial — partition only, no 3D layout",
        ["Map clusters to regions", "Respect major component anchors"],
    ),
    MethodologyStep(
        6,
        "Power Plant Route-Way Placement",
        "5.2.7 / 6.2.7",
        "Assign pipe/cable route-ways between modules/regions.",
        "Pathfinding / LLM-assisted routing suggestions from topology graphs.",
        "not implemented (needs geometry)",
        ["Define route-ways", "Minimize congested crossings"],
    ),
    MethodologyStep(
        7,
        "Component Placement",
        "5.2.8 / 6.2.8",
        "Place major components inside modules/regions.",
        "Constraint solvers + LLM reading equipment lists.",
        "not implemented",
        ["Place major equipment", "Check maintainability access"],
    ),
    MethodologyStep(
        8,
        "Defining Modular Boundaries",
        "5.2.9 / 6.2.9",
        "Cut modules to maximize self-sufficiency / minimize interfaces.",
        "Same as matrix partition objective; GA+LS already improves cut.",
        "DONE for cut objective; DV-proxy extends it",
        ["Propose module boundaries", "Validate transport/weight limits"],
    ),
    MethodologyStep(
        9,
        "Pipe Penalty Routing Value (PPRV)",
        "5.2.10 / 5.5 / 6.2.10",
        "Score pipe length, bends, elevations, crossovers.",
        "Needs pipe-run data; LLM can help digitize tables; surrogate uses cut.",
        "historical PPRV validated; surrogate only for new partitions",
        ["Collect pipe runs", "Compute penalties", "Iterate routing"],
    ),
    MethodologyStep(
        10,
        "Measure of Modularity (MOM)",
        "5.2.11 / 6.2.11",
        "Sum module boundary interface values.",
        "Directly computable from partition + interaction matrix.",
        "DONE for matrix-derived MOM/cut",
        ["Compute MBIV per system", "Feed back into boundary refinement"],
    ),
    MethodologyStep(
        11,
        "Module Alignment Value (MAV)",
        "5.2.12 / 6.2.12",
        "Vertical/horizontal alignment difficulty of modules.",
        "Requires support geometry; surrogate uses size balance.",
        "SH II MAV validated; surrogate for optimizer",
        ["Count aligned/misaligned supports", "Compute MVAV/MHAV"],
    ),
    MethodologyStep(
        12,
        "Design Value (DV) and refinement",
        "5.2.13 / 5.6 / 6.2.13",
        "DV = A1·MOM + A2·MAV + A3·PPRV + A4·CVV + A5·MFV; iterate design.",
        "DV-proxy optimizer closes the gap between cut-only and full DV narrative.",
        "historical DV validated; DV-proxy experiment added",
        ["Compute DV", "Compare Original vs Modular", "Iterate until convergence"],
    ),
]


def get_step(n: int) -> MethodologyStep:
    for step in STEPS:
        if step.number == n:
            return step
    raise KeyError(f"Unknown step {n}")


def methodology_overview() -> list[dict]:
    return [asdict(s) for s in STEPS]


def build_context_pack() -> dict:
    """Context for an LLM agent: steps + digitized tables + constraints."""
    labels = load_system_labels().to_dict(orient="records")
    constraints = load_design_constraints()
    table_9_1 = load_table_9_1().to_dict(orient="records")
    return {
        "thesis": "Lapp, C.W. (1989). A Methodology for Modular Nuclear Power Plant Design and Construction. MIT.",
        "steps": methodology_overview(),
        "systems": labels,
        "constraints": constraints,
        "table_9_1_dv_components": table_9_1,
        "agent_instructions": (
            "You are an engineering assistant for modular NPP design methodology. "
            "Guide the user through Steps 1–12. Cite thesis refs. "
            "Do not invent pipe/layout numbers that are not in the context. "
            "Clearly mark computed vs historical vs surrogate values."
        ),
    }


def render_step_markdown(n: int) -> str:
    s = get_step(n)
    checks = "\n".join(f"- [ ] {c}" for c in s.checklist)
    return (
        f"## Step {s.number}: {s.title}\n\n"
        f"**Thesis:** {s.thesis_ref}\n\n"
        f"{s.description}\n\n"
        f"**AI assist:** {s.ai_assist}\n\n"
        f"**Repo status:** {s.status_in_repo}\n\n"
        f"### Checklist\n{checks}\n"
    )
