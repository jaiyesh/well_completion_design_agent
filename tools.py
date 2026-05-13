from typing import Any


def calculate_fracture_gradient(depth_ft: float, overburden_psi_per_ft: float) -> dict[str, Any]:
    """
    Estimates fracture gradient and associated pressures using Eaton's method.
    Assumes normal salt-water hydrostatic pore pressure (0.465 psi/ft).
    """
    PPG = 0.465          # pore pressure gradient, psi/ft (salt water)
    nu = 0.25            # Poisson's ratio for consolidated sedimentary rock

    eaton_k = nu / (1.0 - nu)   # 0.3333

    fg_psi_per_ft = eaton_k * (overburden_psi_per_ft - PPG) + PPG
    frac_pressure_psi = fg_psi_per_ft * depth_ft

    # Instantaneous shut-in pressure is slightly below fracture extension pressure
    isip_psi = frac_pressure_psi * 0.92

    # Mud weight window (ppg) — 1 ppg = 0.052 psi/ft
    safe_mw_max_ppg = (fg_psi_per_ft * 0.95) / 0.052   # 5 % safety margin below frac
    safe_mw_min_ppg = PPG / 0.052                        # hydrostatic lower bound

    net_pressure_margin_psi = frac_pressure_psi - (PPG * depth_ft)

    return {
        "depth_ft": depth_ft,
        "fracture_gradient_psi_per_ft": round(fg_psi_per_ft, 4),
        "fracture_pressure_psi": round(frac_pressure_psi, 0),
        "closure_pressure_psi": round(frac_pressure_psi, 0),
        "isip_estimate_psi": round(isip_psi, 0),
        "safe_mud_weight_max_ppg": round(safe_mw_max_ppg, 1),
        "safe_mud_weight_min_ppg": round(safe_mw_min_ppg, 1),
        "net_pressure_margin_psi": round(net_pressure_margin_psi, 0),
        "method": "Eaton (Poisson 0.25, hydrostatic PPG 0.465 psi/ft)",
    }


def recommend_perforation_strategy(
    formation_type: str,
    net_pay_ft: float,
    skin_factor: float,
) -> dict[str, Any]:
    """
    Recommends a perforation program based on formation type, net pay, and skin factor.
    """
    key = formation_type.strip().lower()

    base_configs: dict[str, dict[str, Any]] = {
        "sandstone": {
            "shots_per_foot": 4,
            "phase_angle_deg": 60,
            "perf_diameter_in": 0.47,
            "penetration_in": 12,
            "strategy": "Conventional big-hole charges",
            "notes": "High-porosity matrix; optimise for inflow area over penetration.",
        },
        "limestone": {
            "shots_per_foot": 2,
            "phase_angle_deg": 90,
            "perf_diameter_in": 0.65,
            "penetration_in": 10,
            "strategy": "Large-bore charges with acid pre-flush",
            "notes": "Acid-soluble matrix benefits from large entry holes.",
        },
        "shale": {
            "shots_per_foot": 6,
            "phase_angle_deg": 60,
            "perf_diameter_in": 0.35,
            "penetration_in": 14,
            "strategy": "Cluster perforating for multi-stage hydraulic fracturing",
            "notes": "Perfs act as frac initiation points; cluster spacing is critical.",
        },
        "tight gas": {
            "shots_per_foot": 6,
            "phase_angle_deg": 60,
            "perf_diameter_in": 0.40,
            "penetration_in": 16,
            "strategy": "Deep-penetrating charges to bypass near-wellbore damage",
            "notes": "Ultra-low permeability requires deep penetration for effective connection.",
        },
        "carbonate": {
            "shots_per_foot": 3,
            "phase_angle_deg": 120,
            "perf_diameter_in": 0.55,
            "penetration_in": 11,
            "strategy": "Selective perforating with acid stimulation",
            "notes": "Heterogeneous matrix; target high-porosity streaks selectively.",
        },
    }

    config = base_configs.get(key, base_configs["sandstone"]).copy()

    # Adjust shots per foot and flag stimulation based on skin
    if skin_factor > 10:
        config["shots_per_foot"] = min(config["shots_per_foot"] + 2, 12)
        config["stimulation_required"] = True
        config["stimulation_note"] = (
            f"Skin={skin_factor:.1f} indicates severe near-wellbore damage. "
            "Hydraulic fracturing or aggressive matrix acidising strongly recommended."
        )
    elif skin_factor > 3:
        config["shots_per_foot"] += 1
        config["stimulation_required"] = True
        config["stimulation_note"] = (
            f"Skin={skin_factor:.1f} indicates moderate damage. "
            "Matrix acidising recommended to restore productivity before or after perforating."
        )
    elif skin_factor < 0:
        config["shots_per_foot"] = max(config["shots_per_foot"] - 1, 1)
        config["stimulation_required"] = False
        config["stimulation_note"] = (
            f"Negative skin={skin_factor:.1f} suggests natural fractures or prior stimulation benefit. "
            "Conservative perforation density acceptable."
        )
    else:
        config["stimulation_required"] = False
        config["stimulation_note"] = "Skin within acceptable range; standard program applies."

    total_perfs = int(config["shots_per_foot"] * net_pay_ft)

    if net_pay_ft <= 20:
        interval_strategy = "Single continuous interval across full net pay"
    elif net_pay_ft <= 60:
        interval_strategy = "2–3 perforation clusters with 15–20 ft spacing"
    else:
        interval_strategy = "Multiple selective intervals; isolate shale interbeds"

    config.update(
        {
            "formation_type": formation_type.title(),
            "net_pay_ft": net_pay_ft,
            "total_perforations": total_perfs,
            "interval_strategy": interval_strategy,
            "skin_factor": skin_factor,
        }
    )
    return config


