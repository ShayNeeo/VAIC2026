# Bản học liệu tiếng Việt: Applied AI, AI Agent, RAG và Production AI

Tài liệu này được viết lại từ các PDF bài giảng trong thư mục hiện tại, đồng thời bổ sung kiến thức nền từ các tài liệu bên ngoài. Mục tiêu là giúp bạn đọc và hiểu được các nội dung đang được trình bày trong slide, vì nhiều slide chỉ có dạng gợi ý, minh họa hoặc checklist ngắn.

Lưu ý về ký tự: bản này không sao chép trực tiếp phần chữ bị lỗi mã hóa từ PDF. Nội dung được diễn giải lại bằng tiếng Việt có dấu, dùng mã UTF-8.

## Cách dùng tài liệu này cho bài toán thực tế

Tài liệu này không chỉ dùng để xây RAG hoặc agent. Hãy xem nó như bộ kỹ thuật nền để AI không bị "lơ mơ" khi giải bài toán thực tế. Trước khi chọn giải pháp, cần phân tích:

- Bài toán thật là gì: người dùng nào, workflow hiện tại ra sao, kết quả mong muốn là gì.
- AI cần đóng vai trò gì: phân loại, trích xuất, tóm tắt, tìm kiếm, đề xuất, soạn nháp, ra quyết định hay thực thi hành động.
- Dữ liệu nào cần dùng: dữ liệu riêng hay công khai, tĩnh hay thay đổi, có phân quyền hay không.
- Kỹ thuật nào phù hợp: prompt/schema, RAG, tool calling, workflow, agent, fine-tuning, guardrails, eval, observability hoặc logic phần mềm thông thường.
- Output phải như thế nào: báo cáo, JSON, bảng, UI, file, hành động hay audit trail.
- Làm sao biết hệ thống đúng: test cases, golden set, metric, human review, logs/traces và feedback.

Nguyên tắc quan trọng: không mặc định dùng RAG hoặc agent. Chỉ dùng RAG khi cần tri thức riêng/cập nhật/có nguồn; chỉ dùng agent khi hệ thống cần tự chọn hành động hoặc tool theo ngữ cảnh. Nếu bài toán có thể giải bằng workflow, schema hoặc rule-based code thì ưu tiên cách đơn giản hơn.

## 1. Bức tranh tổng thể

Bộ PDF đang xoay quanh một chủ đề lớn: làm thế nào để xây dựng ứng dụng AI, RAG và agent có thể dùng trong thực tế, không chỉ chạy được trong demo.

Một hệ thống AI production thường gồm các lớp sau:

1. Prompt engineering: điều khiển hành vi của mô hình bằng chỉ dẫn rõ ràng.
2. Tool calling: cho mô hình gọi công cụ, API, cơ sở dữ liệu hoặc workflow bên ngoài.
3. Data foundation: chuẩn bị dữ liệu, embedding, vector store và metadata.
4. RAG pipeline: truy xuất ngữ cảnh liên quan rồi dùng mô hình sinh câu trả lời có căn cứ.
5. Multi-agent và orchestration: tổ chức nhiều agent hoặc nhiều bước xử lý khi bài toán phức tạp.
6. Guardrails và AI safety: kiểm soát đầu vào, đầu ra, quyền truy cập và hành động rủi ro.
7. Observability: log, trace, metric, dashboard, alert để biết agent đang hoạt động thế nào.
8. Evaluation: đo chất lượng bằng benchmark, golden dataset, RAGAS và LLM-as-judge.
9. Reliability: cache, fallback, circuit breaker, SLO để hệ thống chịu lỗi tốt hơn.
10. Fine-tuning và alignment: huấn luyện thêm khi prompt/RAG/tool chưa đủ.
11. Human-in-the-loop: thiết kế điểm xin phép con người khi agent không nên tự quyết.

Thông điệp chính: mô hình mạnh không tự tạo ra sản phẩm tốt. Sản phẩm AI tốt cần prompt rõ, dữ liệu đúng, retrieval tốt, kiểm soát an toàn, đánh giá liên tục và vận hành nghiêm túc.

## 2. Prompt Engineering và Tool Calling

Prompt là giao diện giữa ý định của con người và hành vi của mô hình. Prompt tốt không phải là prompt dài, mà là prompt khiến mô hình phản hồi ổn định, đúng nhiệm vụ và đúng định dạng.

Một prompt tốt thường có bốn thành phần:

