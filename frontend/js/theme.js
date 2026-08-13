// Global Theme Manager (Light Theme Default)
(function () {
    const savedTheme = localStorage.getItem("appTheme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
})();

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
    const newTheme = currentTheme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("appTheme", newTheme);
    updateThemeToggleUI(newTheme);
}

function updateThemeToggleUI(theme) {
    const toggleBtns = document.querySelectorAll(".theme-toggle-btn");
    toggleBtns.forEach(btn => {
        if (theme === "dark") {
            btn.innerHTML = "☀️ <span class='theme-btn-text'>Light Mode</span>";
            btn.setAttribute("title", "Switch to Light Mode");
        } else {
            btn.innerHTML = "🌙 <span class='theme-btn-text'>Dark Mode</span>";
            btn.setAttribute("title", "Switch to Dark Mode");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const currentTheme = localStorage.getItem("appTheme") || "light";
    updateThemeToggleUI(currentTheme);
    
    document.querySelectorAll(".theme-toggle-btn").forEach(btn => {
        btn.addEventListener("click", toggleTheme);
    });
});

// Password Eye Toggle Helper
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🙈";
        btn.setAttribute("aria-label", "Hide password");
    } else {
        input.type = "password";
        btn.textContent = "👁️";
        btn.setAttribute("aria-label", "Show password");
    }
}

