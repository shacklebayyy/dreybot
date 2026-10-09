from django.core.management.base import BaseCommand
from catalog.models import Category, Country, Region, Product, StockStatus
from verification.models import VerificationService
from core.models import SystemSetting
from django.utils.text import slugify

US_STATES = [
    ("Alabama", "AL"), ("Alaska", "AK"), ("Arizona", "AZ"), ("Arkansas", "AR"),
    ("California", "CA"), ("Colorado", "CO"), ("Connecticut", "CT"), ("Delaware", "DE"),
    ("Florida", "FL"), ("Georgia", "GA"), ("Hawaii", "HI"), ("Idaho", "ID"),
    ("Illinois", "IL"), ("Indiana", "IN"), ("Iowa", "IA"), ("Kansas", "KS"),
    ("Kentucky", "KY"), ("Louisiana", "LA"), ("Maine", "ME"), ("Maryland", "MD"),
    ("Massachusetts", "MA"), ("Michigan", "MI"), ("Minnesota", "MN"), ("Mississippi", "MS"),
    ("Missouri", "MO"), ("Montana", "MT"), ("Nebraska", "NE"), ("Nevada", "NV"),
    ("New Hampshire", "NH"), ("New Jersey", "NJ"), ("New Mexico", "NM"), ("New York", "NY"),
    ("North Carolina", "NC"), ("North Dakota", "ND"), ("Ohio", "OH"), ("Oklahoma", "OK"),
    ("Oregon", "OR"), ("Pennsylvania", "PA"), ("Rhode Island", "RI"), ("South Carolina", "SC"),
    ("South Dakota", "SD"), ("Tennessee", "TN"), ("Texas", "TX"), ("Utah", "UT"),
    ("Vermont", "VT"), ("Virginia", "VA"), ("Washington", "WA"), ("West Virginia", "WV"),
    ("Wisconsin", "WI"), ("Wyoming", "WY")
]

