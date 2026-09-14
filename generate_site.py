import urllib.request
import json
import os
import re
from datetime import datetime

print("Building OSRS Market Opportunity Tracker (Clean Sub-Rows)...")

if not os.path.exists("recipes.json"):
    print("Error: recipes.json not found!")
    exit(1)

with open("recipes.json", "r", encoding="utf-8-sig") as f:
    recipes = json.load(f)

mapping_url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
prices_url = "https://prices.runescape.wiki/api/v1/osrs/latest"
volume_url = "https://prices.runescape.wiki/api/v1/osrs/volumes"
headers = {"User-Agent": "osrs-crafting-tracker (antarescrane)"}

try:
    print("Fetching live Wiki data...")
    mapping = json.loads(urllib.request.urlopen(urllib.request.Request(mapping_url, headers=headers)).read().decode("utf-8"))
    prices_data = json.loads(urllib.request.urlopen(urllib.request.Request(prices_url, headers=headers)).read().decode("utf-8"))["data"]
    volumes_data = json.loads(urllib.request.urlopen(urllib.request.Request(volume_url, headers=headers)).read().decode("utf-8"))["data"]
    
    def find_id(keyword, exact=False):
        keyword = keyword.lower()
        if exact:
            for item in mapping:
                if item["name"].lower() == keyword:
                    return item["id"], item["name"]
        else:
            for item in mapping:
                name_lower = item["name"].lower()
                if keyword in name_lower and "ornament" not in name_lower:
                    return item["id"], item["name"]
        return None, None

    # --- PART A: ASSEMBLIES & SETS ---
    assembly_results = []
    for recipe in recipes:
        prod_id, prod_fullname = find_id(recipe["product_key"], exact=True)
        if not prod_id:
            prod_id, prod_fullname = find_id(recipe["product_key"], exact=False)
        
        prod_data = prices_data.get(str(prod_id), {}) if prod_id else {}
        sell_offer = prod_data.get("high", 0)  # Instant Sell Offer (Bid)
        
        component_rows = []
        component_total = 0
        for comp in recipe["components"]:
            if "flat_cost" in comp:
                c_cost = comp["flat_cost"]
                component_rows.append({
                    "name": "Assembly Fee",
                    "buy": c_cost
                })
                component_total += c_cost
            else:
                c_id, c_name = find_id(comp["key"], exact=False)
                c_price = prices_data.get(str(c_id), {}).get("low", 0) if c_id else 0  # Instant Buy Offer (Ask)
                mult = comp["mult"]
                subtotal = c_price * mult
                display_name = f"{c_name or comp['key']}" + (f" (x{mult})" if mult > 1 else "")
                component_rows.append({
                    "name": display_name,
                    "buy": subtotal
                })
                component_total += subtotal
        
        chosen_input_cost = component_total
        
        if "hide_alternative" in recipe:
            h_info = recipe["hide_alternative"]
            h_id, h_name = find_id(h_info["key"], exact=False)
            h_price = prices_data.get(str(h_id), {}).get("low", 0) if h_id else 0
            hide_total = h_price * h_info["hides_required"]
            if hide_total > 0 and hide_total < component_total:
                chosen_input_cost = hide_total
                component_rows = [{
                    "name": f"Raw Hides ({h_info['hides_required']}x {h_name})",
                    "buy": hide_total
                }]
        
        ge_tax = int(sell_offer * 0.02) if sell_offer > 0 else 0
        net_revenue = sell_offer - ge_tax
        net_profit = net_revenue - chosen_input_cost
        roi = (net_profit / chosen_input_cost * 100) if chosen_input_cost > 0 else 0
        
        assembly_results.append({
            "name": recipe["name"],
            "buy_offer": chosen_input_cost,
            "sell_offer": sell_offer,
            "tax": -ge_tax,
            "revenue": net_revenue,
            "profit": net_profit,
            "roi": roi,
            "components": component_rows
        })

    assembly_results.sort(key=lambda x: x["profit"], reverse=True)

    # --- PART B: ALL POTION DECANTING ---
    potion_groups = {}
    for item in mapping:
        match = re.search(r"^(.*?)\s+\(([1-4])\)$", item["name"])
        if match:
            b_name = match.group(1).strip()
            dose = int(match.group(2))
            if b_name not in potion_groups:
                potion_groups[b_name] = {}
            potion_groups[b_name][dose] = (item["id"], item["name"])

    potion_results = []
    for base_name, doses in potion_groups.items():
        if 4 not in doses:
            continue
        sell_4_id, sell_4_fullname = doses[4]
        sell_4_price = prices_data.get(str(sell_4_id), {}).get("high", 0)
        sell_4_vol = volumes_data.get(str(sell_4_id), 0)
        if sell_4_price == 0:
            continue
        
        source_options = {}
        for d in range(1, 4):
            if d in doses:
                p_id, p_fullname = doses[d]
                p = prices_data.get(str(p_id), {}).get("low", 0)
                if p > 0:
                    source_options[d] = {"price": p, "name": p_fullname}
        
        if not source_options:
            continue
        
        best_dose = min(source_options, key=lambda d: source_options[d]["price"] / d)
        best_info = source_options[best_dose]
        cost_per_unit = best_info["price"] / best_dose
        total_input = int(cost_per_unit * 4)
        ge_tax = int(sell_4_price * 0.02)
        net_revenue = sell_4_price - ge_tax
        profit = net_revenue - total_input
        roi = (profit / total_input * 100) if total_input > 0 else 0
        
        potion_results.append({
            "potion": base_name,
            "strategy": f"Buy 4x ({best_dose}) [{best_info['name']}]",
            "volume": sell_4_vol,
            "buy_offer": total_input,
            "sell_offer": sell_4_price,
            "tax": -ge_tax,
            "revenue": net_revenue,
            "profit": profit,
            "roi": roi
        })

    potion_results.sort(key=lambda x: (x["profit"], x["volume"]), reverse=True)
    current_time_str = datetime.now().strftime("%I:%M:%S %p")

    # --- PART C: HTML GENERATION ---
    print("Generating index.html...")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OSRS Market Opportunity Tracker</title>
    <style>
        body {{ background-color: #121212; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; margin: 0; }}
        h1 {{ color: #ffa500; font-size: 24px; margin-bottom: 15px; }}
        .header-bar {{ display: flex; align-items: center; gap: 15px; margin-bottom: 25px; background: #1a1a1a; padding: 12px 15px; border-radius: 6px; border: 1px solid #333; }}
        .btn {{ background-color: #28a745; color: white; border: none; padding: 8px 16px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
        .btn:hover {{ background-color: #218838; }}
        select {{ background: #252525; color: #fff; border: 1px solid #444; padding: 6px 10px; border-radius: 4px; }}
        h2 {{ color: #ffa500; font-size: 18px; margin-top: 30px; margin-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; background: #181818; border-radius: 6px; overflow: hidden; font-size: 14px; margin-bottom: 30px; }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #282828; }}
        th {{ background-color: #1f1f1f; color: #ffcc00; font-weight: 600; font-size: 13px; text-transform: uppercase; }}
        .main-row {{ background: #1c1c1c; font-weight: bold; }}
        .main-row:hover {{ background: #252525; }}
        .sub-row {{ background: #151515; color: #aaa; font-size: 13px; }}
        .sub-row:hover {{ background: #1c1c1c; }}
        .pos {{ color: #4ecca3; font-weight: bold; }}
        .neg {{ color: #ff6b6b; font-weight: bold; }}
        .muted {{ color: #666; }}
    </style>
</head>
<body>
    <h1>OSRS Market Opportunity Tracker</h1>
    
    <div class="header-bar">
        <button class="btn" onclick="location.reload()">Refresh Live Prices</button>
        <div>Assembly Sort: <select id="asmSort"><option>Net Profit (High to Low)</option><option>ROI % (High to Low)</option></select></div>
        <div>Potion Sort: <select id="potSort"><option>Custom Score (Volume + Margin)</option><option>Net Profit (High to Low)</option></select></div>
        <div class="muted" style="margin-left: auto;">Updated at {current_time_str}</div>
    </div>

    <h2>Item Assembly Margins</h2>
    <table>
        <tr>
            <th>Item / Component</th>
            <th>Buy Offer (Low)</th>
            <th>Sell Offer (High)</th>
            <th>GE Tax (2%)</th>
            <th>Net Revenue</th>
            <th>Net Profit</th>
            <th>ROI %</th>
        </tr>"""

    for r in assembly_results:
        p_cls = "pos" if r["profit"] >= 0 else "neg"
        html += f"""
        <tr class="main-row">
            <td>{r['name']}</td>
            <td>{r['buy_offer']:,} GP</td>
            <td>{r['sell_offer']:,} GP</td>
            <td class="neg">{r['tax']:,} GP</td>
            <td>{r['revenue']:,} GP</td>
            <td class="{p_cls}">{r['profit']:,} GP</td>
            <td class="{p_cls}">{r['roi']:.1f}%</td>
        </tr>"""
        for comp in r["components"]:
            html += f"""
        <tr class="sub-row">
            <td style="padding-left: 30px;">{comp['name']}</td>
            <td>{comp['buy']:,}</td>
            <td class="muted">-</td>
            <td class="muted">-</td>
            <td class="muted">-</td>
            <td class="muted">-</td>
            <td class="muted">-</td>
        </tr>"""

    html += """
    </table>

    <h2>Potion Decanting Arbitrage</h2>
    <table>
        <tr>
            <th>Potion Name / Strategy</th>
            <th>24h Volume</th>
            <th>Buy Offer (Low)</th>
            <th>Sell Offer (High)</th>
            <th>GE Tax (2%)</th>
            <th>Net Revenue</th>
            <th>Net Profit</th>
            <th>ROI %</th>
        </tr>"""

    for r in potion_results:
        p_cls = "pos" if r["profit"] >= 0 else "neg"
        html += f"""
        <tr class="main-row">
            <td><b>{r['potion']}</b><br><span style="font-size:12px; color:#888;">{r['strategy']}</span></td>
            <td>{r['volume']:,}</td>
            <td>{r['buy_offer']:,} GP</td>
            <td>{r['sell_offer']:,} GP</td>
            <td class="neg">{r['tax']:,} GP</td>
            <td>{r['revenue']:,} GP</td>
            <td class="{p_cls}">{r['profit']:,} GP</td>
            <td class="{p_cls}">{r['roi']:.1f}%</td>
        </tr>"""

    html += """
    </table>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Successfully generated clean index.html!")

except Exception as e:
    print("Error during site generation:", e)
