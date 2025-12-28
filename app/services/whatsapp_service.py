import httpx
from typing import Optional
from app.config import settings
from app.utils.helpers import format_phone_number


class WhatsAppService:
    def __init__(self):
        self.base_url = settings.WHATSAPP_API_URL

    async def check_status(self) -> dict:
        """Check if WhatsApp service is ready"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/status")
                return response.json()
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def send_message(self, phone: str, message: str) -> dict:
        """
        Send a WhatsApp message

        Args:
            phone: Phone number with country code (digits only)
            message: Message text

        Returns:
            Response dict with success status
        """
        try:
            formatted_phone = format_phone_number(phone)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/send",
                    json={
                        "to": formatted_phone,
                        "message": message
                    }
                )
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_otp(self, phone: str, otp_code: str, name: Optional[str] = None) -> bool:
        """
        Send OTP via WhatsApp

        Args:
            phone: Phone number with country code
            otp_code: 6-digit OTP code
            name: Optional recipient name

        Returns:
            True if sent successfully, False otherwise
        """
        greeting = f"Hi {name}," if name else "Hi,"
        message = f"""🔐 *Your Verification Code*

{greeting}

Your OTP code is: *{otp_code}*

Valid for 30 minutes. Do not share this code with anyone.

_Eternalgy Invoicing System_"""

        result = await self.send_message(phone, message)
        return result.get("success", False)

    async def send_invoice_notification(
        self,
        phone: str,
        customer_name: str,
        invoice_number: str,
        amount: float,
        due_date: str,
        view_url: str
    ) -> bool:
        """Send invoice notification via WhatsApp"""
        message = f"""📄 *New Invoice*

Dear {customer_name},

Your invoice {invoice_number} has been generated.

*Amount:* RM {amount:,.2f}
*Due Date:* {due_date}

You can view and pay your invoice here:
{view_url}

Thank you!

_Eternalgy Invoicing System_"""

        result = await self.send_message(phone, message)
        return result.get("success", False)


# Singleton instance
whatsapp_service = WhatsAppService()
