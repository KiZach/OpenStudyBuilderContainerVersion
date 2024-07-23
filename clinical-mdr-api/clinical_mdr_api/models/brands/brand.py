from typing import Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.brands.brand import BrandAR
from clinical_mdr_api.models.utils import BaseModel


class Brand(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the Brand.",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], BrandAR | None],
    ) -> Self | None:
        brand = None
        brand_ar: BrandAR = find_by_uid(uid)
        if brand_ar is not None:
            brand = Brand.from_brand_ar(brand_ar)
        return brand

    @classmethod
    def from_brand_ar(
        cls,
        brand_ar: BrandAR,
    ) -> Self:
        return Brand(
            uid=brand_ar.uid,
            name=brand_ar.name,
        )


class BrandCreateInput(BaseModel):
    name: str = Field(..., title="name", description="", min_length=1)
