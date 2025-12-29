from typing import Dict, Any

def generate_invoice_html(invoice: Dict[str, Any], template: Dict[str, Any]) -> str:
    """
    Generates a minimalist, mobile-optimized HTML invoice.
    
    Style:
    - No card boxes (flat design)
    - Line separators (border-b)
    - No margins between blocks
    """
    
    # Format currency
    def fmt_money(amount):
        if amount is None: return "0.00"
        return "{:,.2f}".format(float(amount))

    # Helper for optional fields
    def get_val(obj, key, default=""):
        return obj.get(key) or default

    items_html = ""
    for item in invoice.get("items", []):
        items_html += f"""
        <div class="py-3 border-b border-gray-200">
            <div class="flex justify-between items-start">
                <div class="w-2/3">
                    <p class="font-medium text-gray-900">{item.get('description')}</p>
                    <p class="text-xs text-gray-500">Qty: {item.get('qty')} x {fmt_money(item.get('unit_price'))}</p>
                </div>
                <div class="w-1/3 text-right">
                    <p class="font-medium text-gray-900">{fmt_money(item.get('total_price'))}</p>
                </div>
            </div>
        </div>
        """

    logo_html = ""
    if template.get("logo_url"):
        logo_html = f'<img src="{template["logo_url"]}" alt="Logo" class="h-16 mb-4 object-contain">'

    tnc_html = ""
    if template.get("terms_and_conditions"):
        tnc_html = f"""
        <div class="py-4 border-b border-gray-200">
            <p class="text-xs font-bold text-gray-500 uppercase mb-1">Terms & Conditions</p>
            <p class="text-xs text-gray-600 whitespace-pre-line">{template["terms_and_conditions"]}</p>
        </div>
        """

    disclaimer_html = ""
    if template.get("disclaimer"):
        disclaimer_html = f"""
        <div class="py-4 border-b border-gray-200">
            <p class="text-xs font-bold text-gray-500 uppercase mb-1">Disclaimer</p>
            <p class="text-xs text-gray-600 whitespace-pre-line">{template["disclaimer"]}</p>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice {invoice.get('invoice_number')}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
            .no-margin-blocks > div {{ margin-bottom: 0; }}
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div class="max-w-md mx-auto bg-white min-h-screen shadow-none sm:shadow-sm">
            
            <!-- Header -->
            <div class="p-6 border-b border-gray-200 text-center">
                {logo_html}
                <h1 class="text-xl font-bold text-gray-900">{template.get('company_name', 'Company Name')}</h1>
                <p class="text-sm text-gray-600 mt-1 whitespace-pre-line">{template.get('company_address', '')}</p>
                <div class="mt-2 text-xs text-gray-500">
                    {f'<span>{template.get("company_phone")}</span>' if template.get('company_phone') else ''}
                    {f'<span class="mx-1">•</span>' if template.get('company_phone') and template.get('company_email') else ''}
                    {f'<span>{template.get("company_email")}</span>' if template.get('company_email') else ''}
                </div>
                <p class="text-xs text-gray-500 mt-1">SST No: {template.get('sst_registration_no', '-')}</p>
            </div>

            <!-- Invoice Details -->
            <div class="grid grid-cols-2 border-b border-gray-200 divide-x divide-gray-200">
                <div class="p-4 text-center">
                    <p class="text-xs text-gray-500 uppercase">Invoice No</p>
                    <p class="font-bold text-gray-900">{invoice.get('invoice_number')}</p>
                </div>
                <div class="p-4 text-center">
                    <p class="text-xs text-gray-500 uppercase">Date</p>
                    <p class="font-bold text-gray-900">{invoice.get('invoice_date')}</p>
                </div>
            </div>

            <!-- Customer -->
            <div class="p-4 border-b border-gray-200 bg-gray-50">
                <p class="text-xs text-gray-500 uppercase mb-1">Bill To</p>
                <p class="font-bold text-gray-900">{invoice.get('customer_name_snapshot')}</p>
                <p class="text-sm text-gray-600 mt-1">{invoice.get('customer_address_snapshot') or 'No address provided'}</p>
            </div>

            <!-- Items -->
            <div class="p-4 border-b border-gray-200">
                <p class="text-xs text-gray-500 uppercase mb-2">Items</p>
                {items_html}
            </div>

            <!-- Totals -->
            <div class="p-4 border-b border-gray-200 space-y-2">
                <div class="flex justify-between text-sm text-gray-600">
                    <span>Subtotal</span>
                    <span>{fmt_money(invoice.get('subtotal'))}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600">
                    <span>SST ({fmt_money(invoice.get('sst_rate'))}%)</span>
                    <span>{fmt_money(invoice.get('sst_amount'))}</span>
                </div>
                <div class="flex justify-between text-xl font-bold text-gray-900 pt-2 border-t border-dashed border-gray-200 mt-2">
                    <span>Total</span>
                    <span>{fmt_money(invoice.get('total_amount'))}</span>
                </div>
            </div>

            <!-- Bank Info -->
            <div class="p-4 border-b border-gray-200 bg-blue-50">
                <p class="text-xs font-bold text-blue-800 uppercase mb-2">Payment Details</p>
                <div class="text-sm text-blue-900">
                    <p><span class="w-20 inline-block opacity-70">Bank:</span> {template.get('bank_name', '-')}</p>
                    <p><span class="w-20 inline-block opacity-70">Account:</span> <span class="font-mono">{template.get('bank_account_no', '-')}</span></p>
                    <p><span class="w-20 inline-block opacity-70">Name:</span> {template.get('bank_account_name', '-')}</p>
                </div>
            </div>

            <!-- Footer Notes -->
            <div class="p-4 pb-8">
                {tnc_html}
                {disclaimer_html}
                
                <div class="mt-8 text-center">
                    <p class="text-xs text-gray-400">Generated by EE Invoicing System</p>
                </div>
            </div>

        </div>
    </body>
    </html>
    """
