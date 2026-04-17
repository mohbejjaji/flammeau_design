from core.models import Quote, QuoteItem
from core.repositories import Repository
from core.database import SessionLocal
from sqlalchemy.orm import joinedload  # ✅ Import nécessaire
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
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
    
    # Format: DE[ANNEE][NUMERO]/MA (ex: DE2026050/MA)
    return f"DE{year}{next_num:03d}/MA"

def create_quote(customer_name, customer_phone="", customer_email="", items=[], notes="", 
                 customer_city="", operation_title="", external_ref="", 
                 delivery_delay="", payment_terms="", delivery_location=""):
    """Crée un nouveau devis"""
    db = SessionLocal()
    
    try:
        quote_number = generate_quote_number()
        
        quote = Quote(
            quote_number=quote_number,
            date=datetime.today(),
            valid_until=datetime.today() + timedelta(days=30),
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            status="brouillon",
            notes=notes,
            customer_city=customer_city,
            operation_title=operation_title,
            external_ref=external_ref,
            delivery_delay=delivery_delay,
            payment_terms=payment_terms,
            delivery_location=delivery_location,
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
                unit_price=item["unit_price"],
                size=item.get("size", "") # Ajout de la taille
            )
            db.add(quote_item)
            total += item["quantity"] * item["unit_price"]
        
        quote.total_amount = total
        db.commit()
        
        # ✅ Recharger le devis avec ses relations
        quote = db.query(Quote).options(joinedload(Quote.quote_items)).filter(Quote.id == quote.id).first()
        
        return quote
    finally:
        db.close()

def get_all_quotes():
    """Récupère tous les devis avec leurs articles"""
    db = SessionLocal()
    try:
        # ✅ Charger les quotes AVEC leurs items en une seule requête
        quotes = db.query(Quote).options(joinedload(Quote.quote_items)).order_by(Quote.date.desc()).all()
        # Forcer le chargement pour éviter les problèmes de session
        for quote in quotes:
            # Accéder à quote_items pour forcer le chargement
            _ = quote.quote_items
        return quotes
    finally:
        db.close()

def get_quote_by_id(quote_id):
    """Récupère un devis par son ID avec ses articles"""
    db = SessionLocal()
    try:
        # ✅ Charger le devis AVEC ses items
        quote = db.query(Quote).options(joinedload(Quote.quote_items)).filter(Quote.id == quote_id).first()
        if quote:
            # Forcer le chargement
            _ = quote.quote_items
        return quote
    finally:
        db.close()

def update_quote_status(quote_id, new_status):
    """Met à jour le statut d'un devis"""
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            quote.status = new_status
            db.commit()
        return quote
    finally:
        db.close()

def delete_quote(quote_id):
    """Supprime un devis"""
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if quote:
            db.delete(quote)
            db.commit()
    finally:
        db.close()

