import urllib.request
import json
import os

if not os.path.exists('recipes.json'):
    print('Error: recipes.json not found!')
    exit(1)

with open('recipes.json', 'r', encoding='utf-8-sig') as f:
    recipes = json.load(f)

mapping_url = 'https://prices.runescape.wiki/api/v1/osrs/mapping'
req = urllib.request.Request(mapping_url, headers={'User-Agent': 'osrs-crafting-tracker (antarescrane)'})

GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

try:
    with urllib.request.urlopen(req) as response:
        mapping = json.loads(response.read().decode('utf-8'))
        
        def find_id(keyword, exact=False):
            keyword = keyword.lower()
            if exact:
                for item in mapping:
                    if item['name'].lower() == keyword:
                        return item['id'], item['name']
            else:
                for item in mapping:
                    name_lower = item['name'].lower()
                    if keyword in name_lower and 'ornament' not in name_lower:
                        return item['id'], item['name']
            return None, None

        prices_url = 'https://prices.runescape.wiki/api/v1/osrs/latest'
        prices_req = urllib.request.Request(prices_url, headers={'User-Agent': 'osrs-crafting-tracker (antarescrane)'})
        
        with urllib.request.urlopen(prices_req) as p_response:
            prices = json.loads(p_response.read().decode('utf-8'))['data']
            
            evaluated_results = []
            
            for recipe in recipes:
                prod_id, prod_fullname = find_id(recipe["product_key"], exact=True)
                if not prod_id:
                    prod_id, prod_fullname = find_id(recipe["product_key"], exact=False)
                
                prod_data = prices.get(str(prod_id), {}) if prod_id else {}
                sell_price = prod_data.get('high', 0)
                
                component_total = 0
                comp_lines = []
                
                for comp in recipe["components"]:
                    if "flat_cost" in comp:
                        flat_price = comp["flat_cost"]
                        component_total += flat_price
                        comp_lines.append(f'  - {comp["name"]} [Fee]: {flat_price:,} GP')
                    else:
                        c_id, c_fullname = find_id(comp["key"], exact=False)
                        c_data = prices.get(str(c_id), {}) if c_id else {}
                        c_price = c_data.get('low', 0)
                        multiplier = comp["mult"]
                        
                        total_c_price = c_price * multiplier
                        component_total += total_c_price
                        
                        mult_str = f" (x{multiplier})" if multiplier > 1 else ""
                        comp_lines.append(f'  - {c_fullname}{mult_str} [ID {c_id}]: {c_price:,} GP -> {total_c_price:,} GP')
                
                # Evaluate alternative sourcing if defined (e.g., raw hides)
                chosen_input_cost = component_total
                sourcing_method = "Pre-crafted Individual Parts"
                
                if "hide_alternative" in recipe:
                    h_info = recipe["hide_alternative"]
                    h_id, h_fullname = find_id(h_info["key"], exact=False)
                    h_data = prices.get(str(h_id), {}) if h_id else {}
                    h_price = h_data.get('low', 0)
                    h_req = h_info["hides_required"]
                    hide_total_cost = h_price * h_req
                    
                    comp_lines.append(f'  -----------------------------------------')
                    comp_lines.append(f'  [Alt Option] {h_fullname} (x{h_req}) [ID {h_id}]: {h_price:,} GP -> {hide_total_cost:,} GP total')
                    
                    if hide_total_cost > 0 and hide_total_cost < component_total:
                        chosen_input_cost = hide_total_cost
                        sourcing_method = "Raw Hides (Crafted into Set)"
                    else:
                        sourcing_method = "Individual Armour Pieces (Boxed into Set)"
                
                ge_tax = int(sell_price * 0.02) if sell_price > 0 else 0
                net_revenue = sell_price - ge_tax
                net_profit = net_revenue - chosen_input_cost
                roi = (net_profit / chosen_input_cost * 100) if chosen_input_cost > 0 else 0
                
                evaluated_results.append({
                    "name": recipe["name"],
                    "prod_fullname": prod_fullname or recipe["name"],
                    "prod_id": prod_id,
                    "comp_lines": comp_lines,
                    "component_total": chosen_input_cost,
                    "sourcing_method": sourcing_method,
                    "sell_price": sell_price,
                    "ge_tax": ge_tax,
                    "net_profit": net_profit,
                    "roi": roi
                })
            
            evaluated_results.sort(key=lambda x: x["net_profit"], reverse=True)
            
            print(f'{BOLD}=== OSRS MARGIN & OPTIMAL SET ASSEMBLY REPORT ==={RESET}\n')
            
            for res in evaluated_results:
                color = GREEN if res["net_profit"] >= 0 else RED
                print(f'{BOLD}=== {res["name"]} -> Resolved: "{res["prod_fullname"]}" (ID: {res["prod_id"]}) ==={RESET}')
                for line in res["comp_lines"]:
                    print(line)
                print(f'  * Optimal Sourcing Choice: {CYAN}{res["sourcing_method"]}{RESET}')
                print(f'  * Lowest Input Cost:     {res["component_total"]:,} GP')
                print(f'  * Set Box Sell Price:    {res["sell_price"]:,} GP')
                print(f'  * GE Tax (2%):           {res["ge_tax"]:,} GP')
                print(f'  * {color}Net Profit:            {res["net_profit"]:,} GP ({res["roi"]:.2f}% ROI){RESET}\n')

except Exception as e:
    print('Error:', e)
