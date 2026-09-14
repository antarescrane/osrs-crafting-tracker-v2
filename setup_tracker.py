import os

print("Writing OSRS tracker files...")

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSRS Item Assembly & Flip Margins Tracker</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <div class="header-title">
                <h1><i class="fa-solid fa-coins"></i> OSRS Assembly & Flip Margins</h1>
                <span class="live-badge"><span class="pulse-dot"></span> Live Wiki API Connected</span>
            </div>
            <div class="header-controls">
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <input type="text" id="searchInput" placeholder="Search item or component...">
                </div>
                <button id="refreshBtn" class="btn-refresh" title="Force Refresh Prices">
                    <i class="fa-solid fa-rotate"></i> Refresh
                </button>
            </div>
        </header>

        <div class="status-bar" id="statusBar">
            Fetching latest mapping and pricing data from OSRS Wiki API...
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table id="marginsTable">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="name">Item / Component <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="buy">Buy Offer (Low) <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="sell">Sell Offer (High) <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="tax">GE Tax (2%) <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="revenue">Net Revenue <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="profit">Net Profit <i class="fa-solid fa-sort"></i></th>
                            <th class="sortable text-right" data-sort="roi">ROI % <i class="fa-solid fa-sort"></i></th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>
    </div>
    <script src="app.js"></script>
