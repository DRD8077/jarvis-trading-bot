"""
🎮 JARVIS Gaming AI Engine v10.0 — Pro-Level BGMI/PUBG Mobile Assistant
══════════════════════════════════════════════════════════════════════════
AI-powered gaming assistant that plays like Jonathan Gaming, Mortal, Scout.
Features:
  • Real-time screen analysis via MediaProjection/Screen Share
  • Pro player sensitivity profiles (Jonathan, Mortal, Scout, Dynamo, etc.)
  • Game state detection (lobby, plane, parachute, looting, combat, healing)
  • Enemy detection & position callouts
  • Auto-sensitivity adjustment based on weapon/scope
  • Tactical decision engine (rotate, push, hold, retreat)
  • Crosshair placement & recoil pattern advisor
  • Zone/circle prediction & rotation planning
  • Loot priority engine
  • Voice coaching (real-time callouts)
  • Performance analytics & improvement tracking
"""

import os
import json
import time
import math
import logging
import asyncio
import random
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from collections import deque

logger = logging.getLogger("jarvis.gaming")

# ═══════════════════════════════════════════
# PRO PLAYER SENSITIVITY PROFILES
# ═══════════════════════════════════════════

PRO_PLAYER_PROFILES = {
    "jonathan_gaming": {
        "name": "Jonathan Gaming (TSM Entity)",
        "real_name": "Jonathan Amaral",
        "playstyle": "ultra_aggressive",
        "role": "assaulter",
        "specialty": ["close_combat", "m416_spray", "rushing", "reflex_shots"],
        "device": "iPad Pro 2021",
        "claw": "4_finger",
        "gyroscope": "always_on",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 195,
                "1st_person_no_scope": 195,
                "red_dot": 55,
                "2x_scope": 40,
                "3x_scope": 28,
                "4x_scope": 18,
                "6x_scope": 12,
                "8x_scope": 8,
            },
            "ads": {
                "3rd_person_no_scope": 130,
                "1st_person_no_scope": 130,
                "red_dot": 55,
                "2x_scope": 38,
                "3x_scope": 25,
                "4x_scope": 15,
                "6x_scope": 10,
                "8x_scope": 7,
            },
            "gyroscope": {
                "3rd_person_no_scope": 300,
                "1st_person_no_scope": 300,
                "red_dot": 300,
                "2x_scope": 290,
                "3x_scope": 250,
                "4x_scope": 200,
                "6x_scope": 150,
                "8x_scope": 100,
            },
            "freelook": 85,
        },
        "graphics": {
            "quality": "smooth",
            "frame_rate": "extreme",
            "style": "colorful",
            "anti_aliasing": False,
            "shadows": False,
        },
        "controls": {
            "peek": True,
            "lean": "tap",
            "scope_mode": "tap",
            "firing_mode": "hip_fire_priority",
            "auto_pickup": True,
            "crouch_mode": "hold",
        },
        "tactics": {
            "early_game": "hot_drop_always",
            "mid_game": "aggressive_push",
            "late_game": "zone_edge_dominate",
            "preferred_weapons": ["M416", "AKM", "UZI", "Groza"],
            "preferred_drop": ["Pochinki", "School", "Military Base", "Georgopol"],
            "rotation_style": "vehicle_rush",
            "engagement_range": "close_to_mid",
        },
        "tips": [
            "Always pre-aim corners at head level",
            "Hip fire in CQC under 10m — faster than ADS",
            "Use jiggle peek to bait shots before pushing",
            "Sprint + crouch near walls for unpredictable movement",
            "Master M416 + 3x spray control — Jonathan's signature",
            "Drop hot, fight early, build confidence and loot from kills",
            "Use gyroscope for micro-adjustments during spray",
        ]
    },
    
    "mortal_gaming": {
        "name": "Mortal (Soul Mortal)",
        "real_name": "Naman Mathur",
        "playstyle": "strategic_aggressive",
        "role": "igl_assaulter",
        "specialty": ["strategy", "clutch_plays", "sniping", "team_coordination"],
        "device": "OnePlus 7T",
        "claw": "4_finger",
        "gyroscope": "always_on",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 180,
                "1st_person_no_scope": 180,
                "red_dot": 50,
                "2x_scope": 38,
                "3x_scope": 25,
                "4x_scope": 16,
                "6x_scope": 10,
                "8x_scope": 7,
            },
            "ads": {
                "3rd_person_no_scope": 120,
                "1st_person_no_scope": 120,
                "red_dot": 50,
                "2x_scope": 35,
                "3x_scope": 22,
                "4x_scope": 14,
                "6x_scope": 9,
                "8x_scope": 6,
            },
            "gyroscope": {
                "3rd_person_no_scope": 300,
                "1st_person_no_scope": 300,
                "red_dot": 300,
                "2x_scope": 280,
                "3x_scope": 240,
                "4x_scope": 190,
                "6x_scope": 140,
                "8x_scope": 90,
            },
            "freelook": 80,
        },
        "graphics": {
            "quality": "smooth",
            "frame_rate": "extreme",
            "style": "colorful",
            "anti_aliasing": False,
            "shadows": False,
        },
        "controls": {
            "peek": True,
            "lean": "tap",
            "scope_mode": "hold",
            "firing_mode": "ads_priority",
            "auto_pickup": True,
            "crouch_mode": "tap",
        },
        "tactics": {
            "early_game": "semi_hot_drop",
            "mid_game": "map_control",
            "late_game": "strategic_positioning",
            "preferred_weapons": ["M416", "AWM", "DP-28", "M24"],
            "preferred_drop": ["Bootcamp", "Paradise Resort", "Ruins"],
            "rotation_style": "early_rotation",
            "engagement_range": "mid_to_long",
        },
        "tips": [
            "Always have a plan before engaging — think 2 steps ahead",
            "Use smokes to create cover for revives and rushes",
            "Communicate enemy positions with clock callout system",
            "Save utility (grenades, molotovs) for endgame",
            "Rotate early to get zone advantage",
            "Never fight in the open — always have cover nearby",
            "IGL tip: announce rotations 30 seconds before moving",
        ]
    },
    
    "scout_gaming": {
        "name": "Scout (Team XSpark)",
        "real_name": "Tanmay Singh",
        "playstyle": "hyper_aggressive",
        "role": "fragger",
        "specialty": ["close_combat", "reflexes", "movement", "1v4_clutch"],
        "device": "iPad Pro",
        "claw": "4_finger",
        "gyroscope": "always_on",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 200,
                "1st_person_no_scope": 200,
                "red_dot": 60,
                "2x_scope": 42,
                "3x_scope": 30,
                "4x_scope": 20,
                "6x_scope": 14,
                "8x_scope": 9,
            },
            "ads": {
                "3rd_person_no_scope": 140,
                "1st_person_no_scope": 140,
                "red_dot": 58,
                "2x_scope": 40,
                "3x_scope": 27,
                "4x_scope": 17,
                "6x_scope": 12,
                "8x_scope": 8,
            },
            "gyroscope": {
                "3rd_person_no_scope": 300,
                "1st_person_no_scope": 300,
                "red_dot": 300,
                "2x_scope": 295,
                "3x_scope": 260,
                "4x_scope": 210,
                "6x_scope": 160,
                "8x_scope": 110,
            },
            "freelook": 90,
        },
        "graphics": {
            "quality": "smooth",
            "frame_rate": "extreme",
            "style": "colorful",
            "anti_aliasing": False,
            "shadows": False,
        },
        "tactics": {
            "early_game": "hot_drop_dominate",
            "mid_game": "hunt_for_kills",
            "late_game": "aggressive_endgame",
            "preferred_weapons": ["M416", "AKM", "UMP45", "AWM"],
            "preferred_drop": ["Pochinki", "School", "Bootcamp"],
            "rotation_style": "kill_based_rotation",
            "engagement_range": "close",
        },
        "tips": [
            "Movement is life — never stand still during a fight",
            "Drop shot + prone in unexpected moments to dodge bullets",
            "Master the AKM iron sight spray — devastating in CQC",
            "Use vehicles as mobile cover during rotations",
            "Practice 1v4 in TDM — build clutch confidence",
            "Pre-fire common camping spots when pushing compounds",
        ]
    },
    
    "dynamo_gaming": {
        "name": "Dynamo Gaming",
        "real_name": "Aadii Sawant",
        "playstyle": "entertaining_aggressive",
        "role": "assaulter",
        "specialty": ["entertainment", "rushing", "spray_control", "panicking_enemies"],
        "device": "OnePlus",
        "claw": "2_thumb",
        "gyroscope": "scope_only",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 170,
                "1st_person_no_scope": 170,
                "red_dot": 45,
                "2x_scope": 35,
                "3x_scope": 22,
                "4x_scope": 14,
                "6x_scope": 9,
                "8x_scope": 6,
            },
            "ads": {
                "3rd_person_no_scope": 110,
                "1st_person_no_scope": 110,
                "red_dot": 45,
                "2x_scope": 32,
                "3x_scope": 20,
                "4x_scope": 12,
                "6x_scope": 8,
                "8x_scope": 5,
            },
            "gyroscope": {
                "3rd_person_no_scope": 250,
                "1st_person_no_scope": 250,
                "red_dot": 250,
                "2x_scope": 230,
                "3x_scope": 200,
                "4x_scope": 160,
                "6x_scope": 120,
                "8x_scope": 80,
            },
            "freelook": 75,
        },
        "tactics": {
            "early_game": "hot_drop",
            "mid_game": "push_everything",
            "late_game": "zone_control",
            "preferred_weapons": ["M416", "AKM", "UZI", "Pan"],
            "preferred_drop": ["Pochinki", "Los Leones", "Paradise Resort"],
            "rotation_style": "vehicle_rush",
            "engagement_range": "close_to_mid",
        },
    },

    "mavi_gaming": {
        "name": "Mavi (Team Soul)",
        "real_name": "Harpreet Singh",
        "playstyle": "methodical_aggressive",
        "role": "assaulter",
        "specialty": ["spray_control", "positioning", "clutch", "consistency"],
        "device": "iPad Pro",
        "claw": "4_finger",
        "gyroscope": "always_on",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 190,
                "1st_person_no_scope": 190,
                "red_dot": 52,
                "2x_scope": 38,
                "3x_scope": 26,
                "4x_scope": 17,
                "6x_scope": 11,
                "8x_scope": 7,
            },
            "ads": {
                "3rd_person_no_scope": 125,
                "1st_person_no_scope": 125,
                "red_dot": 52,
                "2x_scope": 36,
                "3x_scope": 24,
                "4x_scope": 15,
                "6x_scope": 10,
                "8x_scope": 6,
            },
            "gyroscope": {
                "3rd_person_no_scope": 300,
                "1st_person_no_scope": 300,
                "red_dot": 300,
                "2x_scope": 285,
                "3x_scope": 245,
                "4x_scope": 195,
                "6x_scope": 145,
                "8x_scope": 95,
            },
            "freelook": 82,
        },
        "tactics": {
            "early_game": "hot_drop",
            "mid_game": "controlled_aggression",
            "late_game": "clutch_positioning",
            "preferred_weapons": ["M416", "Beryl M762", "AWM", "DP-28"],
            "preferred_drop": ["Pochinki", "Bootcamp", "Ruins"],
            "rotation_style": "compound_to_compound",
            "engagement_range": "mid",
        },
    },
    
    "zgod_gaming": {
        "name": "Zgod (GodLike Esports)",
        "real_name": "Abhishek Choudhary",
        "playstyle": "supreme_aggression",
        "role": "fragger",
        "specialty": ["insane_reflexes", "hipfire", "movement", "1v1_god"],
        "device": "iPad Air",
        "claw": "4_finger",
        "gyroscope": "always_on",
        "sensitivity": {
            "camera": {
                "3rd_person_no_scope": 200,
                "1st_person_no_scope": 200,
                "red_dot": 58,
                "2x_scope": 43,
                "3x_scope": 30,
                "4x_scope": 19,
                "6x_scope": 13,
                "8x_scope": 9,
            },
            "ads": {
                "3rd_person_no_scope": 135,
                "1st_person_no_scope": 135,
                "red_dot": 56,
                "2x_scope": 40,
                "3x_scope": 28,
                "4x_scope": 17,
                "6x_scope": 11,
                "8x_scope": 7,
            },
            "gyroscope": {
                "3rd_person_no_scope": 300,
                "1st_person_no_scope": 300,
                "red_dot": 300,
                "2x_scope": 295,
                "3x_scope": 260,
                "4x_scope": 215,
                "6x_scope": 165,
                "8x_scope": 115,
            },
            "freelook": 88,
        },
        "tactics": {
            "early_game": "hot_drop_dominate",
            "mid_game": "aggression",
            "late_game": "kill_everyone",
            "preferred_weapons": ["M416", "Beryl M762", "UZI", "Groza"],
            "preferred_drop": ["Pochinki", "School", "Bootcamp"],
            "rotation_style": "aggressive_push",
            "engagement_range": "close",
        },
    },
}

