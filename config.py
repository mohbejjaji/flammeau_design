
# config.py
TVA_RATE = 0.20  # 20%
COMMISSION_RATE = 0.10  # 20% sur marge produit
FIXED_CHARGES = {
    "salaries": 7600,  # Salaires fixes des 2 employés
    "cnss": 1500,       # Cotisations CNSS
    "credits_voitures": 2000,  # Crédits voitures de service
    "total": 11100       # Total des charges fixes mensuelles
}
DEFAULT_CURRENCY = "MAD"
USD_TO_MAD_RATE = 10.0  # 1 USD = 10 MAD (à ajuster selon le taux réel)

# Catégories de produits
PRODUCT_CATEGORIES = {
    "electrique": {
        "name": "Cheminée électrique",
        "subtypes": ["mural", "encastré"]
    },
    "bioethanol": {
        "name": "Cheminée bioéthanol",
        "subtypes": ["mural", "encastré", "mobile", "bruleur"]
    },
    "accessoire": {
        "name": "Accessoire",
        "subtypes": ["galets", "buches", "ethanol"]
    }
}