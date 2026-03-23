function togglePw(inputId, btn) {
    var input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';   // eye with line=hidden
    } else {
        input.type = 'password';
        btn.innerHTML = '<i class="bi bi-eye"></i>';         // open eye=visible
    }
}