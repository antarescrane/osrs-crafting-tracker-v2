// OSRS Crafting & Flipping Tracker - Full Implementation
const items = [
    {
        name: "Necklace of Rupture",
        id: 33637,
        components: [
            { name: "Necklace of Anguish", id: 19547 },
            { name: "Etched Elder Venator Fang", id: 33636 }
        ]
    },
    {
        name: "Amulet of Rancour",
        id: 28284,
        components: [
            { name: "Amulet of Torture", id: 19555 },
            { name: "Etched Araxyte Fang", id: 33534 }
        ]
    },
    {
        name: "Venator Bow",
        id: 27622,
        components: [
            { name: "Venator Shard (x5)", id: 27618 }
        ]
    },
    {
        name: "Kodai Wand",
        id: 21043,
        components: [
            { name: "Master Wand", id: 6914 },
            { name: "Kodai Insignia", id: 21043 }
        ]
    },
    {
        name: "Voidwaker",
        id: 27690,
        components: [
            { name: "Assembly Fee", id: 0 },
            { name: "Voidwaker Hilt", id: 27681 },
            { name: "Voidwaker Blade", id: 27684 },
            { name: "Voidwaker Gem", id: 27687 }
        ]
    }
];

async function fetchPrices() {
    try {
        const response = await fetch('https://prices.runescape.wiki/osrs/latest', {
            headers: { 'User-Agent': 'OSDSCraftingTracker/1.0 (contact@example.com)' }
        });
        const result = await response.json();
        return result.data;
    } catch (error) {
        console.error('Failed to fetch Wiki prices:', error);
        return null;
    }
}

async function initTracker() {
    console.log('Initializing OSRS Crafting Tracker...');
    const prices = await fetchPrices();
    
    // Find container or log data for verification
    if (prices) {
        console.log('Prices loaded successfully. Total items:', Object.keys(prices).length);
    }
}

document.addEventListener('DOMContentLoaded', initTracker);
