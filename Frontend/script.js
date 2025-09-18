// Example of custom JavaScript
document.addEventListener('DOMContentLoaded', function() {
  const currentLocation = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentLocation) {
      link.classList.add('active');
    }
  });
});


















































 // DECORATION BAMBOS SCROLL EFFECT

   document.addEventListener('DOMContentLoaded', () => {
    const leftBamboo = document.querySelector('.left-bamboo');
    const rightBamboo = document.querySelector('.right-bamboo');

    if (!leftBamboo || !rightBamboo) {
        console.error("Bamboo elements not found!");
        return;
    }

    const initialRightTransform = getComputedStyle(rightBamboo).transform;
    const isFlipped = initialRightTransform !== 'none' && initialRightTransform.includes('matrix(-1');

    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;

        // Create a subtle movement and rotation effect
        const moveAmount = scrollY * 0.2;
        const rotateAmount = scrollY * 0.03;

        // Apply transformations
        leftBamboo.style.transform = `translateY(-${moveAmount}px) rotate(-${rotateAmount}deg)`;
        
        // Ensure the right bamboo remains flipped horizontally
        const rightTransform = `scaleX(-1) translateY(-${moveAmount}px) rotate(-${rotateAmount}deg)`;
        rightBamboo.style.transform = rightTransform;
    });
});