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


# ==================== FONCTIONS EXISTANTES ====================

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
    filename = f"ticket_{sale.id:04d}_{sale.date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join("temp", filename)
    
    # Configuration du document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#00adb5'),
        spaceAfter=10,
        alignment=1
    ))
    
    # En-tête
    elements.append(Paragraph("FLAMMEAU DESIGN", styles['CompanyName']))
    elements.append(Paragraph("Importateur de cheminées", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Informations du ticket
    elements.append(Paragraph(f"Ticket N°: {sale.id:04d}", styles['Normal']))
    elements.append(Paragraph(f"Date: {sale.date.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Client: {sale.customer_name}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Articles
    product_items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    service_items = db.query(SaleService).filter(SaleService.sale_id == sale_id).all()
    
    if product_items or service_items:
        data = [["Description", "Qté", "Prix unitaire", "Total"]]
        
        for item in product_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            name = product.name if product else "Produit"
            data.append([
                name[:30],
                str(item.quantity),
                f"{item.unit_price:.0f} MAD",
                f"{item.quantity * item.unit_price:.0f} MAD"
            ])
        
        for item in service_items:
            data.append([
                item.description[:30],
                str(item.quantity),
                f"{item.unit_price:.0f} MAD",
                f"{item.quantity * item.unit_price:.0f} MAD"
            ])
        
        table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00adb5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
    
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(f"Total TTC: {sale.total_revenue * 1.20:.0f} MAD", styles['Heading3']))
    
    doc.build(elements)
    db.close()
    
    return filepath


# ==================== NOUVELLES FONCTIONS POUR LES COMMISSIONS ====================

def get_commission_history(start_date=None, end_date=None, seller=None):
    """
    Récupère l'historique détaillé des commissions par vendeur
    """
    db = SessionLocal()
    
    query = db.query(Sale).filter(Sale.commission_amount > 0)
    
    if start_date:
        query = query.filter(Sale.date >= start_date)
    if end_date:
        query = query.filter(Sale.date <= end_date)
    if seller and seller != "Tous":
        query = query.filter(Sale.seller_name == seller)
    
    sales = query.order_by(Sale.date.desc()).all()
    
    result = []
    for sale in sales:
        # Récupérer les détails des produits vendus
        product_items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        
        # Calculer le total des ventes pour ce vendeur
        total_ventes = sum(item.quantity * item.unit_price for item in product_items)
        
        result.append({
            'id': sale.id,
            'date': sale.date.strftime('%d/%m/%Y'),
            'seller': sale.seller_name or 'Non assigné',
            'customer': sale.customer_name,
            'total_ventes': total_ventes,
            'commission': sale.commission_amount,
            'taux_commission': (sale.commission_amount / total_ventes * 100) if total_ventes > 0 else 0,
            'payment_method': sale.payment_method,
            'nb_articles': len(product_items)
        })
    
    db.close()
    return pd.DataFrame(result)


def get_commission_summary_by_seller(start_date=None, end_date=None):
    """
    Récupère un résumé des commissions par vendeur
    """
    df = get_commission_history(start_date, end_date)
    
    if df.empty:
        return pd.DataFrame()
    
    # Grouper par vendeur
    summary = df.groupby('seller').agg({
        'commission': 'sum',
        'total_ventes': 'sum',
        'id': 'count'
    }).reset_index()
    
    summary.columns = ['Vendeur', 'Total Commissions', 'Total Ventes', 'Nombre de ventes']
    summary['Taux moyen'] = (summary['Total Commissions'] / summary['Total Ventes'] * 100).round(1)
    summary['Total Commissions'] = summary['Total Commissions'].round(2)
    summary['Total Ventes'] = summary['Total Ventes'].round(2)
    
    return summary.sort_values('Total Commissions', ascending=False)


def get_daily_commission_summary(date=None):
    """
    Récupère le résumé des commissions pour un jour spécifique
    """
    if date is None:
        date = datetime.now().date()
    
    db = SessionLocal()
    
    sales = db.query(Sale).filter(
        Sale.date == date,
        Sale.commission_amount > 0
    ).all()
    
    summary = {}
    for sale in sales:
        seller = sale.seller_name or 'Non assigné'
        if seller not in summary:
            summary[seller] = {
                'ventes': 0,
                'commissions': 0,
                'nb_transactions': 0
            }
        summary[seller]['ventes'] += sale.total_revenue
        summary[seller]['commissions'] += sale.commission_amount
        summary[seller]['nb_transactions'] += 1
    
    db.close()
    return summary


def generate_commission_report_pdf(start_date, end_date, seller=None):
    """
    Génère un rapport PDF des commissions
    """
    # Récupérer les données
    df = get_commission_history(start_date, end_date, seller)
    
    if df.empty:
        return None
    
    # Créer le dossier temp s'il n'existe pas
    os.makedirs("temp", exist_ok=True)
    
    # Nom du fichier
    if seller and seller != "Tous":
        filename = f"commissions_{seller}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    else:
        filename = f"commissions_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    filepath = os.path.join("temp", filename)
    
    # Configuration du document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#00adb5'),
        spaceAfter=20,
        alignment=1
    ))
    
    # Titre
    elements.append(Paragraph("Rapport des Commissions", styles['ReportTitle']))
    elements.append(Paragraph(
        f"Période du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
        styles['Normal']
    ))
    if seller and seller != "Tous":
        elements.append(Paragraph(f"Vendeur: {seller}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tableau des commissions
    data = [['Date', 'Vendeur', 'Client', 'Total Ventes', 'Commission', 'Taux']]
    
    for _, row in df.iterrows():
        data.append([
            row['date'],
            row['seller'],
            row['customer'][:20] + "..." if len(row['customer']) > 20 else row['customer'],
            f"{row['total_ventes']:,.0f} MAD",
            f"{row['commission']:,.0f} MAD",
            f"{row['taux_commission']:.1f}%"
        ])
    
    # Ajouter les totaux
    total_commissions = df['commission'].sum()
    total_ventes = df['total_ventes'].sum()
    
    data.append(['', '', '', 'TOTAUX', f"{total_commissions:,.0f} MAD", f"{(total_commissions/total_ventes*100):.1f}%" if total_ventes > 0 else "0%"])
    
    # Créer le tableau
    table = Table(data, colWidths=[2.5*cm, 3*cm, 4*cm, 3*cm, 3*cm, 2*cm])
    
    # Style du tableau
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00adb5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
    ]
    
    table.setStyle(TableStyle(style))
    elements.append(table)
    
    # Générer le PDF
    doc.build(elements)
    
    return filepath