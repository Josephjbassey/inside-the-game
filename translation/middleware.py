"""
Language middleware: reads ?lang= query or lang cookie, sets request.language.
"""


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.language = request.GET.get("lang") or request.COOKIES.get("lang", "en")
        response = self.get_response(request)
        if (
            "lang" in request.GET
            and request.GET["lang"] != request.COOKIES.get("lang")
        ):
            response.set_cookie("lang", request.GET["lang"], max_age=60 * 60 * 24 * 30)
        return response