- Vai trò: mô hình đóng vai gì, ví dụ chuyên gia hỗ trợ khách hàng, trợ lý pháp lý, kỹ sư dữ liệu.
- Nhiệm vụ: mô hình cần làm gì, ví dụ tóm tắt, phân loại, trích xuất, lập kế hoạch.
- Bối cảnh: thông tin liên quan, giới hạn, đối tượng người đọc, dữ liệu đầu vào.
- Định dạng: đầu ra cần là JSON, bảng, checklist, email, báo cáo ngắn hay câu trả lời tự nhiên.

Ví dụ prompt yếu:

```text
Viết email cho tôi.
```

Ví dụ prompt tốt hơn:

```text
Viết email xin lỗi khách hàng vì đơn hàng giao trễ 2 ngày.
Giọng văn lịch sự, dưới 120 từ, có lời cam kết xử lý và một lời kêu gọi hành động rõ ràng.
```

### Các kỹ thuật prompting thường gặp

- Zero-shot: không đưa ví dụ. Nên thử đầu tiên vì đơn giản và ít tốn token.
- One-shot: đưa một ví dụ mẫu để mô hình hiểu định dạng mong muốn.
- Few-shot: đưa vài ví dụ khi cần giữ phong cách, format hoặc tiêu chuẩn đánh giá ổn định.
- Decomposition: chia bài toán lớn thành các bước nhỏ.
- Structured output: yêu cầu mô hình trả về JSON, bảng hoặc schema cố định.
- Chain-of-thought/deep reasoning: hữu ích cho bài toán suy luận, nhưng khi đưa vào sản phẩm nên yêu cầu mô hình trình bày kết luận và căn cứ ngắn gọn, không nhất thiết phơi bày toàn bộ suy nghĩ nội bộ.

### System prompt production-grade

System prompt cho agent nên có:

- Phạm vi: agent được làm gì và không được làm gì.
- Quy tắc trả lời: ngắn gọn, có nguồn, không bịa, hỏi lại khi thiếu dữ liệu.
- Hợp đồng đầu ra: cấu trúc bắt buộc, trường dữ liệu, kiểu dữ liệu.
- Chính sách tool: khi nào gọi tool, khi nào trả lời trực tiếp.
- Chính sách lỗi: nếu tool lỗi, timeout hoặc dữ liệu thiếu thì xử lý thế nào.
- Chính sách an toàn: không lộ dữ liệu nhạy cảm, không thực hiện hành động rủi ro khi chưa được phép.

### Tool calling là gì?

Tool calling cho phép mô hình gọi chức năng bên ngoài, ví dụ:

- Tra cứu thời tiết.
- Truy vấn cơ sở dữ liệu.
- Tìm kiếm tài liệu.
- Tạo ticket.
- Gửi email nháp.
- Gọi API nội bộ.

Vòng lặp tool calling:

1. Người dùng đặt câu hỏi hoặc yêu cầu.
2. Mô hình quyết định có cần dùng tool không.
3. Nếu cần, mô hình tạo lời gọi tool với tham số theo schema.
4. Ứng dụng thật sự thực thi tool.
5. Kết quả tool được đưa lại cho mô hình.
6. Mô hình tổng hợp câu trả lời cuối.

Tool schema tốt cần có tên rõ, mô tả ngắn, tham số chặt chẽ, kiểu dữ liệu cụ thể và validation. Với hành động rủi ro như xóa dữ liệu, thanh toán, gửi email hoặc thay đổi cấu hình, cần có bước xin phép người dùng.

## 3. Thiết kế sản phẩm AI trong môi trường bất định

Sản phẩm AI khác phần mềm truyền thống vì đầu ra có tính xác suất. Một hàm phần mềm thường cho cùng kết quả với cùng đầu vào. Một mô hình ngôn ngữ có thể trả lời khác nhau tùy prompt, context, nhiệt độ sinh, dữ liệu truy xuất và phiên bản model.

Vì vậy, câu hỏi không chỉ là “agent có chạy không?”, mà là:

- Ai dùng agent này?
- Khi agent đúng, người dùng nhận được giá trị gì?
- Khi agent sai, hậu quả là gì?
- Bao nhiêu phần trăm đúng là đủ?
- Mỗi lần chạy tốn bao nhiêu chi phí, thời gian và rủi ro?

Một sản phẩm AI tốt thường không tự động hóa 100% ngay từ đầu. Nhiều trường hợp nên thiết kế theo kiểu copilot: AI đề xuất, con người kiểm tra và phê duyệt.

