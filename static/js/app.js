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
    const isDarkMode = document.body.classList.contains('dark-mode');
    
    if (isDarkMode) {
        if (iconDark && iconLight) {
            iconDark.style.display = 'none';
            iconLight.style.display = 'block';
        }
    } else {
        if (iconDark && iconLight) {
            iconDark.style.display = 'block';
            iconLight.style.display = 'none';
        }
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            let theme = 'light';
            
            if (document.body.classList.contains('dark-mode')) {
                theme = 'dark';
                if (iconDark) iconDark.style.display = 'none';
                if (iconLight) iconLight.style.display = 'block';
            } else {
                if (iconDark) iconDark.style.display = 'block';
                if (iconLight) iconLight.style.display = 'none';
            }
            
            localStorage.setItem('theme', theme);
        });
    }
});
