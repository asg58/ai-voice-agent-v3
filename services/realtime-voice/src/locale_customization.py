class LocaleCustomization:
    def customize_response(self, locale, response):
        """
        Pas de AI-respons aan op basis van de locale.
        """
        if locale == "nl":
            return f"[Dutch] {response}"
        elif locale == "en":
            return f"[English] {response}"
        else:
            return f"[Default] {response}"