### AI Product Canvas

Khi thiết kế một sản phẩm AI, nên mô tả rõ:

- Người dùng mục tiêu.
- Vấn đề hiện tại.
- Quy trình trước và sau khi có AI.
- Dữ liệu đầu vào.
- Đầu ra mong muốn.
- Metric thành công.
- Các lỗi nguy hiểm.
- Khi nào AI được tự động làm.
- Khi nào AI phải hỏi lại hoặc xin phép.
- Cách thu thập phản hồi để cải tiến.

## 4. Data Foundations: Embedding, Vector Store và Metadata

Với AI agent, câu hỏi quan trọng không chỉ là “dùng model nào”, mà là “agent được phép biết gì, lấy dữ liệu từ đâu, dữ liệu đó có đúng và mới không”.

Ba loại dữ liệu thường gặp:

- Knowledge data: tài liệu, chính sách, FAQ, hướng dẫn, hợp đồng, manual.
- Operational data: ticket, đơn hàng, CRM, giao dịch, trạng thái hệ thống.
- Contextual data: thông tin phiên làm việc, quyền truy cập, lịch sử hội thoại, thông tin người dùng.

Embedding là cách biểu diễn văn bản, hình ảnh hoặc code thành vector số. Những nội dung gần nghĩa sẽ có vector gần nhau. Vector store là nơi lưu vector, text gốc, ID và metadata để tìm kiếm ngữ nghĩa.

Pipeline cơ bản:

```text
Document -> Parse -> Clean -> Chunk -> Embed -> Store -> Query -> Retrieve -> Inject context -> Generate
```

Metadata rất quan trọng. Mỗi chunk nên lưu:

- Nguồn tài liệu.
- Tiêu đề hoặc section.
- Ngày tạo/cập nhật.
- Phiên bản tài liệu.
- Chủ sở hữu.
- Quyền truy cập.
- Ngôn ngữ.
- Loại tài liệu.

Nếu thiếu metadata, hệ thống rất khó lọc theo quyền, khó debug, khó cập nhật và dễ trả lời bằng tài liệu cũ.

### Chunking

Chunk quá ngắn thì mất ngữ cảnh. Chunk quá dài thì retrieval kém chính xác và tốn token. Cách làm tốt:

- Cắt theo cấu trúc tài liệu: tiêu đề, mục, đoạn, bảng.
- Giữ một ít overlap nếu nội dung liên tục.
- Gắn tiêu đề vào chunk hoặc metadata.
- Với bảng, code, biểu mẫu, nên dùng parser phù hợp thay vì cắt chuỗi thô.

## 5. RAG: Retrieval-Augmented Generation

RAG là kỹ thuật kết hợp truy xuất thông tin và sinh câu trả lời. Thay vì để LLM trả lời hoàn toàn từ kiến thức có sẵn, hệ thống tìm các đoạn tài liệu liên quan rồi đưa vào prompt để model trả lời dựa trên ngữ cảnh đó.

RAG giúp:

- Dùng được dữ liệu riêng của tổ chức.
- Cập nhật kiến thức mà không cần huấn luyện lại model.
- Giảm hallucination.
- Trích dẫn nguồn.
- Kiểm soát quyền truy cập tốt hơn nếu metadata được thiết kế đúng.

Tuy nhiên, RAG không tự động đúng. Lỗi thường nằm ở hai phần:

- Offline pipeline: ingest sai, parse lỗi, chunk kém, embedding sai, dữ liệu cũ, metadata thiếu.
- Online pipeline: query rewrite kém, retrieve nhầm, không rerank, đưa quá nhiều context nhiễu, model tự suy diễn ngoài context.

### Pipeline RAG production

Một pipeline RAG tốt thường có:

1. Hiểu câu hỏi: xác định ý định, entity, thời gian, phạm vi.
2. Viết lại query nếu cần.
3. Hybrid search: kết hợp semantic search và keyword search.
4. Metadata filtering: lọc theo quyền, ngày, sản phẩm, phiên bản.
5. Reranking: sắp xếp lại kết quả để chọn context tốt nhất.
6. Context packing: chọn đoạn phù hợp, tránh đưa quá nhiều nhiễu.
7. Sinh câu trả lời dựa trên context.
8. Trích dẫn nguồn.
9. Từ chối hoặc hỏi lại nếu không đủ căn cứ.

### Các lỗi RAG phổ biến

