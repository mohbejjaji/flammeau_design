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

def create_service_sale_with_deposit(
    customer_name, 
    description, 
    quantity, 
    unit_price, 
    unit_cost,
    deposit_amount=0,
    deposit_payment_method="Espèces",
    seller_name="Moi",
    customer_phone="", 
    customer_email=""
):
    """Crée une vente de prestation avec acompte"""
    db = SessionLocal()
    
    try:
        # Calculer les totaux
        total_revenue = unit_price * quantity
        total_cost = unit_cost * quantity
        
        # Déterminer le statut de paiement
        if deposit_amount == 0:
            payment_status = "en_attente"
            net_profit = 0  # Pas de profit tant que non payé
        elif deposit_amount >= total_revenue:
            payment_status = "payé"
            net_profit = total_revenue - total_cost
        else:
            payment_status = "acompte"
            net_profit = 0  # Profit comptabilisé au paiement final
        
        # Créer la vente (même si pas entièrement payée)
        sale = Sale(
            date=date.today(),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            payment_method=deposit_payment_method if deposit_amount > 0 else "En attente",
            seller_name=seller_name,
            commission_amount=0,
            total_revenue=deposit_amount,  # Seul l'acompte est comptabilisé
            total_cost=0,  # Coût comptabilisé au paiement final
            net_profit=0
        )
        db.add(sale)
        db.commit()
        db.refresh(sale)
        
        # Créer l'item de service avec infos d'acompte
        service_item = SaleService(
            sale_id=sale.id,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            deposit_amount=deposit_amount,
            deposit_date=date.today() if deposit_amount > 0 else None,
            deposit_payment_method=deposit_payment_method if deposit_amount > 0 else None,
            balance_amount=total_revenue - deposit_amount,
            payment_status=payment_status
        )
        db.add(service_item)
        
        db.commit()
        
        return {
            'sale_id': sale.id,
            'service_id': service_item.id,
            'total': total_revenue,
            'deposit': deposit_amount,
            'remaining': total_revenue - deposit_amount,
            'status': payment_status
        }
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def pay_service_balance(service_id, balance_amount, payment_method):
    """Enregistre le paiement du solde d'une prestation"""
    db = SessionLocal()
    
    try:
        # Récupérer l'item de service
        service_item = db.query(SaleService).filter(SaleService.id == service_id).first()
        
        if not service_item:
            raise Exception("Prestation non trouvée")
        
        # Mettre à jour l'item
        service_item.balance_amount = balance_amount
        service_item.balance_date = date.today()
        service_item.balance_payment_method = payment_method
        service_item.payment_status = "payé"
        
        # Mettre à jour la vente associée
        sale = db.query(Sale).filter(Sale.id == service_item.sale_id).first()
        if sale:
            total = service_item.total_amount
            sale.total_revenue = total  # Maintenant le total complet
            sale.total_cost = service_item.unit_cost * service_item.quantity
            sale.net_profit = total - sale.total_cost
            sale.payment_method = payment_method
            sale.payment_status = "payé"
        
        db.commit()
        
        return True
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_pending_service_payments():
    """Récupère toutes les prestations avec paiement en attente"""
    db = SessionLocal()
    
    services = db.query(SaleService).filter(
        SaleService.payment_status.in_(["en_attente", "acompte"])
    ).order_by(SaleService.created_at.desc()).all()
    
    result = []
    for s in services:
        sale = db.query(Sale).filter(Sale.id == s.sale_id).first()
        result.append({
            'id': s.id,
            'sale_id': s.sale_id,
            'date': s.created_at.date(),
            'customer': sale.customer_name if sale else "Inconnu",
            'description': s.description,
            'total': s.total_amount,
            'deposit': s.deposit_amount,
            'remaining': s.remaining_amount,
            'status': s.payment_status
        })
    
    db.close()
    return result