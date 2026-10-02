from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from catalog.models import Category, Country, Region, Product
from telegram_bot.keyboards.inline import (
    get_countries_keyboard, get_us_states_keyboard,
    get_products_keyboard, get_product_detail_keyboard
)

router = Router()

CATALOG_HEADER_NOTE = (
    "📜 *ALL DOCUMENTS & TEMPLATES AVAILABLE!*\n"
    "If your required country, state, or document layout is not listed below, click *[➕ NOT LISTED? ORDER ANY CUSTOM DOC]* to request any custom document instantly!\n\n"
)

@router.message(F.text.in_({"📄 ID MOCKUPS", "📄 ID TEMPLATES"}))
async def show_id_templates(message: Message):
    countries = await sync_to_async(lambda: list(Country.objects.filter(active=True)))()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}🌍 *SELECT COUNTRY FOR ID TEMPLATES*",
        parse_mode="Markdown",
        reply_markup=get_countries_keyboard(countries, "id-templates")
    )

@router.message(F.text.in_({"🛂 PASSPORT MOCKUPS", "🛂 PASSPORT TEMPLATES"}))
async def show_passport_templates(message: Message):
    countries = await sync_to_async(lambda: list(Country.objects.filter(active=True)))()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}🌍 *SELECT COUNTRY FOR PASSPORT TEMPLATES*",
        parse_mode="Markdown",
        reply_markup=get_countries_keyboard(countries, "passport-templates")
    )

@router.message(F.text.in_({"🚗 DRIVER LICENSE MOCKUPS", "🚗 DRIVER LICENSE TEMPLATES"}))
async def show_dl_templates(message: Message):
    countries = await sync_to_async(lambda: list(Country.objects.filter(active=True)))()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}🚗 *DRIVER LICENSE TEMPLATES*\nSelect Country:",
        parse_mode="Markdown",
        reply_markup=get_countries_keyboard(countries, "driver-license-templates")
    )

@router.message(F.text == "🏢 BUSINESS DOCUMENTS")
async def show_business_docs(message: Message):
    def get_prods():
        cat = Category.objects.filter(slug__in=["business-documents"]).first()
        return list(Product.objects.filter(category=cat, is_active=True)) if cat else []
    products = await sync_to_async(get_prods)()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}🏢 *BUSINESS DOCUMENTS TEMPLATES*\nSelect document:",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )

@router.message(F.text == "🎓 CERTIFICATES")
async def show_certificates(message: Message):
    def get_prods():
        cat = Category.objects.filter(slug__in=["certificates"]).first()
        return list(Product.objects.filter(category=cat, is_active=True)) if cat else []
    products = await sync_to_async(get_prods)()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}🎓 *CERTIFICATE TEMPLATES*\nSelect certificate:",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )

@router.message(F.text == "📚 OTHER TEMPLATES")
async def show_other_templates(message: Message):
    def get_prods():
        cat = Category.objects.filter(slug__in=["other-templates"]).first()
        return list(Product.objects.filter(category=cat, is_active=True)) if cat else []
    products = await sync_to_async(get_prods)()
    await message.answer(
        f"{CATALOG_HEADER_NOTE}📚 *OTHER EDUCATIONAL TEMPLATES*\nSelect template:",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )


@router.callback_query(F.data.startswith("cat:"))
async def cb_country_selected(call: CallbackQuery):
    parts = call.data.split(":")
    cat_slug = parts[1]
    iso_code = parts[3]

    country = await sync_to_async(lambda: Country.objects.filter(iso_code=iso_code).first())()

    if cat_slug in ["driver-license-templates", "driver-license-mockups"] and iso_code == "US":
        states = await sync_to_async(lambda: list(Region.objects.filter(country=country, active=True)))()
        await call.message.edit_text(
            "🇺🇸 *UNITED STATES - SELECT STATE*",
            parse_mode="Markdown",
            reply_markup=get_us_states_keyboard(states)
        )
        await call.answer()
        return

    def fetch_cat_products():
        slug_map = {
            "id-templates": ["id-templates", "id-mockups"],
            "passport-templates": ["passport-templates", "passport-mockups"],
            "driver-license-templates": ["driver-license-templates", "driver-license-mockups"]
        }
        allowed_slugs = slug_map.get(cat_slug, [cat_slug])
        cat = Category.objects.filter(slug__in=allowed_slugs).first()
        prods = Product.objects.filter(category=cat, country=country, is_active=True)
        if not prods.exists():
            prods = Product.objects.filter(category=cat, is_active=True)
        return list(prods)

    products = await sync_to_async(fetch_cat_products)()

    await call.message.edit_text(
        f"📄 *AVAILABLE PRODUCTS ({country.name if country else 'Global'})*",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )
    await call.answer()

@router.callback_query(F.data.startswith("dl_state:"))
async def cb_state_selected(call: CallbackQuery):
    code = call.data.split(":")[1]

    def fetch_state_prods():
        state = Region.objects.filter(code=code).first()
        cat = Category.objects.filter(slug__in=["driver-license-templates", "driver-license-mockups"]).first()
        prods = Product.objects.filter(category=cat, state=state, is_active=True)
        if not prods.exists():
            prods = Product.objects.filter(category=cat, is_active=True)[:5]
        return state, list(prods)

    state, products = await sync_to_async(fetch_state_prods)()

    await call.message.edit_text(
        f"🚗 *{state.name if state else code} DRIVER LICENSE TEMPLATES*",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )
    await call.answer()

@router.callback_query(F.data.startswith("prod:"))
async def cb_product_detail(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])
    product = await sync_to_async(lambda: Product.objects.select_related('category', 'country', 'state').filter(id=prod_id).first())()
    if not product:
        await call.answer("Product not found.", show_alert=True)
        return

    text = (
        f"📌 *{product.name}*\n\n"
        f"💰 *Price:* `${product.price}` {product.currency}\n"
        f"📁 *Format:* `{product.file_type}` ({product.file_size})\n"
        f"📂 *Category:* {product.category.name}\n"
        f"🌍 *Region:* {product.country.name if product.country else 'Global'}"
        f"{' - ' + product.state.name if product.state else ''}\n\n"
        f"📝 *Description:*\n{product.description or product.short_description}\n\n"
        f"=============================\n"
        f"⚠️ *COMPLIANCE DISCLAIMER:*\n"
        f"`SAMPLE / EDUCATIONAL TEMPLATE`\n"
        f"`NOT A GOVERNMENT DOCUMENT`\n"
        f"`NOT VALID FOR IDENTIFICATION`\n"
        f"============================="
    )

    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(product.id)
    )
    await call.answer()
