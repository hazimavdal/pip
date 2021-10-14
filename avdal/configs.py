import os
import socket
import requests as req
from .env import Env
from .auth.keycloak import Keycloak


def load_configs(role):
    env = Env()

    configs_protocol = env("CONFIGS_PROTOCOL", default="https")
    configs_host = env("CONFIGS_HOST", default="configs.avd.al")
    configs_client = env("CONFIGS_CLIENT_ID", default="")
    configs_secret = env("CONFIGS_CLIENT_SECRET", default="")

    iam_host = env("IAM_HOST", default="iam.avd.al")
    iam_realm = env("IAM_REALM", default="groot")

    if not configs_client:
        print("CONFIGS_CLIENT_ID not set. Skipping remote configs")
        return

    keycloak = Keycloak(iam_host, iam_realm, configs_client, configs_secret)
    token, error = keycloak.access_token()

    if not token:
        print("failed to get a token due to", error)
        return

    def load_role(role):
        print(f"loading role: {role}")

        res = req.get(f"{configs_protocol}://{configs_host}/api/v1/roles/{role}/configs", headers={
            "Authorization": f"Bearer {token}",
        })

        if not res.ok:
            return

        for k, v in res.json().items():
            os.environ[k] = str(v)
        
        print(f"loaded role: {role}")

    load_role(role)
    load_role("common")
    load_role(socket.gethostname().lower())
