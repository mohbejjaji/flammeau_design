from core.database import SessionLocal
from core.models import Shipment, StockLot, Product, ShipmentItem
from datetime import date
from data.product_catalog import get_product_by_ref
from config import USD_TO_MAD_RATE


def process_arrival(arrival_data):
    """
    Traite un arrivage et crée automatiquement les produits
    arrival_data: {
        'date': date,
        'transport_cost_usd': float,  # Frais en USD
        'customs_cost_mad': float,    # Douane en MAD
        'shipping_cost_usd': float,   # Fret en USD
        'note': str,
        'items': [
            {
                'reference': 'FD 001 ELT ENCASTRE',
                'quantity': 10,
                'purchase_price_usd': 250  # Prix en USD
            }
        ]
    }
    """
    db = SessionLocal()
    
    try:
        # Convertir tous les coûts en MAD
        transport_cost_mad = arrival_data['transport_cost_usd'] * USD_TO_MAD_RATE
        shipping_cost_mad = arrival_data.get('shipping_cost_usd', 0) * USD_TO_MAD_RATE
        customs_cost_mad = arrival_data.get('customs_cost_mad', 0)
        
        # 1. Créer l'arrivage
        shipment = Shipment(
            date=arrival_data['date'],
            transport_cost_total=transport_cost_mad,
            customs_cost_total=customs_cost_mad,
            shipping_cost_total=shipping_cost_mad,
            note=arrival_data.get('note', '')
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        
        # 2. Préparer les items avec prix convertis en MAD
        items_mad = []
        for item in arrival_data['items']:
            items_mad.append({
                'reference': item['reference'],
                'quantity': item['quantity'],
                'purchase_price_mad': item['purchase_price_usd'] * USD_TO_MAD_RATE,
                'purchase_price_usd': item['purchase_price_usd']
            })
        
        # 3. Calculer la valeur totale pour répartir les frais
        total_purchase_value_mad = sum(
            item['purchase_price_mad'] * item['quantity'] 
            for item in items_mad
        )
        
        products_created = 0
        
        # 4. Pour chaque article reçu
        for item in items_mad:
            # Vérifier si le produit existe déjà
            product = db.query(Product).filter(
                Product.reference == item['reference']
            ).first()
            
            # Si le produit n'existe pas, le créer automatiquement
            if not product:
                product_info = get_product_by_ref(item['reference'])
                
                if not product_info:
                    raise Exception(f"Référence inconnue: {item['reference']}")
                
                product = Product(
                    reference=item['reference'],
                    name=product_info['name'],
                    category=product_info['category'],
                    subtype=product_info['subtype'],
                    selling_price=0,
                    purchase_price=item['purchase_price_mad'],  # Stocké en MAD
                    default_margin=30,
                    stock_quantity=0,
                    description=f"Importé de Chine - {arrival_data['date']}"
                )
                db.add(product)
                db.commit()
                db.refresh(product)
                products_created += 1
            
            # Calculer la part des frais pour ce produit
            purchase_value_mad = item['purchase_price_mad'] * item['quantity']
            
            if total_purchase_value_mad > 0:
                transport_share = (purchase_value_mad / total_purchase_value_mad) * transport_cost_mad
                customs_share = (purchase_value_mad / total_purchase_value_mad) * customs_cost_mad
                shipping_share = (purchase_value_mad / total_purchase_value_mad) * shipping_cost_mad
            else:
                transport_share = 0
                customs_share = 0
                shipping_share = 0
            
            # Prix de revient unitaire en MAD (achat + tous les frais)
            unit_real_cost = (
                item['purchase_price_mad']
                + (transport_share / item['quantity'])
                + (customs_share / item['quantity'])
                + (shipping_share / item['quantity'])
            )
            
            # Créer le lot de stock
            stock_lot = StockLot(
                product_id=product.id,
                shipment_id=shipment.id,
                quantity_remaining=item['quantity'],
                unit_cost=unit_real_cost
            )
            db.add(stock_lot)
            
            # Créer l'item d'arrivage
            shipment_item = ShipmentItem(
                shipment_id=shipment.id,
                product_id=product.id,
                quantity=item['quantity'],
                unit_purchase_price=item['purchase_price_mad'],
                allocated_transport_cost=transport_share,
                allocated_customs_cost=customs_share
            )
            db.add(shipment_item)
            
            # Mettre à jour le stock
            product.stock_quantity += item['quantity']
            
            # Suggérer un prix de vente si pas encore défini
            if product.selling_price == 0:
                suggested_price = unit_real_cost * 1.3 * 1.2  # Marge 30% + TVA 20%
                product.selling_price = round(suggested_price, -2)  # Arrondi à la centaine
        
        db.commit()
        
        # Calculer les totaux pour le retour
        total_usd = sum(item['purchase_price_usd'] * item['quantity'] for item in arrival_data['items'])
        total_mad = sum(item['purchase_price_mad'] * item['quantity'] for item in items_mad)
        
        return {
            'shipment_id': shipment.id,
            'products_created': products_created,
            'total_usd': total_usd,
            'total_mad': total_mad,
            'total_frais_mad': transport_cost_mad + customs_cost_mad + shipping_cost_mad,
            'total_cost_mad': total_mad + transport_cost_mad + customs_cost_mad + shipping_cost_mad
        }
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_all_shipments():
    """Récupère tous les arrivages"""
    db = SessionLocal()
    try:
        shipments = db.query(Shipment).order_by(Shipment.date.desc()).all()
        result = []
        for s in shipments:
            result.append({
                'id': s.id,
                'date': s.date,
                'transport_cost_total': s.transport_cost_total,
                'customs_cost_total': s.customs_cost_total,
                'shipping_cost_total': s.shipping_cost_total,
                'note': s.note,
                'created_at': s.created_at
            })
        return result
    finally:
        db.close()


def get_shipment_details(shipment_id):
    """Récupère le détail d'un arrivage et le stock restant de ses lots"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return None
        
        items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment_id).all()
        items_data = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            # Retrouver le lot de stock correspondant
            stock_lot = db.query(StockLot).filter(
                StockLot.shipment_id == shipment_id,
                StockLot.product_id == item.product_id
            ).first()
            
            items_data.append({
                'product_id': item.product_id,
                'reference': product.reference if product else "Inconnu",
                'name': product.name if product else "Inconnu",
                'quantity': item.quantity,
                'unit_purchase_price_mad': item.unit_purchase_price,
                'unit_purchase_price_usd': item.unit_purchase_price / USD_TO_MAD_RATE,
                'allocated_transport_cost': item.allocated_transport_cost or 0.0,
                'allocated_customs_cost': item.allocated_customs_cost or 0.0,
                'qty_remaining': stock_lot.quantity_remaining if stock_lot else 0
            })
            
        return {
            'shipment': {
                'id': shipment.id,
                'date': shipment.date,
                'transport_cost_total': shipment.transport_cost_total,
                'customs_cost_total': shipment.customs_cost_total,
                'shipping_cost_total': shipment.shipping_cost_total,
                'note': shipment.note,
            },
            'items': items_data
        }
    finally:
        db.close()


def recalculate_shipment_costs(db, shipment):
    """Recalcule et réalloue les frais proportionnellement à la valeur d'achat"""
    items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment.id).all()
    
    # Valeur d'achat totale en MAD
    total_purchase_value_mad = sum(item.unit_purchase_price * item.quantity for item in items)
    
    for item in items:
        purchase_value_mad = item.unit_purchase_price * item.quantity
        
        if total_purchase_value_mad > 0:
            transport_share = (purchase_value_mad / total_purchase_value_mad) * (shipment.transport_cost_total or 0)
            customs_share = (purchase_value_mad / total_purchase_value_mad) * (shipment.customs_cost_total or 0)
            shipping_share = (purchase_value_mad / total_purchase_value_mad) * (shipment.shipping_cost_total or 0)
        else:
            transport_share = 0
            customs_share = 0
            shipping_share = 0
            
        # Mettre à jour l'item d'arrivage
        item.allocated_transport_cost = transport_share
        item.allocated_customs_cost = customs_share
        
        # Mettre à jour le lot de stock
        stock_lot = db.query(StockLot).filter(
            StockLot.shipment_id == shipment.id,
            StockLot.product_id == item.product_id
        ).first()
        
        if stock_lot:
            unit_real_cost = (
                item.unit_purchase_price
                + (transport_share / item.quantity)
                + (customs_share / item.quantity)
                + (shipping_share / item.quantity)
            )
            stock_lot.unit_cost = unit_real_cost


