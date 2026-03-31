CONDITIONS = [
    {
        "name": "Diabetes",
        "symptoms": ["frequent urination", "increased thirst", "unexplained weight loss", "fatigue", "blurred vision"],
        "description": "A chronic metabolic disorder characterized by elevated blood glucose levels due to insufficient insulin production or impaired insulin function.",
        "risk_factors": ["obesity", "sedentary lifestyle", "family history", "age over 45", "high blood pressure"],
    },
    {
        "name": "Hypertension",
        "symptoms": ["headache", "shortness of breath", "nosebleeds", "dizziness", "chest pain"],
        "description": "A chronic cardiovascular condition in which arterial blood pressure is persistently elevated, increasing the risk of heart disease and stroke.",
        "risk_factors": ["high sodium diet", "obesity", "smoking", "excessive alcohol consumption", "family history", "stress"],
    },
    {
        "name": "Common Cold",
        "symptoms": ["runny nose", "sore throat", "sneezing", "cough", "mild fever", "congestion"],
        "description": "A mild viral infection of the upper respiratory tract, typically self-limiting and resolving within seven to ten days.",
        "risk_factors": ["weakened immune system", "exposure to infected individuals", "cold weather", "lack of sleep", "stress"],
    },
    {
        "name": "Influenza",
        "symptoms": ["high fever", "body aches", "chills", "fatigue", "cough", "sore throat", "headache"],
        "description": "An acute respiratory illness caused by influenza viruses, often more severe than the common cold and capable of causing serious complications.",
        "risk_factors": ["lack of vaccination", "weakened immune system", "age over 65", "age under 5", "chronic medical conditions"],
    },
    {
        "name": "Migraine",
        "symptoms": ["intense headache", "nausea", "sensitivity to light", "sensitivity to sound", "visual disturbances", "vomiting"],
        "description": "A neurological condition characterized by recurrent episodes of severe, throbbing headache, often accompanied by sensory disturbances and nausea.",
        "risk_factors": ["family history", "hormonal changes", "stress", "sleep irregularity", "certain foods and drinks", "sensory stimuli"],
    },
]


def get_all_conditions() -> list[dict]:
    """Return all conditions in the knowledge base."""
    return list(CONDITIONS)