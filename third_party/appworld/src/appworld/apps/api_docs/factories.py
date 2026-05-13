from typing import Any, cast

from faker import Faker

from appworld.apps.api_docs import models as _models
from appworld.apps.lib.factories import ModelFactory


models = cast(Any, _models)


class ApiDocFactory(ModelFactory):
    __model__ = models.ApiDoc
    id = lambda: None
    url = Faker().url
    response_schemas: Any = lambda: {"success": {}, "failure": {}}
