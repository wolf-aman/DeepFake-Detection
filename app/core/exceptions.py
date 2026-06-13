from __future__ import annotations


class AppError(Exception):
    """Base class for expected application errors."""

    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class InferenceError(AppError):
    status_code = 500


class StorageError(AppError):
    status_code = 500
