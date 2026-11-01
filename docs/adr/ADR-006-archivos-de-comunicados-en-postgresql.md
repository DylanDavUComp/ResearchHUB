# ADR-006: Imágenes y PDF de los comunicados se guardan en PostgreSQL

## Estado

Aceptado el 2026-11-01. Excepción acotada a la regla "binarios en almacenamiento
de objetos" de la skill de ingeniería de producción.

## Contexto

Los comunicados pasan de texto plano a un contenido por bloques, como un blog:
títulos, listas, imágenes, galerías, videos, botones, documentos, tablas y eventos.
La Dirección de Investigación necesita subir imágenes y PDF desde su computador. El
proyecto no tiene almacenamiento de objetos y crearlo exige infraestructura y
secretos nuevos en el servidor, a los que hoy no se accede sin SSH.

## Decisión

1. Los archivos de comunicados se guardan en `announcement_assets` (PostgreSQL),
   con su comunicado, tipo, tamaño, nombre saneado y SHA-256.
2. Límites: imágenes JPG, PNG, WebP o GIF de hasta 2 MB; PDF de hasta 5 MB;
   60 archivos por comunicado. El tipo se decide por la firma del contenido, no por
   el nombre ni el encabezado del navegador. SVG y HTML se rechazan.
3. Solo el Super administrador sube archivos. Un archivo es público solo cuando su
   comunicado está publicado; antes, solo lo ve un superadministrador.
4. Se sirven desde `/media/announcements/<id>` con `nosniff`, una CSP
   `default-src 'none'; sandbox` y descarga forzada para los PDF.
5. Al guardar, cada archivo se vincula a un único comunicado. Los que el comunicado
   deja de usar se eliminan, y las subidas nunca guardadas se purgan a las 24 h.
6. El contenido viaja como bloques JSON validados; nunca como HTML. La portada lo
   pinta con nodos DOM.

## Consecuencias

- Los archivos entran en los respaldos de la base (opción 14 de
  `researchhub-prod.bat`) y en su restauración.
- La base crece con cada imagen. Con los límites, 100 comunicados con 10 imágenes
  de 2 MB suman 2 GB como máximo.
- El proxy delante de la API debe aceptar cuerpos de al menos 6 MB en
  `/api/v1/admin/announcement-assets` (por ejemplo `client_max_body_size 6m` en
  nginx).
- Los documentos de trabajos de grado siguen bloqueados hasta tener almacenamiento
  de objetos, antimalware y retención: esta excepción no los cubre.

## Revisión

Revisar cuando exista almacenamiento de objetos o la tabla supere 5 GB: migrar los
archivos y conservar las mismas URL `/media/announcements/<id>`.
