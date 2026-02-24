from core.database import SessionLocal
from core.models import Shipment, StockLot, Product, ShipmentItem
from datetime import date
from sqlalchemy import func


def create_shipment(items, transport_total, customs_total=0, note=""):
    """
    Crée un nouvel arrivage et met à jour les stocks
    items: liste de dict avec product_id, quantity, unit_purchase_price
    """
    db = SessionLocal()
    
    try:
        # 1. Créer l'arrivage
        shipment = Shipment(
            date=date.today(),
            transport_cost_total=transport_total,
            customs_cost_total=customs_total,
            note=note
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        
        # 2. Calculer la valeur totale de l'arrivage pour répartir les frais
        total_purchase_value = sum(
            item["unit_purchase_price"] * item["quantity"] 
            for item in items
        )
        
        # 3. Pour chaque produit dans l'arrivage
        for item in items:
            product = db.query(Product).get(item["product_id"])
            
            if not product:
                raise Exception(f"Produit ID {item['product_id']} non trouvé")
            
            # Calculer la part des frais pour ce produit
            purchase_value = item["unit_purchase_price"] * item["quantity"]
            
            # Répartition proportionnelle des frais de transport et douane
            if total_purchase_value > 0:
                transport_share = (purchase_value / total_purchase_value) * transport_total
                customs_share = (purchase_value / total_purchase_value) * customs_total
            else:
                transport_share = 0
                customs_share = 0
            
            # Prix de revient unitaire (achat + transport + douane)
            unit_real_cost = (
                item["unit_purchase_price"]
                + (transport_share / item["quantity"])
                + (customs_share / item["quantity"])
            )
            
            # 4. Créer le lot de stock (traçabilité)
            stock_lot = StockLot(
                product_id=product.id,
                shipment_id=shipment.id,  # Lien avec l'arrivage
                quantity_remaining=item["quantity"],
                unit_cost=unit_real_cost
            )
            db.add(stock_lot)
            
            # 5. Créer l'item d'arrivage pour l'historique
            shipment_item = ShipmentItem(
                shipment_id=shipment.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_purchase_price=item["unit_purchase_price"],
                allocated_transport_cost=transport_share,
                allocated_customs_cost=customs_share
            )
            db.add(shipment_item)
            
            # 6. Mettre à jour le stock total du produit
            product.stock_quantity += item["quantity"]
        
        db.commit()
        
        return shipment
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_shipment_history(limit=50):
    """Récupère l'historique des arrivages"""
    db = SessionLocal()
    shipments = db.query(Shipment).order_by(Shipment.date.desc()).limit(limit).all()
    db.close()
    return shipments


def get_shipment_details(shipment_id):
    """Récupère les détails d'un arrivage spécifique"""
    db = SessionLocal()
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    
    if shipment:
        # Récupérer les items
        items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment_id).all()
        
        # Récupérer les lots de stock liés
        stock_lots = db.query(StockLot).filter(StockLot.shipment_id == shipment_id).all()
        
        result = {
            "shipment": shipment,
            "items": items,
            "stock_lots": stock_lots
        }
    else:
        result = None
    
    db.close()
    return result


def get_stock_lots_by_product(product_id):
    """Récupère tous les lots de stock pour un produit (pour la méthode FIFO)"""
    db = SessionLocal()
    lots = db.query(StockLot).filter(
        StockLot.product_id == product_id,
        StockLot.quantity_remaining > 0
    ).order_by(StockLot.id.asc()).all()  # FIFO: plus ancien d'abord
    db.close()
    return lots


def get_shipment_stats():
    """Statistiques sur les arrivages"""
    db = SessionLocal()
    
    total_shipments = db.query(Shipment).count()
    total_spent = db.query(
        func.sum(ShipmentItem.quantity * ShipmentItem.unit_purchase_price)
    ).scalar() or 0
    
    total_transport = db.query(func.sum(Shipment.transport_cost_total)).scalar() or 0
    total_customs = db.query(func.sum(Shipment.customs_cost_total)).scalar() or 0
    
    # Dernier arrivage
    last_shipment = db.query(Shipment).order_by(Shipment.date.desc()).first()
    
    db.close()
    
    return {
        "total_shipments": total_shipments,
        "total_spent": total_spent,
        "total_transport": total_transport,
        "total_customs": total_customs,
        "last_shipment_date": last_shipment.date if last_shipment else None
    }