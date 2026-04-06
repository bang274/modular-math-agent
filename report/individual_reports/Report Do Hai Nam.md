# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên**: Đỗ Hải Nam
- **Mã sinh viên**: 2A202600038
- **Ngày thực hiện**: 06/04/2026

---

## I. Đóng góp kỹ thuật (15 Điểm)

Mình trực tiếp thiết kế và hiện thực hóa hệ thống Agent Pipeline đa tác nhân, đồng thời tuyển chọn mô hình, tool và tối ưu hóa bộ Prompt cho hệ thống.

- **Các mảng đóng góp chính**:
    - **Agent Core Architecture**: Xây dựng toàn bộ luồng điều phối bằng LangGraph. Thiết lập các cơ chế `Conditional Routing` để Agent tự động quyết định lộ trình giải bài (Easy vs Hard). Xử lý bộ nhớ agent, prompt caching và thiết kế luồng solution song song cho các bài toán để tăng tốc độ hệ thống.
    - **Model & Tool Orchestration**: Lựa chọn chiến lược các mô hình ngôn ngữ lớn và tích hợp bộ 3 công cụ: Wolfram Alpha, Tavily Search, và Python Sandbox.
    - **Prompt System Design**: Thiết kế hệ thống Prompt đa tầng, hỗ trợ xử lý ngữ cảnh tiếng Việt, định dạng lời giải LaTeX chuẩn xác, chuẩn hoá đầu ra đúng structure cho từng phase phản hồi.
    - **Testing Framework**: Xây dựng script kiểm thử đầu-cuối (`test_pipeline.py`) để đảm bảo tính ổn định của toàn bộ Workflow.

- **Code Highlights**:

**1. Cấu trúc LangGraph Orchestration (`graph.py`):**
Thiết kế sơ đồ luồng cho phép chạy song song các solver và tự động định tuyến dựa trên độ khó, ví dụ:
```python
# graph.py - Thiết lập Pipeline đa tác nhân (Parallel Fan-out)
graph.add_conditional_edges(
    "classifier",
    route_after_classifier,
    {
        "easy_solver": "easy_solver",
        "hard_solver": "hard_solver",
        "aggregator": "aggregator",
    },
)
...
```

**2. Prompt Engineering - "Math Final Boss" (`prompts.py`):**
Xây dựng logic "Sư phạm" cho Agent để phản hồi tiếng Việt một cách tự nhiên, ví dụ:
```python
# prompts.py - Logic tổng hợp kết quả (Aggregator)
AGGREGATOR_SYSTEM_PROMPT = """\
You are "Math Final Boss", an expert mathematics teacher and synthesizer.
Your goal is to provide a final, polished, and pedagogical response in VIETNAMESE.
STRICT RULES:
1. LANGUAGE: ALWAYS respond in natural, professional Vietnamese.
2. LATEX: Use LaTeX for all mathematical expressions (e.g., $x^2$).
...
"""
```

- **Documentation**:
Mã nguồn của mình điều phối chu trình **ReAct** đa tầng như sau:
1.  **Thought**: Node `classifier` và `critic` đóng vai trò là "bộ não" đưa ra các quyết định suy luận (xác định độ khó bài toán và kiểm định tính đúng đắn).
2.  **Action**: Agent thực thi các hành động thông qua `easy_solver` (LLM-based) hoặc `hard_solver` (gọi các công cụ Wolfram Alpha/Python Sandbox).
3.  **Observation**: Kết quả thô từ các công cụ được thu thập và lưu vào `AgentState` để chuẩn bị cho bước tổng hợp (Aggregate); hỗ trợ tracing bằng Langsmith UI.
4.  **Iteration**: Node fix code đóng vai trò là 1 vòng lặp, nếu code trong sandbox có bug, nó sẽ thực hiện vòng lặp để tự sửa lỗi.

---

## II. Case Study về Debugging (10 Điểm)

- **Mô tả vấn đề**: Xung đột cấu trúc dữ liệu (`dataclass error`) và lỗi mất trạng thái khi Agent chuyển tiếp qua nhiều công cụ.
- **Giải pháp**: Mình đã thực hiện tái cơ cấu hạ tầng tại `app/tools/base.py`, tập trung hóa định nghĩa `ToolResult` và cập nhật `AgentState` để hỗ trợ lưu trữ vết (`tool_trace`) và hình ảnh đồ thị. Điều này giúp hệ thống trở nên minh bạch và dễ quan sát hơn.

---

## III. Phản hồi cá nhân: Chatbot vs ReAct (10 Điểm)

1.  **Lý luận**: Khác biệt lớn nhất là khả năng "tự kiểm chứng". Agent của mình không chỉ trả lời mà còn biết tự quyết định lộ trình công cụ phù hợp nhất.
2.  **Độ tin cậy**: Nhờ sự kết hợp giữa mô hình LLM lớn và công cụ tính toán chính xác, Agent giải quyết được các bài toán ma trận/tích phân/giải tích số phức tạp với tỷ lệ sai sót thấp.
3.  **Quan sát**: Khả năng học từ lỗi của Python Sandbox là điểm sáng; Agent nhìn vào "Observation" để tự sửa script ngay lập tức.

---

## IV. Cải tiến tương lai (5 Điểm)

- **Dynamic Routing**: Tự động thay đổi Model LLM dựa trên ngân sách token và độ phức tạp của bài toán.
- **Agent Intelligent**: Mục tiêu cuối vẫn là tối ưu chất lượng đầu ra của agent với những model chất lượng thấp mà vẫn đảm bảo đầu ra chất lượng cao, đủ cạnh tranh với các ông lớn khác như ChatGPT, Gemini,...

---