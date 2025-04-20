# Cotizador ThreatDown V17 con autenticación y roles de usuario - v3 (Granular Cost Discounts)

# ... (Keep previous imports and constants) ...
# ... (Keep conectar_db, hash_password, autenticar_usuario, crear_usuario, actualizar_contrasena) ...

# =================== Database Functions ===================
# ... (Keep conectar_db definition) ...

def inicializar_db():
    """Initializes the database and creates tables if they don't exist."""
    logging.info("Initializing database if needed...")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Usuarios Table (no changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                correo TEXT UNIQUE NOT NULL,
                contraseña TEXT NOT NULL,
                tipo_usuario TEXT CHECK(tipo_usuario IN ('superadmin', 'admin', 'user')),
                admin_id INTEGER,
                FOREIGN KEY (admin_id) REFERENCES usuarios(id)
            )
        """)
        # Clientes Table (no changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellido_paterno TEXT,
                apellido_materno TEXT,
                empresa TEXT UNIQUE NOT NULL,
                correo TEXT,
                telefono TEXT,
                rfc TEXT,
                calle TEXT,
                numero_exterior TEXT,
                numero_interior TEXT,
                codigo_postal TEXT,
                municipio TEXT,
                ciudad TEXT,
                estado TEXT,
                notas TEXT
            )
        """)
        # Cotizaciones Table (no changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                contacto TEXT,
                propuesta TEXT,
                fecha TEXT,
                responsable TEXT,
                total_venta REAL,
                total_costo REAL,
                utilidad REAL,
                margen REAL,
                vigencia TEXT,
                condiciones_comerciales TEXT,
                usuario_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        # Detalle Productos Table (MODIFIED: Added cost discount columns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER NOT NULL,
                producto TEXT,
                cantidad INTEGER,
                precio_unitario REAL, -- For venta: List Price | For costo: Base/MSRP Price
                precio_total REAL,    -- For venta: Final Sale Price | For costo: Final Cost Price
                descuento_aplicado REAL, -- For venta: Direct Sale Discount % | For costo: Item Discount %
                tipo_origen TEXT CHECK(tipo_origen IN ('venta', 'costo')),
                -- NEW COLUMNS FOR COST BREAKDOWN
                partner_discount REAL DEFAULT 0.0,
                deal_reg_discount REAL DEFAULT 0.0,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id) ON DELETE CASCADE
            )
        """)
        # --- Add columns if they don't exist (for upgrades) ---
        try:
            cursor.execute("ALTER TABLE detalle_productos ADD COLUMN partner_discount REAL DEFAULT 0.0;")
            logging.info("Added 'partner_discount' column to detalle_productos.")
        except sqlite3.OperationalError:
            pass # Column likely already exists
        try:
            cursor.execute("ALTER TABLE detalle_productos ADD COLUMN deal_reg_discount REAL DEFAULT 0.0;")
            logging.info("Added 'deal_reg_discount' column to detalle_productos.")
        except sqlite3.OperationalError:
            pass # Column likely already exists
        # --- End of column addition ---

        conn.commit()
        logging.info("Database schema checked/updated successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        st.error(f"Database initialization failed: {e}")
        st.stop()
    finally:
        if conn:
            conn.close()

# ... (Keep Authentication Functions: hash_password, autenticar_usuario, crear_usuario, actualizar_contrasena) ...
# ... (Keep CRM Functions: agregar_cliente, mostrar_clientes, cargar_clientes_para_seleccion) ...

# =================== Cotizador Functions ===================
# ... (Keep cargar_datos_precios) ...

def guardar_cotizacion(datos, productos_venta, productos_costo):
    """Saves a quotation and its details (including granular cost discounts) to the database."""
    logging.info(f"Saving quotation for: {datos.get('cliente', 'N/A')} | By User ID: {datos.get('usuario_id', 'N/A')}")
    cotizacion_id = None
    conn = None # Initialize conn to None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Insert main cotizacion record
        cursor.execute("""
            INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable,
                                    total_venta, total_costo, utilidad, margen, vigencia,
                                    condiciones_comerciales, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get("cliente"), datos.get("contacto"), datos.get("propuesta"), datos.get("fecha"),
            datos.get("responsable"), datos.get("total_venta"), datos.get("total_costo"),
            datos.get("utilidad"), datos.get("margen"), datos.get("vigencia"),
            datos.get("condiciones_comerciales"), datos.get("usuario_id")
        ))
        cotizacion_id = cursor.lastrowid
        logging.info(f"Quotation base record saved with ID: {cotizacion_id}")

        # Insert venta product details
        for p in productos_venta:
            cursor.execute("""
                INSERT INTO detalle_productos (
                    cotizacion_id, producto, cantidad, precio_unitario,
                    precio_total, descuento_aplicado, tipo_origen
                ) VALUES (?, ?, ?, ?, ?, ?, 'venta')
            """, (
                cotizacion_id, p.get("Producto"), p.get("Cantidad"), p.get("Precio Unitario de Lista"),
                p.get("Precio Total con Descuento"), p.get("Descuento %")
            ))

        # Insert costo product details (MODIFIED: Include new discounts)
        for p in productos_costo:
            cursor.execute("""
                INSERT INTO detalle_productos (
                    cotizacion_id, producto, cantidad, precio_unitario, precio_total,
                    descuento_aplicado, partner_discount, deal_reg_discount, tipo_origen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'costo')
            """, (
                cotizacion_id, p.get("Producto"), p.get("Cantidad"),
                p.get("Precio Base"), # MSRP/Base goes into precio_unitario for costo type
                p.get("Subtotal"),    # Final calculated cost goes into precio_total
                p.get("Item Disc. %"), # Item Discount stored in descuento_aplicado for costo type
                p.get("Partner Disc. %"), # Store Partner Discount
                p.get("Deal Reg. Disc. %"),# Store Deal Reg Discount
            ))

        conn.commit()
        logging.info(f"Quotation {cotizacion_id} and details saved successfully.")
        return cotizacion_id
    except sqlite3.Error as e:
        logging.error(f"Error saving quotation {cotizacion_id if cotizacion_id else 'N/A'}: {e}")
        st.error("Ocurrió un error al guardar la cotización.")
        if conn: # Rollback if commit failed or other error occurred
             conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

