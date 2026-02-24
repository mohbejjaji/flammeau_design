from core.models import Quote, QuoteItem, Product
from core.repositories import Repository
from core.database import SessionLocal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
import os

quote_repo = Repository(Quote)

def generate_quote_number():
    """Génère un numéro de devis unique"""
    db = SessionLocal()
    last_quote = db.query(Quote).order_by(Quote.id.desc()).first()
    db.close()
    
    year = datetime.now().strftime("%Y")
    if last_quote:
        next_num = last_quote.id + 1
    else:
        next_num = 1
    
    return f"DEV-{year}-{next_num:04d}"

def create_quote(customer_name, customer_phone, customer_email, items, notes=""):
    """Crée un nouveau devis"""
    db = SessionLocal()
    
    quote_number = generate_quote_number()
    
    quote = Quote(
        quote_number=quote_number,
        date=datetime.today(),
        valid_until=datetime.today() + timedelta(days=30),  # Valable 30 jours
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        status="brouillon",
        notes=notes,
        total_amount=0
    )
    
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    total = 0
    for item in items:
        quote_item = QuoteItem(
            quote_id=quote.id,
            product_id=item.get("product_id"),
            description=item["description"],
            quantity=item["quantity"],
            unit_price=item["unit_price"]
        )
        db.add(quote_item)
        total += item["quantity"] * item["unit_price"]
    
    quote.total_amount = total
    db.commit()
    db.close()
    
    return quote

def get_all_quotes():
    """Récupère tous les devis"""
    db = SessionLocal()
    quotes = db.query(Quote).order_by(Quote.date.desc()).all()
    db.close()
    return quotes

def get_quote_by_id(quote_id):
    """Récupère un devis par son ID"""
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    db.close()
    return quote

def update_quote_status(quote_id, new_status):
    """Met à jour le statut d'un devis"""
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if quote:
        quote.status = new_status
        db.commit()
    db.close()
    return quote

def delete_quote(quote_id):
    """Supprime un devis"""
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if quote:
        db.delete(quote)
        db.commit()
    db.close()

def generate_quote_pdf(quote_id):
    """Génère un PDF de devis professionnel"""
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        db.close()
        return None
    
    # Créer le nom du fichier
    filename = f"devis_{quote.quote_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join("temp", filename)
    
    # Créer le dossier temp s'il n'existe pas
    os.makedirs("temp", exist_ok=True)
    
    # Créer le PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour l'en-tête
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00adb5'),
        spaceAfter=30
    ))
    
    styles.add(ParagraphStyle(
        name='CompanyInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey
    ))
    
    # En-tête du devis
    elements.append(Paragraph("FLAMMEAU DESIGN", styles['CompanyName']))
    
    # Informations de l'entreprise
    company_info = [
        ["FLAMMEAU DESIGN", f"Devis N°: {quote.quote_number}"],
        ["Importateur de cheminées", f"Date: {quote.date.strftime('%d/%m/%Y')}"],
        ["Tél: +212 XXX-XXXXXX", f"Valable jusqu'au: {quote.valid_until.strftime('%d/%m/%Y')}"],
        ["Email: contact@flammeau-design.ma", f"Statut: {quote.status.upper()}"]
    ]
    
    t = Table(company_info, colWidths=[10*cm, 8*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Informations client
    client_info = [
        ["CLIENT:", ""],
        [quote.customer_name, f"Tél: {quote.customer_phone or 'Non renseigné'}"],
        ["", f"Email: {quote.customer_email or 'Non renseigné'}"]
    ]
    
    t = Table(client_info, colWidths=[3*cm, 15*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#00adb5')),
        ('SPAN', (0, 1), (0, 2)),
        ('VALIGN', (0, 1), (0, 2), 'MIDDLE'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Tableau des articles
    data = [["Description", "Quantité", "Prix unitaire (MAD)", "Total (MAD)"]]
    
    for item in quote.items:
        data.append([
            item.description,
            str(item.quantity),
            f"{item.unit_price:,.2f}",
            f"{item.quantity * item.unit_price:,.2f}"
        ])
    
    # Ligne de total
    data.append(["", "", "TOTAL HT", f"{quote.total_amount:,.2f} MAD"])
    data.append(["", "", "TVA (20%)", f"{quote.total_amount * 0.20:,.2f} MAD"])
    data.append(["", "", "TOTAL TTC", f"{quote.total_amount * 1.20:,.2f} MAD"])
    
    # Créer le tableau
    table = Table(data, colWidths=[10*cm, 3*cm, 4*cm, 4*cm])
    
    # Style du tableau
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -4), 1, colors.black),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f0f0f0')),
        ('LINEABOVE', (0, -3), (-1, -3), 2, colors.black),
    ]
    
    table.setStyle(TableStyle(table_style))
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Notes et conditions
    if quote.notes:
        elements.append(Paragraph("Notes:", styles['Heading6']))
        elements.append(Paragraph(quote.notes, styles['Normal']))
        elements.append(Spacer(1, 15))
    
    # Conditions générales
    conditions = [
        "Conditions générales :",
        "• Devis valable 30 jours",
        "• Paiement à réception de facture",
        "• Garantie 2 ans sur tous nos produits",
        "• Installation possible sur devis séparé"
    ]
    
    for condition in conditions:
        elements.append(Paragraph(condition, styles['Normal']))
    
    # Pied de page
    elements.append(Spacer(1, 30))
    footer_text = "FLAMMEAU DESIGN - Importateur de cheminées - SIREN: XXX XXX XXX - www.flammeau-design.ma"
    elements.append(Paragraph(footer_text, styles['Italic']))
    
    # Générer le PDF
    doc.build(elements)
    db.close()
    
    return filepath

def convert_quote_to_sale(quote_id):
    """Convertit un devis accepté en vente"""
    from services.sales_service import create_product_sale
    
    db = SessionLocal()
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        db.close()
        return None
    
    # Préparer les items pour la vente
    items = []
    for item in quote.items:
        if item.product_id:  # Si c'est un produit
            items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            })
        else:  # Si c'est une prestation
            items.append({
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "unit_cost": 0  # À définir selon votre logique
            })
    
    # Créer la vente
    # Note: Adaptez cette partie selon votre fonction de création de vente
    # create_product_sale(quote.customer_name, items, seller_name="Devis converti")
    
    # Mettre à jour le statut du devis
    quote.status = "converti"
    db.commit()
    db.close()
    
    return True