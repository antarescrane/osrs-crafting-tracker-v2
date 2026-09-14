const ASSEMBLIES = [
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
