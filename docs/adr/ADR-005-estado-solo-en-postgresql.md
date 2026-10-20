# ADR-005: Todo el estado del producto vive en PostgreSQL

## Estado

Aceptado el 2026-10-20.

## Contexto

ResearchHUB y ResearchOS comparten la cuenta institucional. La sesion era un JWT
guardado en `localStorage`: no existia en el servidor, no podia revocarse antes de
expirar y cualquier script inyectado en la pagina podia leerlo. Los limites de
intentos de login solo se exigian al ingress y la aplicacion aceptaba cualquier
`DATABASE_URL`.

## Decision

1. PostgreSQL es la unica fuente de verdad en local, CI y produccion. La
   configuracion rechaza cualquier `DATABASE_URL` que no sea PostgreSQL.
2. Las sesiones son registros de `sesiones`. El navegador recibe un identificador
   aleatorio de 256 bits en una cookie `HttpOnly`, `Secure`, `SameSite=Strict`,
   con prefijo `__Host-`; la base guarda solo su HMAC-SHA256 con `SECRET_KEY`.
3. Las sesiones expiran por inactividad (`SESSION_IDLE_MINUTES`) y por vigencia
   maxima (`SESSION_MAX_HOURS`). Cerrar sesion, desactivar o eliminar la cuenta o
   cambiar su contrasena las revoca en el servidor.
4. Los intentos fallidos se guardan en `intentos_login` como HMAC del correo y
   bloquean el login durante `LOGIN_LOCKOUT_MINUTES` tras
   `LOGIN_MAX_FAILED_ATTEMPTS`, exista o no la cuenta.
5. Toda escritura en `/api/` exige `X-Requested-With: ResearchHUB` como defensa
   CSRF adicional a `SameSite=Strict`.
6. El navegador no guarda credenciales ni datos del producto (`localStorage` y
   `sessionStorage` no se usan).

## Fuera de la base, por diseno

- Secretos (`SECRET_KEY`, credenciales de PostgreSQL): los entrega la plataforma
  de despliegue. Guardarlos en la base expondria todo con una sola filtracion.
- Codigo, estilos e imagenes de marca: se versionan en Git y se sirven como
  archivos estaticos.
- Logs operativos: salen por stdout hacia la plataforma de observabilidad, sin
  tokens, contrasenas ni datos sensibles.

## Consecuencias

- Las replicas de la API siguen sin estado local; escalar no requiere afinidad.
- Cada request autenticado consulta `sesiones`; `last_used_at` se escribe como
  maximo una vez por minuto por sesion.
- Rotar `SECRET_KEY` invalida todas las sesiones y reinicia los contadores de
  bloqueo: es el procedimiento de cierre global de sesiones.
- Los clientes de API distintos al navegador deben enviar el encabezado CSRF.
