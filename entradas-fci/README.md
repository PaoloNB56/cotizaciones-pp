# Cargar cotizaciones de FCI

1. Generá el TXT manualmente desde Balanz y convertí en tu PC con `fondos_txt_a_json.py`, como hasta ahora.
2. De la carpeta local `FCI`, tomá `BCACCA.json`, `BCAHA.json` o `BCMMA.json`.
3. En esta carpeta de GitHub (`entradas-fci`), elegí **Add file → Upload files**, subí los JSON y confirmá el cambio en la rama principal.
4. Abrí **Actions → Actualizar cotizaciones → Run workflow → Actualizar**.

No subas los TXT originales ni tu cartera. Una carga parcial de fechas se combina con el histórico anterior. No hace falta cargar los tres fondos juntos; los que no subas se conservan. Una carga vacía o inválida se rechaza para ese fondo: conserva su histórico anterior y aparece un aviso, mientras las otras series válidas pueden publicarse. Corregí el JSON y volvé a ejecutar el workflow para reintentarlo. No se hace scraping ni ninguna solicitud a Balanz.
