  fetch("footer.html")
  .then(response => response.text())
  .then(data => {
    document.getElementById("footer").innerHTML = data;
  });

{/* <footer>
    <div class="wrap">
      <div class="foot-top">
        <div class="foot-brand">
          <div class="logo"><span class="dot"></span>Raagini</div>
          <p>A new music institute in Uttam Nagar, teaching guitar, piano, tabla, vocals and violin with teachers who've
            been performing for years.</p>
        </div>
        <div class="foot-col">
          <h4>Courses</h4>
          <a href="index.html#courses">Guitar</a>
          <a href="index.html#courses">Piano &amp; Keyboard</a>
          <a href="index.html#courses">Tabla</a>
          <a href="index.html#courses">Vocals</a>
          <a href="index.html#courses">Violin</a>
        </div>
        <div class="foot-col">
          <h4>Institute</h4>
          <a href="index.html#teachers">Teachers</a>
          <a href="index.html#testimonials">Student stories</a>
          <a href="#">Timings</a>
          <a href="#">Fees</a>
        </div>
        <div class="foot-col">
          <h4>Reach us</h4>
          <a href="tel:+9198XXXXXXXX">+91 98XXX XXXXX</a>
          <a href="mailto:hello@raagini.in">hello@raagini.in</a>
          <a href="#">Your city, area</a>
        </div>
      </div>
      <div class="foot-bottom">
        <span>© 2026 Raagini Music Institute</span>
        <span>Built to be played, not just visited</span>
      </div>
    </div>
  </footer> */}

