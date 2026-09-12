# Cotizaciones para Portfolio Performance

Actualización manual desde el celular mediante **GitHub Actions**, con JSON públicos y URL estables en **GitHub Pages**. La PC puede estar apagada.

- Bonos QuickTrade y MEP/CCL: descarga automática al pulsar **Actualizar cotizaciones**.
- FCI: adquisición manual desde Balanz, conversión en la PC y carga de JSON en [entradas-fci](entradas-fci/README.md). No se hace scraping.
- Conservación de históricos, validación completa antes de publicar y verificación de las URL.
- Si falla una serie, conserva su última versión válida y se publican las demás. La ejecución queda verde con avisos que indican cuáles quedaron pendientes; revisar también las fechas del resumen.
- Sin pCloud, Termux, token personal ni conversor web.

**Actualizar desde el celular:** [abrir Actions](https://github.com/PaoloNB56/cotizaciones-pp/actions/workflows/cotizaciones.yml) → **Run workflow → Actualizar → Run workflow**.

**Instrucciones y configuración de PP:** [LEEME-NUBE.md](LEEME-NUBE.md). Ejemplo de URL pública: [S30N6.json](https://paolonb56.github.io/cotizaciones-pp/S30N6.json).

Este repositorio ya está configurado e inicializado. Para el uso diario, elegir **Actualizar**. **Validar** comprueba los datos sin publicar; **Inicializar** se reserva para una instalación nueva sin histórico.

La validación en Linux, la primera publicación y una actualización posterior se comprobaron en GitHub: 17 URL verificadas e histórico conservado. La lectura dentro de PP escritorio/móvil requiere configurar las URL y probarla en esos dispositivos. No subir cartera, transacciones, credenciales ni TXT originales a este repositorio público.
