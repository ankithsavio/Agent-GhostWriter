class Prompt:
    def __init__(self, prompt, **kwargs):
        self.prompt = prompt
        self.dynamic_attr = {}
        if kwargs:
            self.set_new_values(kwargs)

    def set_new_values(self, kwargs):
        if not isinstance(kwargs, dict):
            raise ValueError("Expected dict for kwargs")

        def format_value(value):
            if isinstance(value, str):
                return value
            elif isinstance(value, list):
                return "\n".join(str(item) for item in value)
            else:
                return str(value)

        for key, value in kwargs.items():
            formatted_value = f"<{key}>\n{format_value(value)}\n</{key}>"
            self.dynamic_attr[key] = formatted_value

    def __str__(self):
        return self.prompt + "\n" + "\n".join(self.dynamic_attr.values())
