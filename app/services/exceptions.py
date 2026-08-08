"""Domain-level exceptions raised by the service layer."""


class ServiceError(Exception):
    """Base class for all business-rule violations."""


class DuplicateISBNError(ServiceError):
    pass


class DuplicateEmailError(ServiceError):
    pass


class BookUnavailableError(ServiceError):
    pass


class BookInUseError(ServiceError):
    pass


class DuplicateRequestError(ServiceError):
    pass


class InvalidStateError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass
