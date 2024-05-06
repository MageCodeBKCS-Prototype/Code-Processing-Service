from enum import Enum


class Environment(str, Enum):
    LOCAL = "LOCAL"
    TESTING = "TESTING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_debug(self):
        return self in (self.LOCAL, self.STAGING, self.TESTING)

    @property
    def is_testing(self):
        return self == self.TESTING

    @property
    def is_deployed(self) -> bool:
        return self in (self.STAGING, self.PRODUCTION)


LANGUAGES = [
    {
        "name": "C",
        "value": "c",
        "extension": ".c"
    },
    {
        "name": "C++",
        "value": "cpp",
        "extension": ".cpp"
    },
    {
        "name": "Python3",
        "value": "python3",
        "extension": ".py"
    },
    {
        "name": "Java",
        "value": "java",
        "extension": "java"
    }
]
