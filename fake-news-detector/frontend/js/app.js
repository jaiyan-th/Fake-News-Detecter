// Authentication state management (global scope)
let isLoggedIn = false;
let currentUser = null;

function updateAuthUI() {
    const headerActions = document.querySelector('.header-actions');
    const authNotice = document.getElementById('auth-notice');
    const navProfile = document.getElementById('nav-profile');
    
    if (isLoggedIn && currentUser) {
        // Show user info and logout button
        headerActions.innerHTML = `
            <span style="color: var(--text-dark); font-weight: 500;">Welcome, ${currentUser.name}</span>
            <button class="btn btn-outline" id="btn-logout">Logout</button>
        `;
        
        // Show profile nav link
        if (navProfile) {
            navProfile.classList.remove('hidden');
        }
        
        // Hide authentication notice
        if (authNotice) {
            authNotice.style.display = 'none';
        }
        
        // Update profile section with user data
        updateProfileSection();
        
        // Add logout functionality
        document.getElementById('btn-logout').addEventListener('click', async () => {
            const result = await api.logout();
            if (result.success) {
                logout();
            }
        });
    } else {
        // Show login/signup buttons
        headerActions.innerHTML = `
            <button class="btn btn-outline" id="btn-login">Login</button>
            <button class="btn btn-primary" id="btn-signup">Sign Up</button>
        `;
        
        // Hide profile nav link
        if (navProfile) {
            navProfile.classList.add('hidden');
        }
        
        // Show authentication notice
        if (authNotice) {
            authNotice.style.display = 'block';
        }
        
        // Re-attach modal event listeners
        attachModalListeners();
        
        // Add auth notice login button listener
        document.getElementById('auth-notice-login')?.addEventListener('click', () => {
            document.getElementById('login-modal').classList.remove('hidden');
        });
    }
}

