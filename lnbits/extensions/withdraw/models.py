from starlette.requests import Request
from fastapi.param_functions import Query
from lnurl import Lnurl, LnurlWithdrawResponse, encode as lnurl_encode  # type: ignore
from sqlite3 import Row
from pydantic import BaseModel
import shortuuid  # type: ignore

class CreateWithdrawData(BaseModel):
    title:  str = Query(...)
    min_withdrawable:  int = Query(..., ge=1)
    max_withdrawable:  int = Query(..., ge=1)
    uses:  int = Query(..., ge=1)
    wait_time:  int = Query(..., ge=1)
    is_unique:  bool


class WithdrawLink(BaseModel):
    id: str
    wallet: str
    title: str
    min_withdrawable: int
    max_withdrawable: int
    uses: int
    wait_time: int
    is_unique: bool
    unique_hash: str
    k1: str
    open_time: int
    used: int
    usescsv: str
    number: int

    @classmethod
    def from_row(cls, row: Row) -> "WithdrawLink":
        data = dict(row)
        data["is_unique"] = bool(data["is_unique"])
        data["number"] = 0
        return cls(**data)

    @property
    def is_spent(self) -> bool:
        return self.used >= self.uses

    def lnurl(self, req: Request) -> Lnurl:
        if self.is_unique:
            usescssv = self.usescsv.split(",")
            tohash = self.id + self.unique_hash + usescssv[self.number]
            multihash = shortuuid.uuid(name=tohash)
            url = req.url_for(
                "withdraw.api_lnurl_multi_response",
                unique_hash=self.unique_hash,
                id_unique_hash=multihash
            )
        else:
            url = req.url_for(
                "withdraw.api_lnurl_response",
                unique_hash=self.unique_hash
            )

        return lnurl_encode(url)


    def lnurl_response(self, req: Request) -> LnurlWithdrawResponse:
        url = req.url_for(
            name="withdraw.api_lnurl_callback", unique_hash=self.unique_hash
        )
        return LnurlWithdrawResponse(
            callback=url,
            k1=self.k1,
            min_withdrawable=self.min_withdrawable * 1000,
            max_withdrawable=self.max_withdrawable * 1000,
            default_description=self.title,
        )


class HashCheck(BaseModel):
    id: str
    lnurl_id: str

    @classmethod
    def from_row(cls, row: Row) -> "Hash":
        return cls(**dict(row))
