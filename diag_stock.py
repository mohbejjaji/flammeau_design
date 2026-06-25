"""Diagnostic script to check stock quantity consistency."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.models import Product, StockLot, ShipmentItem, Shipment

db = SessionLocal()

print("=" * 100)
print("DIAGNOSTIC: Stock Quantity Consistency Check")
print("=" * 100)

products = db.query(Product).all()

print(f"\nTotal products in DB: {len(products)}\n")

has_issues = False

for p in products:
    # Sum of all stock lots for this product
    lots = db.query(StockLot).filter(StockLot.product_id == p.id).all()
    total_lot_qty = sum(lot.quantity_remaining for lot in lots)
    
    # Sum of all shipment items for this product
    shipment_items = db.query(ShipmentItem).filter(ShipmentItem.product_id == p.id).all()
    total_shipment_qty = sum(si.quantity for si in shipment_items)
    
    # Check for duplicated items (same product in same shipment)
    from sqlalchemy import func
    dup_check = db.query(
        ShipmentItem.shipment_id,
        func.count(ShipmentItem.id).label('cnt')
    ).filter(
        ShipmentItem.product_id == p.id
    ).group_by(ShipmentItem.shipment_id).having(func.count(ShipmentItem.id) > 1).all()
    
    # Check for duplicated stock lots (same product in same shipment)
    dup_lots = db.query(
        StockLot.shipment_id,
        func.count(StockLot.id).label('cnt')
    ).filter(
        StockLot.product_id == p.id
    ).group_by(StockLot.shipment_id).having(func.count(StockLot.id) > 1).all()
    
    status = "✅"
    notes = []
    
    if p.stock_quantity != total_lot_qty:
        status = "❌"
        notes.append(f"MISMATCH: stock_quantity={p.stock_quantity} vs lot_sum={total_lot_qty}")
        has_issues = True
    
    if total_shipment_qty != total_lot_qty:
        # Could be normal if items were sold (qty_remaining < original qty)
        # But if no sales, they should match
        notes.append(f"INFO: shipment_total={total_shipment_qty} vs lot_remaining={total_lot_qty}")
    
    if dup_check:
        status = "⚠️"
        notes.append(f"DUPLICATE ShipmentItems in shipment(s): {[d[0] for d in dup_check]}")
        has_issues = True
        
    if dup_lots:
        status = "⚠️"
        notes.append(f"DUPLICATE StockLots in shipment(s): {[d[0] for d in dup_lots]}")
        has_issues = True
    
    print(f"{status} {p.reference:25s} | stock_qty={p.stock_quantity:4d} | lot_sum={total_lot_qty:4d} | shipment_total={total_shipment_qty:4d} | lots={len(lots)}")
    for note in notes:
        print(f"   -> {note}")

print("\n" + "=" * 100)

# Check all shipments
print("\nShipments in DB:")
shipments = db.query(Shipment).all()
for s in shipments:
    items = db.query(ShipmentItem).filter(ShipmentItem.shipment_id == s.id).all()
    lots = db.query(StockLot).filter(StockLot.shipment_id == s.id).all()
    print(f"  Shipment #{s.id} ({s.date}) - {len(items)} items, {len(lots)} lots")
    for it in items:
        prod = db.query(Product).filter(Product.id == it.product_id).first()
        lot = db.query(StockLot).filter(StockLot.shipment_id == s.id, StockLot.product_id == it.product_id).first()
        lot_qty = lot.quantity_remaining if lot else "N/A"
        print(f"    Item: {prod.reference if prod else '?':25s} | qty={it.quantity:4d} | lot_remaining={lot_qty}")

print("\n" + "=" * 100)
if has_issues:
    print("⚠️ ISSUES FOUND - See above for details")
else:
    print("✅ All stock quantities are consistent")

db.close()
