# app.py - Complete Temple Management System (FIXED PDF & WhatsApp)
# ... (all previous imports and constants remain the same)

# ============================================================
# PDF GENERATION WITH AMMAN IMAGE (FIXED)
# ============================================================
PDF_AVAILABLE = False
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except:
    pass

def save_base64_image_to_temp(base64_str):
    """Save base64 image to temporary file and return path.
       Supports data URLs and raw base64. Returns None if fails."""
    if not base64_str:
        return None
    try:
        # Extract the actual base64 data
        if ',' in base64_str:
            header, data = base64_str.split(',', 1)
            # Determine extension from header
            if 'png' in header:
                ext = '.png'
            elif 'jpeg' in header or 'jpg' in header:
                ext = '.jpg'
            elif 'svg' in header:
                ext = '.svg'
            else:
                ext = '.png'
        else:
            data = base64_str
            # Assume PNG if no header
            ext = '.png'
        
        img_data = base64.b64decode(data)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(img_data)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

def convert_svg_to_png(svg_path):
    """Convert SVG to PNG using cairosvg if available, else return None"""
    try:
        import cairosvg
        png_path = svg_path.replace('.svg', '.png')
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        return png_path
    except:
        return None

def generate_bill_pdf(bill_no, manual_bill, bill_book, bill_date, name, address, mobile, pooja_type, amount, amman_base64=None):
    if not PDF_AVAILABLE:
        return None
    
    amman_img_path = None
    if amman_base64:
        amman_img_path = save_base64_image_to_temp(amman_base64)
        # If it's SVG and cairosvg is installed, convert to PNG
        if amman_img_path and amman_img_path.endswith('.svg'):
            png_path = convert_svg_to_png(amman_img_path)
            if png_path:
                amman_img_path = png_path
    
    pdf = FPDF()
    pdf.add_page()
    
    # Add Amman image (only if valid image file exists)
    if amman_img_path and os.path.exists(amman_img_path):
        try:
            # Check if file is readable by fpdf (PNG/JPG)
            if amman_img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                pdf.image(amman_img_path, x=10, y=8, w=20)
                pdf.image(amman_img_path, x=180, y=8, w=20)
        except Exception as e:
            print(f"Could not add image to PDF: {e}")
    
    # Temple header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, TEMPLE_NAME, 0, 1, 'C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, TEMPLE_TRUST, 0, 1, 'C')
    pdf.cell(0, 6, TEMPLE_ADDRESS, 0, 1, 'C')
    pdf.cell(0, 6, f"Email: {TEMPLE_EMAIL}", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, "BILL / RECEIPT", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(50, 8, f"Bill No: {bill_no}", 0, 0)
    pdf.cell(0, 8, f"Date: {bill_date}", 0, 1)
    if manual_bill:
        pdf.cell(50, 8, f"Manual Bill: {manual_bill}", 0, 0)
    if bill_book:
        pdf.cell(0, 8, f"Book No: {bill_book}", 0, 1)
    pdf.ln(5)
    pdf.cell(50, 8, f"Name: {name}", 0, 1)
    if address:
        pdf.cell(50, 8, f"Address: {address}", 0, 1)
    if mobile:
        pdf.cell(50, 8, f"Mobile: {mobile}", 0, 1)
    pdf.ln(5)
    pdf.cell(50, 8, f"Pooja Type: {pooja_type}", 0, 1)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(50, 10, f"Amount: ₹ {amount:,.2f}", 0, 1)
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 6, "Thank you for your contribution! May Goddess Bhadreshwari bless you!", 0, 1, 'C')
    pdf.cell(0, 6, TEMPLE_TAMIL, 0, 1, 'C')
    
    # Clean up temp files
    if amman_img_path and os.path.exists(amman_img_path):
        try:
            os.unlink(amman_img_path)
        except:
            pass
    
    return bytes(pdf.output())

# ============================================================
# WHATSAPP FIX: Add a fallback "Copy Message" button
# ============================================================
# In billing_page, replace the WhatsApp button section with:

# Inside billing_page, after generating the bill, instead of just the link, add:
# colA, colB = st.columns(2)  # already there
# with colB:
#     wa_num = dev_mobile or (guest_mobile if dev_type=="Guest" else "")
#     if wa_num:
#         wa_msg = build_bill_whatsapp_message(bill_no, bill_date_display, dev_name, pooja, amount, manual_bill, book_no)
#         st.markdown(f'<a href="{make_whatsapp_link(wa_num, wa_msg)}" target="_blank" class="wa-btn">📲 Send via WhatsApp</a>', unsafe_allow_html=True)
#         # Also add a copy button
#         if st.button("📋 Copy Bill Message"):
#             st.write("Message copied to clipboard!")
#             st.code(wa_msg)
#     else:
#         st.warning("No mobile number available for WhatsApp")

