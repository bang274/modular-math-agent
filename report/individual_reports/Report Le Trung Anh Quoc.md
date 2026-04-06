# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Trung Anh Quốc
- **Student ID**: 2A202600108
- **Date**: 6/4/2026

---

## I. Technical Contribution (15 Points)
Em nhận trách nhiệm cho phần phát triển hệ thống giao diện người dùng (frontend) cho dự án. Công việc của em bao gồm việc xây dựng giao diện chat tương tác, quản lý lịch sử phiên làm việc, và tích hợp các chức năng đa phương tiện như tải lên hình ảnh chứa bài toán. Ngoài ra, em còn tham giam resolve conflict từ các luồng PR của dự án. Em cũng đảm nhiệm vai trò đóng gói toàn bộ dự án thành image và build container trên docker để chạy demo trước lớp 

- **Modules Implementated**: `frontend/`
- **Code Highlights**: 

```javascript
if (images.length > 0) {
  response = await solveFromUpload(text || undefined, images[0].file);
} else {
  response = await solveFromText(text);
}
```
- Dùng để chuyển hướng các luồng dữ liệu đầu vào đến backend service.
- Chuẩn hóa dữ liệu đầu vào bằng trim

- **Documentation**: 
- Phát triển giao diện bao gồm các components chính là ô sessions, Create session button, Chatbox, Input field, Suggest Input, Submit button, Import image.
- Hiển thị nội dung bài toán mà người dùng yêu cầu giải quyết.
![alt text](image-1.png)


---

## II. Debugging Case Study (10 Points)
### Case 1:
 Định dạng đầu vào dựa trên dữ liệu người dùng. Cập nhật phần kiểm tra dữ liệu (validation) của dự án để chỉ định định dạng chính xác, sau đó chuyển đổi sang JSON và gửi đến module đầu vào (input module).
### Case 2:
 Endpoint missmatch. Định nghĩa lại các endpoint để khớp với module đầu vào và module backend.
### Case 3:
 Giao diện hình ảnh bị lỗi. Tìm hiểu và khắc phục lỗi hiển thị hình ảnh.
### Case 4:
 Giải quyết xung đột (conflict) từ GitHub PR.

- **Problem Description**: API missmatch, giải quyết bằng cách log các lỗi ra và tiến hành trace lỗi, thử ở localhost để gọi thử api. API phía backend hoạt động tốt, trả về chuẩn format và chỉ sai Endpoint dẫn đến module frontend của bản thân không thể fetch dữ liệu
- **Log Source**:
![alt text](image-2.png)
- **Diagnosis**: Do đã có kinh nghiệm xây dựng backend, việc frontend không thể fetch dữ liệu từ backend có thể đến từ nhiều nguyên nhân khác nhau, nhưng có thể nhất vẫn là api missmatch
- **Solution**: Giải quyết bằng cách log các lỗi ra và tiến hành trace lỗi, thử ở localhost để gọi thử api. API phía backend hoạt động tốt, trả về chuẩn format và chỉ sai Endpoint dẫn đến module frontend của bản thân không thể fetch dữ liệu

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
Nó giúp bản thân agent có thể đưa ra phán đoán sâu hơn, và nó cũng có thể đưa ra quyết định sử dụng tool để thực hiện task cụ thể. Thứ có thể giúp nó giải quyết bài toán triệt để hơn chatbot thông thường.
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
Trong trường hợp chỉ trả lời thông tin không mang tính tình huống. Hoặc là các thao tác không cần suy luận sâu mà có thể trả lời ngay. Hoặc là cái yêu cầu về độ trễ, phản hồi nhanh
3.  **Observation**: How did the environment feedback (observations) influence the next steps?
Đây chính là yếu tố điều hướng toàn bộ decision loop của agent. Không có nó thì agent chỉ có thể sử dụng tool dựa theo cảm tính của nó.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Cải thiện input đa luồng để có thể giải nhiều bài toán hơn trong khoảng thời gian cố định. Điều đó có thể out- perform các baseline chatbot thông thường ngay cả là những yêu cầu đơn giản
- **Safety**: Implement prompt enjection vào phía frontend lẫn backend để validate input.
Backend có thể sử dụng Jwt token bằng cách xác thực request người dùng.
- **Performance**: Nâng cấp api các model để nâng chất lượng response. Tối ưu system prompt để ràng buộc kỹ hơn về output.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
