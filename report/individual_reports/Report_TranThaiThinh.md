# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: TRAN THAI THINH
- **Student ID**: 2A202600310
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- Xử lý phần input của bài toán, xây dựng module xử lý đầu vào nhận thông tin từ frontend là text hoặc images, sử dụng model Lllama thực hiện extract text và image thành định dạng json chuẩn để thực hiện đưa vào luồng xử lý LLM. 

- {
  "problems": [
    {
      "id": "bai_1",
      "content": "x^2 - 4x - 4 = 0"
    }
  ],
  "total": 1,
  "source": "text",
  "ocr_text": null,
  "error": null
}

- **Modules Implemented**: 
  1. `backend/app/agent/nodes/extractor.py`: 
     - Nếu là text thì thực hiện extract sang định dạng Json để đưa vào luồng LLM
     - Nếu input là image thực hiện trích xuất dữ liệu đầu vào từ frontend. Sử dụng gọi API Vision LLM để thực hiện trích xuất Text/LaTeX từ images.
  2. `backend/app/utils/image.py`: 
     - Nhận input tiền xử lý dữ liệu ảnh thô nhận từ người dùng,  tự động tính toán tỷ lệ để (Resize) để nạp lên Vison LLM. 

- **Code Highlights**: 
  Đoạn code trong `app/agent/nodes/extractor.py` thể hiện việc chuyển đổi từ Text Model -> Multimodal.
  ```python
  async def extract_problems_from_image(image_b64: str) -> Dict[str, Any]:
      try:
          llm = get_extractor_llm()
          messages = [
              SystemMessage(content=EXTRACTOR_SYSTEM_PROMPT),
              HumanMessage(content=[
                  {"type": "text", "text": EXTRACTOR_IMAGE_PROMPT},
                  {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
              ])
          ]
          response = await llm.ainvoke(messages)
          ...
      except Exception as e:
          return {"problems": [], "error": f"Lỗi gọi LLM/Vision: {str(e)}"}
  ```

- **Documentation**: 
 Khi người dùng đưa một đề bài có nhiều câu hỏi, nếu đưa trực tiếp tờ bài tập đó cho Agent đi vào vòng lặp reasoning thì bộ nhớ Agent sẽ bị rối và dễ dàng Hallucinated
  
     Nên trong hệ thống nasyfm tôi thực hiện viết File `image.py` sẽ cắt gọn bức ảnh rồi nối vào file `extractor.py`. Ở đây, chức năng Extracr như một **Filter & Parser**: dùng LLM để đọc ảnh, phân tách từng query, format thành chuẩn toán học LaTeX rồi lưu mỗi câu hỏi thành 1 chuỗi `JSON`. 

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Nó chỉ gặp lỗi như sau : `HTTP 500 Internal Server Error` sau khi em gọi thử API `/api/v1/extract/text`.
- **Log Source**: 
  ```json
  {"detail":"Lỗi cấu hình LLM hoặc gọi API: The api_key client option must be set either by passing api_key to the client or by setting the GROQ_API_KEY environment variable"}
  ```
- **Diagnosis**: Nguyên nhân

  -  **Lỗi Code thiếu Safe-Catch**: Khi em chạy lệnh `get_extractor_llm()` khởi tạo Model bị đặt nằm bên ngoài khối `try-except`. Khi đến Class ChatGroq không tìm thấy API Key, nó trả `ValidationError` dẫn đến gây lỗi 500. 
- **Solution**: 
  1. **Refactor Code API**: em đã chuyển chuỗi lệnh `llm = get_extractor_llm()` vào đóng gói bên trong khối `try-catch`. 
  2. Di chuyển copy file `.env` vào đúng cấp thư mục `backend/` nơi tiến trình Worker Uvicorn hoạt động. Sau đó dùng lệnh `touch` cập nhật file để ép uvicorn Refresh tự động nạp lại API Key mới. 

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)


1.  **Reasoning**: Khối **Though** ép LLM phải suy luận từng bước nên là khả năng cao có thể giảm thiểu hiện tượng hallucination 
2.  **Reliability**: Pipeline phức tạp, tốn nhiều token để triển khai, và có latency cao hơn do mất thời gian retasoning và gọi nhiều khá là nhiều tools 
3.  **Observation**: Agent sẽ đọc được Observation này, nhận ra cách tiếp cận sai và thực hiện sửa chữa lập tức thay vì tiếp tục. 

---

## IV. Future Improvements (5 Points)

- **Scalability**: Có thể triển khai kiến trúc hàng đợi bất đồng bộ để xử lý các tác vụ gọi Tool tốn thời gian.
- **Safety**: Thiết lập cơ chế "Supervisor Agent" (Agent giám sát độc lập) để kiểm duyệt và cấp phép cho các hành động nhạy cảm của Agent chính
- **Performance**: Sử dụng Vector Database để lưu trữ và truy xuất nhanh các công thức toán học hoặc các bài toán tương tự đã từng giải trước đó.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.