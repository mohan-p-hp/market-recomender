// script.js

// Get references to all HTML elements, including the new date input
const form = document.getElementById('recommend-form');
const latInput = document.getElementById('lat');
const lonInput = document.getElementById('lon');
const commodityInput = document.getElementById('commodity');
const quantityInput = document.getElementById('quantity');
const dateInput = document.getElementById('date'); // Get the date input
const resultsContainer = document.getElementById('results-container');

// Set a default date for the input field (tomorrow) for better user experience
const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);
// Format the date as YYYY-MM-DD for the input field
dateInput.value = tomorrow.toISOString().split('T')[0];


// Listen for the form submission event
form.addEventListener('submit', async (event) => {
    // Prevent the default browser action of reloading the page
    event.preventDefault(); 
    resultsContainer.innerHTML = '<p>Fetching forecast...</p>';
    
    // 1. Prepare the data to send to the Python API
    const requestData = {
        farmer_lat: parseFloat(latInput.value),
        farmer_lon: parseFloat(lonInput.value),
        commodity: commodityInput.value,
        quantity_tonnes: parseFloat(quantityInput.value),
        selected_date: dateInput.value // --- THIS IS THE FIX --- Add the date to the request
    };
    
    console.log('Sending this data to API:', requestData); // For debugging

    // 2. Send the data to your FastAPI backend
    try {
        const response = await fetch('http://127.0.0.1:8000/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        
        // 3. Display the results on the page using the updated display function
        displayGroupedResults(data.recommendations);

    } catch (error) {
        resultsContainer.innerHTML = `<p style="color:red;">Error: Could not fetch recommendations. Is the Python server running?</p>`;
        console.error('Fetch error:', error);
    }
});

// MODIFIED: This function can now handle and group the 3-day forecast data
function displayGroupedResults(recommendations) {
    resultsContainer.innerHTML = ''; 

    if (!recommendations || recommendations.length === 0) {
        resultsContainer.innerHTML = '<p>No recommendations found.</p>';
        return;
    }

    // Group recommendations by date
    const groupedByDate = recommendations.reduce((acc, rec) => {
        (acc[rec.date] = acc[rec.date] || []).push(rec);
        return acc;
    }, {});

    // Find and display the overall best option from all days
    const overallBest = recommendations.reduce((best, current) => (current.net_profit > best.net_profit) ? current : best);
    const bestOptionDiv = document.createElement('div');
    bestOptionDiv.className = 'overall-best';
    bestOptionDiv.innerHTML = `💡 <strong>Overall Best Option</strong>: Sell at <strong>${overallBest.market_name}</strong> on <strong>${new Date(overallBest.date).toDateString()}</strong> for an estimated profit of <strong>₹${overallBest.net_profit.toFixed(0)}</strong>!`;
    resultsContainer.appendChild(bestOptionDiv);


    // Display results for each day, grouped under a date heading
    for (const date in groupedByDate) {
        const dateHeader = document.createElement('h2');
        const formattedDate = new Date(date).toDateString();
        dateHeader.textContent = `🗓️ Recommendations for ${formattedDate}`;
        resultsContainer.appendChild(dateHeader);

        // Sort markets for that specific day by profit
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