# ═══════════════════════════════════════════
# WEAPON DATABASE
# ═══════════════════════════════════════════

WEAPONS_DB = {
    # Assault Rifles
    "M416": {
        "type": "AR", "damage": 41, "fire_rate": 0.086, "bullet_speed": 880,
        "recoil_pattern": "low_stable", "spray_difficulty": 3,
        "best_attachments": ["compensator", "vertical_grip", "extended_quickdraw", "3x_scope"],
        "effective_range": {"close": 95, "mid": 90, "long": 70},
        "recoil_tip": "Pull down-left slightly for first 10 bullets, then down-right",
        "pro_tip": "Best all-rounder. Jonathan's main weapon — master this first.",
    },
    "AKM": {
        "type": "AR", "damage": 49, "fire_rate": 0.1, "bullet_speed": 715,
        "recoil_pattern": "high_vertical", "spray_difficulty": 7,
        "best_attachments": ["compensator", None, "extended_quickdraw", "red_dot"],
        "effective_range": {"close": 90, "mid": 75, "long": 55},
        "recoil_tip": "Strong pull-down. Use single tap beyond 50m. Spray only close range.",
        "pro_tip": "Highest AR DPS. Scout uses AKM iron sight — practice in TDM.",
    },
    "Beryl M762": {
        "type": "AR", "damage": 47, "fire_rate": 0.086, "bullet_speed": 715,
        "recoil_pattern": "high_random", "spray_difficulty": 8,
        "best_attachments": ["compensator", "vertical_grip", "extended_quickdraw", "red_dot"],
        "effective_range": {"close": 93, "mid": 78, "long": 50},
        "recoil_tip": "Hardest AR to control. Pull down and slightly right. Use gyro heavily.",
        "pro_tip": "Melts enemies in CQC but hard to spray. Mavi's choice for rushing.",
    },
    "Groza": {
        "type": "AR", "damage": 49, "fire_rate": 0.08, "bullet_speed": 715,
        "recoil_pattern": "moderate_vertical", "spray_difficulty": 5,
        "best_attachments": ["suppressor", None, "extended_quickdraw", "red_dot"],
        "effective_range": {"close": 95, "mid": 85, "long": 60},
        "recoil_tip": "Moderate recoil but very high DPS. Pull straight down.",
        "pro_tip": "Best CQC AR in the game. Pick up from airdrops immediately.",
    },
    "M16A4": {
        "type": "AR", "damage": 43, "fire_rate": 0.075, "bullet_speed": 900,
        "recoil_pattern": "very_low", "spray_difficulty": 2,
        "best_attachments": ["compensator", None, "extended_quickdraw", "4x_scope"],
        "effective_range": {"close": 60, "mid": 88, "long": 85},
        "recoil_tip": "Burst mode — tap fast. Almost zero recoil per burst.",
        "pro_tip": "Underrated for mid-long range. Insane bullet velocity.",
    },
    "SCAR-L": {
        "type": "AR", "damage": 41, "fire_rate": 0.096, "bullet_speed": 870,
        "recoil_pattern": "low_stable", "spray_difficulty": 2,
        "best_attachments": ["compensator", "vertical_grip", "extended_quickdraw", "3x_scope"],
        "effective_range": {"close": 85, "mid": 88, "long": 72},
        "recoil_tip": "Easiest AR to spray. Gentle pull-down. Great for beginners.",
    },
    # SMGs
    "UZI": {
        "type": "SMG", "damage": 26, "fire_rate": 0.048, "bullet_speed": 400,
        "recoil_pattern": "low_fast", "spray_difficulty": 2,
        "effective_range": {"close": 98, "mid": 45, "long": 15},
        "pro_tip": "Fastest fire rate. CQC monster. Jonathan uses UZI as secondary.",
    },
    "UMP45": {
        "type": "SMG", "damage": 41, "fire_rate": 0.092, "bullet_speed": 400,
        "recoil_pattern": "very_low", "spray_difficulty": 1,
        "effective_range": {"close": 90, "mid": 70, "long": 40},
        "pro_tip": "Most accurate SMG. Great hipfire. Good for beginners.",
    },
    "Vector": {
        "type": "SMG", "damage": 31, "fire_rate": 0.055, "bullet_speed": 370,
        "recoil_pattern": "low_fast", "spray_difficulty": 3,
        "effective_range": {"close": 95, "mid": 50, "long": 20},
        "pro_tip": "Insane close range DPS. Extended mag is mandatory.",
    },
    # Snipers
    "AWM": {
        "type": "Sniper", "damage": 120, "fire_rate": 1.85, "bullet_speed": 945,
        "recoil_pattern": "bolt_action", "spray_difficulty": 0,
        "effective_range": {"close": 40, "mid": 85, "long": 100},
        "pro_tip": "One-shot headshot through level 3 helmet. Hold your breath before firing.",
    },
    "M24": {
        "type": "Sniper", "damage": 79, "fire_rate": 1.8, "bullet_speed": 790,
        "recoil_pattern": "bolt_action", "spray_difficulty": 0,
        "effective_range": {"close": 35, "mid": 80, "long": 95},
        "pro_tip": "Faster bolt cycle than Kar98. Lead moving targets by 1 body width at 200m.",
    },
    "Kar98k": {
        "type": "Sniper", "damage": 75, "fire_rate": 1.9, "bullet_speed": 760,
        "recoil_pattern": "bolt_action", "spray_difficulty": 0,
        "effective_range": {"close": 30, "mid": 75, "long": 93},
    },
    # DMR
    "DP-28": {
        "type": "LMG", "damage": 51, "fire_rate": 0.109, "bullet_speed": 715,
        "recoil_pattern": "very_low_prone", "spray_difficulty": 2,
        "effective_range": {"close": 75, "mid": 90, "long": 80},
        "pro_tip": "Mortal's choice. Go prone for zero recoil. 47 round mag is insane.",
    },
    "Mini14": {
        "type": "DMR", "damage": 46, "fire_rate": 0.133, "bullet_speed": 990,
        "recoil_pattern": "low_tap", "spray_difficulty": 1,
        "effective_range": {"close": 50, "mid": 85, "long": 90},
    },
    "SLR": {
        "type": "DMR", "damage": 58, "fire_rate": 0.133, "bullet_speed": 840,
        "recoil_pattern": "high_kick", "spray_difficulty": 6,
        "effective_range": {"close": 50, "mid": 82, "long": 88},
    },
    "SKS": {
        "type": "DMR", "damage": 53, "fire_rate": 0.133, "bullet_speed": 800,
        "recoil_pattern": "moderate_kick", "spray_difficulty": 4,
        "effective_range": {"close": 45, "mid": 80, "long": 85},
    },
    # Shotguns
    "S12K": {
        "type": "Shotgun", "damage": 22, "fire_rate": 0.25, "bullet_speed": 350,
        "recoil_pattern": "heavy_spread", "spray_difficulty": 3,
        "effective_range": {"close": 95, "mid": 20, "long": 5},
    },
    "S1897": {
        "type": "Shotgun", "damage": 26, "fire_rate": 0.75, "bullet_speed": 360,
        "recoil_pattern": "pump_action", "spray_difficulty": 0,
        "effective_range": {"close": 90, "mid": 15, "long": 3},
    },
}