async function updateProfileSection() {
    if (!currentUser) return;
    
    // Update profile header
    document.getElementById('profile-name').textContent = currentUser.name || 'User';
    document.getElementById('profile-email').textContent = currentUser.email || '';
    
    // Update profile details
    document.getElementById('profile-fullname').textContent = currentUser.name || '-';
    document.getElementById('profile-email-detail').textContent = currentUser.email || '-';
    
    // Update auth method
    const authMethod = currentUser.oauth_provider 
        ? `Google OAuth (${currentUser.oauth_provider})` 
        : 'Email/Password';
    document.getElementById('profile-auth-method').textContent = authMethod;
    
    // Update member since
    const memberSince = currentUser.created_at 
        ? new Date(currentUser.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
        : new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    document.getElementById('profile-member-since').textContent = memberSince;
    
    // Load and update statistics
    try {
        const stats = await api.getHistoryStats();
        if (stats) {
            // Update total analyses
            const totalElement = document.getElementById('profile-total-analyses');
            if (totalElement) {
                totalElement.textContent = stats.total_analyses || 0;
            }
            
            // You can add more stats display here if needed
            console.log('User stats loaded:', stats);
        }
    } catch (error) {
        console.error('Failed to load user stats:', error);
    }
}

function login(user) {
    isLoggedIn = true;
    currentUser = user;
    updateAuthUI();
}

function logout() {
    isLoggedIn = false;
    currentUser = null;
    updateAuthUI();
    
    // Redirect to home if on verify page
    const verifySection = document.getElementById('verification-section');
    if (verifySection && !verifySection.classList.contains('hidden')) {
        const navHome = document.getElementById('nav-home');
        const homeSection = document.getElementById('home-section');
        if (navHome && homeSection) {
            switchSection(navHome, homeSection);
        }
    }
}

function requireAuth() {
    if (!isLoggedIn) {
        alert('Please login or sign up to access this feature.');
        document.getElementById('login-modal').classList.remove('hidden');
        return false;
    }
    return true;
}

function switchSection(activeNav, activeSection) {
    const navHome = document.getElementById('nav-home');
    const navVerify = document.getElementById('nav-verify');
    const navHistory = document.getElementById('nav-history');
    const navAbout = document.getElementById('nav-about');
    const navContact = document.getElementById('nav-contact');
    const navProfile = document.getElementById('nav-profile');
    
    const homeSection = document.getElementById('home-section');
    const verifySection = document.getElementById('verification-section');
    const historySection = document.getElementById('history-section');
    const aboutSection = document.getElementById('about-section');
    const contactSection = document.getElementById('contact-section');
    const profileSection = document.getElementById('profile-section');
    
    [navHome, navVerify, navHistory, navAbout, navContact, navProfile].forEach(n => n?.classList.remove('active'));
    [homeSection, verifySection, historySection, aboutSection, contactSection, profileSection].forEach(s => s?.classList.add('hidden'));
    
    activeNav?.classList.add('active');
    activeSection?.classList.remove('hidden');
}

function attachModalListeners() {
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    const btnLogin = document.getElementById('btn-login');
    const btnSignup = document.getElementById('btn-signup');
    const closeLogin = document.getElementById('close-login');
    const closeSignup = document.getElementById('close-signup');
    const switchToSignup = document.getElementById('switch-to-signup');
    const switchToLogin = document.getElementById('switch-to-login');

    btnLogin?.addEventListener('click', () => {
        loginModal?.classList.remove('hidden');
    });

    btnSignup?.addEventListener('click', () => {
        signupModal?.classList.remove('hidden');
    });

    closeLogin?.addEventListener('click', () => {
        loginModal?.classList.add('hidden');
    });

    closeSignup?.addEventListener('click', () => {
        signupModal?.classList.add('hidden');
    });

    switchToSignup?.addEventListener('click', (e) => {
        e.preventDefault();
        loginModal?.classList.add('hidden');
        signupModal?.classList.remove('hidden');
    });

    switchToLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        signupModal?.classList.add('hidden');
        loginModal?.classList.remove('hidden');
    });

    loginModal?.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.classList.add('hidden');
        }
    });

    signupModal?.addEventListener('click', (e) => {
        if (e.target === signupModal) {
            signupModal.classList.add('hidden');
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    const dashboard = new Dashboard();

    // Check if user is already authenticated
    const userResult = await api.getCurrentUser();
    if (userResult.success && userResult.user) {
        login(userResult.user);
    }

    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
        // OAuth successful - fetch user info
        const userResult = await api.getCurrentUser();
        if (userResult.success && userResult.user) {
            login(userResult.user);
        }
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.get('auth') === 'error') {
        alert('Google Sign-in failed. Please try again.');
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Initialize auth UI
    updateAuthUI();

    // Login form handler
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        if (!email || !password) {
            alert('Please enter both email and password.');
            return;
        }
        
        const result = await api.login(email, password);
        
        if (result.success) {
            login(result.user);
            document.getElementById('login-modal')?.classList.add('hidden');
            alert(`Welcome back, ${result.user.name}!`);
            
            // Navigate to home page
            switchSection(navHome, homeSection);
        } else {
            alert(result.error || 'Login failed');
        }
    });

    // Signup form handler
    document.getElementById('signup-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;
        
        if (!name || !email || !password || !confirmPassword) {
            alert('Please fill in all fields.');
            return;
        }
        
        if (password !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }
        
        const result = await api.register(email, password, name);
        
        if (result.success) {
            login(result.user);
            document.getElementById('signup-modal')?.classList.add('hidden');
            alert(`Account created successfully! Welcome, ${result.user.name}! Check your email for a welcome message.`);
            
            // Navigate to home page
            switchSection(navHome, homeSection);
        } else {
            alert(result.error || 'Registration failed');
        }
    });

    // Google Sign-in buttons
    document.getElementById('google-signin-login')?.addEventListener('click', async (e) => {
        e.preventDefault();
        await api.initiateGoogleOAuth();
    });

    document.getElementById('google-signin-signup')?.addEventListener('click', async (e) => {
        e.preventDefault();
        await api.initiateGoogleOAuth();
    });

    // Initial modal listeners
    attachModalListeners();

    // Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const inputViews = document.querySelectorAll('.input-view');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            inputViews.forEach(v => v.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
            
            // Clear results panel when switching tabs
            const resultsPanel = document.getElementById('results-panel');
            if (resultsPanel) {
                resultsPanel.classList.add('hidden');
            }
            
            const loadingIndicator = document.getElementById('loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.classList.add('hidden');
            }
        });
    });

    // Main Navigation
    const navHome = document.getElementById('nav-home');
    const navVerify = document.getElementById('nav-verify');
    const navHistory = document.getElementById('nav-history');
    const navAbout = document.getElementById('nav-about');
    const navContact = document.getElementById('nav-contact');
    
    const homeSection = document.getElementById('home-section');
    const verifySection = document.getElementById('verification-section');
    const historySection = document.getElementById('history-section');
    const aboutSection = document.getElementById('about-section');
    const contactSection = document.getElementById('contact-section');

    navHome?.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection(navHome, homeSection);
    });

    navVerify?.addEventListener('click', (e) => {
        e.preventDefault();
        if (requireAuth()) {
            switchSection(navVerify, verifySection);
        }
    });

    navHistory?.addEventListener('click', async (e) => {
        e.preventDefault();
        switchSection(navHistory, historySection);
        
        const res = await api.getHistory();
        if (res.success) {
            dashboard.renderHistory(res.history);
        }
    });

    navAbout?.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection(navAbout, aboutSection);
    });

    navContact?.addEventListener('click', (e) => {
        e.preventDefault();
        switchSection(navContact, contactSection);
    });

    const navProfile = document.getElementById('nav-profile');
    const profileSection = document.getElementById('profile-section');
    
    navProfile?.addEventListener('click', (e) => {
        e.preventDefault();
        if (requireAuth()) {
            switchSection(navProfile, profileSection);
            updateProfileSection();
        }
    });

    document.getElementById('btn-start-analysis')?.addEventListener('click', () => {
        if (requireAuth()) {
            switchSection(navVerify, verifySection);
        }
    });

    document.getElementById('btn-learn-more')?.addEventListener('click', () => {
        const featuresSection = document.querySelector('.features-header');
        if (featuresSection) {
            featuresSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            switchSection(navAbout, aboutSection);
        }
    });
    
    document.getElementById('btn-new-analysis-history')?.addEventListener('click', () => {
        switchSection(navVerify, verifySection);
    });

    // Verification Triggers
    document.getElementById('btn-verify-text')?.addEventListener('click', async () => {
        if (!requireAuth()) return;
        
        const text = document.getElementById('claim-text').value;
        
        if (!text) return alert('Please enter some text.');
        
        dashboard.showLoading();
        const res = await api.analyzeText(text);
        dashboard.renderResult(res);
    });

    document.getElementById('btn-verify-url')?.addEventListener('click', async () => {
        if (!requireAuth()) return;
        
        const url = document.getElementById('news-url').value;
        
        if (!url) return alert('Please enter a valid URL.');
        
        dashboard.showLoading();
        const res = await api.analyzeUrl(url);
        dashboard.renderResult(res);
    });

    // Contact form handling
    document.getElementById('contact-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('contact-name').value;
        const email = document.getElementById('contact-email').value;
        const subject = document.getElementById('contact-subject').value;
        const message = document.getElementById('contact-message').value;
        
        if (!name || !email || !message) {
            alert('Please fill in all required fields.');
            return;
        }
        
        const submitButton = e.target.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        
        submitButton.textContent = 'Sending...';
        submitButton.disabled = true;
        
        setTimeout(() => {
            alert('Thank you for your message! We\'ll get back to you within 24 hours.');
            document.getElementById('contact-form').reset();
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }, 1500);
    });

    // Profile action handlers
    document.getElementById('btn-change-password')?.addEventListener('click', () => {
        document.getElementById('change-password-modal')?.classList.remove('hidden');
    });

    // Change password modal close
    document.getElementById('close-change-password')?.addEventListener('click', () => {
        document.getElementById('change-password-modal')?.classList.add('hidden');
    });

    // Change password form handler
    document.getElementById('change-password-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-new-password').value;
        
        if (!currentPassword || !newPassword || !confirmPassword) {
            alert('Please fill in all fields.');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            alert('New passwords do not match!');
            return;
        }
        
        if (newPassword.length < 6) {
            alert('Password must be at least 6 characters long.');
            return;
        }
        
        const submitButton = e.target.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Updating...';
        submitButton.disabled = true;
        
        try {
            const result = await api.changePassword(currentPassword, newPassword);
            
            if (result.success) {
                alert('Password changed successfully!');
                document.getElementById('change-password-modal')?.classList.add('hidden');
                document.getElementById('change-password-form').reset();
            } else {
                alert(result.error || 'Failed to change password');
            }
        } catch (error) {
            alert('An error occurred. Please try again.');
        } finally {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });

    document.getElementById('btn-export-data')?.addEventListener('click', async () => {
        if (!requireAuth()) return;
        
        const result = await api.getHistory();
        if (result.success) {
            const dataStr = JSON.stringify(result.history, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `fake-news-detector-data-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            URL.revokeObjectURL(url);
        }
    });

    document.getElementById('btn-delete-account')?.addEventListener('click', () => {
        const confirmed = confirm('Are you sure you want to delete your account? This action cannot be undone.');
        if (confirmed) {
            alert('Account deletion functionality coming soon. Please contact support.');
        }
    });
});


    // Password visibility toggle functionality
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);
            const eyeIcon = this.querySelector('.eye-icon');
            const eyeOffIcon = this.querySelector('.eye-off-icon');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.classList.add('hidden');
                eyeOffIcon.classList.remove('hidden');
            } else {
                passwordInput.type = 'password';
                eyeIcon.classList.remove('hidden');
                eyeOffIcon.classList.add('hidden');
            }
        });
    });

    // Clear form fields when modals are opened
    const loginModal = document.getElementById('login-modal');
    const signupModal = document.getElementById('signup-modal');
    
    const clearLoginForm = () => {
        document.getElementById('login-email').value = '';
        document.getElementById('login-password').value = '';
    };
    
    const clearSignupForm = () => {
        document.getElementById('signup-name').value = '';
        document.getElementById('signup-email').value = '';
        document.getElementById('signup-password').value = '';
        document.getElementById('signup-confirm-password').value = '';
    };
    
    // Clear forms when modals are shown
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                if (!loginModal.classList.contains('hidden')) {
                    clearLoginForm();
                }
                if (!signupModal.classList.contains('hidden')) {
                    clearSignupForm();
                }
            }
        });
    });
    
    observer.observe(loginModal, { attributes: true });
    observer.observe(signupModal, { attributes: true });
