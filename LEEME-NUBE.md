# Cotizaciones PP con GitHub Actions + Pages

El repositorio público [PaoloNB56/cotizaciones-pp](https://github.com/PaoloNB56/cotizaciones-pp) está instalado e inicializado. La validación Linux, la primera publicación Pages y una actualización posterior pasaron el 11/09/2026. Las 17 URL se comprobaron sin parámetros de caché, con nueva generación e histórico conservado. No se necesita pCloud, Termux, registro de desarrollador ni token personal. Falta comprobar la lectura dentro de PP en los dispositivos del usuario.

## Uso cotidiano

1. Desde el navegador del celular, abrir [Actions → Actualizar cotizaciones](https://github.com/PaoloNB56/cotizaciones-pp/actions/workflows/cotizaciones.yml).
2. Pulsar **Run workflow**, dejar la rama principal y el modo **Actualizar**, y confirmar.
3. Esperar que finalice correctamente. El resumen debe indicar **published_verified**, con últimas fechas por instrumento. Si dice **PUBLICACIÓN CON AVISOS**, las series indicadas conservaron su histórico anterior; las demás válidas se publicaron. Verde no significa que todos los proveedores aportaron datos nuevos.
4. Abrir PP y actualizar las cotizaciones históricas. La PC puede estar apagada.

Guardar la página de Actions como favorito o acceso directo del navegador. La app de GitHub no es requisito. No hay horarios ni ejecución automática al subir archivos.

## Instalación inicial

Esta instalación ya se completó para **PaoloNB56/cotizaciones-pp**. La base activa es `https://paolonb56.github.io/cotizaciones-pp/`. Los siguientes pasos se conservan para instalar una copia nueva; no repetir **Inicializar** en el uso cotidiano.

1. Crear una cuenta normal de GitHub y verificar el correo.
2. Crear un repositorio para este proyecto, por ejemplo `cotizaciones-pp`. Para GitHub Pages con GitHub Free debe ser **público**. Eso hace público el código y las cotizaciones cargadas: el paquete excluye cartera, transacciones, TXT originales, Excel y credenciales.
3. Usar el contenido de `pp-feed-github.zip`, no subir el ZIP como único archivo ni copiar toda la carpeta de trabajo. También deben quedar incluidos `.github/workflows/cotizaciones.yml` y los documentos de las carpetas con punto. El paquete trae sólo la lista revisada; la carga inicial puede hacerse desde la PC. Si se usa la web, comprobar que no omitió `.github`.
4. Abrir **Settings → Pages → Build and deployment → Source: GitHub Actions**. Permitir las acciones oficiales utilizadas por el workflow si la cuenta aplica restricciones. El workflow solicita permisos para publicar Pages y guardar la rama histórica.
5. En **Actions → Actualizar cotizaciones**, ejecutar primero **Validar**. Revisa proveedores y entradas sin publicar ni escribir el histórico.
6. Revisar el contenido/destino público descrito abajo. Elegir **Inicializar** para la primera publicación. Descarga precios, conserva las semillas completas, publica, verifica las URL y crea `feed-history`.
7. Esperar éxito; guardar la URL Pages que muestra GitHub. Ejecutar **Actualizar** una segunda vez y comprobar que la misma URL de `publication.json` cambia de generación. El script verifica también todas las cotizaciones y la prueba sintética, sin parámetros para evitar caché.
8. Configurar primero un instrumento en PP, luego los demás.

El token de ejecución lo genera GitHub automáticamente y expira; no hay que crearlo, copiarlo ni guardarlo en el repositorio. Un repositorio público puede usar runners estándar de Actions gratuitamente según las condiciones actuales; la validación inicial tardó 27 segundos y la primera publicación también se completó correctamente desde GitHub; esos tiempos no son una garantía para ejecuciones futuras. Fuentes: [Pages y planes](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [inicio manual](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow), [costos de Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Carga manual de FCI desde la PC

Se mantiene tu procedimiento manual con Balanz. El proyecto no hace scraping ni solicita datos a Balanz.

1. Generar el TXT desde la página de Balanz y convertirlo en la PC con `fondos_txt_a_json.py` como hasta ahora.
2. Tomar el JSON resultante de `FCI/`: `BCACCA.json`, `BCAHA.json` o `BCMMA.json`.
3. Abrir **entradas-fci** en GitHub → **Add file → Upload files**; subir los JSON y confirmar el cambio en la rama principal. Si se crea una propuesta en otra rama, incorporarla a la principal antes de actualizar.
4. Ejecutar **Actualizar cotizaciones**, modo **Actualizar**.

No hace falta subir los tres fondos juntos. Los ausentes conservan su histórico. Una carga con sólo algunas fechas se combina con las anteriores; en fechas coincidentes, el archivo nuevo reemplaza el cierre anterior. Los archivos vacíos, desordenados, duplicados o inválidos se rechazan para ese fondo: se conserva su histórico y se avisa, sin bloquear otras series válidas. El archivo rechazado no se marca como incorporado; corregirlo y ejecutar de nuevo. No existe un conversor web/móvil porque no fue solicitado. [Carga de archivos en GitHub](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

No subir TXT originales, capturas, datos de cuenta ni cartera a `entradas-fci`. No editar `feed-history` ni las semillas `FCI/` para una actualización cotidiana. Borrar una entrada manual no borra precios publicados; tampoco revierte una corrección ya incorporada.

## Contenido público previsto

La base activa es `https://paolonb56.github.io/cotizaciones-pp/`. En los ejemplos siguientes, `BASE` representa esa dirección sin la barra final.

Se despliegan únicamente estos 17 JSON de cotizaciones, todos en la raíz del sitio:

```text
AL35.json AE38.json AL41.json AN29.json AO28.json S30N6.json X29Y6.json
CCL.json MEP.json
T13F6.json T15D5.json T30J6.json TTJ26.json TTM26.json
BCACCA.json BCAHA.json BCMMA.json
```

También se publican `publication.json` (generación, fechas, recuentos, hashes y resultado de cada serie; también el motivo cuando se conserva por error) y `_pp_feed_probe.json` (cotización ficticia para comprobar sobrescritura). No importar la prueba como instrumento real en PP. No hay página de conversión ni datos de cartera.

Los FCI publicados se aplanan: `FCI/BCACCA.json` local corresponde a `BASE/BCACCA.json`. Se conserva el formato `[ {"date": "AAAA-MM-DD", "close": número} ]`.

La rama pública `feed-history` guarda los 17 históricos y `_state.json` para continuidad y auditoría. El estado sólo contiene metadatos de publicación y hashes de cargas FCI, nunca credenciales. El código está en la rama principal; Pages sólo despliega los archivos preparados, no el repositorio entero.

## Configuración de PP

En **Cotizaciones históricas**, elegir proveedor **JSON** y reemplazar localhost por la URL fija correspondiente. Por ejemplo [S30N6.json](https://paolonb56.github.io/cotizaciones-pp/S30N6.json).

| Campo | Valor |
|---|---|
| Ruta para la fecha | `$[*].date` |
| Ruta para cotización | `$[*].close` |
| Formato de fecha si se necesita | `yyyy-MM-dd` |
| Factor para cotizaciones | `1` |

La división QuickTrade por 1000 ya ocurre en el script; no repetirla en PP. FCI mantiene el valor de cuotaparte sin aplicar ese factor. Probar la vista previa con un instrumento y comparar varias fechas/cierres con el JSON público. [Manual JSON de PP](https://help.portfolio-performance.info/en/how-to/downloading-historical-prices/json/).

Guardar la cartera `.portfolio` y sincronizarla por un medio **privado** independiente. Abrir esa cartera en PP móvil y actualizar precios históricos. La FAQ móvil admite JSON y aclara que no usa la configuración separada de últimos precios. El soporte documentado no equivale a una prueba en el Samsung. [FAQ móvil](https://www.portfolio-performance.app/en/faq).

La prueba final será actualizar desde el celular con la PC apagada, verificar última fecha/cierre en PP móvil y después comprobar el escritorio con las mismas URL.

## Protección del histórico y errores

- Cada ejecución recupera un snapshot completo de `feed-history`, fijado a un commit. No depende del disco temporal del runner ni de la caché de Pages. Si falta historia, `Actualizar` exige inicialización explícita; si está corrupta o incompleta, falla.
- Los históricos locales iniciales quedan intactos. QuickTrade debe conservar todas las fechas conocidas de su rango. Dolarazo preserva el histórico y revisa un solapamiento de siete días para admitir correcciones del día actual.
- Los FCI no se descargan. Se validan las cargas manuales, se combinan por fecha y se registra su hash para no reaplicar indefinidamente un archivo antiguo.
- Si falla un proveedor o un JSON FCI reconocido, se conserva la última serie válida del histórico y se publican las otras actualizaciones válidas. No se inventan precios ni fechas para completar huecos. Si fallan todas las actualizaciones intentadas y tampoco hay una carga manual nueva válida, no se publica. Un histórico corrupto o incompleto, un archivo inesperado o una estructura insegura de entradas siguen interrumpiendo la preparación completa.
- Se valida el lote completo antes de crear el sitio desplegable, incluidas las series conservadas. Una publicación parcial correcta termina verde con avisos; el resumen identifica las series pendientes y sus motivos.
- Pages recibe un lote completo. Se comprueba `publication.json`, la prueba ficticia y las 17 URL exactas sin query strings. Se reintenta la lectura durante al menos un minuto más los tiempos de red; la caché propia de PP o de otros puntos de distribución requiere comprobación aparte.
- Sólo después de comprobar la publicación se guarda el nuevo histórico, manteniendo los commits anteriores y sin forzar la rama. Si falla despliegue, verificación o persistencia, el workflow intenta volver a desplegar el sitio confirmado anterior y verificarlo. El intento fallido sigue rojo aunque la restauración funcione.
- La primera publicación no tiene sitio anterior para restaurar. Tampoco se garantiza recuperación después de cancelar el workflow, agotar su tiempo o perder acceso a GitHub. Pages y la rama histórica no forman una transacción única; una escritura con respuesta incierta puede necesitar revisar ambos historiales.
- No ejecutar otros publicadores ni modificar manualmente `feed-history`. El workflow serializa ejecuciones y no cancela automáticamente una publicación en curso.

Si una ejecución aparece roja, leer el primer paso fallido y el resumen. No asumir que se publicaron precios nuevos. `run.json` empieza como `validated_not_published` y sólo termina en `published_verified` cuando publicación y persistencia están confirmadas, incluso si alguna serie conservó sus valores anteriores. Revisar `warnings` en `run.json` y los resultados de `publication.json`: `refreshed` indica una actualización válida, aunque los valores no hayan cambiado; `retained` indica una serie sin actualización prevista o una carga ya incorporada; `retained_after_error` indica que falló su actualización. Las fechas de cada serie reflejan los datos reales conservados. Los artifacts de informes se conservan siete días. El histórico Git permanece en su rama.

Las validaciones detectan estructura inválida, fechas perdidas conocidas y huecos nuevos de Dolarazo; no certifican por sí solas la veracidad económica de cada precio del proveedor.

## Archivos y comprobaciones locales

- `github_feed.py`: runner elegido; no invoca pCloud ni Balanz.
- `cloud_feed.py` y `update_bonos.py`: lógica compartida de descarga y conversión. Las funciones pCloud antiguas permanecen sin uso.
- `.github/workflows/cotizaciones.yml`: manual exclusivamente; subirlo al repositorio no ejecuta por sí solo una actualización.
- `entradas-fci/`: JSON cargados por el usuario, separados de las semillas.
- `package_github.py`: genera el ZIP de instalación mediante lista explícita. No sube nada.
- Los scripts, documentación empaquetada y ZIP de Termux/pCloud anteriores quedaron como alternativas descartadas; no usarlos para esta instalación.
- El BAT original aún apunta a `D:\scriptspython\pp_feed` y abre un servidor. No usarlo para probar este proyecto.

Verificación offline:

```powershell
python -B -m unittest -v -b test_cloud_feed test_github_feed
```

Preparar un lote real sin publicar, usando un nombre de carpeta que todavía no exista:

```powershell
python -B -u github_feed.py stage --local --work .cloud-work/prueba-pages-01
```

Este modo usa semillas locales; no consulta GitHub. El modo **Validar** dentro de Actions sí consulta el histórico remoto si ya existe. Ambos evitan publicar.

Estado comprobado localmente: pruebas offline de FCI, recuperación, persistencia y URL; descarga completa en Windows y preparación de 17 series. Comprobado en GitHub: [Validar](https://github.com/PaoloNB56/cotizaciones-pp/actions/runs/34663922757) y [primera publicación](https://github.com/PaoloNB56/cotizaciones-pp/actions/runs/34663988467), autenticación automática, histórico persistido y 17 URL públicas. La [segunda publicación](https://github.com/PaoloNB56/cotizaciones-pp/actions/runs/34664059981) también pasó: nueva generación y prueba sintética en las mismas URL, 17 series verificadas, todas las fechas anteriores conservadas y segundo commit histórico enlazado al primero. Pendiente: rollback real y consumo en PP escritorio/móvil. Los originales JSON, TXT y Excel se verifican contra `baseline.sha256.json`.
