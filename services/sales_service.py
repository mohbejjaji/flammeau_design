from core.database import SessionLocal
from core.models import Sale, SaleItem, Product, SaleService
from services.shipment_service import get_stock_lots_by_product
from datetime import date


def create_product_sale(customer_name, items, seller_name="Moi", commission=0, 
                        payment_method="Espèces", customer_phone="", customer_email=""):
    """
    Crée une vente de produits en utilisant la méthode FIFO (premier entré, premier sorti)
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
            commission_amount=commission,
            total_revenue=0,
            total_cost=0,
            net_profit=0
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        
        total_revenue = 0
        total_cost = 0
        
        # Pour chaque produit dans la vente
        for item in items:
            product = db.query(Product).get(item["product_id"])
            
            if not product:
                raise Exception(f"Produit ID {item['product_id']} non trouvé")
            
            quantity_needed = item["quantity"]
            
            if quantity_needed > product.stock_quantity:
                raise Exception(f"Stock insuffisant pour {product.name}. Disponible: {product.stock_quantity}")
            
            # Récupérer les lots de stock disponibles (FIFO)
            lots = get_stock_lots_by_product(product.id)
            
            quantity_taken = 0
            item_cost = 0
            
            # Prendre le stock des lots les plus anciens d'abord
            for lot in lots:
                if quantity_needed <= 0:
                    break
                
                qty_from_lot = min(quantity_needed, lot.quantity_remaining)
                
                # Coût de cette partie
                item_cost += qty_from_lot * lot.unit_cost
                
                # Mettre à jour le lot
                lot.quantity_remaining -= qty_from_lot
                
                quantity_needed -= qty_from_lot
                quantity_taken += qty_from_lot
            
            if quantity_needed > 0:
                raise Exception(f"Erreur de calcul de stock pour {product.name}")
            
            # Créer l'item de vente
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_cost_snapshot=item_cost / item["quantity"] if item["quantity"] > 0 else 0
            )
            db.add(sale_item)
            
            # Mettre à jour les totaux
            total_revenue += item["quantity"] * item["unit_price"]
            total_cost += item_cost
            
            # Mettre à jour le stock total du produit
            product.stock_quantity -= item["quantity"]
        
        # Mettre à jour la vente
        sale.total_revenue = total_revenue
        sale.total_cost = total_cost
        sale.net_profit = total_revenue - total_cost - commission
        
        db.commit()
        
        return sale
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_service_sale(customer_name, description, quantity, unit_price, unit_cost,
                        seller_name="Moi", payment_method="Espèces", customer_phone="", customer_email=""):
    """
    Crée une vente de prestation de service
    """
    db = SessionLocal()
    
    try:
        # Calculer les totaux
        total_revenue = unit_price * quantity
        total_cost = unit_cost * quantity
        net_profit = total_revenue - total_cost
        
        # Créer la vente
        sale = Sale(
            date=date.today(),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            payment_method=payment_method,
            seller_name=seller_name,
            commission_amount=0,  # Pas de commission sur les services
            total_revenue=total_revenue,
            total_cost=total_cost,
            net_profit=net_profit
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        
        # Créer l'item de service
        service_item = SaleService(
            sale_id=sale.id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost
        )
        db.add(service_item)
        
        db.commit()
        
        return sale
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_recent_sales(limit=10):
    """Récupère les ventes récentes"""
    db = SessionLocal()
    sales = db.query(Sale).order_by(Sale.date.desc()).limit(limit).all()
    db.close()
    return sales


def get_sales_by_period(start_date, end_date):
    """Récupère les ventes sur une période"""
    db = SessionLocal()
    sales = db.query(Sale).filter(
        Sale.date >= start_date,
        Sale.date <= end_date
    ).order_by(Sale.date.desc()).all()
    db.close()
    return sales