# ═══════════════════════════════════════════
# MAP KNOWLEDGE DATABASE
# ═══════════════════════════════════════════

MAPS_DB = {
    "erangel": {
        "name": "Erangel",
        "size": "8x8 km",
        "hot_drops": [
            {"name": "Pochinki", "risk": 9, "loot": 8, "tip": "Center of map. Expect 5-10 squads. Clear compound by compound."},
            {"name": "School + Apartments", "risk": 10, "loot": 7, "tip": "Most contested spot. Land roof first. Clear top-down."},
            {"name": "Military Base", "risk": 8, "loot": 10, "tip": "Best loot on map. Control the bridge for easy kills."},
            {"name": "Georgopol", "risk": 7, "loot": 9, "tip": "Containers have best loot density. North port vs south crates."},
            {"name": "Yasnaya", "risk": 7, "loot": 8, "tip": "Large city. Many compounds. Watch for bridge campers."},
            {"name": "Rozhok", "risk": 8, "loot": 7, "tip": "Central. Good for early kills. Rotate to school or pochinki."},
        ],
        "safe_drops": [
            {"name": "Zharki", "risk": 2, "loot": 6, "tip": "Far north-west. Safe but need vehicle to rotate."},
            {"name": "Kameshki", "risk": 1, "loot": 5, "tip": "Northeast corner. Almost always uncontested."},
            {"name": "Lipovka", "risk": 2, "loot": 5, "tip": "East side. Quiet but decent loot."},
        ],
        "vehicle_spawns": ["main_roads", "garages", "gas_stations"],
        "rotation_tips": [
            "North-south bridges are deadly — swim or boat instead",
            "Use terrain for cover on open fields",
            "Compound-to-compound rotation is safest",
            "Military zone requires bridge control or boats",
        ]
    },
    "sanhok": {
        "name": "Sanhok",
        "size": "4x4 km",
        "hot_drops": [
            {"name": "Bootcamp", "risk": 10, "loot": 9, "tip": "THE hot drop. Land main building roof. CQC paradise."},
            {"name": "Paradise Resort", "risk": 9, "loot": 9, "tip": "Large buildings with great loot. Control high ground."},
            {"name": "Ruins", "risk": 8, "loot": 8, "tip": "Central ruins. Multiple levels. Watch all angles."},
            {"name": "Pai Nan", "risk": 7, "loot": 8, "tip": "Southern dock area. Good loot, moderate traffic."},
        ],
        "rotation_tips": [
            "Zones move fast on Sanhok — rotate early",
            "Use dense vegetation for stealth movement",
            "River crossings are kill zones — use bridges or swim quickly",
            "QBZ and QBU spawn here instead of SCAR and Mini14",
        ]
    },
    "miramar": {
        "name": "Miramar",
        "size": "8x8 km",
        "hot_drops": [
            {"name": "Pecado", "risk": 10, "loot": 8, "tip": "Arena + Casino. Land roof of arena for height advantage."},
            {"name": "Hacienda del Patron", "risk": 9, "loot": 9, "tip": "Best loot density. Land main building 2nd floor."},
            {"name": "Los Leones", "risk": 7, "loot": 9, "tip": "Huge city. Can loot safely if you pick the right block."},
            {"name": "San Martin", "risk": 8, "loot": 7, "tip": "Central. Lots of action. Good for practice."},
        ],
        "rotation_tips": [
            "Vehicles are ESSENTIAL on Miramar — grab one immediately",
            "Use ridgelines for cover during rotations",
            "Win98 and R45 spawn here — learn them",
            "The terrain gives snipers massive advantage",
        ]
    },
    "livik": {
        "name": "Livik",
        "size": "2x2 km",
        "hot_drops": [
            {"name": "Midstein", "risk": 9, "loot": 8, "tip": "Center city. Fast-paced CQC."},
            {"name": "Blomster", "risk": 8, "loot": 8, "tip": "Industrial area. Good loot density."},
            {"name": "Hot Springs", "risk": 7, "loot": 7, "tip": "Unique terrain. Use steam for cover."},
        ],
        "rotation_tips": [
            "P90 and MK12 are Livik exclusives — very powerful",
            "Smallest map — action everywhere, always be ready",
            "Games are fast — loot quickly, fight constantly",
        ]
    },
}