- Tài liệu bị parse mất bảng hoặc mất tiêu đề.
- Chunk không có ngữ cảnh nên retrieval tìm đúng chữ nhưng sai nghĩa.
- Vector search trả về tài liệu gần nghĩa nhưng sai phiên bản.
- Không lọc theo quyền truy cập.
- Top-k quá cao khiến prompt bị nhiễu.
- Model không được yêu cầu nói “không đủ dữ liệu”.
- Không có evaluation nên không biết hệ thống đang sai ở đâu.

## 6. Data Pipeline và Data Observability

“Garbage in, garbage out” đặc biệt đúng với RAG. Nếu dữ liệu đầu vào sai, cũ, thiếu hoặc bị parse lỗi, model mạnh cũng sẽ trả lời kém.

Một data pipeline cho AI nên có:

- Ingestion: lấy dữ liệu từ PDF, HTML, database, API, CRM, helpdesk.
- Parsing: giữ cấu trúc heading, bảng, danh sách, code.
- Cleaning: xóa boilerplate, chuẩn hóa encoding, loại duplicate.
- Validation: kiểm tra schema, text rỗng, quyền truy cập, ngôn ngữ, ngày cập nhật.
- Versioning: biết chunk thuộc phiên bản tài liệu nào.
- Indexing: chunk, embed, lưu vào vector store.
- Monitoring: theo dõi freshness, error rate, volume, drift và retrieval quality.

Data observability cần theo dõi:

- Freshness: dữ liệu có mới không?
- Completeness: có thiếu tài liệu, thiếu trường, thiếu chunk không?
- Validity: dữ liệu có đúng schema không?
- Uniqueness: có duplicate không?
- Distribution drift: dữ liệu hoặc query có thay đổi bất thường không?
- Access control: có dữ liệu nhạy cảm bị index sai quyền không?

## 7. Multi-Agent, LangGraph, MCP và A2A

Không phải bài toán nào cũng cần multi-agent. Hãy bắt đầu từ workflow đơn giản: prompt, tool, RAG, structured output. Chỉ thêm nhiều agent khi có lý do rõ ràng:

- Một agent phải xử lý quá nhiều vai trò.
- Prompt quá dài vì chứa quá nhiều nhánh logic.
- Tool quá nhiều gây khó chọn.
- Cần chuyên gia hóa theo từng nhiệm vụ.
- Cần chạy song song.
- Cần critic/reviewer để giảm lỗi.

### Các pattern multi-agent

- Supervisor-worker: một agent điều phối, các agent khác làm việc chuyên môn.
- Router: phân loại yêu cầu rồi gửi đến agent phù hợp.
- Debate/critic: một agent tạo kết quả, agent khác phản biện.
- Parallel execution: nhiều agent xử lý song song rồi hợp nhất.
- Shared state: các agent cùng đọc/ghi vào một trạng thái chung có schema.

Rủi ro khi dùng multi-agent:

- Tăng chi phí.
- Tăng latency.
- Khó debug.
- Agent có thể trao đổi vòng vo.
- Lỗi từ agent này lan sang agent khác.
- Không rõ ai chịu trách nhiệm kết quả cuối.

### MCP là gì?

Model Context Protocol là một chuẩn mở để kết nối ứng dụng AI với hệ thống bên ngoài như file, database, search engine, API và workflow. MCP giúp giảm bài toán tích hợp N x M: thay vì mỗi model/provider phải tích hợp riêng với từng tool, tool có thể được expose qua MCP server và các AI client dùng theo cùng một chuẩn.

Các thành phần chính:

- MCP host/client: ứng dụng AI, IDE, chatbot.
- MCP server: nơi expose tool, resource hoặc prompt.
- Tools: hành động có input/output.
- Resources: dữ liệu hoặc tài liệu có thể đọc.
- Prompts: template hoặc workflow prompt dùng lại.

MCP hữu ích nhưng cần kiểm soát bảo mật: allowlist tool, quyền truy cập, audit log, validation, chống prompt injection và approval gate cho hành động nguy hiểm.

### A2A

A2A là giao tiếp giữa các agent. Điều quan trọng là message contract phải rõ:

- Input schema.
- Output schema.
- Trạng thái thành công/thất bại.
- Evidence hoặc citation.
- Retry policy.
- Agent nào chịu trách nhiệm quyết định cuối.

## 8. Reliability: Circuit Breaker, Cache và Fallback

