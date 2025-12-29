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
                html += f'<h4 class="text-[8px] font-bold text-gray-400 uppercase mt-2 mb-0.5">{line}</h4>'
            else:
                html += f'<p class="text-[8px] text-gray-400 leading-normal mb-0.5">{line}</p>'
        return html

    tnc_section = ""
    if template.get("terms_and_conditions"):
        tnc_section = f"""
        <div class="mt-6 pt-3 border-t border-gray-50">
            <h3 class="text-[9px] font-bold text-gray-300 uppercase tracking-widest mb-1">Terms & Conditions</h3>
            <div class="tnc-content">{process_notes(template["terms_and_conditions"])}</div>
        </div>
        """

    disclaimer_section = ""
    if template.get("disclaimer"):
        disclaimer_section = f"""
        <div class="mt-2 pt-2 border-t border-gray-50">
            <h3 class="text-[9px] font-bold text-gray-300 uppercase tracking-widest mb-1">Notice</h3>
            <div class="tnc-content">{process_notes(template["disclaimer"])}</div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice {invoice.get('invoice_number')}</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: 'Open Sans', sans-serif; color: #111827; }}
            .tnc-content p {{ margin-bottom: 4px; }}
            @media print {{ body {{ background: white; }} .p-8 {{ padding: 0 !important; }} }}
        </style>
    </head>
    <body class="bg-gray-100 antialiased p-4">
        <div class="max-w-3xl mx-auto bg-white min-h-screen shadow-lg p-8 md:p-12">
            
            <!-- Header -->
            <div class="flex flex-col md:flex-row justify-between items-start border-b-2 border-gray-900 pb-8 mb-8 gap-6">
                <div>
                    {logo_html}
                    <h1 class="text-3xl font-extrabold tracking-tight mb-1">{template.get('company_name', 'Company Name')}</h1>
                    <div class="text-xs text-gray-500 font-medium uppercase tracking-wide leading-relaxed">
                        <p>{template.get('company_address', '').replace('\n', ' • ')}</p>
                        <p class="mt-1">
                            {f'T: {template.get("company_phone")}' if template.get('company_phone') else ''}
                            {f' • E: {template.get("company_email")}' if template.get('company_email') else ''}
                        </p>
                        {f'<p class="font-bold text-gray-900 mt-1">SST ID: {template.get("sst_registration_no")}</p>' if template.get('sst_registration_no') else ''}
                    </div>
                </div>
                <div class="text-right">
                    <h2 class="text-4xl font-black text-gray-200 uppercase tracking-tighter leading-none mb-4">INVOICE</h2>
                    <div class="space-y-1">
                        <p class="text-xs font-bold text-gray-400 uppercase tracking-widest">Number</p>
                        <p class="text-xl font-bold">#{invoice.get('invoice_number')}</p>
                        <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mt-4">Date</p>
                        <p class="text-base font-bold">{invoice.get('invoice_date')}</p>
                    </div>
                </div>
            </div>

            <!-- Client Info -->
            <div class="mb-12">
                <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 border-b border-gray-100 pb-1 w-24">Billed To</p>
                <p class="text-xl font-extrabold uppercase">{invoice.get('customer_name_snapshot')}</p>
                <p class="text-sm text-gray-500 mt-1 leading-relaxed max-w-sm">{invoice.get('customer_address_snapshot') or 'No address provided'}</p>
            </div>

            <!-- Items -->
            <table class="w-full mb-12">
                <thead>
                    <tr class="text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b-2 border-gray-900">
                        <th class="text-left pb-2">Description</th>
                        <th class="text-right pb-2">Amount (RM)</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <!-- Summary & Payment -->
            <div class="flex flex-col md:flex-row justify-between gap-12">
                <!-- Bank Info (Professional Minimalist) -->
                <div class="flex-1">
                    <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 border-b border-gray-100 pb-1 w-32">Payment Info</p>
                    <div class="grid grid-cols-2 gap-y-3 gap-x-4 text-xs font-semibold">
                        <span class="text-gray-400 uppercase">Bank</span>
                        <span class="text-gray-900">{template.get('bank_name', '-')}</span>
                        <span class="text-gray-400 uppercase">Account</span>
                        <span class="text-gray-900 font-mono tracking-wider text-sm">{template.get('bank_account_no', '-')}</span>
                        <span class="text-gray-400 uppercase">Holder</span>
                        <span class="text-gray-900 uppercase">{template.get('bank_account_name', '-')}</span>
                    </div>
                </div>

                <!-- Totals -->
                <div class="w-full md:w-72 space-y-3">
                    <div class="flex justify-between text-sm font-semibold">
                        <span class="text-gray-400 uppercase">Subtotal</span>
                        <span>RM {fmt_money(invoice.get('subtotal'))}</span>
                    </div>
                    {f'''
                    <div class="flex justify-between text-sm font-semibold text-gray-400">
                        <span class="uppercase font-medium">SST ({fmt_money(invoice.get('sst_rate'))}%)</span>
                        <span class="text-gray-900">RM {fmt_money(invoice.get('sst_amount'))}</span>
                    </div>
                    ''' if float(invoice.get('sst_amount', 0)) > 0 else ''}
                    <div class="flex justify-between text-2xl font-black pt-4 border-t-4 border-gray-900">
                        <span class="uppercase tracking-tighter">Total</span>
                        <span>RM {fmt_money(invoice.get('total_amount'))}</span>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            {tnc_section}
            {disclaimer_section}

            <div class="mt-16 pt-8 border-t border-gray-50 text-center">
                <p class="text-[10px] font-bold text-gray-300 uppercase tracking-[0.4em]">Official Business Document</p>
            </div>
        </div>
    </body>
    </html>
    """
