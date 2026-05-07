// Frontend interactions
document.addEventListener('DOMContentLoaded', () => {
    // Fade out messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    if (messages.length > 0) {
        setTimeout(() => {
            messages.forEach(msg => {
                msg.style.transition = 'opacity 0.5s ease';
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 500);
            });
        }, 5000);
    }

    // Theme Toggle Logic
    const themeToggle = document.getElementById('theme-toggle');
    const iconDark = document.getElementById('theme-icon-dark');
    const iconLight = document.getElementById('theme-icon-light');
    
    // Check for saved theme preference or use OS preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const currentTheme = localStorage.getItem('theme');
    
    if (currentTheme == 'dark' || (!currentTheme && prefersDarkScheme.matches)) {
        document.body.classList.add('dark-mode');
        if(iconDark && iconLight) {
            iconDark.style.display = 'none';
            iconLight.style.display = 'block';
        }
    }
    
    if(themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            let theme = 'light';
            
            if (document.body.classList.contains('dark-mode')) {
                theme = 'dark';
                iconDark.style.display = 'none';
                iconLight.style.display = 'block';
            } else {
                iconDark.style.display = 'block';
                iconLight.style.display = 'none';
            }
            
            localStorage.setItem('theme', theme);
        });
    }
});
