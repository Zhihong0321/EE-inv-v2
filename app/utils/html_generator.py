from typing import Dict, Any

def generate_invoice_html(invoice: Dict[str, Any], template: Dict[str, Any]) -> str:
    """
    Generates a high-professional, business-oriented HTML invoice.
    """
    
    # Format currency
    def fmt_money(amount):
        if amount is None: return "0.00"
        return "{:,.2f}".format(float(amount))

    items_html = ""
    for item in invoice.get("items", []):
        items_html += f"""
        <tr class="border-b border-gray-100">
            <td class="py-3 pr-4">
                <p class="font-semibold text-gray-900 text-base">{item.get('description')}</p>
                <p class="text-[11px] text-gray-400 mt-0.5 uppercase tracking-wider">
                    {item.get('qty')} unit{'' if item.get('qty') == 1 else 's'} × {fmt_money(item.get('unit_price'))}
                </p>
            </td>
            <td class="py-3 text-right font-bold text-gray-900 text-base">
                {fmt_money(item.get('total_price'))}
            </td>
        </tr>
        """

    logo_html = ""
    if template.get("logo_url"):
        logo_html = f'<img src="{template["logo_url"]}" alt="Logo" class="h-10 mb-4 object-contain">'

    def process_notes(text):
        if not text: return ""
        lines = text.split('\n')
        html = ""
        for line in lines:
            line = line.strip()
            if not line: continue
            if len(line) < 40 and (line.isupper() or line.endswith(':')):
                html += f'<h4 class="text-[7px] font-bold text-gray-300 uppercase mt-1 mb-0">{line}</h4>'
            else:
                html += f'<p class="text-[7px] text-gray-300 leading-tight mb-0">{line}</p>'
        return html

    tnc_section = ""
    if template.get("terms_and_conditions"):
        tnc_section = f"""
        <div class="mt-4 pt-2 border-t border-gray-50">
            <h3 class="text-[7px] font-bold text-gray-300 uppercase tracking-widest mb-0.5">Terms & Conditions</h3>
            <div class="tnc-content">{process_notes(template["terms_and_conditions"])}</div>
        </div>
        """

    disclaimer_section = ""
    if template.get("disclaimer"):
        disclaimer_section = f"""
        <div class="mt-1 pt-1 border-t border-gray-50">
            <h3 class="text-[7px] font-bold text-gray-300 uppercase tracking-widest mb-0.5">Notice</h3>
            <div class="tnc-content">{process_notes(template["disclaimer"])}</div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Invoice {invoice.get('invoice_number')}</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: 'Open Sans', sans-serif; color: #111827; -webkit-tap-highlight-color: transparent; }}
            .tnc-content p {{ margin-bottom: 2px; }}
            @media print {{ body {{ background: white; }} .main-container {{ width: 100% !important; max-width: none !important; padding: 0 !important; box-shadow: none !important; }} }}
        </style>
    </head>
    <body class="bg-white antialiased">
        <div class="main-container w-full max-w-2xl mx-auto min-h-screen p-4 sm:p-6 md:p-8">
            
            <!-- Header: Mobile Optimized (Stacked on small, Row on med) -->
            <div class="flex flex-col md:flex-row justify-between items-start border-b border-gray-900 pb-6 mb-6 gap-4">
                <div class="w-full">
                    {logo_html}
                    <h1 class="text-2xl font-extrabold tracking-tight mb-1 uppercase">{template.get('company_name', 'Company Name')}</h1>
                    <div class="text-[10px] text-gray-500 font-medium uppercase tracking-wider leading-relaxed">
                        <p>{template.get('company_address', '').replace('\n', ' • ')}</p>
                        <p class="mt-0.5">
                            {f'T: {template.get("company_phone")}' if template.get('company_phone') else ''}
                            {f' • E: {template.get("company_email")}' if template.get('company_email') else ''}
                        </p>
                        {f'<p class="font-bold text-gray-900 mt-0.5">SST ID: {template.get("sst_registration_no")}</p>' if template.get('sst_registration_no') else ''}
                    </div>
                </div>
                <div class="flex flex-row md:flex-col justify-between md:text-right w-full md:w-auto items-end md:items-end border-t md:border-t-0 pt-4 md:pt-0 mt-2 md:mt-0 border-gray-100">
                    <div class="text-left md:text-right">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Invoice</p>
                        <p class="text-lg font-bold">#{invoice.get('invoice_number')}</p>
                    </div>
                    <div class="text-right mt-0 md:mt-4">
                        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Date</p>
                        <p class="text-sm font-bold">{invoice.get('invoice_date')}</p>
                    </div>
                </div>
            </div>

            <!-- Client Info: Compact -->
            <div class="mb-8">
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Billed To</p>
                <p class="text-lg font-extrabold uppercase leading-tight">{invoice.get('customer_name_snapshot')}</p>
                <p class="text-[11px] text-gray-500 mt-0.5 leading-normal italic">{invoice.get('customer_address_snapshot') or 'No address provided'}</p>
            </div>

            <!-- Items: Zero-Waste Table -->
            <table class="w-full mb-8 border-collapse">
                <thead>
                    <tr class="text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-gray-900">
                        <th class="text-left pb-2 font-black">Description</th>
                        <th class="text-right pb-2 font-black">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <!-- Summary & Payment: Responsive Grid -->
            <div class="flex flex-col md:flex-row justify-between gap-8 mb-8">
                <!-- Totals: Order 1 on mobile to show first -->
                <div class="w-full md:w-64 space-y-2 md:order-2">
                    <div class="flex justify-between text-sm font-semibold">
                        <span class="text-gray-400 uppercase">Subtotal</span>
                        <span>{fmt_money(invoice.get('subtotal'))}</span>
                    </div>
                    {f'''
                    <div class="flex justify-between text-sm font-semibold text-gray-400">
                        <span class="uppercase font-medium">SST ({fmt_money(invoice.get('sst_rate'))}%)</span>
                        <span class="text-gray-900">{fmt_money(invoice.get('sst_amount'))}</span>
                    </div>
                    ''' if float(invoice.get('sst_amount', 0)) > 0 else ''}
                    <div class="flex justify-between text-xl font-black pt-3 border-t-2 border-gray-900">
                        <span class="uppercase tracking-tighter">Total (RM)</span>
                        <span>{fmt_money(invoice.get('total_amount'))}</span>
                    </div>
                </div>

                <!-- Payment Info -->
                <div class="flex-1 md:order-1 border-t md:border-t-0 pt-6 md:pt-0 border-gray-100">
                    <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Payment Info</p>
                    <div class="grid grid-cols-2 gap-y-2 text-xs font-semibold">
                        <span class="text-gray-400 uppercase">Bank</span>
                        <span class="text-gray-900">{template.get('bank_name', '-')}</span>
                        <span class="text-gray-400 uppercase text-[10px]">Account</span>
                        <span class="text-gray-900 font-bold tracking-tight">{template.get('bank_account_no', '-')}</span>
                        <span class="text-gray-400 uppercase">Holder</span>
                        <span class="text-gray-900 uppercase truncate">{template.get('bank_account_name', '-')}</span>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            {tnc_section}
            {disclaimer_section}

            <div class="mt-12 pt-6 border-t border-gray-50 text-center">
                <p class="text-[9px] font-bold text-gray-300 uppercase tracking-[0.3em]">Official Digital Document</p>
            </div>
        </div>
    </body>
    </html>
    """
