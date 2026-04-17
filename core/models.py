from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subtype = Column(String)
    selling_price = Column(Float)
    purchase_price = Column(Float, default=0)
    default_margin = Column(Float, default=30)  # Marge par défaut en %
    stock_quantity = Column(Integer, default=0)
    min_stock_alert = Column(Integer, default=5)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relations
    stock_lots = relationship("StockLot", back_populates="product", foreign_keys="[StockLot.product_id]")
    sale_items = relationship("SaleItem", back_populates="product")
    shipment_items = relationship("ShipmentItem", back_populates="product")
    
    @property
    def average_cost(self):
        """Calcule le coût moyen pondéré du produit basé sur les lots en stock"""
        if not self.stock_lots:
            return self.purchase_price
        total_value = sum(lot.unit_cost * lot.quantity_remaining for lot in self.stock_lots)
        total_qty = sum(lot.quantity_remaining for lot in self.stock_lots)
        return total_value / total_qty if total_qty > 0 else 0
    
    @property
    def suggested_price(self):
        """Calcule un prix suggéré basé sur le coût moyen et la marge par défaut"""
        cost = self.average_cost
        if cost > 0:
            return cost * (1 + self.default_margin / 100)
        return self.selling_price


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    transport_cost_total = Column(Float)
    customs_cost_total = Column(Float, default=0)
    shipping_cost_total = Column(Float, default=0)
    note = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relations - Utiliser un nom différent de "items" pour éviter les conflits
    shipment_items = relationship("ShipmentItem", back_populates="shipment")
    stock_lots = relationship("StockLot", back_populates="shipment")


class StockLot(Base):
    __tablename__ = "stock_lots"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    
    quantity_remaining = Column(Integer)
    unit_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relations
    product = relationship("Product", back_populates="stock_lots", foreign_keys=[product_id])
    shipment = relationship("Shipment", back_populates="stock_lots", foreign_keys=[shipment_id])


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    customer_name = Column(String)
    customer_phone = Column(String)
    customer_email = Column(String)
    payment_method = Column(String)
    payment_status = Column(String, default="payé")
    
    total_revenue = Column(Float)
    total_cost = Column(Float)
    net_profit = Column(Float)
    
    commission_amount = Column(Float, default=0)
    seller_name = Column(String)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relations
    sale_items = relationship("SaleItem", back_populates="sale")
    service_items = relationship("SaleService", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    quantity = Column(Integer)
    unit_price = Column(Float)
    unit_cost_snapshot = Column(Float)
    
    # Relations
    sale = relationship("Sale", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")


class SaleService(Base):
    __tablename__ = "sale_services"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    description = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    
    # Nouveaux champs pour les acomptes
    deposit_amount = Column(Float, default=0)  # Montant de l'acompte
    deposit_date = Column(Date)                 # Date de l'acompte
    deposit_payment_method = Column(String)     # Mode de paiement de l'acompte
    balance_amount = Column(Float, default=0)   # Montant restant
    balance_date = Column(Date)                  # Date du solde
    balance_payment_method = Column(String)      # Mode de paiement du solde
    payment_status = Column(String, default="en_attente")  # en_attente, acompte, payé
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relation
    sale = relationship("Sale", back_populates="service_items")
    
    @property
    def total_amount(self):
        """Montant total TTC de la prestation"""
        return self.quantity * self.unit_price
    
    @property
    def remaining_amount(self):
        """Montant restant à payer"""
        return self.total_amount - self.deposit_amount


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    quantity = Column(Integer)
    unit_purchase_price = Column(Float)
    allocated_transport_cost = Column(Float)
    allocated_customs_cost = Column(Float)
    
    # Relations
    shipment = relationship("Shipment", back_populates="shipment_items")
    product = relationship("Product", back_populates="shipment_items")


class Quote(Base):
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True)
    quote_number = Column(String, unique=True)
    date = Column(Date, nullable=False)
    valid_until = Column(Date)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String)
    customer_email = Column(String)
    status = Column(String, default="brouillon")
    total_amount = Column(Float, default=0)
    notes = Column(String)
    
    # Nouveaux champs pour le design personnalisé
    customer_city = Column(String)
    operation_title = Column(String)
    external_ref = Column(String)
    delivery_delay = Column(String)
    payment_terms = Column(String)
    delivery_location = Column(String)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relations
    quote_items = relationship("QuoteItem", back_populates="quote")


class QuoteItem(Base):
    __tablename__ = "quote_items"
    
    id = Column(Integer, primary_key=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    description = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    size = Column(String)  # Taille / Dimensions
    
    # Relations
    quote = relationship("Quote", back_populates="quote_items")


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class VariableExpense(Base):
    __tablename__ = "variable_expenses"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)  # déplacement, gasoil, menuiserie, soudure, etc.
    amount = Column(Float, nullable=False)
    description = Column(String)
    vehicle = Column(String, nullable=True)  # Pour le gasoil, quel véhicule
    project = Column(String, nullable=True)  # Pour menuiserie/soudure, lié à quel projet
    supplier = Column(String, nullable=True)  # Fournisseur pour les prestations
    payment_method = Column(String, default="Espèces")
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<VariableExpense {self.type} - {self.amount} MAD>"

class FixedChargeTemplate(Base):
    """Modèle pour les charges fixes prédéfinies (template)"""
    __tablename__ = "fixed_charge_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Nom de la charge (ex: "Salaires", "CNSS")
    description = Column(String)            # Description optionnelle
    default_amount = Column(Float, default=0)  # Montant par défaut
    is_active = Column(Boolean, default=True)  # Pour désactiver sans supprimer
    category = Column(String, default="fixe")  # Catégorie (fixe, variable, etc.)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<FixedChargeTemplate {self.name}: {self.default_amount} MAD>"