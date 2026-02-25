from core.database import SessionLocal
from core.models import Product, StockLot, Shipment, SaleItem, ShipmentItem, Sale
from sqlalchemy import func
from datetime import datetime, timedelta  # ✅ Import manquant


def get_current_stock():
    """Récupère l'état actuel du stock pour tous les produits"""
    db = SessionLocal()
    products = db.query(Product).all()
    
    stock_data = []
    for product in products:
        # Calculer la valeur totale du stock
        total_value = sum(lot.unit_cost * lot.quantity_remaining for lot in product.stock_lots)
        
        # Calculer le coût moyen pondéré
        if product.stock_quantity > 0 and product.stock_lots:
            avg_cost = total_value / product.stock_quantity
        else:
            avg_cost = 0
        
        stock_data.append({
            'id': product.id,
            'reference': product.reference,
            'name': product.name,
            'category': product.category,
            'subtype': product.subtype,
            'quantity': product.stock_quantity,
            'purchase_price': product.purchase_price,
            'avg_cost': avg_cost,
            'selling_price': product.selling_price,
            'stock_value': total_value,
            'potential_revenue': product.selling_price * product.stock_quantity,
            'potential_profit': (product.selling_price * product.stock_quantity) - total_value
        })
    
    db.close()
    return stock_data


def get_stock_by_category(category):
    """Récupère le stock pour une catégorie spécifique"""
    all_stock = get_current_stock()
    return [s for s in all_stock if s['category'] == category]


def get_low_stock_products(threshold=5):
    """Récupère les produits avec stock faible"""
    db = SessionLocal()
    products = db.query(Product).filter(Product.stock_quantity < threshold).all()
    db.close()
    return products


def get_out_of_stock_products():
    """Récupère les produits en rupture"""
    db = SessionLocal()
    products = db.query(Product).filter(Product.stock_quantity == 0).all()
    db.close()
    return products


def get_stock_movements(product_id=None, days=30):
    """Récupère l'historique des mouvements de stock"""
    db = SessionLocal()
    
    # Date limite
    since_date = datetime.now() - timedelta(days=days)  # ✅ datetime est maintenant défini
    
    if product_id:
        # Mouvements pour un produit spécifique
        # Entrées (arrivages)
        entries = db.query(ShipmentItem).join(Shipment).filter(
            ShipmentItem.product_id == product_id,
            Shipment.date >= since_date.date()  # ✅ Conversion en date
        ).all()
        
        # Sorties (ventes)
        exits = db.query(SaleItem).join(Sale).filter(
            SaleItem.product_id == product_id,
            Sale.date >= since_date.date()  # ✅ Conversion en date
        ).all()
        
        movements = []
        for entry in entries:
            movements.append({
                'date': entry.shipment.date,
                'type': 'ENTRÉE',
                'quantity': entry.quantity,
                'reference': f"Arrivage #{entry.shipment.id}",
                'unit_price': entry.unit_purchase_price
            })
        
        for exit_item in exits:
            movements.append({
                'date': exit_item.sale.date,
                'type': 'SORTIE',
                'quantity': -exit_item.quantity,
                'reference': f"Vente #{exit_item.sale.id} - {exit_item.sale.customer_name}",
                'unit_price': exit_item.unit_price
            })
        
        # Trier par date
        movements.sort(key=lambda x: x['date'], reverse=True)
        db.close()
        return movements
        
    else:
        # Tous les mouvements (version simplifiée)
        all_movements = []
        
        # Derniers arrivages
        recent_shipments = db.query(ShipmentItem).join(Shipment).filter(
            Shipment.date >= since_date.date()
        ).limit(50).all()
        
        for entry in recent_shipments:
            all_movements.append({
                'date': entry.shipment.date,
                'type': 'ENTRÉE',
                'product': entry.product.name if entry.product else "N/A",
                'quantity': entry.quantity,
                'reference': f"Arrivage #{entry.shipment.id}",
                'unit_price': entry.unit_purchase_price
            })
        
        # Dernières ventes
        recent_sales = db.query(SaleItem).join(Sale).filter(
            Sale.date >= since_date.date()
        ).limit(50).all()
        
        for exit_item in recent_sales:
            all_movements.append({
                'date': exit_item.sale.date,
                'type': 'SORTIE',
                'product': exit_item.product.name if exit_item.product else "N/A",
                'quantity': -exit_item.quantity,
                'reference': f"Vente #{exit_item.sale.id} - {exit_item.sale.customer_name}",
                'unit_price': exit_item.unit_price
            })
        
        # Trier par date
        all_movements.sort(key=lambda x: x['date'], reverse=True)
        db.close()
        return all_movements[:100]  # Limiter à 100 mouvements


def get_stock_value_history(days=90):
    """Historique de la valeur du stock"""
    db = SessionLocal()
    
    # Cette fonction nécessite un suivi historique plus complexe
    # Version simplifiée: valeur actuelle uniquement
    total_value = db.query(
        func.sum(StockLot.quantity_remaining * StockLot.unit_cost)
    ).scalar() or 0
    
    db.close()
    return total_value


def transfer_stock(product_id, from_lot_id, to_lot_id, quantity):
    """Transfère du stock entre lots (utile si on déplace des produits)"""
    db = SessionLocal()
    
    from_lot = db.query(StockLot).get(from_lot_id)
    to_lot = db.query(StockLot).get(to_lot_id)
    
    if not from_lot or not to_lot:
        db.close()
        raise Exception("Lots non trouvés")
    
    if from_lot.quantity_remaining < quantity:
        db.close()
        raise Exception("Quantité insuffisante")
    
    from_lot.quantity_remaining -= quantity
    to_lot.quantity_remaining += quantity
    
    db.commit()
    db.close()
    
    return True


def get_stock_alerts():
    """Récupère toutes les alertes stock"""
    low_stock = get_low_stock_products()
    out_of_stock = get_out_of_stock_products()
    
    alerts = []
    for p in low_stock:
        alerts.append({
            'type': 'warning',
            'product': p.name,
            'message': f"Stock faible: {p.stock_quantity} unités restantes",
            'threshold': 5
        })
    
    for p in out_of_stock:
        alerts.append({
            'type': 'danger',
            'product': p.name,
            'message': f"Rupture de stock",
            'threshold': 0
        })
    
    return alerts