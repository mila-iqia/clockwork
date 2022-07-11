const counterUp = window.counterUp.default

const callback = entries => {
   entries.forEach( entry => {
      const el = entry.target
      if ( entry.isIntersecting ) {
         counterUp( el, {
            duration: 900,
            delay: 50,
         } )
      }
   } )
}

const IO = new IntersectionObserver( callback, { threshold: 1 } )

//const el = document.querySelector( '.num' )
//IO.observe( el )


var slides = document.getElementsByClassName("num");
for (var i = 0; i < slides.length; i++) {
   IO.observe(slides.item(i));
}