"""Application error hierarchy.

Services raise these domain errors; the API layer maps them to HTTP
responses with user-friendly messages. Stack traces are never exposed.
"""


class AppError(Exception):
    """Base application error."""

    status_code = 500
    code = "internal_error"
    message = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found."


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_failed"
    message = "Invalid credentials."


class AuthorizationError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have access to this resource."


class ValidationFailedError(AppError):
    status_code = 422
    code = "validation_failed"
    message = "Invalid input."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Resource already exists."


class FileUploadError(AppError):
    status_code = 400
    code = "invalid_file"
    message = "Invalid or unsupported file."


class TextExtractionError(AppError):
    status_code = 422
    code = "text_extraction_failed"
    message = "Unable to extract text from this file."


class AIServiceError(AppError):
    status_code = 503
    code = "ai_service_unavailable"
    message = "The AI service is temporarily unavailable. Please try again."


class RateLimitExceededError(AppError):
    status_code = 429
    code = "rate_limit_exceeded"
    message = "Too many requests. Please slow down."