class Command(BaseCommand):
    help = "Seed initial DreyDocs categories, countries, 50 US states, products, and verification services."

    def handle(self, *args, **options):
        self.stdout.write("Seeding DreyDocs Initial Data...")

        # System Settings
        SystemSetting.set_setting("site_name", "DreyDocs", "Platform Name")
        SystemSetting.set_setting("tagline", "Learning Documents & Verification Services", "Tagline")
        SystemSetting.set_setting("default_product_price", "12.00", "Default price for products")
        SystemSetting.set_setting("currency", "USD", "Default currency")
        SystemSetting.set_setting("btc_address", "bc1q0h7ql9m8zr3dk3f2f4vvjrgmz4kdt8v3daw2xm0pjr24efgde4ksh4skq6", "BTC Deposit Address")
        SystemSetting.set_setting("btc_network", "Bitcoin Mainnet", "BTC Network")
        SystemSetting.set_setting("ltc_address", "ltc1qydca6ls4qs7wu7rhnm7fh9gpzfz200t5ecukfkqts26ulaelh29sm3pc04", "LTC Deposit Address")
        SystemSetting.set_setting("ltc_network", "Litecoin Mainnet", "LTC Network")
        SystemSetting.set_setting("trx_address", "TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7", "TRX Deposit Address")
        SystemSetting.set_setting("trx_network", "TRON (TRC20)", "TRX Network")
        SystemSetting.set_setting("eth_address", "0x3d33a1641a61af1b3b499a1f6a236176bd1820b4", "ETH Deposit Address")
        SystemSetting.set_setting("eth_network", "Ethereum (ERC20)", "ETH Network")
        SystemSetting.set_setting("usdt_address", "TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7", "USDT Deposit Address")
        SystemSetting.set_setting("usdt_network", "TRC20 / ERC20", "USDT Network")

        # Categories
        cat_data = [
            ("ID Templates", "Educational ID card sample templates."),
            ("Passport Templates", "Sample passport templates for educational design."),
            ("Driver License Templates", "Educational driver license templates for design and UI testing."),
            ("Business Documents", "Business certificates, incorporation templates, letterheads."),
            ("Certificates", "Certificates of completion, training, and achievement templates."),
            ("Other Templates", "Utility bill design templates, invoice layouts, resume templates.")
        ]

        categories = {}
        for idx, (name, desc) in enumerate(cat_data):
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, "description": desc, "ordering": idx, "active": True}
            )
            categories[name] = cat
        self.stdout.write(self.style.SUCCESS(f"Created {len(categories)} Categories."))

        # Countries
        country_data = [
            ("United States", "US", "🇺🇸"),
            ("Canada", "CA", "🇨🇦"),
            ("United Kingdom", "GB", "🇬🇧"),
            ("Australia", "AU", "🇦🇺"),
            ("Kenya", "KE", "🇰🇪"),
            ("Uganda", "UG", "🇺🇬"),
            ("Tanzania", "TZ", "🇹🇿"),
            ("South Africa", "ZA", "🇿🇦"),
            ("Nigeria", "NG", "🇳🇬"),
            ("Ghana", "GH", "🇬🇭"),
            ("Mexico", "MX", "🇲🇽"),
            ("Brazil", "BR", "🇧🇷"),
        ]

        countries = {}
        for name, iso, flag in country_data:
            c, _ = Country.objects.get_or_create(
                iso_code=iso,
                defaults={"name": name, "flag_emoji": flag, "active": True}
            )
            countries[iso] = c
        self.stdout.write(self.style.SUCCESS(f"Created {len(countries)} Countries."))

        # US States
        usa = countries["US"]
        state_count = 0
        states_dict = {}
        for state_name, code in US_STATES:
            st, created = Region.objects.get_or_create(
                country=usa,
                name=state_name,
                defaults={"code": code, "active": True}
            )
            states_dict[code] = st
            if created:
                state_count += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded 50 US States (added {state_count} new)."))

        # Seed Products
        products_seed = [
            {
                "name": "USA National ID Educational Template",
                "category": categories["ID Templates"],
                "country": usa,
                "price": 12.00,
                "short_description": "Educational design template for US National ID.",
                "description": "High resolution PSD template for graphic designers and UI layouts. Sample educational document only.",
                "file_type": "PSD",
                "file_size": "25 MB",
                "is_featured": True,
            },
            {
                "name": "USA Passport Educational Template",
                "category": categories["Passport Templates"],
                "country": usa,
                "price": 12.00,
                "short_description": "Educational passport design template.",
                "description": "Layered PSD sample passport template. Strictly for educational & design preview purposes.",
                "file_type": "PSD",
                "file_size": "45 MB",
                "is_featured": True,
            },
            {
                "name": "California Driver License Educational Template",
                "category": categories["Driver License Templates"],
                "country": usa,
                "state": states_dict["CA"],
                "price": 12.00,
                "short_description": "California state driver license educational template.",
                "description": "Fully customizable Photoshop PSD file with sample watermark for UI testing.",
                "file_type": "PSD",
                "file_size": "30 MB",
                "is_featured": True,
            },
            {
                "name": "Texas Driver License Educational Template",
                "category": categories["Driver License Templates"],
                "country": usa,
                "state": states_dict["TX"],
                "price": 12.00,
                "short_description": "Texas driver license graphic design sample template.",
                "description": "Educational template for design portfolio. Sample watermark included.",
                "file_type": "PSD",
                "file_size": "28 MB",
            },
            {
                "name": "New York Driver License Educational Template",
                "category": categories["Driver License Templates"],
                "country": usa,
                "state": states_dict["NY"],
                "price": 12.00,
                "short_description": "New York DL educational template.",
                "description": "High resolution design template marked with educational disclaimer.",
                "file_type": "PSD",
                "file_size": "32 MB",
            },
            {
                "name": "Business Certificate Design Template",
                "category": categories["Business Documents"],
                "country": usa,
                "price": 10.00,
                "short_description": "Professional business registration design template.",
                "description": "Vector AI and PDF template for business certificates.",
                "file_type": "AI / PDF",
                "file_size": "12 MB",
            },
            {
                "name": "Certificate of Completion Template",
                "category": categories["Certificates"],
                "price": 8.00,
                "short_description": "Elegant course completion award template.",
                "description": "Editable DOCX and PSD template for online course completion certificates.",
                "file_type": "DOCX / PSD",
                "file_size": "15 MB",
            },
            {
                "name": "Bank Statement Design Template",
                "category": categories["Other Templates"],
                "price": 12.00,
                "short_description": "Sample financial statement design template.",
                "description": "Educational spreadsheet/PDF layout template for presentation designs.",
                "file_type": "PDF / XLSX",
                "file_size": "8 MB",
            }
        ]

        for p_data in products_seed:
            slug = slugify(p_data["name"])
            Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": p_data["name"],
                    "category": p_data["category"],
                    "country": p_data.get("country"),
                    "state": p_data.get("state"),
                    "price": p_data["price"],
                    "short_description": p_data["short_description"],
                    "description": p_data["description"],
                    "file_type": p_data["file_type"],
                    "file_size": p_data["file_size"],
                    "is_active": True,
                    "is_featured": p_data.get("is_featured", False),
                    "stock_status": StockStatus.ACTIVE,
                }
            )
        self.stdout.write(self.style.SUCCESS("Seeded Example Products."))

        # Verification Services
        v_services = [
            ("BACKGROUND CHECK / LIVENESS CHECK", "background_check", "Authorized $1 background check and liveness verification service.", 1.00),
            ("EIN / BUSINESS VERIFICATION", "ein_verification", "Verify business registration and EIN matching via authorized provider.", 5.00),
            ("TIN VERIFICATION", "tin_verification", "Taxpayer Identification Number verification through official authorized programs.", 5.00),
            ("SSN VERIFICATION", "ssn_verification", "Social Security Number name & DOB match verification via licensed service.", 5.00),
            ("IDENTITY VERIFICATION", "identity_verification", "Authorized identity verification check with consent.", 15.00),
            ("NAME + DOB VERIFICATION", "name_dob_verification", "Name and Date of Birth validation check.", 8.00),
            ("EMPLOYMENT VERIFICATION", "employment_verification", "Authorized employment verification check.", 12.00),
            ("BUSINESS REGISTRATION", "business_registration", "Official state business registry verification.", 10.00),
            ("➕ OTHER / NOT LISTED (Custom Verification)", "custom_verification", "Custom verification service request. Describe your requirements.", 5.00),
        ]

        for name, code, desc, price in v_services:
            VerificationService.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "price": price,
                    "active": True,
                    "requires_consent": True,
                }
            )
        self.stdout.write(self.style.SUCCESS("Seeded Verification Services."))

        self.stdout.write(self.style.SUCCESS("All seed data created successfully!"))
