from core.models import Product
from core.repositories import Repository
from data.product_catalog import PRODUCT_CATALOG

product_repo = Repository(Product)

def create_product(name, reference, category, subtype, selling_price, 
                   purchase_price=0, default_margin=30, description="", initial_stock=0):
    """Crée un nouveau produit"""
    product = Product(
        reference=reference,
        name=name,
        category=category,
        subtype=subtype,
        selling_price=selling_price,
        purchase_price=purchase_price,
        default_margin=default_margin,
        stock_quantity=initial_stock,
        description=description
    )
    return product_repo.add(product)


def get_products():
    """Récupère tous les produits"""
    return product_repo.get_all()


def get_product_by_id(product_id):
    """Récupère un produit par son ID"""
    return product_repo.get_by_id(product_id)


def update_product(product_id, **kwargs):
    """
    Met à jour un produit existant
    kwargs: champs à mettre à jour (name, selling_price, purchase_price, etc.)
    """
    product = product_repo.get_by_id(product_id)
    if product:
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        product_repo.db.commit()
        product_repo.db.refresh(product)
    return product


def update_product_stock(product_id, new_quantity):
    """Met à jour le stock d'un produit"""
    return update_product(product_id, stock_quantity=new_quantity)


def update_product_price(product_id, new_price):
    """Met à jour le prix de vente d'un produit"""
    return update_product(product_id, selling_price=new_price)


def get_products_by_category(category):
    """Récupère les produits d'une catégorie"""
    products = get_products()
    return [p for p in products if p.category == category]


def get_low_stock_products(threshold=5):
    """Récupère les produits avec stock faible"""
    products = get_products()
    return [p for p in products if 0 < p.stock_quantity < threshold]


def get_out_of_stock_products():
    """Récupère les produits en rupture"""
    products = get_products()
    return [p for p in products if p.stock_quantity == 0]


def delete_product(product_id):
    """Supprime un produit"""
    product = product_repo.get_by_id(product_id)
    if product:
        product_repo.delete(product)
        return True
    return False

def update_product_margin(product_id, new_margin):
    """Met à jour la marge par défaut d'un produit"""
    return update_product(product_id, default_margin=new_margin)