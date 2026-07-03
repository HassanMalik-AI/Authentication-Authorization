from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar, List
from enum import Enum


T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Response status"""
    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


class ErrorDetail(BaseModel):
    """Error detail"""
    field: Optional[str] = Field(None, description="Field name that failed validation")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response"""
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[T] = Field(None, description="Response data")
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of errors")
    timestamp: Optional[str] = Field(None, description="Response timestamp")
    
    class Config:
        use_enum_values = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: List[T] = Field(default_factory=list, description="List of items")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_items: int = Field(default=0, ge=0, description="Total items count")
    total_pages: int = Field(default=0, ge=0, description="Total pages")
    has_more: bool = Field(default=False, description="Whether more items available")
    
    class Config:
        use_enum_values = True


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(..., description="Response message")
    status: ResponseStatus = ResponseStatus.SUCCESS
    
    class Config:
        use_enum_values = True


class ErrorResponse(BaseModel):
    """Error response"""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str = Field(..., description="Error message")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Detailed errors")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        use_enum_values = True


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    status: ResponseStatus = ResponseStatus.VALIDATION_ERROR
    message: str = "Validation error"
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")
    
    class Config:
        use_enum_values = True


class SuccessResponse(BaseModel):
    """Success response with data"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Success message")
    
    class Config:
        use_enum_values = True
