from core.database import SessionLocal
from core.models import Product
from config import TVA_RATE


def calculate_product_price(product_id, margin_percent=None):
    """
    Calcule le prix de vente suggéré pour un produit
    Si margin_percent n'est pas fourni, utilise la marge par défaut du produit
    """
    db = SessionLocal()
    product = db.query(Product).get(product_id)
    
    if not product:
        db.close()
        return None
    
    # Utiliser la marge spécifiée ou la marge par défaut
    margin = margin_percent if margin_percent is not None else product.default_margin
    
    # Coût moyen pondéré
    avg_cost = product.average_cost
    
    if avg_cost == 0:
        # Pas de stock, utiliser le prix d'achat comme base
        avg_cost = product.purchase_price
    
    # Calculs
    price_ht = avg_cost * (1 + margin / 100)
    price_ttc = price_ht * (1 + TVA_RATE)
    
    db.close()
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "avg_cost": avg_cost,
        "margin_percent": margin,
        "price_ht": price_ht,
        "price_ttc": price_ttc,
        "current_price": product.selling_price
    }


def calculate_price_from_cost(cost, margin_percent, tva_included=True):
    """
    Calcule un prix à partir du coût et de la marge
    """
    price_ht = cost * (1 + margin_percent / 100)
    
    if tva_included:
        return price_ht * (1 + TVA_RATE)
    else:
        return price_ht


def get_margin_from_price(cost, selling_price):
    """
    Calcule la marge réalisée à partir du coût et du prix de vente
    """
    if cost <= 0:
        return 0
    return ((selling_price - cost) / cost) * 100


def suggest_prices_for_category(category, target_margin=30):
    """
    Suggère des prix pour tous les produits d'une catégorie
    """
    db = SessionLocal()
    products = db.query(Product).filter(Product.category == category).all()
    
    suggestions = []
    for product in products:
        if product.average_cost > 0:
            suggested = calculate_product_price(product.id, target_margin)
            if suggested:
                suggestions.append(suggested)
    
    db.close()
    return suggestions