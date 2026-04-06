# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Văn Thạch
- **Student ID**: 2A202600237
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Tập trung vào hoàn thiện lớp Cache và Database, đồng thời tăng độ tin cậy bằng bộ test bao phủ behavior quan trọng.

- **Modules Implemented**:
	- backend/app/cache/prompt_cache.py
	- backend/app/cache/rate_limiter.py
	- backend/app/cache/redis_client.py
	- backend/app/db/database.py
	- backend/app/db/repository.py
	- backend/app/agent/nodes/cache_node.py
	- backend/tests/test_cache.py
	- backend/tests/test_repository.py
	- backend/tests/test_api.py (integration test mới cho cache-hit)

- **Code Highlights**:
	- PromptCache + RateLimiter tests (success/failure path, fail-open, quota): [backend/tests/test_cache.py](backend/tests/test_cache.py)
	- RedisManager + DatabaseManager lifecycle/health checks: [backend/tests/test_cache.py](backend/tests/test_cache.py)
	- SessionRepository save/get/history + DB error path: [backend/tests/test_repository.py](backend/tests/test_repository.py)
	- Cache node hardening (only count store on successful cache.set): [backend/app/agent/nodes/cache_node.py](backend/app/agent/nodes/cache_node.py)
	- Cache-hit integration test qua solve endpoint + verify DB cache_hit flag: [backend/tests/test_api.py](backend/tests/test_api.py)

- **Documentation (interaction with ReAct/agent loop)**:
	- Cache node được đặt trước và sau quá trình reasoning/solving trong pipeline:
		- cache_check_node: đọc Redis trước khi gọi solver để tái sử dụng kết quả cũ.
		- cache_store_node: ghi Redis sau khi có kết quả cuối.
	- Ở nhánh API solve, kết quả pipeline được lưu xuống DB thông qua repository, đảm bảo history truy vết được route, độ tin cậy và cache_hit.
	- Thiết kế này giúp giảm latency cho bài toán lặp lại và giữ được audit trail cho các phiên làm bài.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
	- Integration test mới cho cache-hit ban đầu bị fail do không lấy được session từ DB (stored_session = None).

- **Log Source**:
	- Log lỗi khi chạy test:
		- [DB] Error saving session: Database not initialized
		- [DB] Error saving solution: Database not initialized
		- [DB] Error getting session: Database not initialized
	- Lỗi xuất hiện trong lần chạy test:
		- python3 -m pytest tests/test_api.py::TestSolveCacheHitIntegration::test_solve_cache_hit_persists_flag_in_db -q

- **Diagnosis**:
	- Nguyên nhân không nằm ở prompt/model/tool spec mà nằm ở test harness.
	- client fixture hiện có không tự khởi tạo db_manager cho test này, trong khi code solve endpoint vẫn gọi _save_to_db.
	- Do đó dữ liệu response trả đúng nhưng không persist được xuống DB, làm assert sau đó thất bại.

- **Solution**:
	- Sửa test để init DB tạm bằng sqlite file trong tmp_path ngay đầu test.
	- Đóng DB ở finally để tránh rò rỉ tài nguyên và ảnh hưởng test khác.
	- Sau khi sửa, test pass và xác nhận được cả response cache-hit lẫn cờ cache_hit trong bảng solutions.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
	 - Với Chatbot trực tiếp, hệ thống chỉ sinh câu trả lời một lần, khó kiểm soát đường đi nội bộ.
	 - Với ReAct/pipeline agent, luồng có bước kiểm tra cache, chọn nhánh solve, tổng hợp kết quả và lưu vết nên minh bạch hơn, dễ debug hơn.

2. **Reliability**:
	 - Agent có thể tệ hơn Chatbot khi orchestration phức tạp nhưng thiếu guard (ví dụ dependency như DB/Redis chưa init đúng trong môi trường test hoặc runtime).
	 - Trong các case này, overhead điều phối làm tăng điểm lỗi vận hành dù chất lượng reasoning có thể tốt.

3. **Observation**:
	 - Observation từ môi trường (cache hit/miss, lỗi DB, trạng thái tool) ảnh hưởng trực tiếp bước kế tiếp của agent.
	 - Việc đưa observation vào log + test giúp khoanh vùng lỗi nhanh hơn nhiều so với chỉ nhìn output cuối.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
	- Tách write DB/cache sang background queue cho các tác vụ không bắt buộc đồng bộ với response.
	- Chuẩn bị adapter để chuyển từ SQLite sang PostgreSQL khi tải tăng.

- **Safety**:
	- Bổ sung policy kiểm soát kết quả trước khi cache (ví dụ confidence threshold động theo loại bài).
	- Thêm circuit breaker/fallback chiến lược khi Redis hoặc DB bất ổn.

- **Performance**:
	- Tối ưu cache key normalization và mở rộng semantic matching cho các biểu thức tương đương.
	- Bổ sung metrics dashboard cho cache hit rate, DB latency, và error rate theo endpoint.

---