Agent production phải chịu được lỗi thật: provider timeout, API lỗi, rate limit, tool treo, vector store chậm, output sai schema hoặc chi phí tăng bất thường.

Các nhóm lỗi thường gặp:

- Lỗi model/provider: timeout, 5xx, rate limit.
- Lỗi tool: API sai, database down, permission error.
- Lỗi retrieval: không tìm được context đúng.
- Lỗi output: JSON sai, format sai.
- Lỗi safety: prompt injection, PII leak, unsafe output.
- Lỗi cost/latency: gọi model quá nhiều, prompt quá dài.

### Circuit breaker

Circuit breaker ngăn hệ thống tiếp tục gọi một dependency đang lỗi.

- Closed: gọi bình thường.
- Open: dependency lỗi nhiều, tạm dừng gọi và trả fallback.
- Half-open: thử lại một số request để xem dependency đã hồi phục chưa.

### Cache

- Exact cache: cùng input thì trả kết quả cũ.
- Semantic cache: input gần nghĩa thì dùng kết quả cũ.
- Tool-result cache: cache kết quả API/tool theo TTL.
- Retrieval cache: cache top-k cho query phổ biến.

Cache giúp giảm latency và chi phí, nhưng phải có TTL, invalidation và versioning để tránh trả dữ liệu cũ.

### Fallback

Fallback nên được thiết kế trước:

- Dùng model khác.
- Trả lời bằng template khi LLM lỗi.
- Chỉ hiển thị tài liệu nguồn thay vì sinh câu trả lời.
- Yêu cầu người dùng thử lại.
- Chuyển sang human support.

## 9. Guardrails và AI Safety

Guardrails là các lớp kiểm soát đầu vào, quá trình và đầu ra để giảm rủi ro. Không nên chỉ dựa vào system prompt.

### Input guardrails

- Phát hiện và ẩn PII.
- Kiểm tra phạm vi chủ đề.
- Phát hiện jailbreak hoặc prompt injection.
- Kiểm tra quyền truy cập.
- Scan file hoặc nội dung độc hại.
- Rate limit và abuse detection.

### Output guardrails

- Safety classifier.
- Kiểm tra rò rỉ PII.
- Kiểm tra citation.
- Validate JSON/schema.
- Toxicity/policy check.
- Kiểm tra hallucination hoặc grounding.

### Defense in depth

Một hệ thống an toàn nên có nhiều lớp:

1. UX giới hạn hành động.
2. System prompt và tool policy.
3. Input filter.
4. Permission filter trước retrieval.
5. Tool permission và approval gate.
6. Output validation.
7. Logging, audit và alert.
8. Human review cho trường hợp rủi ro cao.

## 10. Monitoring, Logging và Observability

Observability giúp trả lời: agent đang làm gì, lỗi ở đâu, vì sao chậm, vì sao chi phí tăng, vì sao người dùng không hài lòng.

Ba trụ cột cơ bản:

- Metrics: số liệu tổng hợp như latency, error rate, cost, success rate.
- Logs: sự kiện chi tiết, input/output đã sanitize, lỗi, metadata.
- Traces: luồng end-to-end qua các bước model, retrieval, tool, rerank, guardrail.

AI-specific metrics nên có:

- TTFT: thời gian đến token đầu tiên.
- Latency P50/P95/P99.
- Token và cost per request.
- Retrieval hit rate.
- Tool call success rate.
- Faithfulness hoặc grounding score.
- Refusal rate.
- Human escalation rate.
- User feedback.
- Drift của query và answer.

Structured log nên có:

- correlation_id hoặc trace_id.
- user/session id đã ẩn danh.
- model name/version.
- prompt/template version.
- tool calls.
- retrieved document ids.
- latency/cost.
- safety flags.
- error code.

Không nên log dữ liệu nhạy cảm thô nếu không cần. Nên sanitize, mask hoặc hash.

## 11. Evaluation, Benchmarking, RAGAS và LLM-as-Judge

Evaluation là một phần của engineering, không phải cảm tính. Demo 5 câu hỏi đẹp không chứng minh hệ thống sẵn sàng production.

Cần có hai kiểu đánh giá:

- Offline eval: chạy trên golden dataset trước deploy, trong CI/CD hoặc khi đổi prompt/model/retrieval.
- Online eval: lấy mẫu conversation thật để chấm, theo dõi drift và lỗi production.

### Golden dataset

Dataset đánh giá nên có:

