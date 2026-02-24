from config import COMMISSION_RATE, TVA_RATE

def product_margin(unit_price, unit_cost, transport_cost=0):
    """
    Calcule la marge brute d'un produit avant commission.
    unit_price : prix vente
    unit_cost : prix achat
    transport_cost : coût transport Chine
    """
    return unit_price - (unit_cost + transport_cost)

def commission_on_margin(margin):
    """
    Calcule la commission sur la marge brute
    """
    return margin * COMMISSION_RATE

def net_product_margin_after_commission(margin):
    """
    Marge nette après déduction commission commerciale
    """
    return margin - commission_on_margin(margin)

def service_margin(unit_price, unit_cost):
    """
    Marge brute d'une prestation
    """
    return unit_price - unit_cost

def apply_tva(amount):
    """
    Calcule le montant TVA sur un montant HT
    """
    return amount * TVA_RATE

def calculate_sale_summary(product_items, service_items):
    """
    Calcule le total ventes, coût total, marge nette après commission et TVA
    product_items : liste de dict avec product_id, quantity, unit_price, unit_cost, transport_cost
    service_items : liste de dict avec quantity, unit_price, unit_cost
    Retour : dict {total_revenue, total_cost, total_net_margin, total_tva}
    """
    total_revenue = 0
    total_cost = 0
    total_net_margin = 0
    total_tva = 0

    # Produits
    for p in product_items:
        margin = product_margin(p["unit_price"], p["unit_cost"], p.get("transport_cost",0))
        net_margin = net_product_margin_after_commission(margin) * p["quantity"]

        total_revenue += p["unit_price"] * p["quantity"]
        total_cost += (p["unit_cost"] + p.get("transport_cost",0)) * p["quantity"]
        total_net_margin += net_margin
        total_tva += apply_tva(p["unit_price"] * p["quantity"])

    # Prestations
    for s in service_items:
        margin = service_margin(s["unit_price"], s["unit_cost"]) * s["quantity"]
        total_revenue += s["unit_price"] * s["quantity"]
        total_cost += s["unit_cost"] * s["quantity"]
        total_net_margin += margin
        total_tva += apply_tva(s["unit_price"] * s["quantity"])

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_net_margin": total_net_margin,
        "total_tva": total_tva
    }

def calculate_profit_after_fixed_charges(total_net_margin, fixed_charges):
    """
    Calcule le bénéfice réel après charges fixes
    """
    return total_net_margin - fixed_charges