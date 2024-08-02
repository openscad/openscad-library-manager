from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints, field_serializer

REQUIRED = ...
type NonEmptyString = Annotated[str, StringConstraints(min_length=1)]


class Person(BaseModel):
    name: NonEmptyString = Field(
        REQUIRED,
    )
    email: NonEmptyString = Field(
        REQUIRED,
    )


class License(BaseModel):
    file: Optional[NonEmptyString] = Field(
        default=None,
    )
    identifier: Optional[NonEmptyString] = Field(
        default=None,
    )

    def __bool__(self):
        return (self.file is not None) or (self.identifier is not None)


class Library(BaseModel):
    name: NonEmptyString = Field(
        REQUIRED,
    )
    version: NonEmptyString = Field(
        REQUIRED,
    )
    short_description: str = Field(  # limited to 100 char
        default="",
    )
    long_description: str = Field(  # limited to 300 char
        default="",
    )
    authors: list[Person] = Field(
        default_factory=list,
    )
    maintainers: list[Person] = Field(
        default_factory=list,
    )
    tags: list[NonEmptyString] = Field(
        default_factory=list,
    )
    readme: Optional[NonEmptyString] = Field(
        default=None,
    )
    license: Optional[License] = Field(
        default=None,
    )


class Files(BaseModel):
    scad: list[NonEmptyString] = Field(
        REQUIRED,
    )


class Urls(BaseModel):
    repository: str = Field(
        REQUIRED,
    )
    homepage: Optional[str] = Field(
        default=None,
    )
    documentation: Optional[str] = Field(
        default=None,
    )
    preview_images: list[str] = Field(
        default_factory=list,
    )


class Manifest(BaseModel):
    manifest_version: str
    library: Library = Field(
        REQUIRED,
    )
    dependencies: dict[str, str] = Field(
        default_factory=dict,
    )
    # TODO: restore support
    # files: Files = Field(
    #     REQUIRED,
    # )
    urls: Urls = Field(
        REQUIRED,
    )


class RemoteLibrary(BaseModel):
    manifest: Manifest
    download_link: str


class LocalLibrary(BaseModel):
    manifest: Manifest = Field(
        REQUIRED,
    )
    location: str = Field(
        REQUIRED,
    )
    date_added: datetime = Field(
        REQUIRED,
    )

    @field_serializer("date_added")
    def serialize_datetime(self, d: datetime, _info) -> float:
        return d.timestamp()
