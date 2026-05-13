from appworld.apps.lib.responses import ResponseModel as _ResponseModel


class ResponseModel(_ResponseModel):
    pass


@ResponseModel.register("balance")
class BalanceResponse(ResponseModel):
    balance: float


@ResponseModel.register("valid")
class ValidResponse(ResponseModel):
    valid: bool