- Câu hỏi dễ, trung bình, khó.
- Câu hỏi multi-hop.
- Câu hỏi out-of-scope.
- Câu hỏi cần từ chối.
- Câu hỏi có nhiều phiên bản theo thời gian.
- Edge cases và adversarial cases.
- Ground truth answer và nguồn nếu có.

### RAGAS

RAGAS là framework đánh giá ứng dụng LLM/RAG. Các metric thường gặp:

- Faithfulness: câu trả lời có được hỗ trợ bởi context không.
- Answer relevancy: câu trả lời có đúng câu hỏi không.
- Context precision: context truy xuất có liên quan không.
- Context recall: context có bao phủ thông tin cần thiết không.

### LLM-as-Judge

LLM-as-judge dùng một mô hình để chấm đầu ra theo rubric. Cần:

- Rubric rõ ràng.
- Thang điểm cố định.
- Ví dụ điểm tốt/xấu.
- Pairwise comparison khi so sánh hai phiên bản.
- Kiểm tra bias như position bias, verbosity bias, style bias.
- Hiệu chuẩn bằng một tập human labels.

Không nên chỉ dùng một metric. Nên kết hợp automated metric, human review, production feedback và regression test.

## 12. Advanced Agent Architectures

ReAct kết hợp reasoning và acting: agent suy luận, gọi tool, nhận observation, rồi lặp lại cho đến khi có câu trả lời. ReAct hữu ích nhưng có giới hạn:

- Lỗi ở bước đầu có thể lan ra toàn bộ chuỗi.
- Agent có thể lặp vô hạn khi tool trả noise.
- Agent không tự biết quay lại hướng khác.
- Agent có thể tự tin dù evidence yếu.

### Reflexion

Reflexion thêm vòng tự đánh giá:

1. Actor tạo câu trả lời hoặc hành động.
2. Evaluator chấm kết quả.
3. Reflector rút bài học nếu sai.
4. Actor thử lại với reflection memory.

Reflexion hữu ích khi bài toán có tiêu chí đánh giá rõ và có thể thử lại. Tuy nhiên, nó tốn thêm chi phí và latency.

### Planning và search

Các pattern như planner-executor, tree search hoặc LATS giúp agent khám phá nhiều hướng giải. Chỉ nên dùng khi:

- Bài toán nhiều bước.
- Sai một bước gây hỏng cả chuỗi.
- Có evaluator đủ đáng tin.
- Chất lượng quan trọng hơn latency.

Nguyên tắc: dùng kiến trúc đơn giản nhất đáp ứng được yêu cầu.

## 13. Memory Systems cho Agent

Agent mặc định là stateless: mỗi API call không tự nhớ phiên trước nếu ứng dụng không đưa thông tin đó vào context.

Các loại memory:

- Working memory: thông tin trong phiên hiện tại.
- Episodic memory: các sự kiện hoặc tương tác đã xảy ra.
- Semantic memory: tri thức ổn định về user hoặc domain.
- Procedural memory: quy trình, thói quen, preference.

Memory tốt phải có chọn lọc. Không phải mọi thứ người dùng nói đều nên được lưu. Cần có:

- Consent: người dùng có đồng ý lưu không.
- Privacy: dữ liệu nhạy cảm được bảo vệ thế nào.
- Expiration: khi nào memory hết hạn.
- Update: khi thông tin cũ bị thay thế.
- Delete: người dùng có thể xóa memory không.

## 14. GraphRAG và Knowledge Graph

Vector RAG tốt cho tìm kiếm ngữ nghĩa, nhưng yếu khi câu hỏi cần quan hệ giữa nhiều thực thể. Ví dụ: “Những công ty AI nào được đồng sáng lập bởi cựu nhân viên Google?” Thông tin có thể nằm rải rác ở nhiều đoạn, và vector search phẳng không biểu diễn rõ quan hệ.

Knowledge Graph gồm:

- Node: thực thể như người, công ty, sản phẩm, chính sách.
- Edge: quan hệ như sáng lập, làm việc tại, sở hữu, phụ thuộc.
- Property: ngày, vai trò, nguồn, confidence.

GraphRAG kết hợp graph và text:

1. Trích xuất entity và relation từ tài liệu.
2. Xây graph có nguồn và confidence.
3. Khi có query, nhận diện entity và relation cần hỏi.
4. Traverse graph để lấy quan hệ.
5. Lấy text evidence từ node/edge liên quan.
6. Sinh câu trả lời có căn cứ.