def update_shipment_metadata(shipment_id, date_val, transport_cost_usd, shipping_cost_usd, customs_cost_mad, note_val):
    """Met à jour les métadonnées globales de l'arrivage et recalcule les coûts"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise Exception("Arrivage introuvable")
            
        shipment.date = date_val
        shipment.transport_cost_total = transport_cost_usd * USD_TO_MAD_RATE
        shipment.shipping_cost_total = shipping_cost_usd * USD_TO_MAD_RATE
        shipment.customs_cost_total = customs_cost_mad
        shipment.note = note_val
        
        recalculate_shipment_costs(db, shipment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def add_item_to_existing_shipment(shipment_id, reference, quantity, purchase_price_usd):
    """Ajoute un produit à un arrivage enregistré"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise Exception("Arrivage introuvable")
            
        # Trouver ou créer le produit
        product = db.query(Product).filter(Product.reference == reference).first()
        if not product:
            product_info = get_product_by_ref(reference)
            if not product_info:
                raise Exception(f"Référence inconnue: {reference}")
                
            product = Product(
                reference=reference,
                name=product_info['name'],
                category=product_info['category'],
                subtype=product_info['subtype'],
                selling_price=0,
                purchase_price=purchase_price_usd * USD_TO_MAD_RATE,
                default_margin=30,
                stock_quantity=0,
                description=f"Importé de Chine - {shipment.date}"
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            
        # Rechercher s'il y a déjà cet item dans le shipment
        shipment_item = db.query(ShipmentItem).filter(
            ShipmentItem.shipment_id == shipment_id,
            ShipmentItem.product_id == product.id
        ).first()
        
        stock_lot = db.query(StockLot).filter(
            StockLot.shipment_id == shipment_id,
            StockLot.product_id == product.id
        ).first()
        
        purchase_price_mad = purchase_price_usd * USD_TO_MAD_RATE
        
        if shipment_item:
            shipment_item.quantity += quantity
            shipment_item.unit_purchase_price = purchase_price_mad
            if stock_lot:
                stock_lot.quantity_remaining += quantity
            else:
                stock_lot = StockLot(
                    product_id=product.id,
                    shipment_id=shipment.id,
                    quantity_remaining=quantity,
                    unit_cost=purchase_price_mad
                )
                db.add(stock_lot)
        else:
            shipment_item = ShipmentItem(
                shipment_id=shipment.id,
                product_id=product.id,
                quantity=quantity,
                unit_purchase_price=purchase_price_mad,
                allocated_transport_cost=0.0,
                allocated_customs_cost=0.0
            )
            db.add(shipment_item)
            
            stock_lot = StockLot(
                product_id=product.id,
                shipment_id=shipment_id,
                quantity_remaining=quantity,
                unit_cost=purchase_price_mad
            )
            db.add(stock_lot)
            
        product.stock_quantity += quantity
        if product.purchase_price == 0:
            product.purchase_price = purchase_price_mad
            
        db.commit()
        
        # Recalculer les coûts
        recalculate_shipment_costs(db, shipment)
        
        # Suggérer prix vente si 0
        if product.selling_price == 0 and stock_lot.unit_cost > 0:
            suggested_price = stock_lot.unit_cost * 1.3 * 1.2
            product.selling_price = round(suggested_price, -2)
            
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def update_existing_shipment_item(shipment_id, product_id, new_quantity, new_purchase_price_usd):
    """Met à jour un produit existant dans un arrivage enregistré"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise Exception("Arrivage introuvable")
            
        shipment_item = db.query(ShipmentItem).filter(
            ShipmentItem.shipment_id == shipment_id,
            ShipmentItem.product_id == product_id
        ).first()
        
        if not shipment_item:
            raise Exception("Article introuvable dans cet arrivage")
            
        stock_lot = db.query(StockLot).filter(
            StockLot.shipment_id == shipment_id,
            StockLot.product_id == product_id
        ).first()
        
        if not stock_lot:
            raise Exception("Lot de stock introuvable")
            
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise Exception("Produit introuvable")
            
        # Sécurité : ne pas réduire plus que ce qui a été vendu
        qty_sold = shipment_item.quantity - stock_lot.quantity_remaining
        if new_quantity < qty_sold:
            raise Exception(f"Action impossible : {qty_sold} unités de ce lot ont déjà été vendues.")
            
        diff = new_quantity - shipment_item.quantity
        
        shipment_item.quantity = new_quantity
        shipment_item.unit_purchase_price = new_purchase_price_usd * USD_TO_MAD_RATE
        
        stock_lot.quantity_remaining += diff
        product.stock_quantity += diff
        product.purchase_price = new_purchase_price_usd * USD_TO_MAD_RATE
        
        db.commit()
        
        recalculate_shipment_costs(db, shipment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_item_from_existing_shipment(shipment_id, product_id):
    """Supprime un produit d'un arrivage enregistré"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise Exception("Arrivage introuvable")
            
        shipment_item = db.query(ShipmentItem).filter(
            ShipmentItem.shipment_id == shipment_id,
            ShipmentItem.product_id == product_id
        ).first()
        
        if not shipment_item:
            raise Exception("Article introuvable dans cet arrivage")
            
        stock_lot = db.query(StockLot).filter(
            StockLot.shipment_id == shipment_id,
            StockLot.product_id == product_id
        ).first()
        
        if not stock_lot:
            raise Exception("Lot de stock introuvable")
            
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise Exception("Produit introuvable")
            
        # Sécurité : ne pas supprimer si des unités sont déjà vendues
        qty_sold = shipment_item.quantity - stock_lot.quantity_remaining
        if qty_sold > 0:
            raise Exception(f"Action impossible : {qty_sold} unités de ce lot ont déjà été vendues.")
            
        product.stock_quantity -= shipment_item.quantity
        if product.stock_quantity < 0:
            product.stock_quantity = 0
            
        db.delete(shipment_item)
        db.delete(stock_lot)
        db.commit()
        
        recalculate_shipment_costs(db, shipment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_entire_shipment(shipment_id):
    """Supprime complètement un arrivage enregistré"""
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise Exception("Arrivage introuvable")
            
        items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == shipment_id).all()
        
        # Sécurité : s'assurer qu'aucune unité n'a été vendue
        for item in items:
            stock_lot = db.query(StockLot).filter(
                StockLot.shipment_id == shipment_id,
                StockLot.product_id == item.product_id
            ).first()
            if stock_lot:
                qty_sold = item.quantity - stock_lot.quantity_remaining
                if qty_sold > 0:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    prod_name = product.name if product else f"Produit #{item.product_id}"
                    raise Exception(f"Action impossible : {qty_sold} unités du produit '{prod_name}' ont déjà été vendues.")
                    
        # Suppression
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity -= item.quantity
                if product.stock_quantity < 0:
                    product.stock_quantity = 0
            db.delete(item)
            
        stock_lots = db.query(StockLot).filter(StockLot.shipment_id == shipment_id).all()
        for lot in stock_lots:
            db.delete(lot)
            
        db.delete(shipment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()