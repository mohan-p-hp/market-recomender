// Get references to all HTML elements
const form = document.getElementById('recommend-form');
const latInput = document.getElementById('lat');
const lonInput = document.getElementById('lon');
const commodityInput = document.getElementById('commodity');
const quantityInput = document.getElementById('quantity');
const dateInput = document.getElementById('date');
const resultsContainer = document.getElementById('results-container');
const villageInput = document.getElementById('village-name');
const geocodeBtn = document.getElementById('geocode-btn');
const geocodeStatus = document.getElementById('geocode-status');

// Set default date to tomorrow
const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);
dateInput.value = tomorrow.toISOString().split('T')[0];

// Event listener for the "Find" (geocode) button
geocodeBtn.addEventListener('click', async () => {
    const villageName = villageInput.value;
    if (!villageName) {
        geocodeStatus.textContent = 'Please enter a location name.';
        geocodeStatus.style.color = 'orange';
        return;
    }
    geocodeStatus.textContent = 'Searching...';
    geocodeStatus.style.color = 'black';

    const apiUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(villageName)}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        if (data && data.length > 0) {
            const bestResult = data[0];
            latInput.value = parseFloat(bestResult.lat).toFixed(4);
            lonInput.value = parseFloat(bestResult.lon).toFixed(4);
            geocodeStatus.textContent = `Location found: ${bestResult.display_name}`;
            geocodeStatus.style.color = 'green';
        } else {
            geocodeStatus.textContent = 'Location not found. Please try a more specific name.';
            geocodeStatus.style.color = 'red';
        }
    } catch (error) {
        geocodeStatus.textContent = 'Error fetching location.';
        geocodeStatus.style.color = 'red';
        console.error('Geocoding error:', error);
    }
});

// Event listener for the main form submission
form.addEventListener('submit', async (event) => {
    event.preventDefault(); 
    resultsContainer.innerHTML = '<p>Fetching forecast...</p>';
    
    const requestData = {
        farmer_lat: parseFloat(latInput.value),
        farmer_lon: parseFloat(lonInput.value),
        commodity: commodityInput.value,
        quantity_tonnes: parseFloat(quantityInput.value),
        selected_date: dateInput.value
    };
    
    try {
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(requestData)
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        displayGroupedResults(data.recommendations);
    } catch (error) {
        resultsContainer.innerHTML = `<p style="color:red;">Error: Could not fetch recommendations. Is the Python server running?</p>`;
        console.error('Fetch error:', error);
    }
});

function displayGroupedResults(recommendations) {
    resultsContainer.innerHTML = ''; 
    if (!recommendations || recommendations.length === 0) {
        resultsContainer.innerHTML = '<p>No recommendations found.</p>';
        return;
    }

    const overallBest = recommendations.reduce((best, current) => (current.net_profit > best.net_profit) ? current : best);
    const bestOptionDiv = document.createElement('div');
    bestOptionDiv.className = 'overall-best';
    bestOptionDiv.innerHTML = `💡 <strong>Overall Best Option</strong>: Sell at <strong>${overallBest.market_name}</strong> on <strong>${new Date(overallBest.date).toDateString()}</strong> for an estimated profit of <strong>₹${overallBest.net_profit.toFixed(0)}</strong>!`;
    resultsContainer.appendChild(bestOptionDiv);

    const groupedByDate = recommendations.reduce((acc, rec) => {
        (acc[rec.date] = acc[rec.date] || []).push(rec);
        return acc;
    }, {});

    for (const date in groupedByDate) {
        const dateHeader = document.createElement('h2');
        const formattedDate = new Date(date).toDateString();
        dateHeader.textContent = `🗓️ Recommendations for ${formattedDate}`;
        resultsContainer.appendChild(dateHeader);

        const dailyRecs = groupedByDate[date].sort((a, b) => b.net_profit - a.net_profit);
        dailyRecs.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.innerHTML = `
                <h3>${rec.market_name}</h3>
                <p><strong>Net Profit:</strong> ₹${rec.net_profit.toFixed(0)}</p>
                <p><strong>Distance:</strong> ${rec.distance_km} km</p>
                <p><strong>Predicted Price:</strong> ₹${rec.predicted_price_kg}/kg</p>
            `;
            resultsContainer.appendChild(card);
        });
    }
}