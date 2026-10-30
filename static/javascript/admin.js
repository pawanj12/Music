/* ============================================================
   MINERVA ADMIN — SHARED JS
   Theme (sab pages par same), sidebar dropdown, mobile menu,
   "Coming soon" links ke liye toast.
   ============================================================ */

(function () {
    "use strict";

    var THEME_KEY = "minerva_admin_theme";
    var html = document.documentElement;


    /* ---------- THEME ---------- */

    function readTheme() {
        try {
            return localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";
        } catch (e) {
            return "light";
        }
    }

    function applyTheme(theme) {
        html.setAttribute("data-admin-theme", theme === "dark" ? "dark" : "light");
    }

    function saveTheme(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch (e) { /* storage blocked: theme sirf is page par rahega */ }
        applyTheme(theme);
    }

    applyTheme(readTheme());

    /* Dusre tab mein theme badle to yahan bhi badal jaye */
    window.addEventListener("storage", function (event) {
        if (event.key === THEME_KEY) { applyTheme(readTheme()); }
    });

    /* Back/forward se aaye to bhi sahi theme */
    window.addEventListener("pageshow", function () { applyTheme(readTheme()); });


    document.addEventListener("DOMContentLoaded", function () {

        /* ---------- THEME BUTTON ---------- */

        var themeButton = document.getElementById("adminThemeToggle");

        if (themeButton) {
            themeButton.addEventListener("click", function () {
                var current = html.getAttribute("data-admin-theme") === "dark" ? "dark" : "light";
                saveTheme(current === "dark" ? "light" : "dark");
            });
        }


        /* ---------- SIDEBAR DROPDOWNS (ek time par ek khula) ---------- */

        document.querySelectorAll("[data-admin-dropdown]").forEach(function (button) {
            button.addEventListener("click", function () {
                var group = button.closest(".admin-nav-group");
                if (!group) { return; }

                var willOpen = !group.classList.contains("open");

                document.querySelectorAll(".admin-nav-group").forEach(function (other) {
                    if (other !== group) {
                        other.classList.remove("open");
                        var t = other.querySelector("[data-admin-dropdown]");
                        if (t) { t.setAttribute("aria-expanded", "false"); }
                    }
                });

                group.classList.toggle("open", willOpen);
                button.setAttribute("aria-expanded", willOpen ? "true" : "false");
            });
        });


        /* ---------- MOBILE SIDEBAR ---------- */

        var sidebar = document.getElementById("adminSidebar");
        var overlay = document.getElementById("adminSidebarOverlay");
        var openBtn = document.getElementById("adminMobileToggle");
        var closeBtn = document.getElementById("adminSidebarClose");

        function openMenu() {
            if (sidebar) { sidebar.classList.add("open"); }
            if (overlay) { overlay.classList.add("show"); }
        }

        function closeMenu() {
            if (sidebar) { sidebar.classList.remove("open"); }
            if (overlay) { overlay.classList.remove("show"); }
        }

        if (openBtn) { openBtn.addEventListener("click", openMenu); }
        if (closeBtn) { closeBtn.addEventListener("click", closeMenu); }
        if (overlay) { overlay.addEventListener("click", closeMenu); }

        /* Link par click ke baad mobile menu band */
        document.querySelectorAll(".admin-nav a, .admin-sidebar-bottom a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (window.innerWidth <= 900 && !link.hasAttribute("data-soon")) { closeMenu(); }
            });
        });

        /* Desktop par resize ho to menu state reset */
        window.addEventListener("resize", function () {
            if (window.innerWidth > 900) { closeMenu(); }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { closeMenu(); }
        });


        /* ---------- "COMING SOON" LINKS ---------- */

        var toast = null;
        var toastTimer = null;

        function showToast(message) {
            if (!toast) {
                toast = document.createElement("div");
                toast.className = "admin-toast";
                toast.setAttribute("role", "status");
                document.body.appendChild(toast);
            }
            toast.textContent = message;
            toast.classList.add("show");
            clearTimeout(toastTimer);
            toastTimer = setTimeout(function () { toast.classList.remove("show"); }, 1800);
        }

        document.querySelectorAll("[data-soon]").forEach(function (link) {
            link.addEventListener("click", function (event) {
                event.preventDefault();
                showToast("Coming soon — yeh section abhi ban raha hai");
            });
        });
    });
})();
