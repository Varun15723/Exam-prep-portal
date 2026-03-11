document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    const path = window.location.pathname;
    
    // Public paths that don't require auth
    const publicPaths = ['/login', '/register', '/'];
    const isPublic = publicPaths.includes(path);

    const loadingOverlay = document.getElementById('loading-overlay');
    const mainNav = document.getElementById('main-nav');
    const mainContent = document.getElementById('main-content');
    const logoutBtn = document.getElementById('logout-btn');
    const navAdmin = document.getElementById('nav-admin');

    if (!token && !isPublic) {
        window.location.href = '/login';
        return;
    }

    if (token) {
        try {
            const response = await fetch('/api/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Unauthorized');
            }

            const user = await response.json();
            window.currentUser = user;

            // Show admin link if faculty
            if (user.role === 'faculty') {
                if (navAdmin) navAdmin.style.display = 'block';
            }

            // Redirect if on login/register while logged in
            if (isPublic && path !== '/') {
                window.location.href = '/dashboard';
                return;
            }

            // Setup Navigation UI
            if (mainNav) mainNav.style.display = 'flex';
            
            // Set active link
            const activeLink = document.querySelector(`.nav-link[href="${path}"]`);
            if (activeLink) activeLink.classList.add('active');

        } catch (err) {
            console.error('Session validation failed', err);
            localStorage.removeItem('access_token');
            if (!isPublic) {
                window.location.href = '/login';
                return;
            }
        }
    } else {
        // Not logged in, but on a public page
        if (mainNav) mainNav.style.display = 'none';
    }

    // Hide loader and show content
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    if (mainContent) mainContent.style.display = 'block';

    // Logout handling
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        });
    }
});
