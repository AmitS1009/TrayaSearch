from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductBase(BaseModel):
    title: str
    price: str
    description: str | None = None
    features: list[str] = Field(default_factory=list)
    image_url: str | None = None
    category: str | None = None
    url: str


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class ChatHistoryResponse(BaseModel):
    id: str
    query: str
    response: str
    retrieved_docs: list[dict]
    self_rag_retries: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
