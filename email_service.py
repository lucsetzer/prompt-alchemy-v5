import os
from auth import create_magic_link

# Remove ALL QR code dependencies
def send_magic_link_email(email: str):
    """Send magic link - SIMPLIFIED NO QR CODE"""
    link = create_magic_link(email)
    
    print("\n" + "="*60)
    print(f"📨 MAGIC LINK for: {email}")
    print(f"🔗 {link}")
    print("="*60)
    print("\nCopy this link into your browser to login.")
    
    return link
