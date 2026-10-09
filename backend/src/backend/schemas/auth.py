from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class RegisterRequest(BaseModel):
    name: Name
    email: Annotated[EmailStr, AfterValidator(str.lower)]
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: Annotated[
        str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)
    ]
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    name: str
    email: str


class RegisterResponse(BaseModel):
    message: str
    data: UserPublic


class LoginResponse(BaseModel):
    message: str
    token: str
    data: UserPublic
