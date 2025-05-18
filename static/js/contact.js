// Contact Page JS Example
console.log('Contact page JS loaded');

function hideTempMailIcons() {
  // Target the email wrapper and input
  const wrapper = document.querySelector('.email-wrapper');
  if (!wrapper) return;

  // Remove suspicious children inside the wrapper
  wrapper.querySelectorAll(
    'img, button, div, span, [data-temp-mail-org], .temp-mail-btn, [class*="temp"], [id*="temp"], [src*="temp-mail"], [src*="tempmail"], [alt*="temp"], [title*="temp"]'
  ).forEach(el => {
    if (!el.matches('input[type="email"]')) el.remove();
  });

  // Remove suspicious siblings after the input
  const emailInput = wrapper.querySelector('input[type="email"]');
  if (emailInput) {
    let sibling = emailInput.nextSibling;
    while (sibling) {
      if (sibling.nodeType === 1 && (
        sibling.matches('img, button, div, span, [data-temp-mail-org], .temp-mail-btn, [class*="temp"], [id*="temp"], [src*="temp-mail"], [src*="tempmail"], [alt*="temp"], [title*="temp"]')
      )) {
        let toRemove = sibling;
        sibling = sibling.nextSibling;
        toRemove.remove();
      } else {
        sibling = sibling.nextSibling;
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Run on load and every 500ms for a few seconds (to catch late-injected elements)
  let tries = 0;
  const interval = setInterval(() => {
    hideTempMailIcons();
    tries++;
    if (tries > 20) clearInterval(interval); // Stop after 10 seconds
  }, 500);
});
