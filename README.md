# Cotizaciones para Portfolio Performance

Actualización manual desde el celular mediante **GitHub Actions**, con JSON públicos y URL estables en **GitHub Pages**. La PC puede estar apagada.

- Bonos QuickTrade y MEP/CCL: descarga automática al pulsar **Actualizar cotizaciones**.
- FCI: adquisición manual desde Balanz, conversión en la PC y carga de JSON en [entradas-fci](entradas-fci/README.md). No se hace scraping.
- Conservación de históricos, validación completa antes de publicar y verificación de las URL.
- Sin pCloud, Termux, token personal ni conversor web.

**Instalación y uso:** [LEEME-NUBE.md](LEEME-NUBE.md).

En la primera instalación: configurar **Settings → Pages → Source: GitHub Actions**, ejecutar **Validar**, revisar el contenido público y ejecutar **Inicializar**. Para el uso diario: **Actions → Actualizar cotizaciones → Run workflow → Actualizar**.

La preparación local no prueba el funcionamiento remoto. No subir cartera, transacciones, credenciales ni TXT originales a este repositorio público.
