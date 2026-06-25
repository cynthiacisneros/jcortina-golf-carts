const hamburger = document.getElementById('hamburger')
const navLinks = document.getElementById('navLinks')

if (hamburger && navLinks) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open')
    navLinks.classList.toggle('open')
  })

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open')
      navLinks.classList.remove('open')
    })
  })
}

const contactForm = document.getElementById('contactForm')
const formSuccess = document.getElementById('formSuccess')

if (contactForm) {
  contactForm.addEventListener('submit', async function (e) {
    e.preventDefault()

    const name = document.getElementById('name').value.trim()
    const phone = document.getElementById('phone').value.trim()
    const email = document.getElementById('email').value.trim()
    const cartMake = document.getElementById('cartMake').value.trim()
    const issue = document.getElementById('issue').value.trim()
    const date = document.getElementById('date').value

    if (!name || !phone || !issue) return

    const submitBtn = contactForm.querySelector('.form-submit')
    submitBtn.disabled = true
    submitBtn.textContent = 'Sending...'

    const subject = encodeURIComponent('Service Request - J. Cortina Golf Carts')
    const body = encodeURIComponent(
      'Name: ' + name + '\n' +
      'Phone: ' + phone + '\n' +
      'Email: ' + email + '\n' +
      'Cart Make/Model: ' + cartMake + '\n' +
      'Issue Description: ' + issue + '\n' +
      'Preferred Date: ' + date
    )

    fetch('/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, phone, email, cartMake, issue, date })
    }).catch(() => {})

    window.open('mailto:cortinajaime@aol.com?subject=' + subject + '&body=' + body)

    contactForm.style.display = 'none'
    if (formSuccess) formSuccess.style.display = 'block'
  })
}
