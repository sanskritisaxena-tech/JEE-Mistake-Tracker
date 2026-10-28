"""Constants for subjects, error types and chapter lists."""

# Fixed subjects
SUBJECTS = ["Physics", "Chemistry", "Mathematics"]

# Fixed error types stored exactly as these strings
ERROR_TYPES = [
    "Concept gap",
    "Calculation slip",
    "Misread question",
    "Formula not remembered",
    "Time pressure",
    "Guessed",
]

# Full JEE Main chapter list per subject using standard NTA syllabus names
CHAPTERS = {
    "Physics": [
        "Physics and Measurement",
        "Kinematics",
        "Laws of Motion",
        "Work, Energy and Power",
        "Rotational Motion",
        "Gravitation",
        "Properties of Solids and Liquids",
        "Thermodynamics",
        "Kinetic Theory of Gases",
        "Oscillations and Waves",
        "Electrostatics",
        "Current Electricity",
        "Magnetic Effects of Current and Magnetism",
        "Electromagnetic Induction and Alternating Currents",
        "Electromagnetic Waves",
        "Optics",
        "Dual Nature of Matter and Radiation",
        "Atoms and Nuclei",
        "Electronic Devices",
        "Experimental Skills",
    ],
    "Chemistry": [
        "Some Basic Concepts of Chemistry",
        "States of Matter",
        "Atomic Structure",
        "Chemical Bonding and Molecular Structure",
        "Chemical Thermodynamics",
        "Solutions",
        "Equilibrium",
        "Redox Reactions and Electrochemistry",
        "Chemical Kinetics",
        "Surface Chemistry",
        "Classification of Elements and Periodicity",
        "General Principles and Processes of Isolation of Metals",
        "Hydrogen",
        "s-Block Elements",
        "p-Block Elements",
        "d- and f-Block Elements",
        "Coordination Compounds",
        "Environmental Chemistry",
        "Purification and Characterisation of Organic Compounds",
        "Hydrocarbons",
        "Organic Compounds Containing Halogens",
        "Organic Compounds Containing Oxygen",
        "Organic Compounds Containing Nitrogen",
        "Biomolecules",
        "Principles Related to Practical Chemistry",
    ],
    "Mathematics": [
        "Sets, Relations and Functions",
        "Complex Numbers and Quadratic Equations",
        "Matrices and Determinants",
        "Permutations and Combinations",
        "Mathematical Induction",
        "Binomial Theorem",
        "Sequences and Series",
        "Limit, Continuity and Differentiability",
        "Integral Calculus",
        "Differential Equations",
        "Coordinate Geometry",
        "Three Dimensional Geometry",
        "Vector Algebra",
        "Statistics and Probability",
        "Trigonometry",
        "Mathematical Reasoning",
    ],
}

# All chapters flat list for validation helpers
ALL_CHAPTERS = [c for chapters in CHAPTERS.values() for c in chapters]


def is_valid_subject(subject):
    """Return True if subject is in the allowed list."""
    return subject in SUBJECTS


def is_valid_error_type(error_type):
    """Return True if error_type is in the allowed list."""
    return error_type in ERROR_TYPES


def is_valid_chapter_for_subject(subject, chapter):
    """Return True if chapter belongs to the given subject."""
    if subject not in CHAPTERS:
        return False
    return chapter in CHAPTERS[subject]