def estimate_stimulation_design(
    formation_type: str,
    reservoir_pressure_psi: float,
    fluid_type: str,
) -> dict[str, Any]:
    """
    Estimates hydraulic fracture or acid stimulation treatment design parameters.
    """
    key = formation_type.strip().lower()
    fluid_key = fluid_type.strip().lower()

    base_designs: dict[str, dict[str, Any]] = {
        "sandstone": {
            "treatment_type": "Hydraulic Fracture — Crosslinked Gel",
            "fluid_volume_bbl": 5_000,
            "pad_volume_fraction": 0.35,
            "proppant_lbm": 200_000,
            "proppant_type": "20/40 mesh white sand",
            "proppant_concentration_ppg_max": 8.0,
            "pump_rate_bpm": 35,
            "expected_half_length_ft": 450,
            "expected_conductivity_md_ft": 800,
            "fracture_width_in": 0.35,
        },
        "limestone": {
            "treatment_type": "Acid Fracture — 15 % HCl",
            "fluid_volume_bbl": 3_000,
            "pad_volume_fraction": 0.20,
            "proppant_lbm": 0,
            "proppant_type": "None (acid-etched fracture faces)",
            "proppant_concentration_ppg_max": 0.0,
            "pump_rate_bpm": 25,
            "expected_half_length_ft": 300,
            "expected_conductivity_md_ft": 2_000,
            "fracture_width_in": 0.15,
        },
        "shale": {
            "treatment_type": "Slickwater Multi-Stage Hydraulic Fracture",
            "fluid_volume_bbl": 25_000,
            "pad_volume_fraction": 0.40,
            "proppant_lbm": 600_000,
            "proppant_type": "100 mesh + 40/70 mesh Ottawa sand",
            "proppant_concentration_ppg_max": 3.0,
            "pump_rate_bpm": 80,
            "expected_half_length_ft": 1_200,
            "expected_conductivity_md_ft": 200,
            "fracture_width_in": 0.10,
        },
        "tight gas": {
            "treatment_type": "High-Rate Hybrid Slickwater / Crosslinked Frac",
            "fluid_volume_bbl": 10_000,
            "pad_volume_fraction": 0.35,
            "proppant_lbm": 350_000,
            "proppant_type": "40/70 resin-coated sand or intermediate-strength ceramic",
            "proppant_concentration_ppg_max": 6.0,
            "pump_rate_bpm": 60,
            "expected_half_length_ft": 800,
            "expected_conductivity_md_ft": 500,
            "fracture_width_in": 0.20,
        },
        "carbonate": {
            "treatment_type": "Prop-Aided Acid Fracture — 28 % HCl",
            "fluid_volume_bbl": 2_000,
            "pad_volume_fraction": 0.15,
            "proppant_lbm": 50_000,
            "proppant_type": "20/40 intermediate-strength ceramic",
            "proppant_concentration_ppg_max": 4.0,
            "pump_rate_bpm": 20,
            "expected_half_length_ft": 250,
            "expected_conductivity_md_ft": 1_500,
            "fracture_width_in": 0.12,
        },
    }

    design = base_designs.get(key, base_designs["sandstone"]).copy()

    # Pressure-based adjustments
    if reservoir_pressure_psi > 8_000:
        design["fluid_volume_bbl"] = int(design["fluid_volume_bbl"] * 1.25)
        design["pump_rate_bpm"] = int(design["pump_rate_bpm"] * 1.15)
        design["hpht_note"] = (
            "High reservoir pressure: use HPHT-rated wellhead and treating iron; "
            "verify crosslinker thermal stability above 300 °F."
        )
    elif reservoir_pressure_psi < 2_000:
        design["fluid_volume_bbl"] = int(design["fluid_volume_bbl"] * 0.75)
        design["low_pressure_note"] = (
            "Low reservoir pressure: minimise fluid volume to reduce water-loading risk; "
            "consider N₂-assisted or foam-based flowback."
        )

    # Fluid-type adjustments
    if "oil" in fluid_key:
        design["recommended_base_fluid"] = "Oil-based pad (lease crude or diesel) for OBM compatibility"
        design["friction_reducer"] = "OBM-compatible friction reducer required"
    elif "gas" in fluid_key:
        design["recommended_base_fluid"] = "Foam-based fluid (N₂ or CO₂ energised) to minimise water loading in gas reservoir"
        design["friction_reducer"] = "Standard anionic polyacrylamide friction reducer"
    else:
        design["recommended_base_fluid"] = "Slickwater (fresh water + friction reducer) or crosslinked borate gel"
        design["friction_reducer"] = "Anionic polyacrylamide friction reducer at 0.5–1.0 gpt"

    pad_volume_bbl = int(design["fluid_volume_bbl"] * design["pad_volume_fraction"])
    estimated_treating_pressure_psi = int(reservoir_pressure_psi * 1.35)
    treatment_duration_min = round(design["fluid_volume_bbl"] / design["pump_rate_bpm"], 1)

    design.update(
        {
            "pad_volume_bbl": pad_volume_bbl,
            "estimated_treating_pressure_psi": estimated_treating_pressure_psi,
            "treatment_duration_min": treatment_duration_min,
            "reservoir_pressure_psi": reservoir_pressure_psi,
            "fluid_type_input": fluid_type.title(),
            "formation_type": formation_type.title(),
        }
    )
    return design


