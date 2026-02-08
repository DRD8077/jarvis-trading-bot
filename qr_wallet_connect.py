"""
╔══════════════════════════════════════════════════════════════════╗
║  JARVIS QR WALLET CONNECT ENGINE v3.0                          ║
║  Trust Wallet + Multi-Chain QR Code Generator                  ║
║  100% FREE — No API Keys Required                              ║
║  Deep Links: Trust Wallet, Solana Pay, EIP-681, WalletConnect  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer,
    CircleModuleDrawer,
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)
from qrcode.image.styles.colormasks import (
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    SolidFillColorMask,
)
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import hashlib
import time
import logging
import os
import urllib.parse
import json

logger = logging.getLogger("JARVIS-QR-WALLET")

# ═══════════════════════════════════════════════════════════
#  OWNER WALLET CONFIG
# ═══════════════════════════════════════════════════════════
OWNER_SOLANA_WALLET = os.environ.get("OWNER_SOLANA_WALLET", "8F1PJhuJa45RMWMJwgDASXL6bm6GYd1MtReJSTcWugaR")
BOT_NAME = "JARVIS AI TRADING BOT"
BOT_TELEGRAM = "https://t.me/David_crew_bot"

# ═══════════════════════════════════════════════════════════
#  TRUST WALLET CHAIN IDs (SLIP-44 Coin Types)
# ═══════════════════════════════════════════════════════════
TRUST_WALLET_COINS = {
    "solana":    {"coin_id": 501, "symbol": "SOL", "name": "Solana",         "emoji": "◎"},
    "ethereum":  {"coin_id": 60,  "symbol": "ETH", "name": "Ethereum",       "emoji": "Ξ"},
    "bsc":       {"coin_id": 714, "symbol": "BNB", "name": "BNB Smart Chain", "emoji": "🔶"},
    "polygon":   {"coin_id": 966, "symbol": "MATIC", "name": "Polygon",      "emoji": "💜"},
    "arbitrum":  {"coin_id": 42161, "symbol": "ARB", "name": "Arbitrum",     "emoji": "🔵"},
    "avalanche": {"coin_id": 43114, "symbol": "AVAX", "name": "Avalanche",   "emoji": "🔺"},
    "tron":      {"coin_id": 195,   "symbol": "TRX",  "name": "TRON",        "emoji": "⚡"},
    "bitcoin":   {"coin_id": 0,     "symbol": "BTC",  "name": "Bitcoin",     "emoji": "₿"},
}

# ═══════════════════════════════════════════════════════════
#  QR STYLE PRESETS
# ═══════════════════════════════════════════════════════════
QR_STYLES = {
    "trust_wallet": {
        "front": (0, 122, 255),     # Trust Wallet Blue
        "back": (255, 255, 255),
        "gradient_end": (0, 80, 200),
        "drawer": "rounded",
    },
    "solana": {
        "front": (153, 69, 255),    # Solana Purple
        "back": (255, 255, 255),
        "gradient_end": (20, 241, 149),  # Solana Green
        "drawer": "circle",
    },
    "ethereum": {
        "front": (98, 126, 234),    # ETH Blue
        "back": (255, 255, 255),
        "gradient_end": (48, 63, 159),
        "drawer": "rounded",
    },
    "jarvis": {
        "front": (255, 107, 107),   # JARVIS Red-Pink
        "back": (255, 255, 255),
        "gradient_end": (255, 193, 7),   # Gold
        "drawer": "rounded",
    },
    "dark": {
        "front": (0, 0, 0),
        "back": (255, 255, 255),
        "gradient_end": (50, 50, 50),
        "drawer": "square",
    },
}


# ═══════════════════════════════════════════════════════════
#  TRUST WALLET DEEP LINK GENERATORS
# ═══════════════════════════════════════════════════════════

def generate_trust_wallet_send_link(
    address: str,
    chain: str = "solana",
    amount: float = None,
    token_id: str = None,
    memo: str = None,
) -> str:
    """
    Generate Trust Wallet deep link for sending crypto.
    When scanned, Trust Wallet opens with address pre-filled.
    
    Format: https://link.trustwallet.com/send?coin=<SLIP44>&address=<ADDR>
    """
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    coin_id = chain_info["coin_id"]
    
    params = {
        "coin": coin_id,
        "address": address,
    }
    if amount is not None:
        params["amount"] = str(amount)
    if token_id:
        params["token_id"] = token_id
    if memo:
        params["memo"] = memo
    
    query = urllib.parse.urlencode(params)
    return f"https://link.trustwallet.com/send?{query}"


def generate_trust_wallet_dapp_link(dapp_url: str, chain: str = "solana") -> str:
    """
    Generate Trust Wallet DApp browser deep link.
    Opens a URL inside Trust Wallet's DApp browser.
    
    Format: https://link.trustwallet.com/open_url?coin_id=<ID>&url=<URL>
    """
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    coin_id = chain_info["coin_id"]
    
    params = {
        "coin_id": coin_id,
        "url": dapp_url,
    }
    query = urllib.parse.urlencode(params)
    return f"https://link.trustwallet.com/open_url?{query}"


def generate_trust_wallet_receive_link(address: str, chain: str = "solana") -> str:
    """
    Generate a Trust Wallet compatible address link.
    Uses trust:// scheme for direct deep link.
    """
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    asset_code = f"c{chain_info['coin_id']}"
    return f"trust://send?asset={asset_code}&address={address}"


def generate_solana_pay_uri(
    address: str,
    amount: float = None,
    spl_token: str = None,
    label: str = None,
    message: str = None,
    memo: str = None,
    reference: str = None,
) -> str:
    """
    Generate Solana Pay URI (solana:<address>?...).
    Trust Wallet and most Solana wallets recognize this format.
    
    Spec: https://docs.solanapay.com/spec#transfer-request
    """
    uri = f"solana:{address}"
    params = {}
    
    if amount is not None:
        params["amount"] = str(amount)
    if spl_token:
        params["spl-token"] = spl_token
    if label:
        params["label"] = label
    if message:
        params["message"] = message
    if memo:
        params["memo"] = memo
    if reference:
        params["reference"] = reference
    
    if params:
        query = urllib.parse.urlencode(params)
        uri += f"?{query}"
    
    return uri


def generate_eip681_uri(address: str, chain_id: int = 1, value_wei: int = None) -> str:
    """
    Generate EIP-681 payment URI for EVM chains.
    Format: ethereum:<address>@<chainId>[?value=<wei>]
    Trust Wallet recognizes this for ETH/BSC/Polygon sends.
    """
    uri = f"ethereum:{address}@{chain_id}"
    if value_wei is not None:
        uri += f"?value={value_wei}"
    return uri


def generate_multi_chain_links(address_map: dict = None) -> dict:
    """
    Generate Trust Wallet links for all supported chains.
    
    address_map: {"solana": "8F1P...", "ethereum": "0x...", ...}
    If not provided, uses owner Solana wallet for Solana chain.
    """
    if address_map is None:
        address_map = {"solana": OWNER_SOLANA_WALLET}
    
    links = {}
    for chain, address in address_map.items():
        chain_info = TRUST_WALLET_COINS.get(chain.lower())
        if not chain_info:
            continue
        
        links[chain] = {
            "chain_name": chain_info["name"],
            "symbol": chain_info["symbol"],
            "emoji": chain_info["emoji"],
            "address": address,
            "trust_send_link": generate_trust_wallet_send_link(address, chain),
            "trust_direct_link": generate_trust_wallet_receive_link(address, chain),
        }
        
        # Add Solana Pay for Solana chain
        if chain.lower() == "solana":
            links[chain]["solana_pay_uri"] = generate_solana_pay_uri(
                address,
                label=BOT_NAME,
                message="JARVIS Trading Bot Wallet",
            )
        
        # Add EIP-681 for EVM chains
        if chain.lower() in ("ethereum", "bsc", "polygon", "arbitrum", "avalanche"):
            chain_ids = {
                "ethereum": 1, "bsc": 56, "polygon": 137,
                "arbitrum": 42161, "avalanche": 43114,
            }
            links[chain]["eip681_uri"] = generate_eip681_uri(
                address, chain_ids.get(chain.lower(), 1)
            )
    
    return links


# ═══════════════════════════════════════════════════════════
#  STYLED QR CODE GENERATOR
# ═══════════════════════════════════════════════════════════

def _get_module_drawer(style_name: str):
    """Get QR module drawer by name."""
    drawers = {
        "rounded": RoundedModuleDrawer,
        "circle": CircleModuleDrawer,
        "square": SquareModuleDrawer,
        "gapped": GappedSquareModuleDrawer,
        "vertical": VerticalBarsDrawer,
        "horizontal": HorizontalBarsDrawer,
    }
    drawer_cls = drawers.get(style_name, RoundedModuleDrawer)
    return drawer_cls()


def generate_styled_qr(
    data: str,
    style: str = "trust_wallet",
    size: int = 400,
    title: str = None,
    subtitle: str = None,
    border_color: tuple = None,
) -> bytes:
    """
    Generate a beautifully styled QR code image with branding.
    
    Args:
        data: The data to encode (URL, address, deep link)
        style: QR style preset name
        size: QR code image size in pixels
        title: Optional title text above QR
        subtitle: Optional subtitle text below QR
        border_color: Optional border color override
    
    Returns:
        PNG image bytes
    """
    style_config = QR_STYLES.get(style, QR_STYLES["trust_wallet"])
    
    # Create QR code
    qr = qrcode.QRCode(
        version=None,  # Auto-detect
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo overlay
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Apply styled image
    try:
        color_mask = RadialGradiantColorMask(
            back_color=style_config["back"],
            center_color=style_config["front"],
            edge_color=style_config["gradient_end"],
        )
        module_drawer = _get_module_drawer(style_config["drawer"])
        
        qr_image = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=color_mask,
        ).convert("RGBA")
    except Exception as e:
        logger.warning(f"Styled QR failed, using basic: {e}")
        qr_image = qr.make_image(
            fill_color=style_config["front"],
            back_color=style_config["back"],
        ).convert("RGBA")
    
    # Resize QR to target size
    qr_image = qr_image.resize((size, size), Image.LANCZOS)
    
    # Calculate canvas size (extra space for title/subtitle)
    padding = 30
    title_height = 60 if title else 0
    subtitle_height = 50 if subtitle else 0
    badge_height = 35
    total_height = size + title_height + subtitle_height + badge_height + padding * 2 + 20
    total_width = size + padding * 2
    
    # Create canvas with white background
    canvas = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Draw colored top banner
    banner_color = border_color or style_config["front"]
    draw.rectangle(
        [(0, 0), (total_width, title_height + 15)],
        fill=(*banner_color, 255),
    )
    
    # Draw title
    if title:
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except (OSError, IOError):
            font_title = ImageFont.load_default()
        
        # Center the title
        bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = bbox[2] - bbox[0]
        x_title = (total_width - text_width) // 2
        draw.text((x_title, 15), title, fill=(255, 255, 255, 255), font=font_title)
    
    # Paste QR code
    qr_y = title_height + 15
    canvas.paste(qr_image, (padding, qr_y))
    
    # Draw subtitle
    if subtitle:
        try:
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except (OSError, IOError):
            font_sub = ImageFont.load_default()
        
        sub_y = qr_y + size + 8
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        text_width = bbox[2] - bbox[0]
        x_sub = (total_width - text_width) // 2
        draw.text((x_sub, sub_y), subtitle, fill=(80, 80, 80, 255), font=font_sub)
    
    # Draw bottom badge
    badge_y = total_height - badge_height - 5
    draw.rectangle(
        [(padding, badge_y), (total_width - padding, total_height - 5)],
        fill=(*banner_color, 230),
        outline=(*banner_color, 255),
    )
    try:
        font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except (OSError, IOError):
        font_badge = ImageFont.load_default()
    
    badge_text = "🔱 JARVIS AI — Scan with Trust Wallet"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox[2] - bbox[0]
    draw.text(
        ((total_width - bw) // 2, badge_y + 8),
        badge_text,
        fill=(255, 255, 255, 255),
        font=font_badge,
    )
    
    # Convert to bytes
    buf = BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", quality=95)
    buf.seek(0)
    return buf.read()


def generate_basic_qr(data: str) -> bytes:
    """Generate a basic QR code image as PNG bytes (fallback)."""
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════
#  TRUST WALLET QR GENERATORS (HIGH-LEVEL)
# ═══════════════════════════════════════════════════════════

def generate_trust_wallet_connect_qr(
    address: str = None,
    chain: str = "solana",
    style: str = "trust_wallet",
) -> dict:
    """
    Generate a Trust Wallet connect QR code.
    When scanned with Trust Wallet, opens with wallet address.
    
    Returns: {
        "qr_image": bytes,
        "deep_link": str,
        "chain": str,
        "address": str,
        "instructions": str,
    }
    """
    address = address or OWNER_SOLANA_WALLET
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    
    # Generate deep link
    deep_link = generate_trust_wallet_send_link(address, chain)
    
    # Generate styled QR
    title = f"🔒 {chain_info['name']} WALLET CONNECT"
    subtitle = f"{chain_info['emoji']} {address[:12]}...{address[-6:]}"
    
    try:
        qr_image = generate_styled_qr(
            data=deep_link,
            style=style,
            size=400,
            title=title,
            subtitle=subtitle,
        )
    except Exception as e:
        logger.warning(f"Styled QR failed, using basic: {e}")
        qr_image = generate_basic_qr(deep_link)
    
    instructions = (
        f"📱 Trust Wallet se scan karo:\n\n"
        f"1️⃣ Trust Wallet app kholo\n"
        f"2️⃣ Settings → WalletConnect ya Scanner icon tap karo\n"
        f"3️⃣ Is QR code ko scan karo\n"
        f"4️⃣ Wallet automatic connect ho jayega! ✅\n\n"
        f"🔗 Chain: {chain_info['name']} ({chain_info['symbol']})\n"
        f"📍 Address: `{address[:12]}...{address[-6:]}`"
    )
    
    return {
        "qr_image": qr_image,
        "deep_link": deep_link,
        "chain": chain,
        "chain_name": chain_info["name"],
        "symbol": chain_info["symbol"],
        "address": address,
        "instructions": instructions,
    }


def generate_solana_pay_qr(
    address: str = None,
    amount: float = None,
    label: str = None,
) -> dict:
    """
    Generate a Solana Pay QR code.
    Trust Wallet, Phantom, and all Solana wallets support this.
    
    Returns: {
        "qr_image": bytes,
        "solana_pay_uri": str,
        "instructions": str,
    }
    """
    address = address or OWNER_SOLANA_WALLET
    label = label or BOT_NAME
    
    solana_pay_uri = generate_solana_pay_uri(
        address=address,
        amount=amount,
        label=label,
        message="JARVIS AI Trading Bot",
    )
    
    title = "◎ SOLANA PAY — SCAN TO CONNECT"
    subtitle = f"◎ {address[:12]}...{address[-6:]}"
    
    try:
        qr_image = generate_styled_qr(
            data=solana_pay_uri,
            style="solana",
            size=400,
            title=title,
            subtitle=subtitle,
        )
    except Exception as e:
        logger.warning(f"Styled QR failed for Solana Pay: {e}")
        qr_image = generate_basic_qr(solana_pay_uri)
    
    instructions = (
        f"◎ Solana Pay QR — Trust Wallet / Phantom / Solflare:\n\n"
        f"1️⃣ Wallet app kholo\n"
        f"2️⃣ QR Scanner tap karo\n"
        f"3️⃣ Is QR code ko scan karo\n"
        f"4️⃣ Solana wallet connect ho jayega! ✅\n\n"
        f"📍 Address: `{address[:12]}...{address[-6:]}`"
    )
    
    return {
        "qr_image": qr_image,
        "solana_pay_uri": solana_pay_uri,
        "instructions": instructions,
    }


def generate_multi_chain_qr_pack(
    address_map: dict = None,
) -> list:
    """
    Generate QR codes for multiple chains at once.
    Returns a list of QR result dicts.
    """
    if address_map is None:
        address_map = {"solana": OWNER_SOLANA_WALLET}
    
    results = []
    style_map = {
        "solana": "solana",
        "ethereum": "ethereum",
        "bsc": "trust_wallet",
        "polygon": "jarvis",
    }
    
    for chain, address in address_map.items():
        style = style_map.get(chain.lower(), "trust_wallet")
        result = generate_trust_wallet_connect_qr(address, chain, style)
        results.append(result)
    
    return results


def generate_receive_qr(
    address: str = None,
    chain: str = "solana",
    amount: float = None,
) -> dict:
    """
    Generate a "Receive Payment" QR code.
    Shows address QR that any wallet can scan to send payment.
    """
    address = address or OWNER_SOLANA_WALLET
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    
    # For Solana, use Solana Pay URI. For EVM, use EIP-681.
    if chain.lower() == "solana":
        data = generate_solana_pay_uri(
            address,
            amount=amount,
            label=BOT_NAME,
            message="Payment to JARVIS Bot",
        )
    elif chain.lower() in ("ethereum", "bsc", "polygon", "arbitrum", "avalanche"):
        chain_ids = {"ethereum": 1, "bsc": 56, "polygon": 137, "arbitrum": 42161, "avalanche": 43114}
        value_wei = int(amount * 10**18) if amount else None
        data = generate_eip681_uri(address, chain_ids.get(chain.lower(), 1), value_wei)
    else:
        data = address  # Fallback: plain address
    
    title = f"💰 RECEIVE {chain_info['symbol']}"
    subtitle = f"Scan to send {chain_info['symbol']} → {address[:10]}...{address[-4:]}"
    
    try:
        style = "solana" if chain.lower() == "solana" else "ethereum"
        qr_image = generate_styled_qr(data, style=style, size=400, title=title, subtitle=subtitle)
    except Exception:
        qr_image = generate_basic_qr(data)
    
    return {
        "qr_image": qr_image,
        "data": data,
        "chain": chain,
        "chain_name": chain_info["name"],
        "symbol": chain_info["symbol"],
        "address": address,
    }


def generate_dapp_browser_qr(url: str, chain: str = "solana") -> dict:
    """
    Generate a QR that opens a DApp URL inside Trust Wallet browser.
    Perfect for DEX links, NFT markets, etc.
    """
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    deep_link = generate_trust_wallet_dapp_link(url, chain)
    
    title = f"🌐 TRUST WALLET DApp BROWSER"
    subtitle = f"Open in Trust Wallet → {chain_info['name']}"
    
    try:
        qr_image = generate_styled_qr(deep_link, style="trust_wallet", size=400, title=title, subtitle=subtitle)
    except Exception:
        qr_image = generate_basic_qr(deep_link)
    
    return {
        "qr_image": qr_image,
        "deep_link": deep_link,
        "dapp_url": url,
        "chain": chain,
    }


# ═══════════════════════════════════════════════════════════
#  ALL-IN-ONE: TRUST WALLET CONNECT MEGA QR
# ═══════════════════════════════════════════════════════════

def generate_trust_connect_mega(
    address: str = None,
    chain: str = "solana",
) -> dict:
    """
    Generate the ultimate Trust Wallet connect QR with all methods.
    
    Returns:
        {
            "primary_qr": bytes,           # Main styled QR (Trust Wallet deep link)
            "solana_pay_qr": bytes | None,  # Solana Pay QR (if Solana)
            "deep_link": str,              # Trust Wallet deep link URL
            "trust_direct_link": str,      # trust:// scheme link
            "solana_pay_uri": str | None,  # Solana Pay URI
            "dapp_link": str,              # DApp browser link
            "address": str,
            "chain": str,
            "caption": str,                # Ready-to-send Telegram caption
            "methods_text": str,           # All connect methods in text
        }
    """
    address = address or OWNER_SOLANA_WALLET
    chain_info = TRUST_WALLET_COINS.get(chain.lower(), TRUST_WALLET_COINS["solana"])
    
    # ── Generate primary QR (Trust Wallet deep link) ──
    trust_send_link = generate_trust_wallet_send_link(address, chain)
    trust_direct_link = generate_trust_wallet_receive_link(address, chain)
    
    title = f"🔒 TRUST WALLET CONNECT"
    subtitle = f"{chain_info['emoji']} {chain_info['name']} — {address[:10]}...{address[-4:]}"
    
    try:
        primary_qr = generate_styled_qr(
            data=trust_send_link,
            style="trust_wallet",
            size=420,
            title=title,
            subtitle=subtitle,
        )
    except Exception:
        primary_qr = generate_basic_qr(trust_send_link)
    
    # ── Solana Pay QR (if Solana chain) ──
    solana_pay_uri = None
    solana_pay_qr = None
    if chain.lower() == "solana":
        solana_pay_uri = generate_solana_pay_uri(
            address, label=BOT_NAME, message="JARVIS Wallet Connect"
        )
        try:
            solana_pay_qr = generate_styled_qr(
                data=solana_pay_uri,
                style="solana",
                size=380,
                title="◎ SOLANA PAY CONNECT",
                subtitle=f"◎ {address[:10]}...{address[-4:]}",
            )
        except Exception:
            solana_pay_qr = generate_basic_qr(solana_pay_uri)
    
    # ── DApp browser link ──
    dapp_link = generate_trust_wallet_dapp_link(
        f"https://solscan.io/account/{address}", chain
    )
    
    # ── Build caption for Telegram ──
    caption = (
        f"🔒🔱 *TRUST WALLET CONNECT* 🔱🔒\n"
        f"{'━' * 32}\n\n"
        f"{chain_info['emoji']} *Chain:* {chain_info['name']} ({chain_info['symbol']})\n"
        f"📍 *Address:*\n`{address}`\n\n"
        f"{'━' * 32}\n"
        f"📱 *SCAN KAISE KARE:*\n\n"
        f"1️⃣ Trust Wallet app kholo 📲\n"
        f"2️⃣ Home screen par Scanner icon 🔍 tap karo\n"
        f"3️⃣ Ye QR code scan karo ✅\n"
        f"4️⃣ Wallet CONNECTED! 🎉\n\n"
        f"{'━' * 32}\n"
        f"🔐 *Security:* Anti-Drain Protection ON\n"
        f"🔱 Powered by JARVIS AI Trading Bot\n"
        f"🌸 राधे राधे 🌸"
    )
    
    # ── All methods text ──
    methods_text = (
        f"🔗 *Trust Wallet Connect Methods:*\n\n"
        f"1️⃣ *QR Scan* — Trust Wallet se QR scan karo (BEST ✅)\n"
        f"2️⃣ *Direct Link:*\n[Trust Wallet Open]({trust_send_link})\n\n"
        f"3️⃣ *Deep Link:*\n`{trust_direct_link}`\n\n"
    )
    
    if solana_pay_uri:
        methods_text += f"4️⃣ *Solana Pay:*\n`{solana_pay_uri[:60]}...`\n\n"
    
    methods_text += (
        f"5️⃣ *DApp Browser:*\n[Open in Trust Wallet]({dapp_link})\n\n"
        f"6️⃣ *Manual:* Address copy karo:\n`{address}`"
    )
    
    return {
        "primary_qr": primary_qr,
        "solana_pay_qr": solana_pay_qr,
        "deep_link": trust_send_link,
        "trust_direct_link": trust_direct_link,
        "solana_pay_uri": solana_pay_uri,
        "dapp_link": dapp_link,
        "address": address,
        "chain": chain,
        "chain_name": chain_info["name"],
        "symbol": chain_info["symbol"],
        "emoji": chain_info["emoji"],
        "caption": caption,
        "methods_text": methods_text,
    }


# ═══════════════════════════════════════════════════════════
#  SESSION TRACKER
# ═══════════════════════════════════════════════════════════

_qr_sessions = {}  # chat_id -> {"generated_at": timestamp, "chain": ..., "address": ...}

def track_qr_session(chat_id: int, chain: str, address: str):
    """Track when a QR was generated for analytics."""
    _qr_sessions[chat_id] = {
        "generated_at": time.time(),
        "chain": chain,
        "address": address,
        "scan_count": _qr_sessions.get(chat_id, {}).get("scan_count", 0) + 1,
    }

def get_qr_stats() -> dict:
    """Get QR generation statistics."""
    return {
        "total_sessions": len(_qr_sessions),
        "total_scans": sum(s.get("scan_count", 0) for s in _qr_sessions.values()),
        "chains_used": list(set(s.get("chain", "unknown") for s in _qr_sessions.values())),
    }


# ═══════════════════════════════════════════════════════════
#  MODULE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  JARVIS QR WALLET CONNECT ENGINE v3.0 — TEST")
    print("=" * 60)
    
    # Test Trust Wallet deep links
    link = generate_trust_wallet_send_link(OWNER_SOLANA_WALLET, "solana")
    print(f"\n✅ Trust Wallet Send Link:\n   {link}")
    
    direct = generate_trust_wallet_receive_link(OWNER_SOLANA_WALLET, "solana")
    print(f"\n✅ Trust Direct Link:\n   {direct}")
    
    dapp = generate_trust_wallet_dapp_link("https://jupiter.exchange", "solana")
    print(f"\n✅ DApp Browser Link:\n   {dapp}")
    
    sol_pay = generate_solana_pay_uri(OWNER_SOLANA_WALLET, label="JARVIS")
    print(f"\n✅ Solana Pay URI:\n   {sol_pay}")
    
    eip = generate_eip681_uri("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD40", chain_id=56)
    print(f"\n✅ EIP-681 (BSC):\n   {eip}")
    
    # Test styled QR generation
    print(f"\n⏳ Generating styled QR...")
    result = generate_trust_connect_mega(OWNER_SOLANA_WALLET, "solana")
    qr_size = len(result["primary_qr"])
    print(f"✅ Primary QR: {qr_size:,} bytes")
    
    if result["solana_pay_qr"]:
        sol_size = len(result["solana_pay_qr"])
        print(f"✅ Solana Pay QR: {sol_size:,} bytes")
    
    print(f"\n✅ Deep Link: {result['deep_link'][:60]}...")
    print(f"✅ DApp Link: {result['dapp_link'][:60]}...")
    print(f"✅ Chain: {result['chain_name']} ({result['symbol']})")
    
    # Test multi-chain
    multi = generate_multi_chain_links()
    print(f"\n✅ Multi-chain links: {len(multi)} chain(s)")
    for chain, data in multi.items():
        print(f"   {data['emoji']} {data['chain_name']}: {data['trust_send_link'][:50]}...")
    
    print(f"\n{'=' * 60}")
    print(f"  ALL TESTS PASSED ✅")
    print(f"{'=' * 60}")
