# Complete NEET UG syllabus data for Physics, Chemistry, and Biology
# Based on NTA NEET 2025 syllabus

NEET_SYLLABUS = {
    'Physics': [
        'Units and Measurement',
        'Motion in straight lines',
        'Motion in planes'
        'Laws of Motion',
        'Work, Energy and Power',
        'Rotational Motion',
        'Gravitation',
        'Properties of Solids',
        'Properties of Liquids'
        'Thermodynamics',
        'Kinetic Theory of Gases',
        'Oscillations and Waves',
        'Electrostatics',
        'Current Electricity',
        'Magnetic Effects of Current and Magnetism',
        'Electromagnetic Induction and Alternating Currents',
        'Electromagnetic Waves',
        'Optics',
        'Dual Nature of Matter and Radiation',
        'Atoms and Nuclei',
        'Electronic Devices',
        'Communication Systems'
    ],
    'Chemistry': [
        'Some Basic Concepts of Chemistry',
        'Atomic Structure',
        'Chemical Bonding and Molecular Structure',
        'Chemical Thermodynamics',
        'Solutions',
        'Equilibrium',
        'Redox Reactions and Electrochemistry',
        'Chemical Kinetics',
        'Classification of Elements and Periodicity in Properties',
        'P-Block Elements',
        'D and F Block Elements',
        'Coordination Compounds',
        'Purification and Characterisation of Organic Compounds',
        'Some Basic Principles of Organic Chemistry',
        'Hydrocarbons',
        'Organic Compounds Containing Halogens',
        'Organic Compounds Containing Oxygen',
        'Organic Compounds Containing Nitrogen',
        'Biomolecules',
        'Principles Related to Practical Chemistry',
        'Environmental Chemistry'
    ],
    'Biology': [
        # Botany
        'Diversity in Living World',
        'Structural Organisation in Plants',
        'Cell Structure and Function',
        'Plant Physiology',
        'Human Physiology',
        'Reproduction',
        'Genetics and Evolution',
        'Biology and Human Welfare',
        'Biotechnology and Its Applications',
        'Ecology and Environment',
        # Zoology
        'Structural Organisation in Animals',
        'Human Reproduction',
        'Reproductive Health',
        'Principles of Inheritance and Variation',
        'Molecular Basis of Inheritance',
        'Evolution',
        'Human Health and Disease',
        'Strategies for Enhancement in Food Production',
        'Microbes in Human Welfare',
        'Organisms and Populations',
        'Ecosystem',
        'Biodiversity and Conservation'
    ]
}

# Helper function to get total chapter count
def get_total_chapters():
    """Returns total number of chapters across all subjects"""
    return sum(len(chapters) for chapters in NEET_SYLLABUS.values())

# Helper function to get chapters by subject
def get_chapters_by_subject(subject):
    """Returns list of chapters for a specific subject"""
    return NEET_SYLLABUS.get(subject, [])