</body>
</html>
"""

css_content = """:root {
    --bg-color: #121418;
    --card-bg: #1a1d24;
    --border-color: #2a2e39;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --accent-gold: #f59e0b;
    --green-profit: #22c55e;
    --red-loss: #ef4444;
    --row-hover: #222632;
    --child-bg: #161920;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background-color: var(--bg-color); color: var(--text-primary); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; padding: 24px; }
.app-container { max-width: 1400px; margin: 0 auto; }
.app-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 16px; }
.header-title { display: flex; align-items: center; gap: 16px; }
.header-title h1 { font-size: 20px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
.header-title h1 i { color: var(--accent-gold); }
.live-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.1); color: var(--green-profit); padding: 4px 10px; border-radius: 20px; font-size: 12px; border: 1px solid rgba(34, 197, 94, 0.2); }
.pulse-dot { width: 8px; height: 8px; background-color: var(--green-profit); border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); } }
.header-controls { display: flex; gap: 12px; align-items: center; }
.search-box { position: relative; }
.search-box i { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-secondary); }
.search-box input { background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-primary); padding: 8px 12px 8px 36px; border-radius: 6px; outline: none; width: 260px; }
.search-box input:focus { border-color: var(--accent-gold); }
.btn-refresh { background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-primary); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; display: flex; align-items: center; gap: 8px; }
.btn-refresh:hover { background: var(--row-hover); border-color: var(--text-secondary); }
.status-bar { background: var(--card-bg); border: 1px solid var(--border-color); padding: 10px 16px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; color: var(--text-secondary); }
.table-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.table-responsive { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; white-space: nowrap; }
th, td { padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
th { background: #16181f; color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; cursor: pointer; }
th:hover { color: var(--text-primary); }
tbody tr.parent-row:hover { background-color: var(--row-hover); }
tbody tr.component-row { background-color: var(--child-bg); color: var(--text-secondary); font-size: 13px; }
tbody tr.component-row:hover { background-color: #1a1e28; }
.text-right { text-align: right; }
.text-profit { color: var(--green-profit); font-weight: 600; }
.text-loss { color: var(--red-loss); font-weight: 600; }
.muted { color: var(--text-secondary); }
.component-icon { display: inline-block; width: 20px; text-align: center; color: var(--border-color); margin-right: 6px; }
"""

js_content = """const ASSEMBLIES = [
    {
        name: "Necklace of Rupture",
        id: 33639,
        taxCap: 5000000,
        components: [
            { name: "Necklace of Anguish", id: 19535, quantity: 1 },
            { name: "Etched Araxyte Fang", id: 33534, quantity: 1 }
        ]
    },
    {
        name: "Amulet of Rancour",
        id: 29801,
        taxCap: 5000000,
        components: [
            { name: "Amulet of Torture", id: 19553, quantity: 1 },
            { name: "Etched Araxyte Fang", id: 33534, quantity: 1 }
        ]
    },
    {
        name: "Venator Bow",
        id: 27612,
        taxCap: 5000000,
        components: [
            { name: "Venator Shard", id: 27614, quantity: 5 }
        ]
    },
    {
        name: "Kodai Wand",
        id: 21006,
        taxCap: 5000000,
        components: [
            { name: "Master Wand", id: 6914, quantity: 1 },
            { name: "Kodai Insignia", id: 21047, quantity: 1 }
        ]
    },
    {
        name: "Voidwalker",
        id: 27602,
        taxCap: 5000000,
        components: [
            { name: "Assembly Fee", id: null, quantity: 1, fixedPrice: 500000 },
            { name: "Voidwalker Hilt", id: 27606, quantity: 1 },
            { name: "Voidwalker Blade", id: 27604, quantity: 1 },
            { name: "Voidwalker Gem", id: 27608, quantity: 1 }
        ]
    }
];

let mappingData = {};
let latestPrices = {};
let currentSort = { column: 'profit', ascending: false };
let searchTerm = '';

const statusBar = document.getElementById('statusBar');
const tableBody = document.getElementById('tableBody');
const searchInput = document.getElementById('searchInput');
const refreshBtn = document.getElementById('refreshBtn');

async function initTracker() {
    statusBar.textContent = 'Connecting to OSRS Wiki API...';
    try {
        const [mappingRes, pricesRes] = await Promise.all([
            fetch('https://prices.runescape.wiki/api/v1/osrs/mapping', { headers: { 'User-Agent': 'OSRS Tracker' } }),
            fetch('https://prices.runescape.wiki/api/v1/osrs/latest', { headers: { 'User-Agent': 'OSRS Tracker' } })
        ]);
        const mappingJson = await mappingRes.json();
        const pricesJson = await pricesRes.json();

        mappingData = {};
        mappingJson.forEach(item => { mappingData[item.name.toLowerCase()] = item.id; });
        latestPrices = pricesJson.data;
        statusBar.textContent = `Synced at ${new Date().toLocaleTimeString()}.`;
        renderTable();
    } catch (err) {
        statusBar.textContent = `Error: ${err.message}`;
        renderTable();
    }
}

function getItemPrice(name, id, type) {
    let resolvedId = id || mappingData[name.toLowerCase()];
    return resolvedId && latestPrices[resolvedId] ? latestPrices[resolvedId][type] || 0 : 0;
}

function calculateAssemblyData() {
    return ASSEMBLIES.map(assembly => {
        let parentId = assembly.id || mappingData[assembly.name.toLowerCase()];
        const parentSellHigh = parentId && latestPrices[parentId] ? latestPrices[parentId].high : 0;
        const parentBuyLow = parentId && latestPrices[parentId] ? latestPrices[parentId].low : 0;

        let totalComponentCost = 0;
        const evaluatedComponents = assembly.components.map(comp => {
            let unitCost = comp.fixedPrice ? comp.fixedPrice : getItemPrice(comp.name, comp.id, 'high');
            let totalCost = unitCost * comp.quantity;
            totalComponentCost += totalCost;
            return { ...comp, unitCost, totalCost };
        });

        let tax = parentSellHigh > 0 ? Math.min(parentSellHigh * 0.02, assembly.taxCap || 5000000) : 0;
        let netRevenue = parentSellHigh > 0 ? parentSellHigh - tax : 0;
        let netProfit = parentSellHigh > 0 && totalComponentCost > 0 ? netRevenue - totalComponentCost : 0;
        let roi = totalComponentCost > 0 && parentSellHigh > 0 ? (netProfit / totalComponentCost) * 100 : 0;

        return { ...assembly, parentBuyLow, parentSellHigh, totalComponentCost, tax, netRevenue, netProfit, roi, components: evaluatedComponents };
    });
}

function formatGP(val) { return !val ? '-' : val.toLocaleString(); }
function formatROI(val) { return !val ? '-' : val.toFixed(1) + '%'; }

function renderTable() {
    let data = calculateAssemblyData();
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        data = data.filter(item => item.name.toLowerCase().includes(term) || item.components.some(c => c.name.toLowerCase().includes(term)));
    }
    data.sort((a, b) => {
        let valA = a[currentSort.column], valB = b[currentSort.column];
        if (typeof valA === 'string') { valA = valA.toLowerCase(); valB = valB.toLowerCase(); }
        return valA < valB ? (currentSort.ascending ? -1 : 1) : valA > valB ? (currentSort.ascending ? 1 : -1) : 0;
    });

    tableBody.innerHTML = '';
    if (data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="muted" style="text-align: center; padding: 24px;">No matches found.</td></tr>`;
        return;
    }

    data.forEach(item => {
        const pClass = item.netProfit > 0 ? 'text-profit' : item.netProfit < 0 ? 'text-loss' : 'muted';
        const rClass = item.roi > 0 ? 'text-profit' : item.roi < 0 ? 'text-loss' : 'muted';

        tableBody.innerHTML += `
            <tr class="parent-row">
                <td><strong>${item.name}</strong></td>
                <td class="text-right">${formatGP(item.parentBuyLow)}</td>
                <td class="text-right">${formatGP(item.parentSellHigh)}</td>
                <td class="text-right muted">${item.tax > 0 ? '-' + formatGP(Math.round(item.tax)) : '-'}</td>
                <td class="text-right">${formatGP(Math.round(item.netRevenue))}</td>
                <td class="text-right ${pClass}">${item.netProfit ? formatGP(Math.round(item.netProfit)) + ' GP' : '-'}</td>
                <td class="text-right ${rClass}">${formatROI(item.roi)}</td>
            </tr>`;
        item.components.forEach(comp => {
            tableBody.innerHTML += `
                <tr class="component-row">
                    <td><span class="component-icon">❖❖❖</span> ${comp.name}${comp.quantity > 1 ? ` (x${comp.quantity})` : ''}</td>
                    <td class="text-right">${formatGP(comp.unitCost)}</td>
                    <td class="text-right muted">-</td><td class="text-right muted">-</td><td class="text-right muted">-</td><td class="text-right muted">-</td><td class="text-right muted">-</td>
                </tr>`;
        });
    });
}

document.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        currentSort.ascending = currentSort.column === col ? !currentSort.ascending : col === 'name';
        currentSort.column = col;
        renderTable();
    });
});
searchInput.addEventListener('input', e => { searchTerm = e.target.value; renderTable(); });
refreshBtn.addEventListener('click', initTracker);
initTracker();
"""

with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
with open("style.css", "w", encoding="utf-8") as f: f.write(css_content)
with open("app.js", "w", encoding="utf-8") as f: f.write(js_content)
print("Files created successfully!")
