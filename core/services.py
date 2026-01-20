

class ErrorHanders:
    ''' Pass the serializer.errors to the serializer_errors it will
    return the error messages in a single line by separate by default sep '''

    spt = None

    def __init__(self):
        self.spt = "|"

    def _add_message(self, value):
        ''' To add messages by checking the type '''
        if isinstance(value, dict):
            value = self.serializer_errors(value, many=False)
            error_message = value + ","
        elif isinstance(value, str):
            error_message = value + ","
        else:
            error_message = "Error occurred" + ","
        return error_message

    def _get_errors(self, args):
        message = ""
        for key, values in args.items():
            error_message = ""
            if isinstance(values, list):
                for value in values:
                    error_message += self._add_message(value)
            else:
                error_message += self._add_message(values)

            error_message = error_message[:-1]
            message += f"{error_message} {self.spt} ".replace("This field", key.capitalize().replace('_', ' '))

        return message

    def serializer_errors(self, args, many=False):
        message = ""
        if many:
            for arg in args:
                message = self._get_errors(arg)
        else:
            message = self._get_errors(args)

        return message[:-3]

    def form_errors(self, args, formset=False):
        message = ""
        if not formset:
            for field in args:
                if field.errors:
                    message += field.label + " : "
                    error = field.errors[0]
                    message += str(error)
                    message += "\n"

            for err in args.non_field_errors():
                error = err
                message += str(error)
                message += "\n"
        elif formset:
            for form in args:
                for field in form:
                    if field.errors:
                        message += field.label + " : "
                        error = field.errors[0]
                        message += str(error)
                        message += "\n"
                for err in form.non_field_errors():
                    error = err
                    message += str(error)
                    message += "\n"

        return message


generate_errors = ErrorHanders()


