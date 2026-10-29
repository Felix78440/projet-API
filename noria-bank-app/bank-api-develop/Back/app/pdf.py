"""Relevé de compte en PDF, écrit à la main pour éviter une dépendance.

Polices standard du format PDF (Helvetica, Courier) en encodage WinAnsi : accents et « € » compris.
"""

from datetime import datetime, timezone

from .schemas import Account, Transaction

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4, en points
MARGIN = 50
LINE_HEIGHT = 14
LINES_PER_PAGE = (PAGE_HEIGHT - 2 * MARGIN) // LINE_HEIGHT

TITLE, TEXT = "F1", "F2"  # Helvetica-Bold, Courier (largeur fixe : colonnes alignées)


def euros(cents: int) -> str:
    """-425 → « -4,25 € »."""
    sign = "-" if cents < 0 else ""
    return sign + f"{abs(cents) / 100:,.2f}".replace(",", " ").replace(".", ",") + " €"


def french_date(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}"


def _pdf_string(text: str) -> bytes:
    raw = text.encode("cp1252", errors="replace")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def _page_content(lines: list[tuple[str, int, str]]) -> bytes:
    commands = [b"BT"]
    y = PAGE_HEIGHT - MARGIN
    for font, size, text in lines:
        commands.append(f"/{font} {size} Tf 1 0 0 1 {MARGIN} {y} Tm ".encode() + _pdf_string(text) + b" Tj")
        y -= LINE_HEIGHT
    commands.append(b"ET")
    return b"\n".join(commands)


def _build_pdf(pages: list[list[tuple[str, int, str]]]) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",  # /Pages, complété quand on connaît les pages
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>",
    ]
    kids = []
    for lines in pages:
        content = _page_content(lines)
        objects.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}]"
            f" /Resources << /Font << /{TITLE} 3 0 R /{TEXT} 4 0 R >> >>"
            f" /Contents {len(objects)} 0 R >>".encode()
        )
        kids.append(f"{len(objects)} 0 R")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def statement_pdf(owner: str, account: Account, transactions: list[Transaction]) -> bytes:
    header = [
        (TITLE, 18, "Relevé de compte"),
        (TEXT, 10, ""),
        (TEXT, 10, f"Titulaire : {owner}"),
        (TEXT, 10, f"IBAN      : {account.iban}"),
        (TEXT, 10, f"Type      : compte {account.type}"),
        (TEXT, 10, f"Solde     : {euros(round(account.balance * 100))}"),
        (TEXT, 10, f"Édité le  : {datetime.now(timezone.utc).strftime('%d/%m/%Y')}"),
        (TEXT, 10, ""),
    ]
    columns = (TEXT, 9, f"{'Date':<10}  {'Libellé':<30}  {'Contrepartie':<27}  {'Montant':>16}")
    rule = (TEXT, 9, "-" * 89)

    rows = []
    for t in transactions:
        cents = round(t.amount * 100)
        other = t.toIban if t.direction == "debit" else (t.fromIban or "—")
        amount = euros(-cents if t.direction == "debit" else cents)
        if t.direction == "credit":
            amount = "+" + amount
        rows.append((TEXT, 9, f"{french_date(t.createdAt):<10}  {t.label[:30]:<30}  {other:<27}  {amount:>16}"))
    if not rows:
        rows.append((TEXT, 9, "Aucune opération sur ce compte."))

    pages = []
    lines = header + [columns, rule]
    for row in rows:
        if len(lines) == LINES_PER_PAGE:
            pages.append(lines)
            lines = [columns, rule]
        lines.append(row)
    pages.append(lines)
    return _build_pdf(pages)
