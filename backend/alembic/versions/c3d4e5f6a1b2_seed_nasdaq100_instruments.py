"""seed nasdaq 100 instruments

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-03-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a1b2"
down_revision: str | None = "b2c3d4e5f6a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_instrument_classes_table = sa.table(
    "instrument_classes",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
)

_instruments_table = sa.table(
    "instruments",
    sa.column("class_id", sa.Integer()),
    sa.column("ticker", sa.String()),
    sa.column("name", sa.String()),
    sa.column("currency", sa.String()),
)

_NASDAQ100 = [
    {"class_id": 1, "ticker": "AAPL", "name": "APPLE INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "ABNB", "name": "AIRBNB, INC CL A CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "ADBE", "name": "ADOBE INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "ADI", "name": "ANALOG DEVICES CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "ADP", "name": "AUTOMATIC DATA PROCS", "currency": "USD"},
    {"class_id": 1, "ticker": "ADSK", "name": "AUTODESK INC", "currency": "USD"},
    {"class_id": 1, "ticker": "AEP", "name": "AMER ELC PWR CO CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "ALNY", "name": "ALNYLAM PHARMACEUTICALS, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "AMAT", "name": "APPLIED MATERIALS", "currency": "USD"},
    {"class_id": 1, "ticker": "AMD", "name": "ADV MICRO DEVICES", "currency": "USD"},
    {"class_id": 1, "ticker": "AMGN", "name": "AMGEN", "currency": "USD"},
    {"class_id": 1, "ticker": "AMZN", "name": "AMAZON.COM INC", "currency": "USD"},
    {"class_id": 1, "ticker": "APP", "name": "APPLOVIN CORP CLA CM", "currency": "USD"},
    {"class_id": 1, "ticker": "ARM", "name": "ARM HOLDINGS PLC ADS", "currency": "USD"},
    {"class_id": 1, "ticker": "ASML", "name": "ASML HLDG NY REG", "currency": "USD"},
    {"class_id": 1, "ticker": "AVGO", "name": "BROADCOM INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "AXON", "name": "AXON ENTERPRISE, INC", "currency": "USD"},
    {"class_id": 1, "ticker": "BKNG", "name": "BOOKING HOLDINGS INC", "currency": "USD"},
    {"class_id": 1, "ticker": "BKR", "name": "BAKER HUGHES CO", "currency": "USD"},
    {"class_id": 1, "ticker": "CCEP", "name": "COCA-COLA EUROPACIFI", "currency": "USD"},
    {"class_id": 1, "ticker": "CDNS", "name": "CADENCE DESIGN SYS", "currency": "USD"},
    {"class_id": 1, "ticker": "CEG", "name": "CONSTELLATION EN CM", "currency": "USD"},
    {"class_id": 1, "ticker": "CHTR", "name": "CHARTER COMMUNICATIO", "currency": "USD"},
    {"class_id": 1, "ticker": "CMCSA", "name": "COMCAST CORP A", "currency": "USD"},
    {"class_id": 1, "ticker": "COST", "name": "COSTCO WHOLESALE", "currency": "USD"},
    {"class_id": 1, "ticker": "CPRT", "name": "COPART, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "CRWD", "name": "CROWDSTRIKE HLD CM A", "currency": "USD"},
    {"class_id": 1, "ticker": "CSCO", "name": "CISCO SYSTEMS INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "CSGP", "name": "COSTAR GROUP INC", "currency": "USD"},
    {"class_id": 1, "ticker": "CSX", "name": "CSX CORPORATION", "currency": "USD"},
    {"class_id": 1, "ticker": "CTAS", "name": "CINTAS CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "CTSH", "name": "COGNIZANT TECH SOL", "currency": "USD"},
    {"class_id": 1, "ticker": "DASH", "name": "DOORDASH, INC. CL A", "currency": "USD"},
    {"class_id": 1, "ticker": "DDOG", "name": "DATADOG INC.L A CM", "currency": "USD"},
    {"class_id": 1, "ticker": "DXCM", "name": "DEXCOM", "currency": "USD"},
    {"class_id": 1, "ticker": "EA", "name": "ELECTRONIC ARTS INC", "currency": "USD"},
    {"class_id": 1, "ticker": "EXC", "name": "EXELON CORP CMN STK", "currency": "USD"},
    {"class_id": 1, "ticker": "FANG", "name": "DIAMONDBACK ENERGY", "currency": "USD"},
    {"class_id": 1, "ticker": "FAST", "name": "FASTENAL CO", "currency": "USD"},
    {"class_id": 1, "ticker": "FER", "name": "FERROVIAL SE", "currency": "USD"},
    {"class_id": 1, "ticker": "FTNT", "name": "FORTINET, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "GEHC", "name": "GE HEALTHCARE CM", "currency": "USD"},
    {"class_id": 1, "ticker": "GILD", "name": "GILEAD SCIENCES, INC", "currency": "USD"},
    {"class_id": 1, "ticker": "GOOGL", "name": "ALPHABET CL A CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "HON", "name": "HONEYWELL INTL INC", "currency": "USD"},
    {"class_id": 1, "ticker": "IDXX", "name": "IDEXX LABORATORIES", "currency": "USD"},
    {"class_id": 1, "ticker": "INSM", "name": "INSMED INCORPORATED", "currency": "USD"},
    {"class_id": 1, "ticker": "INTC", "name": "INTEL CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "INTU", "name": "INTUIT INC", "currency": "USD"},
    {"class_id": 1, "ticker": "ISRG", "name": "INTUITIVE SURG, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "KDP", "name": "KEURIG DR PEPPER INC", "currency": "USD"},
    {"class_id": 1, "ticker": "KHC", "name": "KRAFT HEINZ CO CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "KLAC", "name": "KLA CP CMN STK", "currency": "USD"},
    {"class_id": 1, "ticker": "LIN", "name": "LINDE PLC", "currency": "USD"},
    {"class_id": 1, "ticker": "LRCX", "name": "LAM RESEARCH CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "MAR", "name": "MARRIOTT INT CL A CM", "currency": "USD"},
    {"class_id": 1, "ticker": "MCHP", "name": "MICROCHIP TECHNOLOGY", "currency": "USD"},
    {"class_id": 1, "ticker": "MDLZ", "name": "MONDELEZ INTL CMN A", "currency": "USD"},
    {"class_id": 1, "ticker": "MELI", "name": "MERCADOLIBRE, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "META", "name": "META PLATFORMS, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "MNST", "name": "MONSTER BEVERAGE CP", "currency": "USD"},
    {"class_id": 1, "ticker": "MPWR", "name": "MONOLITHIC POWER SYSTEMS, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "MRVL", "name": "MARVELL TECH INC CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "MSFT", "name": "MICROSOFT CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "MSTR", "name": "MICROSTRATEGY INCORPORATED", "currency": "USD"},
    {"class_id": 1, "ticker": "MU", "name": "MICRON TECHNOLOGY", "currency": "USD"},
    {"class_id": 1, "ticker": "NFLX", "name": "NETFLIX, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "NVDA", "name": "NVIDIA CORPORATION", "currency": "USD"},
    {"class_id": 1, "ticker": "NXPI", "name": "NXP SEMICONDUCTORS", "currency": "USD"},
    {"class_id": 1, "ticker": "ODFL", "name": "OLD DOMINION FREIG", "currency": "USD"},
    {"class_id": 1, "ticker": "ORLY", "name": "O'REILLY AUTOMOTIVE", "currency": "USD"},
    {"class_id": 1, "ticker": "PANW", "name": "PALO ALTO NTWKS CM", "currency": "USD"},
    {"class_id": 1, "ticker": "PAYX", "name": "PAYCHEX, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "PCAR", "name": "PACCAR INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "PDD", "name": "PDD HOLDINGS INC ADS", "currency": "USD"},
    {"class_id": 1, "ticker": "PEP", "name": "PEPSICO INC", "currency": "USD"},
    {"class_id": 1, "ticker": "PLTR", "name": "PALANTIR TECHNOLOGIES INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "PYPL", "name": "PAYPAL HOLDINGS", "currency": "USD"},
    {"class_id": 1, "ticker": "QCOM", "name": "QUALCOMM INC", "currency": "USD"},
    {"class_id": 1, "ticker": "REGN", "name": "REGENERON PHARMACEUT", "currency": "USD"},
    {"class_id": 1, "ticker": "ROP", "name": "ROPER TECH CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "ROST", "name": "ROSS STORES, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "SBUX", "name": "STARBUCKS CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "SHOP", "name": "SHOPIFY, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "SNPS", "name": "SYNOPSYS, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "STX", "name": "SEAGATE TECHNOLOGY HOLDINGS PLC", "currency": "USD"},
    {"class_id": 1, "ticker": "TEAM", "name": "ATLASSIAN CLS A CS", "currency": "USD"},
    {"class_id": 1, "ticker": "TMUS", "name": "T-MOBILE US CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "TRI", "name": "THOMSON REUTERS CORP", "currency": "USD"},
    {"class_id": 1, "ticker": "TSLA", "name": "TESLA, INC.", "currency": "USD"},
    {"class_id": 1, "ticker": "TTWO", "name": "TAKE-TWO INTERACTI", "currency": "USD"},
    {"class_id": 1, "ticker": "TXN", "name": "TEXAS INSTRUMENTS", "currency": "USD"},
    {"class_id": 1, "ticker": "VRSK", "name": "VERISK ANALYTICS INC", "currency": "USD"},
    {"class_id": 1, "ticker": "VRTX", "name": "VERTEX PHARMACEUTIC", "currency": "USD"},
    {"class_id": 1, "ticker": "WBD", "name": "WRNR BRS DS CM WI", "currency": "USD"},
    {"class_id": 1, "ticker": "WDAY", "name": "WORKDAY INC CL A", "currency": "USD"},
    {"class_id": 1, "ticker": "WDC", "name": "WESTERN DIGITAL CORP.", "currency": "USD"},
    {"class_id": 1, "ticker": "WMT", "name": "WALMART. INC", "currency": "USD"},
    {"class_id": 1, "ticker": "XEL", "name": "XCEL ENERGY CMN", "currency": "USD"},
    {"class_id": 1, "ticker": "ZS", "name": "ZSCALER, INC. CMN", "currency": "USD"},
]


def upgrade() -> None:
    op.bulk_insert(_instrument_classes_table, [{"id": 1, "name": "Stocks"}])
    op.bulk_insert(_instruments_table, _NASDAQ100)


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM instruments WHERE class_id = 1"))
    op.execute(sa.text("DELETE FROM instrument_classes WHERE id = 1"))
