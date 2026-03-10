from core.database import SessionLocal
from core.models import Sale, SaleItem, SaleService, Product
from datetime import datetime, timedelta
import pandas as pd
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import streamlit as st


def get_sales_history(start_date=None, end_date=None, limit=100):
    """Récupère l'historique des ventes avec filtres optionnels"""
    db = SessionLocal()
    
    query = db.query(Sale).order_by(Sale.date.desc())
    
    if start_date:
        query = query.filter(Sale.date >= start_date)
    if end_date:
        query = query.filter(Sale.date <= end_date)
    
    sales = query.limit(limit).all()
    
    result = []
    for sale in sales:
        # Récupérer les items de la vente
        product_items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        service_items = db.query(SaleService).filter(SaleService.sale_id == sale.id).all()
        
        # Compter le nombre d'articles
        total_items = len(product_items) + len(service_items)
        
        result.append({
            'id': sale.id,
            'date': sale.date,
            'customer': sale.customer_name,
            'seller': sale.seller_name,
            'payment': sale.payment_method,
            'items_count': total_items,
            'revenue': sale.total_revenue,
            'cost': sale.total_cost,
            'profit': sale.net_profit,
            'commission': sale.commission_amount,
            'product_items': product_items,
            'service_items': service_items
        })
    
    db.close()
    return result


def get_sale_details(sale_id):
    """Récupère les détails complets d'une vente"""
    db = SessionLocal()
    
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        db.close()
        return None
    
    product_items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    service_items = db.query(SaleService).filter(SaleService.sale_id == sale_id).all()
    
    # Préparer les données pour l'affichage
    items = []
    
    for item in product_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        items.append({
            'type': 'Produit',
            'name': product.name if product else "Produit inconnu",
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item.quantity * item.unit_price,
            'cost': item.unit_cost_snapshot
        })
    
    for item in service_items:
        items.append({
            'type': 'Service',
            'name': item.description,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item.quantity * item.unit_price,
            'cost': item.unit_cost
        })
    
    db.close()
    
    return {
        'sale': sale,
        'items': items,
        'total_revenue': sale.total_revenue,
        'total_cost': sale.total_cost,
        'profit': sale.net_profit,
        'profit_margin': (sale.net_profit / sale.total_revenue * 100) if sale.total_revenue > 0 else 0
    }


