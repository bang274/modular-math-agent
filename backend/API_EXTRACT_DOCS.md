# Tài liệu API - Module A (Input Processing & Extraction)

Tài liệu này dành cho team Frontend để tích hợp chức năng gửi đoạn văn bản (Text) hoặc hình ảnh (Image) lên Backend để trích xuất ra danh sách các bài toán (dưới định dạng JSON) trước khi đưa vào luồng giải.

> **Lưu ý:**
> Backend đã có sẵn Swagger UI tự động tại `http://localhost:8000/docs`. Frontend có thể vào thẳng link này để test API trực tiếp qua giao diện.

---

## 1. Đầu cuối 1 (Endpoint): Trích xuất bài toán từ Văn Bản (Text)

Sử dụng khi người dùng nhập tay một đoạn văn bản dài có chứa các bài toán.

*   **URL:** `/api/v1/extract/text`
*   **Method:** `POST`
*   **Content-Type:** `application/json`

### Body Request

```json
{
  "text": "Giải hệ phương trình 2x + y = 5 và x - y = 1. Bài 2: Tính tích phân của x^2 từ 0 đến 1"
}
```

---

## 2. Đầu cuối 2 (Endpoint): Trích xuất bài toán từ Hỉnh Ảnh (Image)

Sử dụng khi người dùng upload ảnh chụp bài tập. Backend sẽ sử dụng Mô hình Thị giác (Vision LLM) để tự đọc ảnh và trả về JSON chuẩn.

*   **URL:** `/api/v1/extract/image`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`

### Body Request
Gửi đi ở dạng `FormData`.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `image` | `File` | File ảnh của người dùng (Giới hạn tối đa 10MB. Chấp nhận: JPEG, PNG, WebP, GIF) |

*Ví dụ dùng JS/TS (Fetch API):*
```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('/api/v1/extract/image', {
  method: 'POST',
  body: formData
});
```

---

## 3. Định dạng Response (Dành chung cho 2 loại)

Khi thành công (Status Code `200 OK`), Backend luôn trả về chung một cấu trúc JSON duy nhất:

```json
{
  "problems": [
    {
      "id": "bai_1",
      "content": "Giải hệ phương trình $2x + y = 5$ và $x - y = 1$"
    },
    {
      "id": "bai_2",
      "content": "Tính $\\int_0^1 x^2\\,dx$"
    }
  ],
  "total": 2,
  "source": "text", 
  "ocr_text": null,
  "error": null
}
```

### Giải thích các trường dữ liệu:
*   `problems`: Mảng chứa danh sách các bài toán đã bóc tách. Mỗi bài sẽ có `id` (hiển thị UI) và `content` là nội dung bài toán (Công thức toán sẽ luôn ở định dạng chuẩn **LaTeX** với dấu `$`).
*   `total`: Tổng số bài toán bóc tách được.
*   `source`: Trả về `"text"` hoặc `"image"` để Frontend biết luồng nào vừa hoạt động.
*   `error`: Trả về `null`. (*Sẽ chứa string nội dung cảnh báo nếu như bị lỗi gì râu ria mà vẫn muốn trả Status 200*).

---

## 4. Các mã lỗi HTTP (Error Codes) có thể xảy ra

Frontend cần bắt các mã trạng thái này để hiển thị Toast / Alert báo lỗi cho người dùng:

*   `400 Bad Request`: Validation lỗi (Gửi chữ rỗng).
*   `413 Payload Too Large`: File ảnh upload lớn hơn 10MB.
*   `415 Unsupported Media Type`: Cố tình upload file không phải là ảnh hợp lệ (VD: Ném file PDF, TXT vào Endpoint image).
*   `422 Unprocessable Entity`: Mô hình LLM không thể tìm thấy bất kỳ bài toán nào trong ảnh / đoạn văn bản.
*   `500 Internal Server Error`: Lỗi sập cấu hình Backend hoặc lỗi gọi Model LLM bị đứt kết nối.
