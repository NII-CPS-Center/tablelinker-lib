class ValidationError(Exception):
    def __init__(self, message, errors):
        super(ValidationError, self).__init__(message)
        self.errors = errors


class Errors(object):
    def __init__(self):
        self._has_error = False
        self.error_messages = {}

    def __str__(self):
        return str(self.error_messages)

    def append(self, message, param=None):
        key = "none" if param is None else param.key

        if key not in self.error_messages:
            self.error_messages[key] = []

        if param is None:
            formated_message = message
        else:
            formated_message = "{}は、{}".format(param.label, message)

        self.error_messages[key].append(formated_message)

        self._has_error = True

    def has_error(self):
        return self._has_error


class Validator(object):
    def valid(self, value, errors, param=None, input=None, output=None):
        pass

    def help_text(self):
        pass

    def stop_when_error(self):
        return False


class RequiredValidator(Validator):
    REQUIRED_MESSAGE = "必須入力です。"

    def valid(self, value, errors, param=None, input=None, output=None):
        _valid = True
        if value is None or value == "":
            errors.append(self.REQUIRED_MESSAGE, param)
            _valid = False
        return _valid


class IntValidator(Validator):
    INT_MESSAGE = "数字を入力してください。"

    def valid(self, value, errors, param=None, input=None, output=None):

        if value is None:
            errors.append(self.INT_MESSAGE, param)
            return False

        try:
            # FIXME
            int(value)
        except ValueError:
            errors.append(self.INT_MESSAGE, param)
            return False

        return True

    def stop_when_error(self):
        return True


class BooleanValidator(Validator):
    BOOLEAN_MESSAGE = "不正な値です。"

    def valid(self, value, errors, param=None, input=None, output=None):

        if value is None:
            errors.append(self.BOOLEAN_MESSAGE, param)
            return False
        if value not in (True, False, "false"):
            errors.append("{}({})".format(
                self.BOOLEAN_MESSAGE, str(value)), param)
            return False

        return True

    def stop_when_error(self):
        return True


class FloatValidator(Validator):
    FLOAT_MESSAGE = "実数を入力してください。"
    stop_when_error = True

    def valid(self, value, errors, param=None, input=None, output=None):
        _valid = True
        try:
            # FIXME
            float(value)
        except ValueError:
            errors.append(self.FLOAT_MESSAGE, param)
            _valid = False

        return _valid

    def stop_when_error(self):
        return True


class RangeValidator(Validator):
    MAX_MESSAGE = "{max}以下で入力してください。"
    MIN_MESSAGE = "{min}以上で入力してください。"

    def __init__(self, max=None, min=None):
        self.max = max
        self.min = min

    def _parse(self, value):
        return float(value)

    def valid(self, value, errors, param=None, input=None, output=None):
        try:
            parsed = self._parse(value)
            _valid = True
            if self.max is not None and parsed > self.max:
                errors.append(self.MAX_MESSAGE.format(max=self.max), param)
                _valid = False

            if self.min is not None and parsed < self.min:
                errors.append(self.MIN_MESSAGE.format(min=self.min), param)
                _valid = False
            return _valid
        except ValueError:
            return False
