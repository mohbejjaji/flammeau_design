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