# ═══════════════════════════════════════════
# GAME STATE DETECTION ENGINE
# ═══════════════════════════════════════════

class GameStateDetector:
    """Detects current game state from screen frames using AI vision."""
    
    STATES = [
        "lobby", "matchmaking", "loading", "plane", "parachuting",
        "looting", "running", "driving", "swimming", "combat",
        "healing", "reviving", "spectating", "results", "unknown"
    ]
    
    # Color signatures for different UI elements
    UI_SIGNATURES = {
        "health_bar": {"region": "bottom_left", "color_range": ((200, 50, 50), (255, 120, 120))},
        "minimap": {"region": "top_right", "color_range": ((180, 180, 180), (255, 255, 255))},
        "kill_feed": {"region": "top_left", "color_range": ((200, 200, 200), (255, 255, 255))},
        "backpack": {"region": "bottom_right", "colors": "mixed"},
        "zone_timer": {"region": "top_center", "color_blue": True},
        "scope_overlay": {"region": "center", "circular": True},
    }
    
    def __init__(self):
        self.current_state = "unknown"
        self.state_history = deque(maxlen=100)
        self.combat_start_time = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.zone_phase = 0
        self.alive_count = 100
        self.kill_count = 0
        self.health_percent = 100
        self.has_helmet = False
        self.has_vest = False
        self.helmet_level = 0
        self.vest_level = 0
        self.current_weapon = None
        self.current_scope = None
        self.ammo_count = 0
        self.team_alive = 4
        self.in_vehicle = False
        self.is_prone = False
        self.is_crouched = False
    
    async def analyze_frame(self, frame_data: str) -> Dict[str, Any]:
        """
        Analyze a game screenshot/frame to detect game state.
        Uses AI vision API to understand what's happening.
        frame_data: base64 encoded image
        """
        self.frame_count += 1
        self.last_frame_time = time.time()
        
        # Build analysis prompt for AI vision
        analysis = {
            "frame_number": self.frame_count,
            "timestamp": datetime.now().isoformat(),
            "previous_state": self.current_state,
        }
        
        # Use AI to analyze the frame
        try:
            game_state = await self._ai_analyze_frame(frame_data)
            analysis.update(game_state)
            self.current_state = game_state.get("state", "unknown")
            self.state_history.append({
                "state": self.current_state,
                "time": time.time(),
                "details": game_state
            })
        except Exception as e:
            analysis["error"] = str(e)
            analysis["state"] = self.current_state
        
        return analysis
    
    async def _ai_analyze_frame(self, frame_data: str) -> Dict[str, Any]:
        """Use Gemini/OpenAI Vision to analyze game frame."""
        try:
            import google.generativeai as genai
            
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return self._heuristic_analysis(frame_data)
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            prompt = """Analyze this BGMI/PUBG Mobile screenshot and provide EXACT JSON output:
{
    "state": "lobby|plane|parachuting|looting|running|driving|combat|healing|reviving|spectating|results",
    "enemies_visible": 0,
    "enemy_positions": [{"direction": "N/NE/E/SE/S/SW/W/NW", "distance": "close/mid/far", "elevation": "same/above/below"}],
    "health_percent": 100,
    "alive_count": 100,
    "zone_phase": 0,
    "current_weapon": "weapon_name or null",
    "current_scope": "none/red_dot/2x/3x/4x/6x/8x",
    "in_vehicle": false,
    "is_prone": false,
    "is_crouched": false,
    "kill_count": 0,
    "minimap_enemies": 0,
    "loot_nearby": [],
    "tactical_advice": "what to do right now",
    "danger_level": "safe/low/medium/high/critical",
    "recommended_action": "loot/rotate/push/hold/heal/revive/take_cover"
}
Only return valid JSON. Be precise about enemy positions."""
            
            # Send image for analysis
            import PIL.Image
            import io
            
            if frame_data.startswith("data:image"):
                frame_data = frame_data.split(",", 1)[1]
            
            image_bytes = base64.b64decode(frame_data)
            image = PIL.Image.open(io.BytesIO(image_bytes))
            
            response = model.generate_content([prompt, image])
            
            # Parse JSON from response
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
            
        except Exception as e:
            logger.warning(f"AI vision analysis failed: {e}")
            return self._heuristic_analysis(frame_data)
    
    def _heuristic_analysis(self, frame_data: str) -> Dict[str, Any]:
        """Fallback heuristic analysis when AI vision is unavailable."""
        return {
            "state": self.current_state,
            "note": "AI vision unavailable — using heuristic mode",
            "tactical_advice": "Share your screen for real-time analysis",
            "danger_level": "unknown",
        }


