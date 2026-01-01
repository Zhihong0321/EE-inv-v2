# Invoice Creation Link - Quick Reference
## AI Agent Quick Reference Card
**Purpose:** Fast lookup for generating invoice creation links

---

## Base URL

```
https://quote.atap.solar/create-invoice
```

---

## URL Structure

```
{base_url}?package_id={id}&param1=value1&param2=value2
```

---

## Required Parameter

| Parameter | Type | Example |
|-----------|------|---------|
| `package_id` | String | `1703833647950x572894707690242050` |

---

## Optional Parameters

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `panel_qty` | Integer | `8` | Panel quantity |
| `panel_rating` | String | `450W` | Panel wattage |
| `discount_given` | String | `500` or `10%` or `500 10%` | URL encode `%` as `%25`, space as `%20` |
| `customer_name` | String | `John Doe` | URL encode space as `%20` |
| `customer_phone` | String | `60123456789` | No encoding needed |
| `customer_address` | String | `123 Main St` | URL encode space as `%20`, comma as `%2C` |
| `template_id` | String | `template_123` | Invoice template ID |
| `apply_sst` | Boolean | `true` | Turn on 8% SST (Default: false) |

---

## Quick Examples

### Minimal (Package Only)
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050
```

### With Discount (RM 500)
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&discount_given=500
```

### With Discount (10%)
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&discount_given=10%25
```

### With Customer
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&customer_name=John%20Doe&customer_phone=60123456789
```

### Complete Example
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&panel_rating=450W&discount_given=500%2010%25&customer_name=John%20Doe&customer_phone=60123456789&customer_address=123%20Main%20St
```

---

## URL Encoding Rules

| Character | Encoded | Example |
|-----------|---------|---------|
| Space | `%20` or `+` | `John Doe` → `John%20Doe` |
| `%` | `%25` | `10%` → `10%25` |
| `&` | `%26` | Not needed in values |
| `=` | `%3D` | Not needed in values |
| `,` | `%2C` | `City, State` → `City%2C%20State` |

---

## Code Snippets

### JavaScript/TypeScript
```javascript
const params = new URLSearchParams({
    package_id: '1703833647950x572894707690242050',
    discount_given: '500',
    customer_name: 'John Doe'
});
const url = `https://quote.atap.solar/create-invoice?${params}`;
```

### Python
```python
from urllib.parse import urlencode

params = {
    'package_id': '1703833647950x572894707690242050',
    'discount_given': '500',
    'customer_name': 'John Doe'
}
url = f"https://quote.atap.solar/create-invoice?{urlencode(params)}"
```

---

## Discount Format

| Format | Example | URL Encoded |
|--------|---------|-------------|
| Fixed amount | `500` | `500` |
| Percentage | `10%` | `10%25` |
| Combined | `500 10%` | `500%2010%25` |

---

## Common Patterns

### Pattern 1: Basic Invoice
```
?package_id={id}
```

### Pattern 2: With Discount
```
?package_id={id}&discount_given={amount}
```

### Pattern 3: With Customer
```
?package_id={id}&customer_name={name}&customer_phone={phone}
```

### Pattern 4: Complete
```
?package_id={id}&panel_qty={qty}&panel_rating={rating}&discount_given={discount}&customer_name={name}&customer_phone={phone}&customer_address={address}
```

---

## Validation Rules

- ✅ `package_id` is REQUIRED
- ✅ `package_id` must exist in database
- ✅ All other parameters are optional
- ✅ Use URL encoding for special characters
- ✅ Parameters are case-sensitive (use lowercase with underscore)

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Package not found" | Invalid `package_id` | Verify package exists |
| Special chars display wrong | Not URL encoded | Encode special characters |
| Discount not applied | Wrong format | Use correct discount format |

---

## See Also

- Full Guide: [SALES_TEAM_INVOICE_LINK_GUIDE.md](./SALES_TEAM_INVOICE_LINK_GUIDE.md)
- API Docs: [API_GUIDELINE.md](./API_GUIDELINE.md)

---

**Last Updated:** 2025-01-30