# ... (Keep ver_historial) ...

def obtener_detalle_cotizacion(cotizacion_id):
    """Fetches full details including granular cost discounts for a specific quotation ID."""
    logging.info(f"Fetching details for quotation ID: {cotizacion_id}")
    detalles = {}
    conn = None # Initialize conn to None
    try:
        conn = conectar_db()
        # Get main data
        datos_df = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = ?", conn, params=(cotizacion_id,))
        if datos_df.empty:
            logging.warning(f"Quotation ID {cotizacion_id} not found.")
            return None
        detalles['datos'] = datos_df.iloc[0]

        # Get venta products
        df_venta = pd.read_sql_query(f"""
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
            FROM detalle_productos
            WHERE cotizacion_id = ? AND tipo_origen = 'venta'
        """, conn, params=(cotizacion_id,))
        detalles['venta'] = df_venta

        # Get costo products (MODIFIED: Fetch new discount columns)
        df_costo = pd.read_sql_query(f"""
            SELECT
                producto, cantidad,
                precio_unitario, -- Base Price (MSRP)
                descuento_aplicado AS item_discount, -- Renamed for clarity
                partner_discount,
                deal_reg_discount,
                precio_total -- Final Calculated Cost
            FROM detalle_productos
            WHERE cotizacion_id = ? AND tipo_origen = 'costo'
        """, conn, params=(cotizacion_id,))
        detalles['costo'] = df_costo

        logging.info(f"Details fetched successfully for quotation ID: {cotizacion_id}")
        return detalles
    except sqlite3.Error as e:
        logging.error(f"Error fetching details for quotation {cotizacion_id}: {e}")
        st.error(f"Ocurrió un error al cargar el detalle de la cotización {cotizacion_id}.")
        return None
    finally:
        if conn:
            conn.close()

# ... (Keep PDF Generation Class - CotizacionPDFConLogo) ...
# ... (Keep Streamlit App UI & Logic - Initialization, Authentication Check) ...

# --- Main Application (User is Logged In) ---
# ... (Keep Sidebar setup) ...

# --- Dashboard View ---
# ... (Keep Dashboard code) ...

# --- Client Management View ---
# ... (Keep Client Management code) ...

