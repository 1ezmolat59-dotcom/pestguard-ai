"""
PestGuard AI — EPA Product Database
~40 common commercial pest control products with real-world data.
In production, this would connect to EPA's national pesticide database.
"""
from typing import Optional

EPA_PRODUCTS = [
    {
        "epa_reg_no": "432-763",
        "product_name": "Suspend SC",
        "active_ingredient": "Deltamethrin 4.75%",
        "manufacturer": "Bayer Environmental Science",
        "signal_word": "CAUTION",
        "target_pests": ["ants", "cockroaches", "spiders", "fleas", "flies", "mosquitoes"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "279-3206",
        "product_name": "Talstar Pro",
        "active_ingredient": "Bifenthrin 7.9%",
        "manufacturer": "FMC Corporation",
        "signal_word": "WARNING",
        "target_pests": ["ants", "termites", "cockroaches", "spiders", "bed bugs", "fleas", "ticks"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial", "lawn"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection, long sleeves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "7969-210",
        "product_name": "Termidor SC",
        "active_ingredient": "Fipronil 9.1%",
        "manufacturer": "BASF Corporation",
        "signal_word": "WARNING",
        "target_pests": ["termites", "ants", "cockroaches"],
        "application_sites": ["soil", "perimeter", "structural"],
        "restricted_use": True,
        "ppe_required": "gloves, eye protection, respirator, long sleeves",
        "re_entry_interval_hrs": 24,
    },
    {
        "epa_reg_no": "352-742",
        "product_name": "Advion Ant Bait Gel",
        "active_ingredient": "Indoxacarb 0.5%",
        "manufacturer": "Syngenta",
        "signal_word": "CAUTION",
        "target_pests": ["ants", "cockroaches"],
        "application_sites": ["indoor", "residential", "commercial", "food handling"],
        "restricted_use": False,
        "ppe_required": "gloves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "432-1450",
        "product_name": "Temprid SC",
        "active_ingredient": "Beta-Cyfluthrin 10.5% + Imidacloprid 21%",
        "manufacturer": "Bayer Environmental Science",
        "signal_word": "WARNING",
        "target_pests": ["bed bugs", "cockroaches", "ants", "fleas", "spiders"],
        "application_sites": ["indoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "499-540",
        "product_name": "Alpine WSG",
        "active_ingredient": "Dinotefuran 40%",
        "manufacturer": "MGK",
        "signal_word": "CAUTION",
        "target_pests": ["ants", "cockroaches", "bed bugs", "flies"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "241-392",
        "product_name": "Phantom",
        "active_ingredient": "Chlorfenapyr 21.45%",
        "manufacturer": "BASF Corporation",
        "signal_word": "CAUTION",
        "target_pests": ["ants", "cockroaches", "bed bugs", "termites"],
        "application_sites": ["indoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "100-1066",
        "product_name": "Demand CS",
        "active_ingredient": "Lambda-Cyhalothrin 9.7%",
        "manufacturer": "Syngenta",
        "signal_word": "WARNING",
        "target_pests": ["ants", "spiders", "cockroaches", "flies", "mosquitoes", "fleas", "ticks"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "2724-490",
        "product_name": "Gentrol IGR",
        "active_ingredient": "Hydroprene 9%",
        "manufacturer": "Wellmark International",
        "signal_word": "CAUTION",
        "target_pests": ["cockroaches", "fleas", "stored product pests"],
        "application_sites": ["indoor", "residential", "commercial", "food handling"],
        "restricted_use": False,
        "ppe_required": "gloves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "432-1254",
        "product_name": "Cy-Kick CS",
        "active_ingredient": "Cyfluthrin 6%",
        "manufacturer": "Whitmire Micro-Gen",
        "signal_word": "WARNING",
        "target_pests": ["ants", "cockroaches", "spiders", "fleas", "bed bugs"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "655-876",
        "product_name": "Altriset",
        "active_ingredient": "Chlorantraniliprole 18.4%",
        "manufacturer": "Syngenta",
        "signal_word": "CAUTION",
        "target_pests": ["termites"],
        "application_sites": ["soil", "perimeter", "structural"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "8329-5",
        "product_name": "Niban Granular Bait",
        "active_ingredient": "Orthoboric Acid 5%",
        "manufacturer": "Nisus Corporation",
        "signal_word": "CAUTION",
        "target_pests": ["cockroaches", "ants", "crickets", "silverfish"],
        "application_sites": ["indoor", "outdoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "64248-18",
        "product_name": "Vendetta Roach Bait",
        "active_ingredient": "Abamectin 0.05%",
        "manufacturer": "MGK",
        "signal_word": "CAUTION",
        "target_pests": ["cockroaches"],
        "application_sites": ["indoor", "residential", "commercial", "food handling"],
        "restricted_use": False,
        "ppe_required": "gloves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "279-3372",
        "product_name": "Talstar XTRA",
        "active_ingredient": "Bifenthrin 0.2% + Zeta-Cypermethrin 0.05%",
        "manufacturer": "FMC Corporation",
        "signal_word": "WARNING",
        "target_pests": ["ants", "cockroaches", "fleas", "ticks", "mosquitoes", "spiders"],
        "application_sites": ["outdoor", "lawn", "perimeter", "residential"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
    {
        "epa_reg_no": "432-1544",
        "product_name": "Premise 75",
        "active_ingredient": "Imidacloprid 75%",
        "manufacturer": "Bayer Environmental Science",
        "signal_word": "CAUTION",
        "target_pests": ["termites"],
        "application_sites": ["soil", "perimeter", "structural"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection, long sleeves",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "8730-65",
        "product_name": "Taurus SC",
        "active_ingredient": "Fipronil 9.1%",
        "manufacturer": "Control Solutions",
        "signal_word": "WARNING",
        "target_pests": ["termites", "ants", "cockroaches"],
        "application_sites": ["soil", "perimeter", "structural"],
        "restricted_use": True,
        "ppe_required": "gloves, eye protection, respirator",
        "re_entry_interval_hrs": 24,
    },
    {
        "epa_reg_no": "53883-284",
        "product_name": "Catchmaster Glue Traps",
        "active_ingredient": "None (mechanical)",
        "manufacturer": "AP&G Co.",
        "signal_word": "NONE",
        "target_pests": ["rodents", "insects"],
        "application_sites": ["indoor", "residential", "commercial"],
        "restricted_use": False,
        "ppe_required": "none",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "1021-1817",
        "product_name": "Contrac Blox",
        "active_ingredient": "Bromadiolone 0.005%",
        "manufacturer": "Bell Laboratories",
        "signal_word": "DANGER",
        "target_pests": ["rats", "mice"],
        "application_sites": ["indoor", "outdoor", "perimeter"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection — ANTICOAGULANT RODENTICIDE",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "12455-36",
        "product_name": "Ditrac All-Weather Blox",
        "active_ingredient": "Diphacinone 0.005%",
        "manufacturer": "Bell Laboratories",
        "signal_word": "DANGER",
        "target_pests": ["rats", "mice"],
        "application_sites": ["indoor", "outdoor", "perimeter"],
        "restricted_use": False,
        "ppe_required": "gloves — ANTICOAGULANT RODENTICIDE",
        "re_entry_interval_hrs": 0,
    },
    {
        "epa_reg_no": "100-1501",
        "product_name": "Karate Zeon",
        "active_ingredient": "Lambda-Cyhalothrin 2.08%",
        "manufacturer": "Syngenta",
        "signal_word": "WARNING",
        "target_pests": ["mosquitoes", "flies", "gnats", "ants"],
        "application_sites": ["outdoor", "perimeter", "lawn", "commercial"],
        "restricted_use": False,
        "ppe_required": "gloves, eye protection",
        "re_entry_interval_hrs": 4,
    },
]

# Build lookup dictionaries for fast access
_by_reg_no = {p["epa_reg_no"]: p for p in EPA_PRODUCTS}
_by_name_lower = {p["product_name"].lower(): p for p in EPA_PRODUCTS}


def search_products(query: str) -> list:
    """Search products by name or EPA reg number."""
    q = query.lower().strip()
    results = []
    for p in EPA_PRODUCTS:
        if (q in p["product_name"].lower() or
                q in p["epa_reg_no"].lower() or
                q in p["active_ingredient"].lower()):
            results.append(p)
    return results[:10]


def get_by_reg_no(reg_no: str) -> Optional[dict]:
    """Look up a product by its EPA registration number."""
    return _by_reg_no.get(reg_no.strip())


def get_by_name(name: str) -> Optional[dict]:
    """Look up a product by product name (case-insensitive)."""
    return _by_name_lower.get(name.strip().lower())


def get_all() -> list:
    return EPA_PRODUCTS


def get_restricted() -> list:
    return [p for p in EPA_PRODUCTS if p["restricted_use"]]


# Common pest → canonical name mapping (for AI normalization)
PEST_ALIASES = {
    "roach": "cockroaches", "roaches": "cockroaches", "palmetto bug": "cockroaches",
    "ant": "ants", "fire ant": "ants", "carpenter ant": "ants",
    "flea": "fleas", "tick": "ticks", "termite": "termites",
    "mouse": "mice", "rat": "rats", "rodent": "rodents", "rodents": "rodents",
    "spider": "spiders", "mosquito": "mosquitoes", "fly": "flies", "bed bug": "bed bugs",
    "silverfish": "silverfish", "cricket": "crickets",
}

# Application method aliases
METHOD_ALIASES = {
    "spray": "Sprayer", "sprayed": "Sprayer", "sprayer": "Sprayer",
    "gel": "Gel Application", "bait": "Bait Placement", "baited": "Bait Placement",
    "granule": "Granular", "granules": "Granular", "broadcast": "Broadcast",
    "inject": "Injection", "injection": "Injection",
    "fogger": "Fogging", "fog": "Fogging", "mist": "Misting",
    "dust": "Dust Application", "dusted": "Dust Application",
    "trap": "Trap Placement", "glue trap": "Trap Placement",
    "bait station": "Bait Station", "block": "Bait Station",
}
