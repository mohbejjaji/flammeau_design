
# config.py
TVA_RATE = 0.20  # 20%
COMMISSION_RATE = 0.10  # 20% sur marge produit

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