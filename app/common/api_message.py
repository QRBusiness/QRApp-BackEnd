from enum import Enum


class KeyResponse(str, Enum):
    SUCCESS = "SUCCESS"
    CONFLICT = "CONFLICT"
    USERNAME_CONFLICT = "USERNAME_CONFLICT"
    PHONE_CONFLICT = "PHONE_CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVER_ERROR = "SERVER_ERROR"


MessageResponse = {
    "vi": {
        KeyResponse.SUCCESS: "Thành công",
        KeyResponse.USERNAME_CONFLICT: "username đã được sử dụng",
        KeyResponse.PHONE_CONFLICT: "Số điện thoại đã được sử dụng",
        KeyResponse.UNAUTHORIZED: "Yêu cầu đăng nhập",
        KeyResponse.INVALID_CREDENTIALS: "Tên đăng nhập hoặc mật khẩu không chính xác",
        KeyResponse.INVALID_TOKEN: "Token không hợp lệ",
        KeyResponse.SESSION_EXPIRED: "Session không hợp lệ",
        KeyResponse.PERMISSION_DENIED: "Bạn không đủ quyền thực hiện hành động này",
        KeyResponse.SERVER_ERROR: "Hệ thống đang bận, vui lòng thử lại sau.",
    },
    "en": {
        KeyResponse.SUCCESS: "Success",
        KeyResponse.USERNAME_CONFLICT: "Username already exists",
        KeyResponse.PHONE_CONFLICT: "Phone number already exists",
        KeyResponse.UNAUTHORIZED: "Please login to continue",
        KeyResponse.INVALID_CREDENTIALS: "Invalid username or password",
        KeyResponse.INVALID_TOKEN: "Invalid token",
        KeyResponse.SESSION_EXPIRED: "Session expired",
        KeyResponse.PERMISSION_DENIED: "Permission denied",
        KeyResponse.SERVER_ERROR: "An error occurred, please try again later",
    },
}


def get_message(key: KeyResponse, lang: str = "vi") -> str:
    return MessageResponse.get(lang, MessageResponse["vi"]).get(key, "")
