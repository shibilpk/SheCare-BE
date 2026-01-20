from django.template import Library
from django.template.defaultfilters import stringfilter


register = Library()


@register.filter
@stringfilter
def underscore_smallletter(value):
    value = value.replace(" ", "_")
    return value


@register.filter
def make_title(value):
    value = value.replace("get_", "").replace("_display", "")
    value = value.replace("_", " ").capitalize()
    return value


@register.filter
def to_fixed_two(value):
    return "{:10.2f}".format(value)


@register.filter
def split(value, seperator):
    if value:
        values = value.split(seperator)
        return list(filter(None, values))


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for key in kwargs:
        query[key] = kwargs[key]
    return query.urlencode()


@register.filter
def get_attr(instance, key):
    # Check if the key is a function/method
    if callable(getattr(instance, key, None)):
        return getattr(instance, key)()
    else:
        return getattr(instance, key, None)


@register.filter
def get_model_verbose(item):
    """Returns the name of the model."""
    return item._meta.model._meta.verbose_name


@register.filter
def get_reverse_data(instance, form):
    """Returns the name of the model."""
    related_name = form.get_fk_field(instance._meta.model)[1]
    instances = getattr(instance, related_name).all()
    return instances


@register.filter
def get_fk_field(formset, form):
    """Returns the name of the model."""
    if formset.instance:
        fk_field = form.get_fk_field(formset.instance._meta.model)[0]
        return fk_field
    else:
        return None


@register.filter
def convert_num2word(amount):
    return num2words(float(amount or 0))


@register.filter
def check_type_html(value):
    if '.html' in value:
        return True
    else:
        return False


@register.filter
def format_actor_date(actor, date):
    return f"{actor} ({date or '-'})"


@register.filter
def get_by_section(headings, section):
    """
    Filter headings by section.
    Usage: {% headings|get_by_section:'home_spotlight' %}
    """
    try:
        return headings.filter(section=section).first()
    except AttributeError:
        # If headings is not a queryset, return None
        return None


@register.filter
def times(number):
    """
    Returns a range for the given number.
    Usage: {% for i in rating|times %}
    """
    try:
        return range(int(number))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def json_dumps(value):
    import json
    return json.dumps(value)


@register.simple_tag(takes_context=True)
def build_full_uri(context, relative_url):
    request = context['request']
    return request.build_absolute_uri(relative_url)