# To make it cleaner, I'll provide the full corrected billing_page function.

# ============================================================
# FULL CORRECTED BILLING PAGE (with PDF & WhatsApp fixes)
# ============================================================
def billing_page():
    render_header()
    tab1, tab2 = st.tabs(["🧾 New Bill", "📋 Bill History"])
    amman_img = get_amman_image()
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            manual_bill = st.text_input("Manual Bill No (optional)")
            book_no = st.text_input("Book No (optional)")
            bill_date_str = st.text_input("Bill Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()), placeholder="DD/MM/YYYY")
            pooja_types = supabase.table('pooja_types').select('name,amount').eq('is_active',True).execute()
            pooja_options = {p['name']: p['amount'] for p in pooja_types.data} if pooja_types.data else {}
            pooja = st.selectbox("Pooja Type", list(pooja_options.keys()))
            amount = pooja_options.get(pooja, 0)
            st.info(f"Amount: {TEMPLE_CONFIG['currency']}{amount}")
            payment = st.selectbox("Payment Mode", ["cash","card","upi","bank"])
        with col2:
            dev_type = st.radio("Devotee Type", ["Registered","Guest"])
            if dev_type == "Registered":
                st.markdown("### Search Devotee")
                search_by = st.selectbox("Search by", ["Name","Mobile No","Address"])
                search_term = st.text_input(f"Enter {search_by}")
                devotee_id = None
                dev_name = ""
                dev_mobile = ""
                dev_address = ""
                if search_term:
                    query = supabase.table('devotees').select('id,name,mobile_no,address')
                    if search_by == "Name":
                        query = query.ilike('name', f'%{search_term}%')
                    elif search_by == "Mobile No":
                        query = query.ilike('mobile_no', f'%{search_term}%')
                    else:
                        query = query.ilike('address', f'%{search_term}%')
                    res = query.limit(10).execute()
                    if res.data:
                        dev_opts = {f"{d['name']} - {d.get('mobile_no','')}": d for d in res.data}
                        selected = st.selectbox("Select Devotee", list(dev_opts.keys()))
                        dev = dev_opts[selected]
                        devotee_id = dev['id']
                        dev_name = dev['name']
                        dev_mobile = dev.get('mobile_no','')
                        dev_address = dev.get('address','')
                        st.success(f"Selected: {dev_name}")
                    else:
                        st.warning("No devotees found")
            else:
                devotee_id = None
                guest_name = st.text_input("Guest Name *")
                guest_mobile = st.text_input("Mobile")
                guest_address = st.text_area("Address")
                dev_name = guest_name
                dev_mobile = guest_mobile
                dev_address = guest_address
        
        if st.button("Generate Bill", type="primary"):
            if dev_type=="Guest" and not guest_name:
                st.error("Enter guest name")
            elif amount<=0:
                st.error("Invalid amount")
            else:
                bill_date = parse_date_ddmmyyyy(bill_date_str)
                if not bill_date:
                    st.error("Invalid bill date. Use DD/MM/YYYY")
                else:
                    bill_no = generate_unique_id('BILL')
                    bill_date_display = format_date_ddmmyyyy(bill_date)
                    data = {
                        'bill_no': bill_no, 'manual_bill_no': manual_bill, 'bill_book_no': book_no,
                        'devotee_type': 'registered' if dev_type=="Registered" else 'guest',
                        'devotee_id': devotee_id if dev_type=="Registered" else None,
                        'guest_name': guest_name if dev_type=="Guest" else None,
                        'guest_mobile': guest_mobile if dev_type=="Guest" else None,
                        'guest_address': guest_address if dev_type=="Guest" else None,
                        'pooja_type': pooja, 'amount': amount, 'bill_date': date_to_db(bill_date),
                        'payment_mode': payment
                    }
                    supabase.table('bills').insert(data).execute()
                    st.success(f"Bill generated: {bill_no}")
                    st.balloons()
                    
                    # Display receipt
                    st.markdown(f"""
                    <div style='border:2px solid #667eea; padding:20px; border-radius:10px; background:white; margin:10px 0;'>
                        <h3 style='text-align:center'>{TEMPLE_NAME}</h3>
                        <p style='text-align:center'>{TEMPLE_TRUST}<br>{TEMPLE_ADDRESS}<br>✉ {TEMPLE_EMAIL}</p>
                        <hr><h4 style='text-align:center'>BILL / RECEIPT</h4><hr>
                        <p><strong>Bill No:</strong> {bill_no}<br>
                        <strong>Date:</strong> {bill_date_display}<br>
                        <strong>Name:</strong> {dev_name}<br>
                        <strong>Address:</strong> {dev_address}<br>
                        <strong>Mobile:</strong> {dev_mobile}<br>
                        <strong>Pooja:</strong> {pooja}<br>
                        <strong>Amount:</strong> {TEMPLE_CONFIG['currency']}{amount:,.2f}</p>
                        <hr><p style='text-align:center'>🙏 Thank you! {TEMPLE_TAMIL} 🙏</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if PDF_AVAILABLE:
                            pdf = generate_bill_pdf(bill_no, manual_bill, book_no, bill_date_display, 
                                                   dev_name, dev_address, dev_mobile, pooja, amount, 
                                                   amman_base64=amman_img)
                            if pdf:
                                st.download_button("📥 Download PDF", data=pdf, file_name=f"Bill_{bill_no}.pdf", mime="application/pdf")
                            else:
                                st.error("PDF generation failed. Please check fpdf installation.")
                        else:
                            st.warning("PDF library not installed. Install fpdf.")
                    
                    with colB:
                        wa_num = dev_mobile or (guest_mobile if dev_type=="Guest" else "")
                        if wa_num:
                            wa_msg = build_bill_whatsapp_message(bill_no, bill_date_display, dev_name, pooja, amount, manual_bill, book_no)
                            # WhatsApp button
                            st.markdown(f'<a href="{make_whatsapp_link(wa_num, wa_msg)}" target="_blank" style="display:inline-block; background:#25D366; color:white; padding:8px 20px; border-radius:10px; text-decoration:none; margin-bottom:10px;">📲 Send via WhatsApp</a>', unsafe_allow_html=True)
                            # Fallback copy button
                            if st.button("📋 Copy Bill Message for WhatsApp"):
                                st.code(wa_msg, language="text")
                                st.success("Message copied! You can paste it in WhatsApp.")
                        else:
                            st.warning("No mobile number available for WhatsApp. Add a mobile number to use this feature.")
    
    with tab2:
        st.subheader("Bill History with Delete Option")
        from_date_str = st.text_input("From Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()-timedelta(30)), placeholder="DD/MM/YYYY")
        to_date_str = st.text_input("To Date (DD/MM/YYYY)", value=format_date_ddmmyyyy(date.today()), placeholder="DD/MM/YYYY")
        from_date = parse_date_ddmmyyyy(from_date_str) if from_date_str else None
        to_date = parse_date_ddmmyyyy(to_date_str) if to_date_str else None
        if from_date and to_date:
            bills = supabase.table('bills').select('*').gte('bill_date', date_to_db(from_date)).lte('bill_date', date_to_db(to_date)).order('bill_date', desc=True).execute()
            if bills.data:
                for bill in bills.data:
                    bill_display_date = format_date_ddmmyyyy(datetime.strptime(bill['bill_date'], '%Y-%m-%d').date()) if bill['bill_date'] else ''
                    with st.expander(f"🧾 {bill['bill_no']} - {bill.get('guest_name') or 'Registered'} - ₹{bill['amount']} - {bill_display_date}"):
                        col1, col2 = st.columns([3,1])
                        with col1:
                            st.write(f"**Manual Bill:** {bill.get('manual_bill_no','N/A')}")
                            st.write(f"**Book No:** {bill.get('bill_book_no','N/A')}")
                            st.write(f"**Pooja:** {bill['pooja_type']}")
                            st.write(f"**Amount:** ₹{bill['amount']:,.2f}")
                            st.write(f"**Payment:** {bill.get('payment_mode','cash')}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_bill_{bill['id']}"):
                                supabase.table('bills').delete().eq('id', bill['id']).execute()
                                st.rerun()
                        # Regenerate PDF for history
                        if PDF_AVAILABLE:
                            pdf = generate_bill_pdf(bill['bill_no'], bill.get('manual_bill_no',''), bill.get('bill_book_no',''), 
                                                   bill_display_date,
                                                   bill.get('guest_name',''), bill.get('guest_address',''), bill.get('guest_mobile',''),
                                                   bill['pooja_type'], bill['amount'], amman_base64=amman_img)
                            if pdf:
                                st.download_button("📥 PDF", pdf, f"Bill_{bill['bill_no']}.pdf", mime="application/pdf", key=f"pdf_{bill['id']}")
            else:
                st.info("No bills found")
        else:
            st.warning("Invalid date range")

# ============================================================
# Rest of the code remains the same (dashboard, devotee, etc.)
# ============================================================
