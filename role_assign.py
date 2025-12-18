import firebase_admin
from firebase_admin import credentials, auth

sa_json_fp = "/Users/praveenkumar/Projects/Swyft/platform/misc/zoom-shops-dev-SA.json"
cred = credentials.Certificate(sa_json_fp)
firebase_admin.initialize_app(cred)

user_uuid = "hARpSpLJVRgK8mxZgs4FxI25OXG2"
role_name = "viewer" # "admin" # 
auth.set_custom_user_claims(
    uid=user_uuid,
    custom_claims={"role": role_name}
)

# # To make viewer
# {"role": "viewer"}
