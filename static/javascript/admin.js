(function () {
    "use strict";


    /* ============================================================
       GLOBAL ADMIN THEME
       ============================================================ */

    const THEME_KEY = "minerva_admin_theme";
    const html = document.documentElement;


    function applyTheme(theme) {

        const safeTheme =
            theme === "dark"
                ? "dark"
                : "light";

        html.setAttribute(
            "data-admin-theme",
            safeTheme
        );

        localStorage.setItem(
            THEME_KEY,
            safeTheme
        );
    }


    function loadSavedTheme() {

        const savedTheme =
            localStorage.getItem(THEME_KEY);

        if (savedTheme === "dark") {

            html.setAttribute(
                "data-admin-theme",
                "dark"
            );

        } else {

            html.setAttribute(
                "data-admin-theme",
                "light"
            );

        }
    }


    /* Apply theme BEFORE page interaction */

    loadSavedTheme();


    /* ============================================================
       DOM READY
       ============================================================ */

    document.addEventListener(
        "DOMContentLoaded",
        function () {


            /* ====================================================
               THEME BUTTON
               ==================================================== */

            const themeButton =
                document.getElementById(
                    "adminThemeToggle"
                );


            if (themeButton) {

                themeButton.addEventListener(
                    "click",
                    function () {

                        const currentTheme =
                            html.getAttribute(
                                "data-admin-theme"
                            ) || "light";


                        const newTheme =
                            currentTheme === "dark"
                                ? "light"
                                : "dark";


                        applyTheme(newTheme);

                    }
                );

            }


            /* ====================================================
               DROPDOWNS
               ==================================================== */

            const dropdownButtons =
                document.querySelectorAll(
                    "[data-admin-dropdown]"
                );


            dropdownButtons.forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function (event) {

                            event.preventDefault();
                            event.stopPropagation();


                            const targetId =
                                button.getAttribute(
                                    "data-admin-dropdown"
                                );


                            const target =
                                document.getElementById(
                                    targetId
                                );


                            if (!target) {
                                return;
                            }


                            const group =
                                button.closest(
                                    ".admin-nav-group"
                                );


                            if (!group) {
                                return;
                            }


                            const isOpen =
                                group.classList.contains(
                                    "open"
                                );


                            /* Close other dropdowns */

                            document
                                .querySelectorAll(
                                    ".admin-nav-group"
                                )
                                .forEach(
                                    function (item) {

                                        if (
                                            item !== group
                                        ) {

                                            item.classList.remove(
                                                "open"
                                            );

                                            const toggle =
                                                item.querySelector(
                                                    "[data-admin-dropdown]"
                                                );

                                            if (toggle) {

                                                toggle.setAttribute(
                                                    "aria-expanded",
                                                    "false"
                                                );

                                            }

                                        }

                                    }
                                );


                            /* Toggle current */

                            if (isOpen) {

                                group.classList.remove(
                                    "open"
                                );

                                button.setAttribute(
                                    "aria-expanded",
                                    "false"
                                );

                            } else {

                                group.classList.add(
                                    "open"
                                );

                                button.setAttribute(
                                    "aria-expanded",
                                    "true"
                                );

                            }

                        }
                    );

                }
            );


            /* ====================================================
               CLOSE DROPDOWNS WHEN CLICKING OUTSIDE
               ==================================================== */

            document.addEventListener(
                "click",
                function (event) {

                    const insideGroup =
                        event.target.closest(
                            ".admin-nav-group"
                        );


                    if (!insideGroup) {

                        document
                            .querySelectorAll(
                                ".admin-nav-group"
                            )
                            .forEach(
                                function (group) {

                                    group.classList.remove(
                                        "open"
                                    );

                                    const button =
                                        group.querySelector(
                                            "[data-admin-dropdown]"
                                        );

                                    if (button) {

                                        button.setAttribute(
                                            "aria-expanded",
                                            "false"
                                        );

                                    }

                                }
                            );

                    }

                }
            );


            /* ====================================================
               MOBILE SIDEBAR
               ==================================================== */

            const sidebar =
                document.getElementById(
                    "adminSidebar"
                );


            const overlay =
                document.getElementById(
                    "adminSidebarOverlay"
                );


            const mobileButton =
                document.getElementById(
                    "adminMobileToggle"
                );


            function closeMobileSidebar() {

                if (sidebar) {

                    sidebar.classList.remove(
                        "open"
                    );

                }


                if (overlay) {

                    overlay.classList.remove(
                        "show"
                    );

                }

            }


            if (
                mobileButton &&
                sidebar
            ) {

                mobileButton.addEventListener(
                    "click",
                    function () {

                        sidebar.classList.toggle(
                            "open"
                        );


                        if (overlay) {

                            overlay.classList.toggle(
                                "show"
                            );

                        }

                    }
                );

            }


            if (overlay) {

                overlay.addEventListener(
                    "click",
                    closeMobileSidebar
                );

            }


            /* Close mobile sidebar after navigation */

            document
                .querySelectorAll(
                    ".admin-nav-item, .admin-subnav-item"
                )
                .forEach(
                    function (item) {

                        item.addEventListener(
                            "click",
                            function () {

                                if (
                                    window.innerWidth <= 900
                                ) {

                                    closeMobileSidebar();

                                }

                            }
                        );

                    }
                );


            /* ====================================================
               ESC KEY
               ==================================================== */

            document.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Escape"
                    ) {

                        closeMobileSidebar();

                        document
                            .querySelectorAll(
                                ".admin-nav-group"
                            )
                            .forEach(
                                function (group) {

                                    group.classList.remove(
                                        "open"
                                    );

                                }
                            );

                    }

                }
            );

        }
    );

})();