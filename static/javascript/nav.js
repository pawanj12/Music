(function () {

  var NAV_ITEMS = [
    {
      label: "Home",
      href: "/",
      key: "home"
    },
    {
      label: "Courses",
      href: "/courses",
      key: "courses"
    },
    {
      label: "Gallery",
      href: "/#Gallery",
      key: "gallery"
    },
    {
      label: "Why us",
      href: "/#why",
      key: "why"
    },
    {
      label: "Stories",
      href: "/#testimonials",
      key: "stories"
    },
    {
      label: "Contact",
      href: "/contact",
      key: "contact"
    }
  ];


  function renderLinks(current) {

    return NAV_ITEMS.map(function (item) {

      var activeClass =
        item.key === current
          ? ' class="active"'
          : "";

      return (
        '<a href="' +
        item.href +
        '"' +
        activeClass +
        '>' +
        item.label +
        '</a>'
      );

    }).join("");

  }


  document.addEventListener("DOMContentLoaded", function () {

    var mount = document.getElementById("site-header");

    if (!mount) return;


    var current =
      mount.getAttribute("data-active") || "home";


    var ctaHref =
      mount.getAttribute("data-cta-href") ||
      "/contact#form";


    var ctaLabel =
      mount.getAttribute("data-cta-label") ||
      "Book a demo class";


    var linksHTML = renderLinks(current);


    mount.innerHTML =
      "<header>" +

      '<nav class="wrap">' +

      '<a href="/" class="logo">' +
      '<span class="dot"></span>' +
      'Minerva Institute' +
      '</a>' +

      '<div class="nav-links">' +
      linksHTML +
      "</div>" +

      '<div class="nav-right">' +

      '<a href="' +
      ctaHref +
      '" class="btn btn-primary">' +
      ctaLabel +
      "</a>" +

      '<button class="hamburger" id="hamburgerBtn" aria-label="Toggle menu">' +
      "<span></span>" +
      "<span></span>" +
      "<span></span>" +
      "</button>" +

      "</div>" +

      "</nav>" +


      '<div class="mobile-menu" id="mobileMenu">' +

      linksHTML +

      '<a href="' +
      ctaHref +
      '" class="btn btn-primary">' +
      ctaLabel +
      "</a>" +

      "</div>" +

      "</header>";


    var btn =
      document.getElementById("hamburgerBtn");

    var menu =
      document.getElementById("mobileMenu");


    if (btn && menu) {

      btn.addEventListener("click", function () {

        btn.classList.toggle("open");

        menu.classList.toggle("open");

      });


      menu.querySelectorAll("a").forEach(function (a) {

        a.addEventListener("click", function () {

          btn.classList.remove("open");

          menu.classList.remove("open");

        });

      });


      document.addEventListener("click", function (e) {

        var insideMenu =
          menu.contains(e.target);

        var onHamburger =
          btn.contains(e.target);


        if (
          !insideMenu &&
          !onHamburger &&
          menu.classList.contains("open")
        ) {

          btn.classList.remove("open");

          menu.classList.remove("open");

        }

      });

    }

  });

})();