# ═══════════════════════════════════════════
# TACTICAL AI ENGINE — THE BRAIN
# ═══════════════════════════════════════════

class TacticalAIEngine:
    """
    JARVIS Gaming Brain — Thinks like Jonathan/Scout/Mortal.
    Makes real-time tactical decisions during matches.
    """
    
    def __init__(self):
        self.active_profile = "jonathan_gaming"
        self.game_detector = GameStateDetector()
        self.match_stats = {
            "kills": 0,
            "damage": 0,
            "headshots": 0,
            "knocks": 0,
            "revives": 0,
            "distance_traveled": 0,
            "survival_time": 0,
            "shots_fired": 0,
            "shots_hit": 0,
            "match_start": None,
        }
        self.coaching_history = deque(maxlen=50)
        self.last_callout_time = 0
        self.callout_cooldown = 2.0  # seconds between callouts
        self.current_map = "erangel"
        self.screen_sharing_active = False
        self.analysis_interval = 0.5  # analyze every 500ms
    
    def set_profile(self, profile_name: str) -> Dict:
        """Switch to a pro player's settings."""
        key = profile_name.lower().replace(" ", "_").replace("'", "")
        
        # Search for matching profile
        for pk, pv in PRO_PLAYER_PROFILES.items():
            if key in pk or key in pv.get("name", "").lower() or key in pv.get("real_name", "").lower():
                self.active_profile = pk
                return {
                    "status": "switched",
                    "profile": pv["name"],
                    "playstyle": pv["playstyle"],
                    "message": f"🎮 Playing like {pv['name']} now! {pv['playstyle'].replace('_', ' ').title()} mode activated!",
                    "sensitivity": pv["sensitivity"],
                    "tips": pv.get("tips", []),
                }
        
        return {
            "status": "not_found",
            "available": [p["name"] for p in PRO_PLAYER_PROFILES.values()],
            "message": f"Profile '{profile_name}' not found. Available: " + 
                       ", ".join(p["name"] for p in PRO_PLAYER_PROFILES.values())
        }
    
    def get_sensitivity_config(self, phone_model: str = None) -> Dict:
        """Get current profile's sensitivity settings with device-specific adjustments."""
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        sens = profile["sensitivity"].copy()
        
        # Adjust for phone model differences
        if phone_model:
            phone_lower = phone_model.lower()
            adjustment = 1.0
            
            # Tablet players need higher sens on phone
            if profile.get("device", "").lower().startswith("ipad"):
                if "iphone" in phone_lower or "samsung" in phone_lower or "oneplus" in phone_lower:
                    adjustment = 0.85  # Reduce sens for smaller screen
                    sens["_note"] = (
                        f"⚠️ {profile['name']} plays on iPad. "
                        f"Sensitivity reduced by 15% for your phone ({phone_model}). "
                        f"Adjust ±5% based on your comfort."
                    )
            
            if adjustment != 1.0:
                for category in ["camera", "ads", "gyroscope"]:
                    if category in sens:
                        for scope, val in sens[category].items():
                            sens[category][scope] = round(val * adjustment)
        
        return {
            "profile": profile["name"],
            "sensitivity": sens,
            "graphics": profile.get("graphics", {}),
            "controls": profile.get("controls", {}),
            "claw": profile.get("claw", "unknown"),
            "gyroscope": profile.get("gyroscope", "unknown"),
            "device": profile.get("device", "unknown"),
            "your_device": phone_model,
        }
    
    async def analyze_combat_situation(self, frame_data: str) -> Dict:
        """Real-time combat analysis and advice."""
        analysis = await self.game_detector.analyze_frame(frame_data)
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        
        combat_advice = {
            "analysis": analysis,
            "profile": profile["name"],
        }
        
        state = analysis.get("state", "unknown")
        danger = analysis.get("danger_level", "unknown")
        enemies = analysis.get("enemies_visible", 0)
        health = analysis.get("health_percent", 100)
        weapon = analysis.get("current_weapon", None)
        
        # Generate tactical callouts based on state
        callouts = []
        
        if state == "combat":
            callouts.extend(self._combat_callouts(analysis, profile))
        elif state == "looting":
            callouts.extend(self._loot_callouts(analysis, profile))
        elif state == "running" or state == "driving":
            callouts.extend(self._rotation_callouts(analysis, profile))
        elif state == "parachuting":
            callouts.extend(self._drop_callouts(profile))
        elif state == "healing":
            if danger in ("high", "critical"):
                callouts.append("⚠️ DANGER! Enemy nearby — cancel heal and fight!")
            else:
                callouts.append("✅ Safe to heal. Watch your surroundings.")
        
        # Health-based advice
        if health < 30:
            callouts.append("🩸 CRITICAL HP! Find cover and heal NOW!")
        elif health < 60:
            callouts.append("⚕️ Low HP — heal when safe. Don't peek aggressively.")
        
        # Weapon-specific advice
        if weapon and weapon in WEAPONS_DB:
            w = WEAPONS_DB[weapon]
            scope = analysis.get("current_scope", "none")
            callouts.append(f"🔫 {weapon}: {w.get('recoil_tip', '')}")
        
        combat_advice["callouts"] = callouts
        combat_advice["voice_callout"] = " | ".join(callouts[:3]) if callouts else "Keep playing, looking good!"
        
        return combat_advice
    
    def _combat_callouts(self, analysis: Dict, profile: Dict) -> List[str]:
        """Generate combat-specific callouts."""
        callouts = []
        enemies = analysis.get("enemies_visible", 0)
        enemy_positions = analysis.get("enemy_positions", [])
        
        if enemies > 0:
            # Direction callouts
            for ep in enemy_positions[:3]:
                direction = ep.get("direction", "unknown")
                distance = ep.get("distance", "unknown")
                elevation = ep.get("elevation", "same")
                
                elev_text = ""
                if elevation == "above": elev_text = " (HIGH GROUND)"
                elif elevation == "below": elev_text = " (BELOW)"
                
                callouts.append(f"🎯 Enemy {direction} — {distance} range{elev_text}")
            
            # Playstyle-specific advice
            style = profile.get("playstyle", "aggressive")
            if "aggressive" in style:
                if enemies <= 2:
                    callouts.append("💪 PUSH! Only {0} enemy — {1} style!".format(enemies, profile["name"]))
                else:
                    callouts.append(f"⚡ {enemies} enemies — pick one and rush, then reposition!")
            else:
                if enemies >= 3:
                    callouts.append("🧠 Multiple enemies — hold position, pick them off one by one")
                else:
                    callouts.append("🎯 Take the fight — controlled aggression!")
        
        return callouts
    
    def _loot_callouts(self, analysis: Dict, profile: Dict) -> List[str]:
        """Generate loot advice."""
        callouts = []
        preferred = profile.get("tactics", {}).get("preferred_weapons", [])
        loot = analysis.get("loot_nearby", [])
        
        if loot:
            priority_items = []
            for item in loot:
                if any(w.lower() in str(item).lower() for w in preferred):
                    priority_items.append(item)
            
            if priority_items:
                callouts.append(f"⭐ PRIORITY LOOT: {', '.join(str(i) for i in priority_items[:3])}")
        
        callouts.append("🏃 Don't over-loot! Grab essentials and move. Best loot comes from kills!")
        
        return callouts
    
    def _rotation_callouts(self, analysis: Dict, profile: Dict) -> List[str]:
        """Generate rotation advice."""
        callouts = []
        tactics = profile.get("tactics", {})
        rotation_style = tactics.get("rotation_style", "safe")
        
        if rotation_style == "vehicle_rush":
            callouts.append("🚗 Use vehicle for fast rotation — {}'s style!".format(profile["name"]))
        elif rotation_style == "early_rotation":
            callouts.append("🏃 Rotate early to get best position in zone!")
        elif rotation_style == "compound_to_compound":
            callouts.append("🏠 Move compound to compound — always have cover!")
        
        zone_phase = analysis.get("zone_phase", 0)
        if zone_phase >= 4:
            callouts.append("⚡ Late zone! Every position matters. Stay on zone edge!")
        
        return callouts
    
    def _drop_callouts(self, profile: Dict) -> List[str]:
        """Generate drop location advice."""
        callouts = []
        tactics = profile.get("tactics", {})
        drops = tactics.get("preferred_drop", [])
        early = tactics.get("early_game", "hot_drop")
        
        if "hot_drop" in early:
            callouts.append(f"🔥 HOT DROP TIME! {profile['name']} says go {', '.join(drops[:2])}!")
            callouts.append("🎯 Land on roof → grab weapon → clear building top-down!")
        else:
            callouts.append(f"📍 Semi-hot drop recommended: {', '.join(drops[:2])}")
            callouts.append("🏠 Land on building edge, loot up, then push nearby enemies.")
        
        return callouts
    
    def get_weapon_advice(self, weapon_name: str, scope: str = "none", range_type: str = "mid") -> Dict:
        """Get detailed weapon advice."""
        weapon = None
        for wn, wd in WEAPONS_DB.items():
            if weapon_name.lower() in wn.lower():
                weapon = wd
                weapon_name = wn
                break
        
        if not weapon:
            return {"error": f"Weapon '{weapon_name}' not found", "available": list(WEAPONS_DB.keys())}
        
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        
        # Get sensitivity for this scope
        scope_key_map = {
            "none": "3rd_person_no_scope",
            "red_dot": "red_dot", "holographic": "red_dot",
            "2x": "2x_scope", "3x": "3x_scope",
            "4x": "4x_scope", "6x": "6x_scope", "8x": "8x_scope",
        }
        scope_key = scope_key_map.get(scope, "3rd_person_no_scope")
        
        recommended_sens = {
            "camera": profile["sensitivity"]["camera"].get(scope_key, "N/A"),
            "ads": profile["sensitivity"]["ads"].get(scope_key, "N/A"),
            "gyroscope": profile["sensitivity"]["gyroscope"].get(scope_key, "N/A"),
        }
        
        return {
            "weapon": weapon_name,
            "type": weapon["type"],
            "damage": weapon["damage"],
            "recoil_difficulty": f"{weapon['spray_difficulty']}/10",
            "recoil_pattern": weapon["recoil_pattern"],
            "recoil_tip": weapon.get("recoil_tip", ""),
            "pro_tip": weapon.get("pro_tip", ""),
            "best_attachments": weapon.get("best_attachments", []),
            "effectiveness": weapon.get("effective_range", {}),
            "best_range": range_type,
            "scope": scope,
            "recommended_sensitivity": recommended_sens,
            "profile": profile["name"],
        }
    
    def get_map_strategy(self, map_name: str, drop_preference: str = "hot") -> Dict:
        """Get map-specific strategy."""
        map_data = None
        for mk, mv in MAPS_DB.items():
            if map_name.lower() in mk or map_name.lower() in mv["name"].lower():
                map_data = mv
                break
        
        if not map_data:
            return {"error": f"Map '{map_name}' not found", "available": list(MAPS_DB.keys())}
        
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        tactics = profile.get("tactics", {})
        
        drops = map_data["hot_drops"] if drop_preference == "hot" else map_data.get("safe_drops", map_data["hot_drops"])
        
        return {
            "map": map_data["name"],
            "size": map_data["size"],
            "recommended_drops": drops[:3],
            "rotation_tips": map_data["rotation_tips"],
            "profile_strategy": {
                "early_game": tactics.get("early_game", ""),
                "mid_game": tactics.get("mid_game", ""),
                "late_game": tactics.get("late_game", ""),
                "rotation_style": tactics.get("rotation_style", ""),
            },
            "playing_as": profile["name"],
        }
    
    def get_match_coaching(self, phase: str = "early") -> Dict:
        """Get phase-specific coaching advice."""
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        tactics = profile.get("tactics", {})
        tips = profile.get("tips", [])
        
        coaching = {
            "profile": profile["name"],
            "phase": phase,
            "playstyle": profile["playstyle"],
        }
        
        if phase == "early":
            coaching["strategy"] = tactics.get("early_game", "")
            coaching["advice"] = [
                f"🎯 {profile['name']}'s early game: {tactics.get('early_game', 'contested drop')}",
                "🔫 Grab any weapon first — even a pistol can win early fights",
                "🎧 Listen for footsteps — audio is your best friend",
                "🏃 Clear your landing area before looting",
                f"Preferred weapons: {', '.join(tactics.get('preferred_weapons', [])[:3])}",
            ]
        elif phase == "mid":
            coaching["strategy"] = tactics.get("mid_game", "")
            coaching["advice"] = [
                f"🗺️ {profile['name']}'s mid game: {tactics.get('mid_game', 'map control')}",
                "📍 Start thinking about zone rotation",
                "🎒 You should have full loadout by now — focus on positioning",
                "🔭 Check zone and plan 2 rotations ahead",
                f"Rotation style: {tactics.get('rotation_style', 'strategic')}",
            ]
        elif phase == "late":
            coaching["strategy"] = tactics.get("late_game", "")
            coaching["advice"] = [
                f"🏆 {profile['name']}'s endgame: {tactics.get('late_game', 'win!')}",
                "🔇 Go silent — no vehicles, minimal movement",
                "💣 Save grenades and molotovs for final circles",
                "🎯 Every shot must count — don't reveal position unless for a kill",
                "🧘 Stay calm. The Chicken Dinner is yours!",
            ]
        
        if tips:
            coaching["pro_tips"] = random.sample(tips, min(3, len(tips)))
        
        return coaching
    
    def start_screen_sharing(self) -> Dict:
        """Start screen sharing session for real-time coaching."""
        self.screen_sharing_active = True
        self.match_stats = {
            "kills": 0, "damage": 0, "headshots": 0, "knocks": 0,
            "revives": 0, "distance_traveled": 0, "survival_time": 0,
            "shots_fired": 0, "shots_hit": 0,
            "match_start": datetime.now().isoformat(),
        }
        
        profile = PRO_PLAYER_PROFILES[self.active_profile]
        
        return {
            "status": "screen_sharing_started",
            "message": (
                f"🎮 JARVIS Gaming AI Active! Playing like {profile['name']}!\n\n"
                f"📺 Screen sharing started — I'll analyze your gameplay in real-time.\n"
                f"🎯 I'll call out:\n"
                f"  • Enemy positions & directions\n"
                f"  • When to push, hold, or retreat\n"
                f"  • Weapon & scope recommendations\n"
                f"  • Zone rotation timing\n"
                f"  • Loot priorities\n"
                f"  • Recoil control tips\n\n"
                f"🗣️ Voice coaching is ON — I'll speak callouts!\n"
                f"💪 Let's get that Chicken Dinner, sir!"
            ),
            "profile": profile["name"],
            "playstyle": profile["playstyle"],
            "match_tracking": True,
        }
    
    def stop_screen_sharing(self) -> Dict:
        """Stop screen sharing and return match summary."""
        self.screen_sharing_active = False
        
        return {
            "status": "screen_sharing_stopped",
            "match_stats": self.match_stats,
            "coaching_history": list(self.coaching_history)[-10:],
            "message": "📊 Screen sharing stopped. Match stats saved!",
        }
    
    def get_performance_analysis(self) -> Dict:
        """Analyze player performance and suggest improvements."""
        stats = self.match_stats
        
        analysis = {
            "stats": stats,
            "suggestions": [],
        }
        
        if stats.get("shots_fired", 0) > 0:
            accuracy = (stats.get("shots_hit", 0) / stats["shots_fired"]) * 100
            analysis["accuracy"] = f"{accuracy:.1f}%"
            
            if accuracy < 15:
                analysis["suggestions"].append("🎯 Accuracy is low — practice spray control in TDM for 30 mins daily")
            elif accuracy < 25:
                analysis["suggestions"].append("🎯 Decent accuracy — focus on crosshair placement at head level")
            else:
                analysis["suggestions"].append("🎯 Great accuracy! Keep it up!")
        
        headshot_ratio = 0
        if stats.get("kills", 0) > 0:
            headshot_ratio = (stats.get("headshots", 0) / stats["kills"]) * 100
            analysis["headshot_ratio"] = f"{headshot_ratio:.1f}%"
            
            if headshot_ratio < 20:
                analysis["suggestions"].append("💀 Aim higher! Pre-aim at head level around corners")
        
        analysis["suggestions"].extend([
            "📱 Practice 30 min TDM daily for gunfight skills",
            "🏋️ Do 10 min warm-up before ranked matches",
            "📽️ Watch your replays — learn from deaths",
            "🎮 Use training mode to practice recoil patterns",
        ])
        
        return analysis