# --- New Quotation View ---
elif menu == "Nueva Cotización":
    st.title("📝 Crear Nueva Cotización")

    # --- Load prerequisite data ---
    df_precios = cargar_datos_precios()
    if df_precios.empty:
        st.error("No se pueden crear cotizaciones sin datos de precios. Verifique el archivo Excel.")
        st.stop()

    df_clientes = cargar_clientes_para_seleccion()
    if df_clientes.empty:
        st.warning("⚠️ No hay clientes registrados. Por favor, agregue uno en la sección 'Clientes' antes de cotizar.")
        st.stop()

    # --- Form for Quotation Details ---
    with st.form("cotizacion_form"):
        st.subheader("1. Datos Generales")
        # ... (Keep client selection, propuesta, fecha, responsable, vigencia, condiciones) ...
        col_form1, col_form2 = st.columns(2)
        # Client Selection
        empresa_seleccionada = col_form1.selectbox("Selecciona la empresa cliente (*)", df_clientes["display_empresa"].unique(), key="empresa_sel")
        # Make sure df_clientes is not empty before attempting iloc
        if not df_clientes.empty and empresa_seleccionada:
            cliente_row = df_clientes[df_clientes["empresa"] == empresa_seleccionada].iloc[0]
            cliente_nombre_completo = f"{cliente_row['nombre']} {cliente_row['apellido_paterno']} {cliente_row['apellido_materno']}".strip()
            contacto_display = cliente_nombre_completo if cliente_nombre_completo else cliente_row['correo'] # Fallback to email if no name
            col_form1.info(f"Contacto principal detectado: **{contacto_display}**")
        else:
             contacto_display = "" # Handle case where selection might be empty initially


        propuesta = col_form2.text_input("Nombre de la propuesta (*)")
        fecha_cot = st.date_input("Fecha (*)", value=date.today())
        responsable = st.text_input("Responsable / Vendedor (*)", value=st.session_state.usuario['nombre']) # Default to logged in user
        vigencia = st.text_input("Vigencia de la propuesta", value="15 días")
        condiciones_comerciales = st.text_area(
            "Condiciones de Pago y Comerciales",
            value="Precios en USD más IVA. Pago anticipado. Licenciamiento anual. No incluye servicios de implementación.",
            height=120
        )


        st.subheader("2. Selección de Productos y Cantidades")
        # ... (Keep term selection, product selection) ...
        terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique().astype(int))
        termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (meses) (*):", terminos_disponibles, key="term_sel")

        df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado].copy()
        productos_disponibles = sorted(df_filtrado_termino["Product Title"].unique())
        productos_seleccionados = st.multiselect("Selecciona los productos a cotizar (*):", productos_disponibles, key="prod_sel")


        st.subheader("3. Configuración de Precios y Descuentos")
        productos_cotizacion_costo = []
        productos_cotizacion_venta = []
        costo_total_calculado = 0.0
        venta_total_calculada = 0.0
        input_valid = True

        if not productos_seleccionados:
            st.warning("Seleccione al menos un producto.")
            input_valid = False
        else:
            # Calculate Costs (Internal View - MODIFIED for granular discounts)
            st.markdown("**Cálculo de Costos (Referencia Interna)**")
            # Adjust column count if needed
            cols_costo_header = st.columns([2, 1, 1.5, 1, 1, 1, 1.5]) # Product, Qty, Base, Item%, Part%, Deal%, Subtotal
            cols_costo_header[0].markdown("**Producto**")
            cols_costo_header[1].markdown("**Cant.**")
            cols_costo_header[2].markdown("**P. Base (USD)**")
            cols_costo_header[3].markdown("**Item %**")
            cols_costo_header[4].markdown("**Partner %**")
            cols_costo_header[5].markdown("**Deal Reg %**")
            cols_costo_header[6].markdown("**Subtotal Costo**")


            for i, prod in enumerate(productos_seleccionados):
                cols_prod_costo = st.columns([2, 1, 1.5, 1, 1, 1, 1.5]) # Align with header
                df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]

                with cols_prod_costo[0]: # Product Name
                    st.markdown(f"*{prod}*", unsafe_allow_html=True)
                with cols_prod_costo[1]: # Quantity
                    cantidad = st.number_input(f"Qty", min_value=1, value=1, step=1, key=f"qty_cost_{i}", label_visibility="collapsed")

                # Find Price Base based on Quantity
                df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]
                if df_rango.empty:
                     with cols_prod_costo[2]: # Base Price
                         st.error(f"No TIER") # Show error in price column
                         precio_base = 0
                         input_valid = False
                     # Set subsequent values to 0 or disable inputs if no base price
                     item_disc = 0.0
                     partner_disc = 0.0
                     deal_reg_disc = 0.0
                     precio_final_unit_costo = 0.0
                else:
                     precio_base = df_rango.iloc[0]["MSRP USD"]
                     with cols_prod_costo[2]: # Base Price
                         st.metric(label="", value=f"${precio_base:,.2f}")

                     # Get Discounts
                     with cols_prod_costo[3]: # Item Discount
                        item_disc = st.number_input(f"ItemD", 0.0, 100.0, 0.0, step=0.5, key=f"item_disc_{i}", format="%.2f", label_visibility="collapsed", help="Item Discount %")
                     with cols_prod_costo[4]: # Partner Discount
                        partner_disc = st.number_input(f"PartD", 0.0, 100.0, 0.0, step=0.5, key=f"partner_disc_{i}", format="%.2f", label_visibility="collapsed", help="Partner Discount %")
                     with cols_prod_costo[5]: # Deal Reg Discount
                        deal_reg_disc = st.number_input(f"DealD", 0.0, 100.0, 0.0, step=0.5, key=f"deal_disc_{i}", format="%.2f", label_visibility="collapsed", help="Deal Registration Discount %")

                     # === GRANULAR COST CALCULATION ===
                     # 1. Apply Item Discount
                     precio_after_item_disc = precio_base * (1.0 - item_disc / 100.0)
                     # 2. Combine Partner & Deal Reg Discounts (Applied to result of step 1)
                     #    IMPORTANT: Ensure this logic is correct. If Partner is applied first, then DealReg on THAT result, it's different.
                     #    Current logic: Both Partner% and DealReg% apply to the 'precio_after_item_disc'.
                     combined_second_stage_disc_rate = (partner_disc + deal_reg_disc) / 100.0
                     precio_final_unit_costo = precio_after_item_disc * (1.0 - combined_second_stage_disc_rate)
                     # ==================================

                # Calculate and display Cost Subtotal
                subtotal_costo = precio_final_unit_costo * cantidad
                costo_total_calculado += subtotal_costo
                with cols_prod_costo[6]: # Subtotal Cost
                     st.metric(label="", value=f"${subtotal_costo:,.2f}")

                # Append to list for saving (MODIFIED: include all discounts)
                productos_cotizacion_costo.append({
                    "Producto": prod,
                    "Cantidad": cantidad,
                    "Precio Base": precio_base,
                    "Item Disc. %": item_disc,
                    "Partner Disc. %": partner_disc, # Added
                    "Deal Reg. Disc. %": deal_reg_disc, # Added
                    "Precio Final Unitario Costo": round(precio_final_unit_costo, 2), # For reference
                    "Subtotal": round(subtotal_costo, 2) # Final cost subtotal
                })
                st.divider() # Visually separate products in the form

            # Calculate Sale Price (Client View - No changes needed here unless Sale logic changes)
            st.markdown("**Cálculo de Precio de Venta (Para Cliente)**")
            cols_venta = st.columns(5)
            cols_venta[0].markdown("**Producto**")
            cols_venta[1].markdown("**Cantidad**")
            cols_venta[2].markdown("**P. Lista Unit. (USD)**")
            cols_venta[3].markdown("**Desc. Venta (%)**")
            cols_venta[4].markdown("**Subtotal Venta (USD)**")

            for i, prod in enumerate(productos_seleccionados):
                cost_item = next((item for item in productos_cotizacion_costo if item["Producto"] == prod), None)
                if not cost_item or not input_valid: continue # Skip if cost calc failed

                cols_prod_venta = st.columns(5)
                with cols_prod_venta[0]:
                     st.markdown(f"*{prod}*", unsafe_allow_html=True)
                with cols_prod_venta[1]:
                     st.metric(label="", value=f"{cost_item['Cantidad']}")
                with cols_prod_venta[2]:
                     precio_unitario_lista = cost_item['Precio Base'] # Use MSRP as list price for client
                     st.metric(label="", value=f"${precio_unitario_lista:,.2f}")

                with cols_prod_venta[3]:
                     descuento_venta_directo = st.number_input(f"Desc. Venta", 0.0, 100.0, 0.0, step=0.5, key=f"venta_disc_{i}", format="%.2f", label_visibility="collapsed")

                precio_total_lista_linea = precio_unitario_lista * cost_item['Cantidad']
                precio_con_descuento_venta = precio_total_lista_linea * (1 - descuento_venta_directo / 100.0)
                venta_total_calculada += precio_con_descuento_venta

                with cols_prod_venta[4]:
                    st.metric(label="", value=f"${precio_con_descuento_venta:,.2f}")

                productos_cotizacion_venta.append({
                    "Producto": prod,
                    "Cantidad": cost_item['Cantidad'],
                    "Precio Unitario de Lista": round(precio_unitario_lista, 2),
                    "Precio Total de Lista": round(precio_total_lista_linea, 2),
                    "Descuento %": descuento_venta_directo,
                    "Precio Total con Descuento": round(precio_con_descuento_venta, 2)
                })
                st.divider()

        # --- Summary and Submit ---
        st.subheader("4. Resumen y Guardar")
        # ... (Keep Summary columns: Costo Total, Venta Total, Utilidad, Margen) ...
        if venta_total_calculada > 0 and input_valid:
            utilidad_calculada = venta_total_calculada - costo_total_calculado
            margen_calculado = (utilidad_calculada / venta_total_calculada) * 100 if venta_total_calculada else 0

            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            col_res1.metric("Costo Total Estimado", f"${costo_total_calculado:,.2f}")
            col_res2.metric("Venta Total (Cliente)", f"${venta_total_calculada:,.2f}")
            col_res3.metric("Utilidad Estimada", f"${utilidad_calculada:,.2f}")
            col_res4.metric("Margen Estimado", f"{margen_calculado:.2f}%",
                           delta=f"{margen_calculado - 15:.2f}%" if margen_calculado < 15 else None,
                           delta_color="inverse")
        else:
            st.warning("Complete la selección y configuración de productos para ver el resumen.")


        submitted_cot = st.form_submit_button("💾 Guardar Cotización")
        if submitted_cot:
             # Final validation before saving
            if not all([empresa_seleccionada, propuesta, fecha_cot, responsable, termino_seleccionado, productos_seleccionados]) or not input_valid:
                 st.error("❌ Faltan datos obligatorios (*) o hay errores en la configuración de precios/tier. Revise el formulario.")
            elif venta_total_calculada <= 0:
                 st.error("❌ El total de la venta no puede ser cero o negativo.")
            elif not productos_cotizacion_costo or not productos_cotizacion_venta:
                 st.error("❌ Error interno: No se generaron los detalles de productos para guardar.")
            else:
                datos_guardar = {
                    "cliente": empresa_seleccionada,
                    "contacto": contacto_display,
                    "propuesta": propuesta,
                    "fecha": fecha_cot.strftime('%Y-%m-%d'),
                    "responsable": responsable,
                    "total_venta": venta_total_calculada,
                    "total_costo": costo_total_calculado,
                    "utilidad": utilidad_calculada,
                    "margen": margen_calculado,
                    "vigencia": vigencia,
                    "condiciones_comerciales": condiciones_comerciales,
                    "usuario_id": st.session_state.usuario['id']
                }

                cot_id = guardar_cotizacion(datos_guardar, productos_cotizacion_venta, productos_cotizacion_costo)
                if cot_id:
                    st.success(f"✅ Cotización #{cot_id} guardada exitosamente.")
                    # Consider clearing form state or using st.rerun() if desired after save
                else:
                    st.error("❌ Hubo un problema al guardar la cotización en la base de datos.")


