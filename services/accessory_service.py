from core.database import SessionLocal
from core.models import Sale, SaleItem, Product
from datetime import date


def create_accessory_sale(customer_name, items, seller_name="Moi", 
                          payment_method="Espèces", customer_phone="", customer_email=""):
    """
    Crée une vente d'accessoires (sans gestion FIFO complexe)
    items: liste de dict avec product_id, quantity, unit_price
    """
    db = SessionLocal()
    
    try:
        # Créer la vente
        sale = Sale(
            date=date.today(),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            payment_method=payment_method,
            seller_name=seller_name,
            commission_amount=0,
            total_revenue=0,
            total_cost=0,
            net_profit=0
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        
        total_revenue = 0
        total_cost = 0
        
        # Pour chaque accessoire
        for item in items:
            product = db.query(Product).get(item["product_id"])
            
            if not product:
                raise Exception(f"Accessoire ID {item['product_id']} non trouvé")
            
            if item["quantity"] > product.stock_quantity:
                raise Exception(f"Stock insuffisant pour {product.name}. Disponible: {product.stock_quantity}")
            
            # Coût simplifié (prix d'achat moyen)
            item_cost = product.purchase_price * item["quantity"]
            
            # Créer l'item de vente
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_cost_snapshot=product.purchase_price
            )
            db.add(sale_item)
            
            # Mettre à jour les totaux
            total_revenue += item["quantity"] * item["unit_price"]
            total_cost += item_cost
            
            # Mettre à jour le stock
            product.stock_quantity -= item["quantity"]
        
        # Mettre à jour la vente
        sale.total_revenue = total_revenue
        sale.total_cost = total_cost
        sale.net_profit = total_revenue - total_cost
        
        db.commit()
        
        return sale
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_accessory_catalog():
    """Récupère tous les accessoires"""
    db = SessionLocal()
    accessories = db.query(Product).filter(Product.category == "accessoire").all()
    db.close()
    return accessories


def update_accessory_stock(accessory_id, quantity_change):
    """Met à jour le stock d'un accessoire (entrée/sortie)"""
    db = SessionLocal()
    accessory = db.query(Product).get(accessory_id)
    if accessory:
        accessory.stock_quantity += quantity_change
        db.commit()
    db.close()
    return accessory