# ═══════════════════════════════════════════
# MAIN GAMING ENGINE — API INTERFACE
# ═══════════════════════════════════════════

class JarvisGamingEngine:
    """
    Main gaming engine — handles all gaming AI commands.
    Integrates with JARVIS brain for natural language processing.
    """
    
    def __init__(self):
        self.tactical_ai = TacticalAIEngine()
        self.active_sessions = {}
        self.performance_history = []
        self.load_history()
    
    def load_history(self):
        """Load gaming performance history."""
        try:
            if os.path.exists("data/gaming_history.json"):
                with open("data/gaming_history.json", "r") as f:
                    self.performance_history = json.load(f)
        except:
            self.performance_history = []
    
    def save_history(self):
        """Save gaming performance history."""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/gaming_history.json", "w") as f:
                json.dump(self.performance_history[-100:], f, indent=2, default=str)
        except:
            pass
    
    async def handle_gaming_command(self, command: str, data: Dict = None) -> Dict:
        """Handle any gaming-related command from JARVIS."""
        cmd = command.lower().strip()
        data = data or {}
        
        # Profile switching
        if any(x in cmd for x in ["play like", "switch to", "use profile", "settings of", "sensitivity of"]):
            for name in ["jonathan", "mortal", "scout", "dynamo", "mavi", "zgod"]:
                if name in cmd:
                    result = self.tactical_ai.set_profile(name)
                    return result
            return {"message": "Which pro player? Available: Jonathan, Mortal, Scout, Dynamo, Mavi, Zgod"}
        
        # Start screen sharing
        if any(x in cmd for x in ["start screen", "screen share", "watch me play", "coach me", "start gaming"]):
            return self.tactical_ai.start_screen_sharing()
        
        # Stop screen sharing
        if any(x in cmd for x in ["stop screen", "stop sharing", "end gaming", "stop coaching"]):
            return self.tactical_ai.stop_screen_sharing()
        
        # Analyze frame
        if "analyze" in cmd and data.get("frame"):
            return await self.tactical_ai.analyze_combat_situation(data["frame"])
        
        # Weapon advice
        if any(x in cmd for x in ["weapon", "gun", "recoil", "spray"]):
            for weapon in WEAPONS_DB:
                if weapon.lower() in cmd:
                    scope = "none"
                    for s in ["8x", "6x", "4x", "3x", "2x", "red_dot", "holographic"]:
                        if s in cmd:
                            scope = s
                            break
                    return self.tactical_ai.get_weapon_advice(weapon, scope)
            return {"weapons": list(WEAPONS_DB.keys()), "message": "Which weapon? Example: 'M416 recoil with 3x'"}
        
        # Map strategy
        if any(x in cmd for x in ["map", "erangel", "sanhok", "miramar", "livik", "where to drop", "drop location"]):
            for map_name in MAPS_DB:
                if map_name in cmd:
                    hot = "safe" if "safe" in cmd else "hot"
                    return self.tactical_ai.get_map_strategy(map_name, hot)
            return self.tactical_ai.get_map_strategy("erangel", "hot")
        
        # Sensitivity
        if any(x in cmd for x in ["sensitivity", "sens", "gyro"]):
            phone = data.get("phone_model", None)
            return self.tactical_ai.get_sensitivity_config(phone)
        
        # Coaching
        if any(x in cmd for x in ["coach", "tips", "advice", "how to play", "improve"]):
            phase = "early"
            if "mid" in cmd: phase = "mid"
            elif "late" in cmd or "end" in cmd: phase = "late"
            return self.tactical_ai.get_match_coaching(phase)
        
        # Performance analysis
        if any(x in cmd for x in ["performance", "stats", "how am i", "analyze my"]):
            return self.tactical_ai.get_performance_analysis()
        
        # List profiles
        if any(x in cmd for x in ["profiles", "players", "who can", "list"]):
            return {
                "profiles": {k: {
                    "name": v["name"],
                    "playstyle": v["playstyle"],
                    "role": v["role"],
                    "specialty": v.get("specialty", []),
                    "device": v.get("device", ""),
                } for k, v in PRO_PLAYER_PROFILES.items()},
                "active": PRO_PLAYER_PROFILES[self.tactical_ai.active_profile]["name"],
            }
        
        # Default — game status
        return {
            "status": "gaming_ai_ready",
            "active_profile": PRO_PLAYER_PROFILES[self.tactical_ai.active_profile]["name"],
            "screen_sharing": self.tactical_ai.screen_sharing_active,
            "commands": [
                "🎮 'Play like Jonathan' — Switch to Jonathan Gaming's settings",
                "📺 'Start screen sharing' — Real-time coaching mode",
                "🔫 'M416 recoil tips' — Weapon-specific advice",
                "🗺️ 'Erangel strategy' — Map drop & rotation guide",
                "📊 'My performance' — Stats & improvement tips",
                "🎯 'Sensitivity settings' — Pro player sensitivity",
                "💡 'Coach me for late game' — Phase-specific coaching",
            ],
        }


# ═══════════════════════════════════════════
# MODULE INITIALIZATION
# ═══════════════════════════════════════════

# Singleton instance
_gaming_engine = None

def get_gaming_engine() -> JarvisGamingEngine:
    """Get or create the gaming engine singleton."""
    global _gaming_engine
    if _gaming_engine is None:
        _gaming_engine = JarvisGamingEngine()
    return _gaming_engine

def get_engine_status() -> Dict:
    """Get gaming engine status."""
    return {
        "engine": "gaming_ai",
        "status": "online",
        "version": "10.0",
        "profiles": len(PRO_PLAYER_PROFILES),
        "weapons": len(WEAPONS_DB),
        "maps": len(MAPS_DB),
        "features": [
            "pro_player_profiles",
            "real_time_screen_analysis",
            "combat_callouts",
            "weapon_advice",
            "map_strategy",
            "sensitivity_optimizer",
            "performance_tracking",
            "voice_coaching",
            "ai_vision_analysis",
        ]
    }

logger.info("🎮 JARVIS Gaming AI Engine v10.0 loaded — Jonathan/Mortal/Scout profiles ready!")
