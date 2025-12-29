from typing import Dict, Any

def generate_invoice_html(invoice: Dict[str, Any], template: Dict[str, Any]) -> str:
    """
    Generates a premium, minimalist, and modern mobile-optimized HTML invoice.
    """
    
    # Format currency
    def fmt_money(amount):
        if amount is None: return "0.00"
        return "{:,.2f}".format(float(amount))

    items_html = ""
    for item in invoice.get("items", []):
        items_html += f"""
        <div class="py-4 border-b border-gray-100 last:border-0">
            <div class="flex justify-between items-start">
                <div class="flex-1 pr-4">
                    <p class="font-semibold text-gray-800 text-sm">{item.get('description')}</p>
                    <p class="text-xs text-gray-400 mt-0.5 font-medium">
                        {item.get('qty')} unit{'' if item.get('qty') == 1 else 's'} × {fmt_money(item.get('unit_price'))}
                    </p>
                </div>
                <div class="text-right">
                    <p class="font-bold text-gray-900 text-sm">RM {fmt_money(item.get('total_price'))}</p>
                </div>
            </div>
        </div>
        """

    logo_html = ""
    if template.get("logo_url"):
        logo_html = f'<img src="{template["logo_url"]}" alt="Logo" class="h-12 mb-6 object-contain">'

    def process_notes(text):
        if not text: return ""
        # Simple heading detection: lines ending with : or short lines followed by content
        lines = text.split('\n')
        html = ""
        for line in lines:
            line = line.strip()
            if not line: continue
            if len(line) < 40 and (line.isupper() or line.endswith(':')):
                html += f'<h4 class="text-[10px] font-bold text-gray-900 uppercase tracking-widest mt-4 mb-1 border-b border-gray-100 pb-1">{line}</h4>'
            else:
                html += f'<p class="text-[11px] text-gray-500 leading-relaxed mb-2">{line}</p>'
        return html

    tnc_section = ""
    if template.get("terms_and_conditions"):
        tnc_section = f"""
        <div class="mt-8 pt-6 border-t-2 border-gray-50">
            <h3 class="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4">Terms & Conditions</h3>
            {process_notes(template["terms_and_conditions"])}
        </div>
        """

    disclaimer_section = ""
    if template.get("disclaimer"):
        disclaimer_section = f"""
        <div class="mt-6 pt-4 border-t border-gray-50 bg-gray-50/50 p-4 rounded-xl">
            <h3 class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Notice</h3>
            {process_notes(template["disclaimer"])}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Invoice {invoice.get('invoice_number')}</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ 
                font-family: 'Open Sans', sans-serif; 
                -webkit-font-smoothing: antialiased;
                color: #1a1a1a;
            }}
            @media print {{
                .no-print {{ display: none; }}
                body {{ background: white; }}
            }}
        </style>
    </head>
    <body class="bg-slate-50 antialiased">
        <div class="max-w-xl mx-auto bg-white min-h-screen shadow-2xl shadow-slate-200/50 relative overflow-hidden flex flex-col">
            
            <!-- Branding Stripe -->
            <div class="h-1.5 w-full bg-indigo-600"></div>

            <div class="p-8 flex-grow">
                <!-- Header -->
                <div class="flex flex-col md:flex-row justify-between items-start gap-6 mb-12">
                    <div class="w-full md:w-auto">
                        {logo_html}
                        <h1 class="text-2xl font-extrabold tracking-tight text-gray-900 leading-none mb-2 uppercase italic">{template.get('company_name', 'Company Name')}</h1>
                        <div class="text-[11px] text-gray-400 font-medium space-y-0.5 uppercase tracking-wider">
                            <p>{template.get('company_address', '').replace('\n', ' • ')}</p>
                            <p>
                                {f'TEL: {template.get("company_phone")}' if template.get('company_phone') else ''}
                                {f' • EMAIL: {template.get("company_email")}' if template.get('company_email') else ''}
                            </p>
                            {f'<p class="text-indigo-600 font-bold mt-1">SST NO: {template.get("sst_registration_no")}</p>' if template.get('sst_registration_no') else ''}
                        </div>
                    </div>
                    
                    <div class="bg-gray-900 text-white p-6 rounded-2xl w-full md:w-48 text-center md:text-right">
                        <p class="text-[10px] font-bold uppercase tracking-widest opacity-50 mb-1">Total Amount</p>
                        <p class="text-2xl font-black leading-none">RM {fmt_money(invoice.get('total_amount'))}</p>
                    </div>
                </div>

                <!-- Meta Info -->
                <div class="grid grid-cols-2 gap-8 mb-12 bg-indigo-50/30 p-6 rounded-2xl border border-indigo-50/50">
                    <div>
                        <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-2">Invoice Details</p>
                        <div class="space-y-1">
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-gray-400">Number</span>
                                <span class="font-bold text-gray-900">#{invoice.get('invoice_number')}</span>
                            </div>
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-gray-400">Issued</span>
                                <span class="font-bold text-gray-900">{invoice.get('invoice_date')}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-2">Billed To</p>
                        <p class="text-xs font-bold text-gray-900 uppercase truncate">{invoice.get('customer_name_snapshot')}</p>
                        <p class="text-[10px] text-gray-500 font-medium mt-1 leading-relaxed line-clamp-2 italic">{invoice.get('customer_address_snapshot') or 'Address not provided'}</p>
                    </div>
                </div>

                <!-- Items Table -->
                <div class="mb-12">
                    <div class="flex justify-between text-[10px] font-black text-gray-400 uppercase tracking-widest mb-4 px-1">
                        <span>Description</span>
                        <span>Amount (RM)</span>
                    </div>
                    <div class="space-y-1">
                        {items_html}
                    </div>
                </div>

                <!-- Totals -->
                <div class="flex justify-end mb-12">
                    <div class="w-full md:w-64 space-y-2 px-1">
                        <div class="flex justify-between text-xs text-gray-400 font-medium">
                            <span>Subtotal</span>
                            <span class="text-gray-900 font-bold">RM {fmt_money(invoice.get('subtotal'))}</span>
                        </div>
                        {f'''
                        <div class="flex justify-between text-xs text-gray-400 font-medium">
                            <span>SST ({fmt_money(invoice.get('sst_rate'))}%)</span>
                            <span class="text-gray-900 font-bold">RM {fmt_money(invoice.get('sst_amount'))}</span>
                        </div>
                        ''' if float(invoice.get('sst_amount', 0)) > 0 else ''}
                        <div class="pt-2 border-t-2 border-gray-900 flex justify-between items-baseline">
                            <span class="text-xs font-black uppercase tracking-tighter">Grand Total</span>
                            <span class="text-xl font-black text-gray-900 tracking-tighter">RM {fmt_money(invoice.get('total_amount'))}</span>
                        </div>
                    </div>
                </div>

                <!-- Payment Details -->
                <div class="bg-indigo-600 rounded-3xl p-8 text-white relative overflow-hidden shadow-xl shadow-indigo-200">
                    <!-- Decor -->
                    <div class="absolute -right-4 -top-4 w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>
                    
                    <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-6 opacity-80 flex items-center">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>
                        How to Pay
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="space-y-4">
                            <div class="flex flex-col">
                                <span class="text-[10px] font-bold text-indigo-200 uppercase tracking-widest mb-1">Bank Name</span>
                                <span class="text-sm font-extrabold uppercase">{template.get('bank_name', '-')}</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-[10px] font-bold text-indigo-200 uppercase tracking-widest mb-1">Account Holder</span>
                                <span class="text-sm font-extrabold uppercase tracking-tight">{template.get('bank_account_name', '-')}</span>
                            </div>
                        </div>
                        <div class="bg-white/10 p-4 rounded-2xl flex flex-col justify-center border border-white/10">
                            <span class="text-[10px] font-bold text-indigo-100 uppercase tracking-[0.3em] mb-1">Account Number</span>
                            <span class="text-xl font-black tracking-widest font-mono tabular-nums">{template.get('bank_account_no', '-')}</span>
                        </div>
                    </div>
                </div>

                <!-- Footer Section (TNC & Disclaimer) -->
                {tnc_section}
                {disclaimer_section}

                <!-- Bottom Signature/Closing -->
                <div class="mt-12 text-center">
                    <p class="text-[10px] font-black text-gray-300 uppercase tracking-[0.5em] mb-4">Thank you for your business</p>
                    <p class="text-[9px] text-gray-300 italic">Generated by EE Invoicing Cloud System</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
