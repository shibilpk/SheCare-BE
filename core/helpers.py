import base64
import collections
import math
import os
import random
import re
import string
from decimal import ROUND_HALF_UP, Decimal
from numbers import Number

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Max
from django.utils import timezone

from .services import generate_errors

# def send_email(
#     to_address,
#     subject,
#     content,
#     html_content,
#     attachment=None,
#     attachment2=None,
#     attachment3=None,
# ):
#     new_message = MailerMessage()
#     new_message.subject = subject
#     new_message.to_address = to_address
#     # if bcc_address:
#     #     new_message.bcc_address = bcc_address
#     new_message.from_address = settings.DEFAULT_FROM_EMAIL
#     new_message.content = content
#     new_message.html_content = html_content
#     if attachment:
#         new_message.add_attachment(attachment)
#     if attachment2:
#         new_message.add_attachment(attachment2)
#     if attachment3:
#         new_message.add_attachment(attachment3)
#     new_message.app = "default"
#     new_message.save()


def generate_unique_id(size=8, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def generate_order_id(auto_id=""):
    today = timezone.now()
    return (
        str(today.year)
        + str(today.day).zfill(2)
        + str(today.month).zfill(2)
        + str(today.strftime("%I%M%s"))
    )


generate_form_errors = generate_errors.form_errors
generate_serializer_errors = generate_errors.serializer_errors


def get_auto_id(model):
    if model.objects.exists():
        latest_auto_id = model.objects.aggregate(
            max_auto_id=Max("auto_id")
        ).get("max_auto_id", 0)
        auto_id = int(latest_auto_id) + 1
    else:
        auto_id = 1

    return auto_id


def random_string():
    return f"{string.ascii_letters}{string.digits}"


class CPaginator(Paginator):
    def validate_number(self, number):
        try:
            return super().validate_number(number)
        except EmptyPage:
            if int(number) > 1:
                return self.num_pages
            elif int(number) < 1:
                return 1
            else:
                return 1


def get_surrounding_pages(current_page, total_pages, surrounding_pages=1):
    pages = []

    # First block: middle of 1 page middle block
    first_block_end = current_page // 2
    if first_block_end > 1:
        pages += range(
            first_block_end - surrounding_pages, first_block_end + 1, 1
        )
        pages.append("...")

    # Current block: Pages around the current page (1 page before and after)
    start_block = max(current_page - surrounding_pages, 1)
    end_block = min(current_page + surrounding_pages, total_pages)
    pages += range(start_block, end_block + 1)

    # Add an ellipsis if there's a gap between the current block and the next
    if end_block + 2 < total_pages - 2:
        pages.append("...")

    last_block_start = (total_pages + current_page) // 2
    if last_block_start not in pages:
        pages += range(
            last_block_start, last_block_start + 1 + surrounding_pages
        )

    return pages


def paginate(instances, request, default_page_count=10):
    try:
        # Get the current page and items per page from the request
        page = int(request.GET.get("page", 1))
        items = int(request.GET.get("items", default_page_count))
    except (TypeError, ValueError):
        # Default to the first page and default item count if any error occurs
        page = 1
        items = default_page_count

    paginator = Paginator(instances, items)

    try:
        # Get the desired page of results
        instances = paginator.page(page)
    except PageNotAnInteger:
        # If the page is not an integer, show the first page
        instances = paginator.page(1)
    except EmptyPage:
        # If the page is out of range, show the last page
        instances = paginator.page(paginator.num_pages)

    data = {
        "count": instances.paginator.count,
        "num_pages": instances.paginator.num_pages,
        "items_per_page": instances.paginator.per_page,
    }

    data["has_other_pages"] = instances.has_other_pages()
    if instances.has_other_pages():
        data["page"] = instances.number
        data["start_index"] = instances.start_index()
        data["has_previous"] = instances.has_previous()
        if instances.has_previous():
            data["previous_page_number"] = instances.previous_page_number()

        data["has_next"] = instances.has_next()
        if instances.has_next():
            data["next_page_number"] = instances.next_page_number()

        data["page_range"] = list(
            get_surrounding_pages(instances.number, paginator.num_pages)
        )

    return instances, data


def round_nearest(x, a):
    return round(round(x / a) * a, -int(math.floor(math.log10(a))))


def get_current_roles(user):
    user_roles = []
    if user.is_authenticated:
        if user.is_superuser:
            user_roles.append("superuser")

        if hasattr(user, "customer"):
            user_roles.append("customer")

    return user_roles


def generate_otp(size=4, chars=string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def stringify_flattern(data):
    for k, v in data.items():
        data.update({k: str(v)})

    return data


def load_key():
    key = getattr(settings, "PASSWORD_ENCRYPTION_KEY", None)
    if key:
        return key
    else:
        raise ImproperlyConfigured(
            "No configuration  found in your PASSWORD_ENCRYPTION_KEY setting."
        )


def transform_string(input_str):
    # Case 1: All uppercase - convert to lowercase
    if input_str.isupper():
        return input_str.lower()

    # Case 2: Starts with single lowercase followed by uppercase (aCCOUNTGROUP)
    if (
        len(input_str) > 1
        and input_str[0].islower()
        and input_str[1:].isupper()
    ):
        return f"{input_str[0]}_{input_str[1:].lower()}"

    # Case 3: Contains any lowercase followed by uppercase
    # (camelCase or PascalCase)
    if re.search(r"[a-z][A-Z]", input_str):
        # Insert separator before capital letters and make lowercase
        transformed = re.sub(r"([a-z])([A-Z])", r"\1-\2", input_str).lower()
        return transformed

    # Default case: convert to lowercase with hyphens for any
    # non-alphanumeric chars
    transformed = re.sub(r"[^a-zA-Z0-9]+", "-", input_str).lower()
    return transformed


def is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def encrypt_small(txt):
    data = str(txt).encode("utf-8")
    aesgcm = AESGCM(settings.FERNET_KEY[:32].encode())  # Key must be 32 bytes
    nonce = os.urandom(12)  # Standard 12-byte nonce for GCM
    # Encrypt data
    ct = aesgcm.encrypt(nonce, data, None)
    # Combine nonce + ciphertext and encode once
    # Result: [12 bytes nonce][Length of text][16 bytes tag]
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii").rstrip("=")


def decrypt_small(token):
    # Add padding back if missing
    token += "=" * (4 - len(token) % 4)
    data = base64.urlsafe_b64decode(token)
    aesgcm = AESGCM(settings.FERNET_KEY[:32].encode())
    nonce = data[:12]
    ciphertext = data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def to_fixed(value: Number, places: int = 1):
    if value is None:
        return None

    d = value if isinstance(value, Decimal) else Decimal(str(value))

    quant = Decimal("1." + "0" * places)
    fixed = d.quantize(quant, rounding=ROUND_HALF_UP)

    # remove trailing .0 if possible
    if fixed == fixed.to_integral():
        return int(fixed)

    return float(fixed)


def normalize_number(value, fx_place: int = None):
    if isinstance(value, Decimal):
        if value == value.to_integral():
            return int(value)
        return float(value)
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return value
    if fx_place is not None:
        value = to_fixed(value, fx_place)
    return value
