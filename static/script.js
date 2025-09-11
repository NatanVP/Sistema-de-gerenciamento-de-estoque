document.addEventListener('DOMContentLoaded', function() {
    // 1. Auto-dismiss mensagens
    const alerts = document.querySelectorAll('.alert.success');
    alerts.forEach(alert => {
        setTimeout(() => alert.remove(), 3000);
    });
});

// Validação do formulário
function validarFormulario() {
    const preco = parseFloat(document.querySelector('input[name="preco"]').value);
    const quantidade = parseInt(document.querySelector('input[name="quantidade"]').value);

    if (quantidade < 0 || isNaN(quantidade)) {
        alert('Quantidade não pode ser negativa!');
        return false;
    }
    return true;
}
