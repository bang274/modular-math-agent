# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Đức Cường
- **Student ID**: 2A202600174
- **Date**: 07/04/2026

---

## I. Technical Contribution (15 Points)

Xử lý phần tools của agent (wolfram, python sandbox, web search), nhận thông tin llm xử lý và trả lại dưới dạng json.

- **Modules Implementated**: `backend/app/tools/wolfram.py`
- **Code Highlights**: 

Cải tiến quan trọng: Sử dụng LLM-API thay cho API truyền thống để lấy kết quả diễn giải thay vì kết quả thô

```self.base_url = "https://www.wolframalpha.com/api/v1/llm-api"```

Tier 1.5: Sử dụng một LLM nội bộ để tối ưu hóa truy vấn trước khi gửi đến Wolfram

```translated_query = await self._translate_query(query)```

Xử lý fallback: Tự động dọn dẹp các ký tự LaTeX để đảm bảo API hiểu đúng

```clean_query = self._prepare_query(translated_query)```

- **Documentation**: 
Đoạn code này triển khai một Tool trong vòng lặp ReAct. Khi Agent đối mặt với các bài toán symbolic math phức tạp (tích phân, đạo hàm, phương trình), nó sẽ thực hiện bước Action: wolfram.
Điểm khác biệt chính là việc sử dụng llm-api, giúp kết quả trả về ở bước Observation không chỉ là một con số mà là một đoạn văn bản giải thích các bước giải. Điều này cung cấp ngữ cảnh cực kỳ quý giá cho bước Thought tiếp theo, giúp Agent hiểu tại sao có kết quả đó để tiếp tục lập luận hoặc tổng hợp câu trả lời cuối cùng cho người dùng.
---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Dù đã có bộ lọc LaTeX và Prompt translation, Agent vẫn liên tục nhận phản hồi lỗi từ Wolfram Alpha v2 khi gặp các biểu thức tích phân phức tạp hoặc câu hỏi có ngữ cảnh tiếng Việt xen lẫn. Điều này khiến Agent bị kẹt trong vòng lặp: Thought -> Action (Lỗi) -> Thought -> Action (Lỗi lại).
- **Log Source**: [Wolfram] Original: tích phân x^2... [Wolfram] Result success=False: Wolfram Alpha did not understand your input.
- **Diagnosis**: API của Wolfram Alpha (đặc biệt là bản LLM) hoạt động tốt nhất với ngôn ngữ tự nhiên hoặc cú pháp toán học đơn giản, trong khi LLM của hệ thống thường có xu hướng giữ nguyên định dạng LaTeX từ prompt.
- **Solution**: Tôi đã quyết định Refactor (viết lại) toàn bộ Tool để chuyển sang dùng llm-api. Đây là phiên bản API hiện đại hơn, có khả năng tự dung lỗi (error-tolerant) và hỗ trợ tốt cho các Agent. Tôi giữ lại lớp tiền xử lý chuỗi như một lớp bảo vệ bổ sung để tối ưu hóa chi phí và độ chính xác.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối Thought giúp Agent nhận ra khi nào khả năng tính toán của bản thân (LLM nội bộ) là không đủ tin cậy. Thay vì tự "bịa" ra kết quả tích phân (hallucination), Agent suy nghĩ: "Tôi cần tính đạo hàm chính xác, tôi sẽ dùng công cụ Wolfram".
2.  **Reliability**: Agent chạy chậm hơn Chatbot thông thường do phải qua nhiều bước trung gian. Trong các bài toán số học cực đơn giản (như 1+1), việc gọi ReAct và Wolfram là dư thừa và làm tăng chi phí API không cần thiết.
3.  **Observation**: Việc sử dụng llm-api của Wolfram giúp Observation trở nên trực quan. Khi Wolfram trả về các bước giải, Agent có thể sử dụng các bước đó để giải thích lại cho người dùng, làm tăng độ tin cậy (Transparency) của hệ thống so với việc chỉ đưa ra con số cuối cùng.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Triển khai cơ chế Caching (như Redis) cho các truy vấn toán học phổ biến để tránh lặp lại các request tốn phí đến Wolfram Alpha API (giới hạn 2000 lần/tháng).
- **Safety**: Thêm một lớp kiểm tra độ dài và tính hợp lệ của query đầu vào để tránh việc Agent bị lợi dụng để thực hiện các truy vấn phá hoại hoặc quá tải hệ thống.
- **Performance**: Chuyển đổi việc chọn Tool từ hard-coded sang Semantic Tool Selection (sử dụng Vector DB để chọn tool phù hợp nhất với câu hỏi), giúp hệ thống mở rộng lên hàng trăm tool mà không làm nhiễu Context Window của LLM.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