# ── OpenAI function-calling schemas ──────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_fracture_gradient",
            "description": (
                "Calculates fracture gradient and fracture pressure using Eaton's method. "
                "Returns fracture gradient (psi/ft), fracture pressure (psi), closure pressure, "
                "ISIP estimate, and safe mud-weight window. "
                "If the user does not supply overburden gradient, use 1.0 psi/ft as the default."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "depth_ft": {
                        "type": "number",
                        "description": "True vertical depth of the target formation in feet.",
                    },
                    "overburden_psi_per_ft": {
                        "type": "number",
                        "description": (
                            "Overburden stress gradient in psi/ft. "
                            "Typical range 0.90–1.10 psi/ft; use 1.0 psi/ft if not specified."
                        ),
                    },
                },
                "required": ["depth_ft", "overburden_psi_per_ft"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_perforation_strategy",
            "description": (
                "Recommends a perforation program—shots per foot, phase angle, charge diameter, "
                "and completion strategy—based on formation lithology, net pay thickness, and skin factor."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "formation_type": {
                        "type": "string",
                        "enum": ["Sandstone", "Limestone", "Shale", "Tight Gas", "Carbonate"],
                        "description": "Lithology of the target formation.",
                    },
                    "net_pay_ft": {
                        "type": "number",
                        "description": "Net pay thickness in feet.",
                    },
                    "skin_factor": {
                        "type": "number",
                        "description": (
                            "Dimensionless skin factor. "
                            "Positive values indicate near-wellbore damage; "
                            "negative values indicate stimulation benefit or natural fractures."
                        ),
                    },
                },
                "required": ["formation_type", "net_pay_ft", "skin_factor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_stimulation_design",
            "description": (
                "Estimates hydraulic fracture or acid stimulation treatment parameters including "
                "fluid volume, proppant loading, pump rate, expected fracture half-length, "
                "conductivity, and treating pressure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "formation_type": {
                        "type": "string",
                        "enum": ["Sandstone", "Limestone", "Shale", "Tight Gas", "Carbonate"],
                        "description": "Lithology of the target formation.",
                    },
                    "reservoir_pressure_psi": {
                        "type": "number",
                        "description": "Static reservoir pressure in psi.",
                    },
                    "fluid_type": {
                        "type": "string",
                        "description": (
                            "Drilling or completion fluid type "
                            "(e.g. 'Water-based', 'Oil-based', 'Gas')."
                        ),
                    },
                },
                "required": ["formation_type", "reservoir_pressure_psi", "fluid_type"],
            },
        },
    },
]