# --- History View ---
elif menu == "Historial":
    st.title("📋 Historial de Cotizaciones")
    df_hist = ver_historial(st.session_state.usuario)

    if df_hist.empty:
        st.info("No hay cotizaciones guardadas para mostrar.")
    else:
        st.dataframe(df_hist) # Show main history table

        st.subheader("🔍 Ver Detalle y Generar PDF")
        cotizacion_id_seleccionada = st.selectbox(
            "Selecciona el ID de una cotización para ver detalles:",
            options=[""] + list(df_hist['id'].unique()),
            format_func=lambda x: f"Cotización #{x}" if x else "Seleccionar..."
        )

        if cotizacion_id_seleccionada:
            detalles_cot = obtener_detalle_cotizacion(cotizacion_id_seleccionada)

            if detalles_cot:
                datos = detalles_cot['datos']
                df_venta_det = detalles_cot['venta']
                df_costo_det = detalles_cot['costo'] # Contains the detailed cost breakdown

                # ... (Keep display of general data, financial summary, commercial conditions) ...
                st.markdown("---")
                st.markdown(f"### Detalle Cotización #{cotizacion_id_seleccionada}")
                col_det1, col_det2 = st.columns(2)
                col_det1.markdown(f"**Cliente:** {datos['cliente']}")
                col_det1.markdown(f"**Contacto:** {datos['contacto']}")
                col_det1.markdown(f"**Propuesta:** {datos['propuesta']}")
                col_det2.markdown(f"**Fecha:** {datos['fecha']}")
                col_det2.markdown(f"**Responsable:** {datos['responsable']}")
                col_det2.markdown(f"**Vigencia:** {datos['vigencia']}")

                st.markdown("**Resumen Financiero:**")
                col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
                col_fin1.metric("Total Venta", f"${datos['total_venta']:,.2f}")
                col_fin2.metric("Total Costo", f"${datos['total_costo']:,.2f}")
                col_fin3.metric("Utilidad", f"${datos['utilidad']:,.2f}")
                col_fin4.metric("Margen", f"{datos['margen']:.2f}%")

                st.markdown(f"**Condiciones Comerciales:** \n{datos['condiciones_comerciales']}")


                st.markdown("#### Productos Cotizados (Precio Cliente)")
                # Display Sale items - use appropriate columns
                st.dataframe(df_venta_det[[
                    "producto", "cantidad", "precio_unitario", "descuento_aplicado", "precio_total"
                ]].rename(columns={
                    "precio_unitario": "P. Unit. Lista",
                    "descuento_aplicado": "Desc. Venta %",
                    "precio_total": "Total Venta"
                    }))


                # MODIFIED: Show cost breakdown with all discounts (conditionally)
                if st.session_state.usuario['tipo'] in ['admin', 'superadmin']:
                    with st.expander("Ver desglose de costos (interno)"):
                         st.markdown("#### Productos Base (Costos Internos Detallados)")
                         # Rename columns for clarity in the display
                         df_costo_display = df_costo_det.rename(columns={
                             "precio_unitario": "P. Base MSRP",
                             "item_discount": "Item Disc. %",
                             "partner_discount": "Partner Disc. %",
                             "deal_reg_discount": "Deal Reg. Disc. %",
                             "precio_total": "Costo Final"
                         })
                         # Select and order columns for display
                         st.dataframe(df_costo_display[[
                             "producto", "cantidad", "P. Base MSRP", "Item Disc. %",
                             "Partner Disc. %", "Deal Reg. Disc. %", "Costo Final"
                         ]])

                # --- PDF Generation Button ---
                st.markdown("---")
                if st.button(f"📄 Generar PDF para Cliente (Cotización #{cotizacion_id_seleccionada})"):
                    # ... (Keep PDF generation logic - it uses df_venta_det which is correct for client) ...
                    with st.spinner("Generando PDF..."):
                        try:
                            pdf = CotizacionPDFConLogo()
                            pdf.set_auto_page_break(auto=True, margin=15)
                            pdf.set_title(f"Cotizacion {datos['propuesta']}")
                            pdf.set_author(datos['responsable'])
                            pdf.alias_nb_pages()
                            pdf.add_page()

                            datos_dict_pdf = datos.to_dict()

                            pdf.encabezado_cliente(datos_dict_pdf)
                            # Prepare venta data for PDF - ensure correct columns are passed if needed by PDF class
                            pdf_venta_data_for_table = df_venta_det.rename(columns={
                                'precio_unitario': 'precio_unitario_lista', # Example rename if needed
                                'descuento_aplicado': 'descuento_venta_perc',
                                'precio_total': 'precio_final_venta'
                            })
                            pdf.tabla_productos(pdf_venta_data_for_table) # Pass venta DataFrame
                            pdf.totales(datos['total_venta'])
                            pdf.condiciones(datos['vigencia'], datos['condiciones_comerciales'])
                            pdf.firma(datos['responsable'])

                            pdf_output_path = f"Cotizacion_{datos['cliente'].replace(' ','_')}_{cotizacion_id_seleccionada}.pdf"
                            pdf_bytes = pdf.output(dest='S').encode('latin-1')

                            st.download_button(
                                label="📥 Descargar PDF de Cotización",
                                data=pdf_bytes,
                                file_name=pdf_output_path,
                                mime="application/pdf"
                            )
                            logging.info(f"PDF generated successfully for Cotizacion {cotizacion_id_seleccionada}")

                        except Exception as e:
                            logging.error(f"Error generating PDF for {cotizacion_id_seleccionada}: {e}")
                            st.error(f"Error al generar el PDF: {e}")
            else:
                st.error(f"No se pudieron cargar los detalles para la cotización {cotizacion_id_seleccionada}.")


# --- User Management View ---
# ... (Keep User Management code) ...

# --- Fallback for unknown menu option ---
# ... (Keep Fallback code) ...