def generate_ticket_pdf(sale_id):
    """Génère un PDF professionnel du ticket de vente (format A4)"""
    db = SessionLocal()
    
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        db.close()
        return None
    
    # Créer le dossier temp s'il n'existe pas
    os.makedirs("temp", exist_ok=True)
    
    # Nom du fichier
    filename = f"facture_{sale.id:04d}_{sale.date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join("temp", filename)
    
    # Configuration du document (format A4 avec marges ajustées)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.2*cm,
        bottomMargin=1*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#00adb5'),
        spaceAfter=6,
        alignment=1
    ))
    
    styles.add(ParagraphStyle(
        name='CompanyInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        name='DocumentTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#393e46'),
        spaceAfter=12,
        alignment=1
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#393e46'),
        spaceAfter=8,
        spaceBefore=6,
        alignment=0
    ))
    
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1,
        spaceBefore=12
    ))
    
    # En-tête avec logo
    try:
        logo_path = os.path.join("assets", "logo.PNG")
        if os.path.exists(logo_path):
            from reportlab.platypus import Image
            logo = Image(logo_path, width=90, height=45)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.3*cm))
    except:
        pass
    
    # Nom de l'entreprise
    elements.append(Paragraph("FLAMMEAU DESIGN", styles['CompanyName']))
    elements.append(Paragraph("Importateur de cheminées | Tél: +212 661-XXXXXX", styles['CompanyInfo']))
    elements.append(Paragraph("contact@flammeau.ma | www.flammeau-design.ma", styles['CompanyInfo']))
    elements.append(Spacer(1, 0.4*cm))
    
    # Titre du document
    elements.append(Paragraph("FACTURE / TICKET DE VENTE", styles['DocumentTitle']))
    
    # Informations du document
    data_info = [
        ["N° Facture:", f"FAC-{sale.id:04d}", "Date:", sale.date.strftime('%d/%m/%Y')],
        ["Client:", sale.customer_name, "Tél client:", sale.customer_phone or "Non renseigné"],
        ["Vendeur:", sale.seller_name or "N/A", "Mode paiement:", sale.payment_method or "N/A"],
    ]
    
    t_info = Table(data_info, colWidths=[2.8*cm, 5.2*cm, 2.8*cm, 5.2*cm])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#00adb5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 0.6*cm))
    
    # Section articles
    elements.append(Paragraph("Détail des articles", styles['SectionTitle']))
    
    # Récupérer les articles
    product_items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    service_items = db.query(SaleService).filter(SaleService.sale_id == sale_id).all()
    
    # Créer le tableau des articles (sans lignes vides)
    data_articles = []
    
    # En-tête
    data_articles.append(['Désignation', 'Qté', 'Prix unitaire', 'Total HT'])
    
    # Ajouter les produits
    for item in product_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            # Tronquer le nom si nécessaire
            name = product.name
            if len(name) > 40:
                name = name[:37] + "..."
        else:
            name = "Produit"
        
        data_articles.append([
            name,
            str(item.quantity),
            f"{item.unit_price:,.0f} MAD",
            f"{item.quantity * item.unit_price:,.0f} MAD"
        ])
    
    # Ajouter les services
    for item in service_items:
        description = item.description
        if len(description) > 40:
            description = description[:37] + "..."
        
        data_articles.append([
            description,
            str(item.quantity),
            f"{item.unit_price:,.0f} MAD",
            f"{item.quantity * item.unit_price:,.0f} MAD"
        ])
    
    # Calculer les totaux
    total_ht = sale.total_revenue
    total_ttc = total_ht * 1.20
    total_tva = total_ttc - total_ht
    
    # Ajouter la ligne de total
    data_articles.append(['', '', 'TOTAL HT', f"{total_ht:,.0f} MAD"])
    data_articles.append(['', '', 'TVA (20%)', f"{total_tva:,.0f} MAD"])
    data_articles.append(['', '', 'TOTAL TTC', f"{total_ttc:,.0f} MAD"])
    
    # Calculer le nombre de lignes d'articles (sans l'en-tête et sans les totaux)
    articles_count = len(product_items) + len(service_items)
    
    # Ajuster dynamiquement la hauteur des lignes
    if articles_count <= 2:
        row_heights = [0.8*cm] * (articles_count + 4)  # +4 pour en-tête + 3 lignes de totaux
    elif articles_count <= 4:
        row_heights = [0.7*cm] * (articles_count + 4)
    elif articles_count <= 6:
        row_heights = [0.6*cm] * (articles_count + 4)
    else:
        row_heights = [0.5*cm] * (articles_count + 4)
    
    # Définir les largeurs de colonnes
    if articles_count > 5:
        col_widths = [8.5*cm, 1.5*cm, 2.5*cm, 2.5*cm]
    else:
        col_widths = [9.5*cm, 1.5*cm, 2.5*cm, 2.5*cm]
    
    # Créer le tableau avec hauteurs de lignes spécifiques
    table_articles = Table(data_articles, colWidths=col_widths, rowHeights=row_heights)
    
    # Style du tableau
    style_articles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -4), 9),  # Articles
        ('FONTSIZE', (0, -3), (-1, -1), 10),  # Totaux
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -4), 'CENTER'),
        ('ALIGN', (2, 1), (2, -4), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -4), 'RIGHT'),
        ('ALIGN', (2, -3), (3, -1), 'RIGHT'),
        ('GRID', (0, 1), (-1, -4), 0.5, colors.grey),  # Grille seulement sur les articles
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#f0f0f0')),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('SPAN', (0, -3), (1, -3)),
        ('SPAN', (0, -2), (1, -2)),
        ('SPAN', (0, -1), (1, -1)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]
    
    table_articles.setStyle(TableStyle(style_articles))
    elements.append(table_articles)
    elements.append(Spacer(1, 0.6*cm))
    
    # Section paiement
    elements.append(Paragraph("Paiement", styles['SectionTitle']))
    
    data_payment = [
        ["Montant TTC:", f"{total_ttc:,.0f} MAD", "Statut:", "Payé"],
    ]
    
    t_payment = Table(data_payment, colWidths=[3.5*cm, 4*cm, 3*cm, 4*cm])
    t_payment.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#00adb5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_payment)
    
    # Note si présente
    if hasattr(sale, 'note') and sale.note:
        elements.append(Spacer(1, 0.2*cm))
        elements.append(Paragraph(f"Note: {sale.note}", styles['Normal']))
    
    # Mentions légales
    elements.append(Spacer(1, 0.4*cm))
    elements.append(Paragraph("Merci de votre confiance ! 🔥", styles['Footer']))
    elements.append(Paragraph("FLAMMEAU DESIGN - SIREN: XXX XXX XXX - TVA: FRXXXXXXXXX", styles['Footer']))
    
    # Générer le PDF
    doc.build(elements)
    db.close()
    
    return filepath


def get_sales_stats(period="month"):
    """Statistiques des ventes par période"""
    db = SessionLocal()
    
    today = datetime.now().date()
    
    if period == "day":
        start_date = today
        sales = db.query(Sale).filter(Sale.date == today).all()
    elif period == "week":
        start_date = today - timedelta(days=7)
        sales = db.query(Sale).filter(Sale.date >= start_date).all()
    elif period == "month":
        start_date = today.replace(day=1)
        sales = db.query(Sale).filter(Sale.date >= start_date).all()
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        sales = db.query(Sale).filter(Sale.date >= start_date).all()
    else:
        sales = db.query(Sale).all()
    
    total_revenue = sum(s.total_revenue for s in sales)
    total_profit = sum(s.net_profit for s in sales)
    total_commission = sum(s.commission_amount for s in sales)
    
    db.close()
    
    return {
        'count': len(sales),
        'revenue': total_revenue,
        'profit': total_profit,
        'commission': total_commission,
        'avg_ticket': total_revenue / len(sales) if sales else 0
    }


def export_sales_to_excel(start_date=None, end_date=None):
    """Exporte les ventes au format Excel"""
    sales = get_sales_history(start_date, end_date, limit=1000)
    
    data = []
    for sale in sales:
        data.append({
            'ID Vente': sale['id'],
            'Date': sale['date'],
            'Client': sale['customer'],
            'Vendeur': sale['seller'],
            'Paiement': sale['payment'],
            'Articles': sale['items_count'],
            'CA HT': sale['revenue'],
            'TVA': sale['revenue'] * 0.20,
            'CA TTC': sale['revenue'] * 1.20,
            'Coût': sale['cost'],
            'Bénéfice': sale['profit'],
            'Marge %': (sale['profit'] / sale['revenue'] * 100) if sale['revenue'] > 0 else 0,
            'Commission': sale['commission']
        })
    
    df = pd.DataFrame(data)
    
    # Créer le dossier temp s'il n'existe pas
    os.makedirs("temp", exist_ok=True)
    
    # Créer le fichier Excel
    filename = f"ventes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("temp", filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Ventes', index=False)
        
        # Ajuster la largeur des colonnes
        worksheet = writer.sheets['Ventes']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return filepath