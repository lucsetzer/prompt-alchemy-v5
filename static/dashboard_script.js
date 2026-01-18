// dashboard_script.js
console.log('✅ Dashboard script loaded!');

// Logout function
function logout() {
    console.log('Logging out...');
    document.cookie = "session_token=; path=/; max-age=0;";
    window.location.href = "/";
}

// Token purchase simulation
function buyTokens(packName, tokens, price) {
    console.log(`Buying ${packName}: ${tokens} tokens for $${price}`);
    alert(`In production, this would process payment for ${tokens} tokens.`);
    // In production: Redirect to payment processor
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Add click handlers to token pack buttons
    document.querySelectorAll('.token-pack').forEach(button => {
        button.addEventListener('click', function() {
            const pack = this.dataset.pack;
            const tokens = this.dataset.tokens;
            const price = this.dataset.price;
            buyTokens(pack, tokens, price);
        });
    });
    
    // Add click handler to logout button if it exists
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});