def generate_quote_pdf(quote_id):
    """Génère un PDF de devis professionnel correspondant au design Flammeau Design"""
    db = SessionLocal()
    try:
        # Charger le devis avec ses items
        quote = db.query(Quote).options(joinedload(Quote.quote_items)).filter(Quote.id == quote_id).first()
        
        if not quote:
            return None
        
        # Nom du fichier
        filename = f"devis_{quote.quote_number.replace('/', '_')}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join("temp", filename)
        os.makedirs("temp", exist_ok=True)
        
        # Styles de base
        styles = getSampleStyleSheet()
        
        # Style pour le texte normal (petit)
        style_norm = ParagraphStyle(
            name='NormalStyle',
            fontSize=9,
            leading=11,
            alignment=0 # Gauche
        )
        
        style_bold = ParagraphStyle(
            name='BoldStyle',
            fontSize=9,
            leading=11,
            fontName='Helvetica-Bold'
        )
        
        style_title = ParagraphStyle(
            name='DocTitle',
            fontSize=16,
            leading=20,
            fontName='Helvetica-Bold',
            alignment=1, # Centre
            textColor=colors.black
        )

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            topMargin=1.5*cm,
            bottomMargin=1*cm,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm
        )
        
        elements = []

        # --- 1. EN-TÊTE (Logo + Numéro Devis) ---
        logo_path = os.path.join("assets", "logo.PNG")
        logo = None
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=4*cm, height=2.2*cm)
        
        devis_num_data = [
            ["DEVIS", quote.quote_number]
        ]
        t_devis_num = Table(devis_num_data, colWidths=[2.5*cm, 3.5*cm])
        t_devis_num.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))

        header_data = [[logo if logo else "FLAMMEAU DESIGN", "", t_devis_num]]
        t_header = Table(header_data, colWidths=[10*cm, 1*cm, 6*cm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 5*mm))

        # Barres Marrons/Oranges
        line_table = Table([[""]], colWidths=[18*cm], rowHeights=[1*mm])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B4513')), # Marron
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(line_table)
        
        # Titre DEVIS
        devis_title_table = Table([[Paragraph("DEVIS", style_title)]], colWidths=[18*cm])
        devis_title_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(devis_title_table)
        elements.append(Spacer(1, 8*mm))

        # --- 2. CLIENT & DIVERS ---
        # Bloc Client
        client_table_data = [
            [Paragraph("Client", style_bold), ""],
            [Paragraph("Nom", style_norm), Paragraph(f"<b>{quote.customer_name}</b>", style_norm)],
            [Paragraph("Ville", style_norm), Paragraph(quote.customer_city or "", style_norm)],
        ]
        t_client = Table(client_table_data, colWidths=[2*cm, 7*cm])
        t_client.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
            ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, 0), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        # Bloc Divers
        divers_table_data = [
            [Paragraph("Divers", style_bold), ""],
            [Paragraph("Date", style_norm), Paragraph(quote.date.strftime('%d/%m/%Y'), style_norm)],
            [Paragraph("Réf N°", style_norm), Paragraph(quote.external_ref or "", style_norm)],
            [Paragraph("Opération", style_norm), Paragraph(quote.operation_title or "", style_norm)],
        ]
        t_divers = Table(divers_table_data, colWidths=[2.5*cm, 5.5*cm])
        t_divers.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        info_data = [[t_client, Spacer(1.5*cm, 1), t_divers]]
        t_info = Table(info_data, colWidths=[9*cm, 1*cm, 8*cm])
        t_info.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 10*mm))

        # --- 3. ARTICLES ---
        data = [
            [Paragraph("Qté", style_bold), Paragraph("Description", style_bold), 
             Paragraph("Size", style_bold), Paragraph("Prix unitaire", style_bold), 
             Paragraph("TOTAL", style_bold)]
        ]
        
        for item in quote.quote_items:
            unit_price_str = f"{item.unit_price:,.2f}" if item.unit_price > 0 else ""
            total_price_str = f"{item.quantity * item.unit_price:,.2f}" if item.unit_price > 0 else "GRATUIT"
            
            desc_p = Paragraph(item.description.replace("\n", "<br/>"), style_norm)
            size_p = Paragraph(item.size or "", style_norm) # Affichage de la taille
            
            data.append([
                str(item.quantity),
                desc_p,
                size_p,
                unit_price_str,
                total_price_str
            ])
        
        # Ajouter les conditions de livraison/paiement dans le tableau (design dynamique)
        if quote.delivery_location:
            data.append(["1", Paragraph(quote.delivery_location, style_norm), "", "", ""])
            
        data.append(["", Paragraph(f"<b>Mode de paiement:</b> {quote.payment_terms or ''}", style_norm), "", "", ""])
        data.append(["", Paragraph(f"<b>Délai de livraison:</b> {quote.delivery_delay or ''}", style_norm), "", "", ""])

        # 5 colonnes désormais
        t_articles = Table(data, colWidths=[1.2*cm, 7.8*cm, 3.0*cm, 3.0*cm, 3.0*cm])
        t_articles.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -4), 0.5, colors.black, None, (2, 2)), # Pointillés pour les items
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, 0), 0.5, colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'), # Qté centrée
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'), # Size/Prix/Total centrés
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        # Modifier le style de grille pour les items (pointillés) - on s'arrête avant les conditions
        for i in range(1, len(data) - 3):
            t_articles.setStyle(TableStyle([
                ('LINEBELOW', (0, i), (-1, i), 0.5, colors.black, None, (1, 1)),
            ]))

        elements.append(t_articles)
        
        # --- 4. TOTALS & CACHET ---
        total_ht = quote.total_amount
        total_p_vente = quote.total_amount # Dans l'image "Prix de vente" est identique au total
        
        totals_data = [
            [Paragraph("TOTAL", style_norm), f"{total_ht:,.2f}"],
            [Paragraph("Prix de vente", style_norm), f"{total_p_vente:,.2f}"],
            [Paragraph("TOTAL", style_bold), Paragraph(f"<b>{total_ht:,.2f}</b>", style_bold)],
        ]
        t_totals = Table(totals_data, colWidths=[2.5*cm, 3*cm])
        t_totals.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black, None, (1, 1)),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 2), (1, 2), colors.white),
        ]))

        cachet_data = [[Paragraph("Cachet", style_bold)]]
        t_cachet = Table(cachet_data, colWidths=[5*cm], rowHeights=[2.5*cm])
        t_cachet.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        footer_boxes_data = [[t_cachet, Spacer(7.5*cm, 1), t_totals]]
        t_footer_boxes = Table(footer_boxes_data, colWidths=[5*cm, 7.5*cm, 5.5*cm])
        t_footer_boxes.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        
        elements.append(Spacer(1, 5*mm))
        elements.append(t_footer_boxes)

        # --- 5. PIED DE PAGE LÉGAL ---
        elements.append(Spacer(1, 10*mm))
        
        # Ligne marron en bas
        elements.append(line_table)
        
        style_footer_bold = ParagraphStyle(name='FooterBold', fontSize=10, fontName='Helvetica-Bold')
        style_footer_small = ParagraphStyle(name='FooterSmall', fontSize=8, textColor=colors.grey, leading=10)
        
        elements.append(Paragraph("Flammeau Design", style_footer_bold))
        legal_info = (
            "R.C: 394471 IF: 25036297 TP: 35779187 ICE: 002019352000032<br/>"
            "Siège : Lotissement DAR AL AMANE DAR BOUAZZA CASABLANCA<br/>"
            "Capital : 100.000,00 DHS<br/>"
            "Tel : +212 (0) 522 655986<br/>"
            "GSM : +212 (0) 66536006<br/>"
            "Email : Flammeaudesign@gmail.com<br/>"
            "Site web : www.Flammeaudesign.com"
        )
        elements.append(Paragraph(legal_info, style_footer_small))

        # Générer
        doc.build(elements)
        return filepath
        
    except Exception as e:
        print(f"Erreur PDF: {e}")
        return None
    finally:
        db.close()
    finally:
        db.close()

