# config.py
TVA_RATE = 0.20  # 20%
COMMISSION_RATE = 0.20  # 20% sur marge produit
FIXED_CHARGES = {
    "salaries": 10000,  # Salaires fixes des 2 employés
    "cnss": 2500,       # Cotisations CNSS
    "credits_voitures": 2500,  # Crédits voitures de service
    "total": 15000       # Total des charges fixes mensuelles
}
DEFAULT_CURRENCY = "MAD"

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