from django.utils.html import mark_safe


def color_icon(color):
    return mark_safe(u"""
        <svg style="display: inline-block;
            vertical-align: middle;" height="12" width="12">
            <circle cx="6" cy="6" r="5" stroke="{color}" stroke-width="1"
                fill="{color}" />
        </svg>
        """.format(color=color))
