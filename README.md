# 🚀 QRApp Backend

---

## 📦 Project Setup

### ✅ Yêu cầu

- Python 3.12+
- [UV](https://astral.sh/blog/uv/) (trình quản lý gói siêu nhanh)
- Docker (tuỳ chọn)

---

### 🔧 Cài đặt & chạy bằng mã nguồn

#### 1. Cài đặt UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Clone repository

```bash
git clone https://github.com/QRCoffee/QRApp-BackEnd.git
cd QRApp-BackEnd
```

#### 3. Tạo file `.env`

```ini
# .env
ACCESS_KEY=
REFRESH_KEY=
MONGO_URL=
REDIS_URL=
MINIO_ENDPOINT=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```

#### 4. Tạo môi trường ảo và cài dependencies

```bash
uv venv
source .venv/bin/activate      # Linux/MacOS
source .venv/Scripts/activate  # Windows
uv sync
```

#### 5. Chạy ứng dụng

```bash
make dev         # chế độ phát triển (hot reload)
make production  # chế độ production
```

---

### 🐳 Chạy bằng Docker

#### 1. Dùng image có sẵn trên Docker Hub

```bash
docker pull nhathuyd4hp/qrapp-backend:latest
```
#### 2. Tạo file `.env`

```ini
# .env
ACCESS_KEY=
REFRESH_KEY=
MONGO_URL=
REDIS_URL=
MINIO_ENDPOINT=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
```

#### 3. Chạy container

```bash
docker run -p 8000:8000 --env-file .env nhathuyd4hp/qrapp-backend:latest
```

## 📑 Tài liệu API

Truy cập Swagger UI tại:
👉 [http://103.7.43.118:8000/docs](http://103.7.43.118:8000/docs)