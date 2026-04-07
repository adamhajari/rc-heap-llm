import httpx
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

OPEN_WEBUI_URL = "http://mercer.cluster.recurse.com:8080"
RC_BASE_URL = "https://www.recurse.com"


@app.route("/.well-known/openid-configuration")
def openid_configuration():
    base = request.host_url.rstrip("/")
    return jsonify({
        "issuer": base,
        "authorization_endpoint": f"{RC_BASE_URL}/oauth/authorize",
        "token_endpoint": f"{RC_BASE_URL}/oauth/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["profile"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
    })


@app.route("/userinfo")
def userinfo():
    auth = request.headers.get("Authorization")
    resp = httpx.get(
        f"{RC_BASE_URL}/api/v1/profiles/me",
        headers={"Authorization": auth},
    )
    resp.raise_for_status()
    profile = resp.json()
    return jsonify({
        "sub": str(profile["id"]),
        "name": profile["name"],
        "email": profile.get("email", ""),
        "picture": profile.get("image_path", ""),
    })


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path):
    url = f"{OPEN_WEBUI_URL}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() != "host"}
    resp = httpx.request(
        method=request.method,
        url=url,
        headers=headers,
        content=request.get_data(),
        params=request.args,
        follow_redirects=False,
    )
    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
    return Response(resp.content, status=resp.status_code, headers=response_headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
