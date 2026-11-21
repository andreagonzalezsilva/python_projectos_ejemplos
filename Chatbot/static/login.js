// Login: deja una marca de un solo uso para que la pagina del chat reproduzca la bienvenida
// justo despues de entrar (y no cada vez que se recarga).
const formularioLogin = document.getElementById("formulario-login");
if (formularioLogin) {
  try {
    sessionStorage.removeItem("introPendiente");
    formularioLogin.addEventListener("submit", () => sessionStorage.setItem("introPendiente", "1"));
  } catch (error) {
    // Sin almacenamiento de sesion simplemente no hay animacion de bienvenida
  }
}