Dùng GraphRAG khi domain có nhiều quan hệ: pháp lý, tài chính, y tế, doanh nghiệp, tri thức nội bộ. Không nên dùng nếu bài toán chỉ là FAQ đơn giản.

## 15. Fine-tuning: Full Fine-tune, LoRA và QLoRA

Thứ tự ưu tiên khi model chưa tốt:

1. Sửa prompt.
2. Thêm ví dụ hoặc structured output.
3. Thêm RAG nếu thiếu knowledge.
4. Thêm tool nếu cần dữ liệu realtime hoặc hành động.
5. Fine-tune nếu cần hành vi, style, format ổn định ở quy mô lớn.

Fine-tuning không phải cách tốt để nạp kiến thức thay đổi liên tục. Nếu tri thức cập nhật hằng ngày, RAG phù hợp hơn.

Nên fine-tune khi:

- Cần format đặc thù lặp lại nhiều.
- Cần style/tone riêng.
- Cần giảm prompt dài.
- Cần model nhỏ làm tốt một task hẹp.
- Có dataset chất lượng cao.

LoRA huấn luyện các adapter nhỏ thay vì cập nhật toàn bộ trọng số model. QLoRA kết hợp quantization để fine-tune trên GPU nhỏ hơn.

Dataset quyết định chất lượng fine-tune. Dữ liệu kém sẽ khiến model học lỗi. Cần tách train/validation/test và đánh giá trước/sau fine-tune.

## 16. Alignment: RLHF, DPO và ORPO

SFT dạy model bắt chước câu trả lời mẫu, nhưng chưa chắc model biết câu trả lời nào tốt hơn khi có nhiều lựa chọn.

Alignment dùng preference learning để dạy model ưu tiên câu trả lời:

- Hữu ích.
- An toàn.
- Trung thực.
- Đúng phong cách.
- Phù hợp tiêu chuẩn của domain.

RLHF truyền thống gồm:

1. Supervised fine-tuning.
2. Thu thập preference pairs.
3. Huấn luyện reward model.
4. Tối ưu model bằng reinforcement learning.

DPO tối ưu trực tiếp trên preference pairs mà không cần reward model riêng. ORPO và các biến thể khác cố gắng đơn giản hóa quá trình alignment.

Preference data nên có chosen answer, rejected answer và lý do vì sao chosen tốt hơn.

## 17. Human-in-the-Loop UX

Full autonomy nguy hiểm khi agent có thể gây hậu quả thật: xóa dữ liệu, gửi email, hoàn tiền, thanh toán, thay đổi cấu hình hoặc tiết lộ thông tin.

Không phải lúc nào cũng hỏi người dùng. Cần routing theo rủi ro và độ chắc chắn:

- Rủi ro thấp, confidence cao: có thể tự động.
- Rủi ro thấp, confidence thấp: hỏi làm rõ.
- Rủi ro cao, confidence cao: xin phê duyệt.
- Rủi ro cao, confidence thấp: không thực hiện, chuyển người xử lý.

Các pattern HITL:

- Confirm: agent nói việc sắp làm và hỏi xác nhận.
- Edit-before-send: AI soạn nháp, người dùng sửa và gửi.
- Approve batch: AI đề xuất nhiều hành động, người dùng chọn.
- Escalate: chuyển sang người thật.
- Audit/review: cho phép tự động trong giới hạn, nhưng ghi log để review sau.

UX tốt cần nói rõ agent sắp làm gì, dùng dữ liệu nào, hậu quả là gì và có thể undo/rollback không.

## 18. Hackathon, SPEC và Prototype

Prototype tốt nên tập trung vào một core flow, không cố làm quá nhiều.

SPEC nên có:

- Problem statement.
- Target user.
- Current workflow.
- AI workflow mới.
- Input/output.
- Demo scenario.
- Data source.
- Tools/API.
- Success metric.
- Failure cases.
- Guardrails.
- Scope trong/ngoài.
- Kế hoạch demo.

Demo tốt cần cho thấy:

- Trước khi có AI, người dùng đau ở đâu.
- AI giúp gì.
- Khi AI sai hoặc không chắc, hệ thống xử lý thế nào.
- Có log, eval hoặc feedback loop nào để cải tiến.

## 19. Ghi chú riêng về file tiểu luận nghiên cứu khoa học

File `Tieu_luan_NCKH_dong_luc_HVCH.pdf` không cùng mạch với các bài AI agent/RAG. Đây là tài liệu về phương pháp nghiên cứu khoa học và động lực nghiên cứu của học viên cao học.

