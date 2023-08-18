from fastapi import Form, Depends
from routers.api_router import APIRouter

from config import API_KEY
from models import (
    ErrorMessage,
    APIKeyErrorMessage,
    ClientSuccessMessage,
    ClientListMessage
)
from locales import get_locale_model
from common import (
    ClientType
)
from database.db_access import DBAccessLayer
from database.models import Client
from depends import create_dal, connection_count_inc

router = APIRouter(
    prefix="/client",
    dependencies=[Depends(connection_count_inc)]
)


@router.post("/new")
async def client_new_handler(
        api_key: str = Form(),
        token: str = Form(),
        client_type: str = Form(),
        locale: str = Form(),
        mobile: bool = Form(),
        proxied: bool = Form(),
        dal: DBAccessLayer = Depends(create_dal)
) -> ErrorMessage | ClientSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    client_type: str = client_type.upper()
    if client_type not in ClientType.__members__:
        return ErrorMessage(
            error_type="032",
            message="Invalid client type."
        )
    locale_model = get_locale_model(locale)
    if not locale_model:
        return ErrorMessage(
            error_type="032",
            message="Invalid locale."
        )
    client_type_value = ClientType[client_type].value
    await dal.new_client(
        token=token,
        client_type=client_type_value,
        locale=locale,
        mobile=mobile,
        proxied=proxied
    )
    await dal.commit()
    return ClientSuccessMessage(
        success="Successfully created client.",
        token=token,
        client_type=client_type,
        locale=locale,
        mobile=mobile,
        proxied=proxied
    )


@router.post("/list")
async def client_list_handler(
        api_key: str = Form(),
        dal: DBAccessLayer = Depends(create_dal)
) -> ErrorMessage | ClientListMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    clients: list[Client] = await dal.get_all_clients()
    return ClientListMessage(
        result=[
            ClientSuccessMessage(
                success=None,
                token=client.token,
                client_type=ClientType(client.type).name,
                locale=client.locale,
                mobile=client.mobile,
                proxied=client.proxied
            ) for client in clients
        ]
    )


@router.post("/{token}/revoke")
async def client_revoke_handler(
        token: str,
        api_key: str = Form(),
        dal: DBAccessLayer = Depends(create_dal)
) -> ErrorMessage | ClientSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    client: Client | None = await dal.get_client_by_token(token=token)
    if client is None:
        return ErrorMessage(
            error_type="033",
            message="Client not found."
        )
    await dal.revoke_client(client=client)
    await dal.commit()
    return ClientSuccessMessage(
        success="Successfully revoked client.",
        token=token
    )


@router.post("/{token}/delete")
async def client_delete_handler(
        token: str,
        api_key: str = Form(),
        dal: DBAccessLayer = Depends(create_dal)
) -> ErrorMessage | ClientSuccessMessage:
    if api_key != API_KEY:
        return APIKeyErrorMessage(api_key=api_key)
    client: Client | None = await dal.get_client_by_token(token=token)
    if client is None:
        return ErrorMessage(
            error_type="033",
            message="Client not found."
        )
    await dal.delete_client(client=client)
    await dal.commit()
    return ClientSuccessMessage(
        success="Successfully deleted client.",
        token=token
    )
