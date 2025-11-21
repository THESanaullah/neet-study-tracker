# Complete NEET UG syllabus data for Physics, Chemistry, and Biology
# Based on NTA NEET 2025 syllabus

NEET_SYLLABUS = {
    'Physics': [
        'Basic Maths',
        "Vectors",
        'Units and Measurement',
        'Motion in straight lines',
        'Motion in planes'
        'Laws of Motion',
        'Work, Energy and Power',
        'Centre of mass and System of Particles',
        'Rotational Motion',
        'Gravitation',
        'Properties of Solids',
        'Properties of Liquids'
        'Thermodynamics',
        'Kinetic Theory of Gases',
        'Oscillations',
        'Waves',
        'Electric Charges and current',
        'Electrostatic Potential and Capacitance'
        'Current Electricity',
        'Moving Charges and Magnetism',
        'Matter and Magnetism',
        'Electromagnetic Induction',
        'Alternating Currents',
        'Electromagnetic Waves',
        'Wave Optics',
        'Ray Optics',
        'Dual Nature of Matter and Radiation',
        'Atoms',
        'Nuclei',
        'Semiconductor'
    ],
    'Chemistry': [
        'Some Basic Concepts of Chemistry',
        'Redox Reactions',
        'Thermodynamics',
        'Chemical Equilibrium',
        'Ionic Equilibrium'
        'Solutions',
        'Electrochemistry',
        'Chemical Kinetics',
        'Atomic Structure',
        'Practical Physical Chemistry'
        'Classification of Elements and Periodicity in Properties',
        'Chemical Bonding and Molecular Structure',
        'Coordination Compounds',
        'P-Block Elements',
        'D and F Block Elements',
        'Salt analysis',
        'IUPAC',
        'Isomerism',
        'GOC',
        'Hydrocarbons',
        'Haloalkanes and Haloarenes',
        'Alcohols, Ethers and Phenols',
        'Aldehydes, Ketones and Carboxylic Acids',
        'Amines',
        'Biomolecule',
        'Purification and Analysis of Organic Compounds',
    ],
    'Biology': [
        # Botany
        'Cell Structure and Function',
        'Cell Cycle'
        'The living world',
        'Biological classification',
        'Plant Kingdom',
        'Morphology of Flowering Plants'
        'Anatomy of Flowering Plants',
        'Respiration in Plants',
        'Photosynthesis in Higher Plant',
        'Plant Growth and Development',
        'Sexual Reproduction in Flowering plants',
        'Molecular Basis of Inheritance',
        'Principles of Inheritance and Variation',
        'Microbes in Human Welfare',
        'Organisms and Populations',
        'Ecosystem',
        'Biodiversity and Conservation',
        
        # Zoology
        'Structural Organisation in Animals',
        'Breathing and Exchange of Gases',
        'Body Fluids and Circulation',
        'Excretory Products & their Elimination',
        'Locomotion & Movement',
        'Neural Control & Coordination',
        'Chemical Coordination & Integration',
        'Animal Kingdom',
        'Biomolecules',
        'Human Reproduction',
        'Reproductive Health',
        'Biotechnology: Principles & Processes',
        'Biotechnology and its Applications',
        'Evolution'
        
        
    ]
}

# Helper function to get total chapter count
#def get_total_chapters():
 #   """Returns total number of chapters across all subjects"""
  #  return sum(len(chapters) for chapters in NEET_SYLLABUS.values())

# Helper function to get chapters by subject
#def get_chapters_by_subject(subject):
 #   """Returns list of chapters for a specific subject"""
  #  return NEET_SYLLABUS.get(subject, [])