Để hiểu file này, cần nắm:

- Lý do chọn đề tài.
- Tổng quan nghiên cứu.
- Câu hỏi hoặc giả thuyết nghiên cứu.
- Mô hình nghiên cứu.
- Biến độc lập, biến phụ thuộc, biến kiểm soát.
- Phương pháp khảo sát hoặc phỏng vấn.
- Thang đo.
- Kết quả kỳ vọng.
- Hàm ý quản trị hoặc giải pháp.

Nếu cần, nên viết riêng một bản tóm tắt cho file này, vì nó không thuộc chuỗi kỹ thuật AI production.

## 20. Lộ trình học đề xuất

Nên học theo thứ tự:

1. Prompt Engineering và Tool Calling.
2. Thiết kế sản phẩm AI.
3. Data Foundations, Embedding và Vector Store.
4. RAG Pipeline.
5. Production RAG.
6. Data Pipeline và Data Observability.
7. Multi-Agent, MCP và A2A.
8. Guardrails và AI Safety.
9. Monitoring, Logging và Observability.
10. Evaluation, Benchmarking, RAGAS.
11. Reliability Engineering.
12. Memory Systems.
13. Advanced Agent Architectures.
14. GraphRAG và Knowledge Graph.
15. Fine-tuning.
16. DPO, ORPO và Alignment.
17. Human-in-the-loop UX.

## 21. Checklist xây một agent production-ready

- Prompt có vai trò, nhiệm vụ, bối cảnh và định dạng rõ.
- Output có schema nếu cần parse.
- Tool schema có validation.
- Có chính sách lỗi khi tool timeout hoặc trả lỗi.
- Retrieval có chunking, metadata, filtering và reranking.
- Dữ liệu có versioning và quan sát chất lượng.
- Có guardrails đầu vào và đầu ra.
- Có permission check trước retrieval và tool.
- Có HITL cho hành động rủi ro.
- Có log, trace, metric và dashboard.
- Có SLO và alert.
- Có offline eval với golden dataset.
- Có online sampling và feedback.
- Có cache, fallback và circuit breaker.
- Có cost budget.
- Có audit trail cho hành động quan trọng.

## 22. Nguồn ngoài nên đọc thêm

- OpenAI Function Calling: https://developers.openai.com/api/docs/guides/function-calling
- OpenAI Retrieval và Vector Stores: https://developers.openai.com/api/docs/guides/retrieval
- OpenAI Model Optimization/Fine-tuning: https://developers.openai.com/api/docs/guides/model-optimization
- OpenAI Agents SDK: https://developers.openai.com/api/docs/guides/agents
- Model Context Protocol: https://modelcontextprotocol.io/docs/getting-started/intro
- RAGAS: https://docs.ragas.io/en/stable/
- Prompt Engineering Guide: https://www.promptingguide.ai/

## 23. Tóm tắt nhanh theo cụm bài

- Prompt và tool calling: dùng prompt để điều khiển model, dùng tool để nối model với hệ thống thật.
- Thiết kế sản phẩm AI: sản phẩm AI phải xử lý bất định, lỗi và phản hồi người dùng.
- Data foundation: chất lượng câu trả lời bị giới hạn bởi dữ liệu và retrieval.
- RAG: lấy đúng context quan trọng hơn nhồi nhiều context.
- Data pipeline: ingest sai thì RAG sai có hệ thống.
- Multi-agent: chỉ dùng khi bài toán thật sự cần chia vai.
- MCP/A2A: chuẩn hóa kết nối tool và giao tiếp giữa agent.
- Guardrails: an toàn cần nhiều lớp, không chỉ system prompt.
- Observability: không log/trace/metric thì không vận hành được AI production.
- Evaluation: không có benchmark thì không biết hệ thống tốt hay tệ.
- Reliability: provider và tool sẽ lỗi, nên cần fallback, cache và circuit breaker.
- Memory: agent chỉ nhớ khi ta thiết kế bộ nhớ có chọn lọc.
- GraphRAG: phù hợp khi câu hỏi cần quan hệ giữa nhiều thực thể.
- Fine-tuning: dùng để học hành vi/format/style, không thay thế RAG cho kiến thức thay đổi liên tục.
- Alignment: preference learning giúp model chọn câu trả lời tốt và an toàn hơn.
- HITL: agent nên xin phép khi rủi ro cao hoặc độ chắc chắn thấp.
