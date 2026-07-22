// Discord OAuth2 configuration
const CLIENT_ID = '924666357050654790';
const CLIENT_SECRET = 'U4aqbYro1uDj6NUwTJmz7f4zry3injZ6'; // Add this from Discord Developer Portal

const REDIRECT_URI = 'http://localhost:5173'; // Update this with your actual redirect URI
const DISCORD_ENDPOINT = `https://discord.com/api/oauth2/authorize?client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code&scope=identify`;

// DOM Elements
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const userInfo = document.getElementById('userInfo');
const loginCard = document.querySelector('.login-card');
const avatarImg = document.getElementById('avatar');
const usernameText = document.getElementById('username');

// Event Listeners
loginBtn.addEventListener('click', () => {
    window.location.href = DISCORD_ENDPOINT;
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('discord_token');
    showLoginCard();
});



// Update the load event listener
window.addEventListener('load', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    // if local storage contains token, fetch user data
    if (localStorage.getItem('discord_token')) {
        checkAndDisplayUser();
    } else if (code) {
        try {
            // Exchange code for access token
            const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
                method: 'POST',
                body: new URLSearchParams({
                    client_id: CLIENT_ID,
                    client_secret: CLIENT_SECRET,
                    code,
                    grant_type: 'authorization_code',
                    redirect_uri: REDIRECT_URI,
                    scope: 'identify',
                }),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            const tokenData = await tokenResponse.json();
            
            // Get user data using access token
            const userResponse = await fetch('https://discord.com/api/users/@me', {
                headers: {
                    Authorization: `Bearer ${tokenData.access_token}`,
                },
            });

            const userData = await userResponse.json();
            
            // Display actual user data
            showUserInfo({
                username: userData.username,
                avatar: `https://cdn.discordapp.com/avatars/${userData.id}/${userData.avatar}.png`,
            });

            // Store token securely
            localStorage.setItem('discord_token', tokenData.access_token);
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to authenticate with Discord');
        }
    }
});

function showUserInfo(user) {
    loginCard.style.display = 'none';
    userInfo.style.display = 'block';
    avatarImg.src = user.avatar;
    usernameText.textContent = user.username;
}

function showLoginCard() {
    loginCard.style.display = 'block';
    userInfo.style.display = 'none';
}

// Important Note:
// This is a basic frontend implementation. In a production environment, you would need:
// 1. A backend server to handle the OAuth token exchange
// 2. Secure storage of client secret
// 3. Proper session management
// 4. CSRF protection
// 5. Proper error handling
// ...existing code...

// Add check token and fetch user function
async function checkAndDisplayUser() {
    const token = localStorage.getItem('discord_token');
    if (token) {
        try {
            const userResponse = await fetch('https://discord.com/api/users/@me', {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            const userData = await userResponse.json();
            showUserInfo({
                username: userData.username,
                avatar: `https://cdn.discordapp.com/avatars/${userData.id}/${userData.avatar}.png`,
            });
        } catch (error) {
            console.error('Error fetching user:', error);
            localStorage.removeItem('discord_token');
            showLoginCard();
        }
    } else {
        showLoginCard();
    }
}

// ... rest of existing code ...