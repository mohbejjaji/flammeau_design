# data/product_catalog.py

# Catalogue des produits Flammeau Design
PRODUCT_CATALOG = {
    "electrique": {
        "name": "Cheminée électrique",
        "subtypes": {
            "encastre": {
                "name": "Encastré",
                "products": [
                    {"ref": "FD 001 ELT ENCASTRE", "name": "FD 001 ELT ENCASTRE"},
                    {"ref": "FD 002 ELT ENCASTRE", "name": "FD 002 ELT ENCASTRE"},
                    {"ref": "FD 004 ELT ENCASTRE", "name": "FD 004 ELT ENCASTRE"}
                ]
            },
            "mural": {
                "name": "Mural",
                "products": [
                    {"ref": "FD 003 ELT MURALE", "name": "FD 003 ELT MURALE"}
                ]
            }
        }
    },
    "bioethanol": {
        "name": "Cheminée bioéthanol",
        "subtypes": {
            "encastre": {
                "name": "Encastré",
                "products": [
                    {"ref": "FD 001 EN", "name": "FD 001 EN"},
                    {"ref": "FD 002 EN", "name": "FD 002 EN"},
                    {"ref": "FD 003 EN", "name": "FD 003 EN"},
                    {"ref": "FD 004 EN", "name": "FD 004 EN"},
                    {"ref": "FD 005 EN", "name": "FD 005 EN"},
                    {"ref": "FD 006 EN", "name": "FD 006 EN"}
                ]
            },
            "mural": {
                "name": "Mural",
                "products": [
                    {"ref": "FD 001 MU", "name": "FD 001 MU"},
                    {"ref": "FD 002 MU", "name": "FD 002 MU"},
                    {"ref": "FD 003 MU", "name": "FD 003 MU"}
                ]
            },
            "mobile": {
                "name": "Mobile",
                "products": [
                    {"ref": "FD 001 MO", "name": "FD 001 MO"},
                    {"ref": "FD 002 MO", "name": "FD 002 MO"},
                    {"ref": "FD 003 MO", "name": "FD 003 MO"},
                    {"ref": "FD 004 MO", "name": "FD 004 MO"},
                    {"ref": "FD 005 MO", "name": "FD 005 MO"},
                    {"ref": "FD 006 MO", "name": "FD 006 MO"},
                    {"ref": "FD 007 MO", "name": "FD 007 MO"},
                    {"ref": "FD 008 MO", "name": "FD 008 MO"},
                    {"ref": "FD 009 MO", "name": "FD 009 MO"}
                ]
            },
            "bruleur": {
                "name": "Brûleur",
                "products": [
                    {"ref": "FD 001 BR", "name": "FD 001 BR"},
                    {"ref": "FD 002 BR", "name": "FD 002 BR"},
                    {"ref": "FD 003 BR", "name": "FD 003 BR"},
                    {"ref": "FD 004 BR", "name": "D 004 BR"},
                    {"ref": "FD 005 BR", "name": "FD 005 BR"},
                    {"ref": "FD 006 BR", "name": "FD 006 BR"}
                ]
            }
        }
    },
    "accessoire": {
        "name": "Accessoires",
        "subtypes": {
            "galets": {
                "name": "Galets",
                "products": [
                    {"ref": "GALETS", "name": "Galets décoratifs"}
                ]
            },
            "buches": {
                "name": "Bûches",
                "products": [
                    {"ref": "BUCHES", "name": "Bûches décoratives"}
                ]
            },
            "ethanol": {
                "name": "Éthanol",
                "products": [
                    {"ref": "ETHANOL", "name": "Bioéthanol 5L"},
                    {"ref": "ETHANOL10", "name": "Bioéthanol 10L"},
                    {"ref": "ETHANOL20", "name": "Bioéthanol 20L"}
                ]
            }
        }
    }
}

def get_categories():
    """Retourne la liste des catégories"""
    return list(PRODUCT_CATALOG.keys())

def get_subtypes(category):
    """Retourne la liste des sous-catégories pour une catégorie donnée"""
    if category in PRODUCT_CATALOG:
        return list(PRODUCT_CATALOG[category]["subtypes"].keys())
    return []

def get_products_by_subtype(category, subtype):
    """Retourne la liste des produits pour une catégorie et sous-catégorie données"""
    if category in PRODUCT_CATALOG and subtype in PRODUCT_CATALOG[category]["subtypes"]:
        return PRODUCT_CATALOG[category]["subtypes"][subtype]["products"]
    return []

def get_all_products_list():
    """Retourne tous les produits du catalogue"""
    all_products = []
    for category, cat_data in PRODUCT_CATALOG.items():
        for subtype, sub_data in cat_data["subtypes"].items():
            for product in sub_data["products"]:
                all_products.append({
                    "category": category,
                    "category_name": cat_data["name"],
                    "subtype": subtype,
                    "subtype_name": sub_data["name"],
                    "ref": product["ref"],
                    "name": product["name"]
                })
    return all_products