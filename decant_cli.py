import urllib.request
import json
import re

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
        
        # Group items by base potion name
        potion_groups = {}
        for item in mapping:
            name = item['name']
            match = re.search(r'^(.*?)\s+\(([1-4])\)$', name)
            if match:
                base_name = match.group(1).strip()
                dose = int(match.group(2))
                if base_name not in potion_groups:
                    potion_groups[base_name] = {}
                potion_groups[base_name][dose] = {'id': item['id'], 'name': name}

        prices_url = 'https://prices.runescape.wiki/api/v1/osrs/latest'
        prices_req = urllib.request.Request(prices_url, headers={'User-Agent': 'osrs-crafting-tracker (antarescrane)'})
        
        volume_url = 'https://prices.runescape.wiki/api/v1/osrs/volumes'
        volume_req = urllib.request.Request(volume_url, headers={'User-Agent': 'osrs-crafting-tracker (antarescrane)'})
        
        with urllib.request.urlopen(prices_req) as p_resp, urllib.request.urlopen(volume_req) as v_resp:
            prices_data = json.loads(p_resp.read().decode('utf-8'))['data']
            volumes_data = json.loads(v_resp.read().decode('utf-8'))['data']
            
            results = []
            
            for base_name, doses in potion_groups.items():
                # We must have the 4-dose variant to sell into
                if 4 not in doses:
                    continue
                
                sell_4_id = doses[4]['id']
                sell_4_data = prices_data.get(str(sell_4_id), {})
                sell_4_price = sell_4_data.get('high', 0)
                sell_4_vol = volumes_data.get(str(sell_4_id), 0)
                
                if sell_4_price == 0:
                    continue
                
                # Check available source doses (1, 2, or 3) to buy from
                source_options = {}
                for d in range(1, 4):
                    if d in doses:
                        item_id = doses[d]['id']
                        p_info = prices_data.get(str(item_id), {})
                        price = p_info.get('low', 0)
                        if price > 0:
                            source_options[d] = price
                
                if not source_options:
                    continue
                
                # Find which source dose gives the cheapest cost per individual dose unit
                best_source_dose = None
                lowest_cost_per_unit = float('inf')
                
                for d, price in source_options.items():
                    cost_per_unit = price / d
                    if cost_per_unit < lowest_cost_per_unit:
                        lowest_cost_per_unit = cost_per_unit
                        best_source_dose = d
                
                buy_price = source_options[best_source_dose]
                
                # Cost to assemble a full 4-dose potion from the optimal source dose
                total_input_cost = int(lowest_cost_per_unit * 4)
                
                # Apply 2% GE Tax on the final 4-dose sale price
                ge_tax = int(sell_4_price * 0.02)
                net_revenue = sell_4_price - ge_tax
                profit_per_4dose = net_revenue - total_input_cost
                roi = (profit_per_4dose / total_input_cost * 100) if total_input_cost > 0 else 0
                
                if profit_per_4dose <= 0:
                    continue
                
                results.append({
                    "potion": base_name,
                    "strategy": f"Buy ({best_source_dose}) @ {buy_price:,} gp",
                    "volume": sell_4_vol,
                    "input_cost": total_input_cost,
                    "sell_price": sell_4_price,
                    "profit": profit_per_4dose,
                    "roi": roi
                })
            
            # Sort by profit and 4-dose volume descending
            results.sort(key=lambda x: (x["profit"], x["volume"]), reverse=True)
            
            print(f'{BOLD}=== OSRS POTION DECANTING ARBITRAGE (TARGETING 4-DOSE SALES) ==={RESET}\n')
            print(f"{'POTION':<26} | {'OPTIMAL BUY STRATEGY':<22} | {'4D VOL':<8} | {'COST':<8} | {'SELL (4D)':<9} | {'PROFIT':<8} | {'ROI'} ")
            print("-" * 105)
            
            for r in results:
                color = GREEN if r["profit"] >= 0 else RED
                print(f"{r['potion']:<26} | {r['strategy']:<22} | {r['volume']:<8,} | {r['input_cost']:<8,} | {r['sell_price']:<9,} | {color}{r['profit']:<8,}{RESET} | {r['roi']:.1f}%")

except Exception as e:
    print('Error:', e)