def convert_quote_to_sale(quote_id):
    """Convertit un devis accepté en vente"""
    from services.sales_service import create_product_sale
    from services.product_service import get_product_by_id
    
    db = SessionLocal()
    try:
        # Charger le devis avec ses articles
        quote = db.query(Quote).options(joinedload(Quote.quote_items)).filter(Quote.id == quote_id).first()
        
        if not quote:
            return None, "Devis non trouvé"
        
        # Vérifier que le devis est accepté
        if quote.status not in ["accepté", "converti"]:
            return None, "Seuls les devis acceptés peuvent être convertis en vente"
        
        # Préparer les items pour la vente
        items = []
        produits_manquants = []
        
        for item in quote.quote_items:
            if item.product_id:  # Si c'est un produit
                # Vérifier le stock
                product = get_product_by_id(item.product_id)
                if not product:
                    produits_manquants.append(f"Produit {item.description} non trouvé")
                    continue
                
                if product.stock_quantity < item.quantity:
                    produits_manquants.append(f"Stock insuffisant pour {item.description} (dispo: {product.stock_quantity}, besoin: {item.quantity})")
                    continue
                
                items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price
                })
            else:  # Si c'est une prestation
                # Pour les prestations, on pourrait créer une vente de service
                items.append({
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "unit_cost": 0  # À définir selon votre logique
                })
        
        if produits_manquants:
            return None, "\n".join(produits_manquants)
        
        if not items:
            return None, "Aucun article valide à convertir"
        
        # Créer la vente
        # Note: Adaptez cette partie selon votre fonction de création de vente
        # Pour les produits
        produits = [i for i in items if "product_id" in i]
        if produits:
            sale = create_product_sale(
                customer_name=quote.customer_name,
                items=produits,
                seller_name="Devis converti",
                commission=0,
                payment_method="À définir",
                customer_phone=quote.customer_phone,
                customer_email=quote.customer_email
            )
        
        # Mettre à jour le statut du devis
        quote.status = "converti"
        db.commit()
        
        return True, "Devis converti avec succès en vente"
        
    except Exception as e:
        db.rollback()
        return None, f"Erreur lors de la conversion: {str(e)}"
    finally:
        db.close()