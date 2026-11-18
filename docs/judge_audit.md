# Judge audit — M2

Calibration chạy offline trên hai CSV replay. Nhãn `FAIL` là lớp dương vì nhiệm vụ của judge là phát hiện lỗi. Kết quả dưới đây dùng nhãn trong CSV ở thời điểm chạy.

## Kết quả calibration

| Tiêu chí | n | TP | FP | FN | TN | κ | Precision | Recall | Quyết định |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `tone_ok` | 100 | 24 | 4 | 6 | 66 | 0,757 | 0,857 | 0,800 | PASS, có thể dùng cho tiêu chí giọng văn |
| `helpful` | 100 | 9 | 0 | 21 | 70 | 0,375 | 1,000 | 0,300 | FAIL, loại khỏi gate |

Ngưỡng đạt đồng thời là κ ≥ 0,6, precision ≥ 0,8 và recall ≥ 0,7. κ không xác định thì FAIL. Với `helpful`, cả 9 cảnh báo đều đúng theo nhãn CSV, nhưng judge bỏ sót 21 trong 30 ca lỗi. Một số ca lọt báo sai số tiền hoàn dù câu trả lời lịch sự.

| Tiêu chí | Tỷ lệ FAIL judge báo | Tỷ lệ FAIL hiệu chỉnh Rogan–Gladen |
|---|---:|---:|
| `tone_ok` | 28% | 30% |
| `helpful` | 9% | 30% |

Hiệu chỉnh Rogan–Gladen ước lượng tỷ lệ lỗi toàn tập từ sensitivity và specificity. Hai tỷ lệ hiệu chỉnh khớp tỷ lệ nhãn người trên chính tập dùng để ước lượng hai tham số. Gate cần phát hiện lỗi ở từng ca, nên `helpful` vẫn bị loại.

## Audit bất đồng

| Case | Judge | Nhãn người | Phán quyết sau rà soát | Sửa rubric hoặc nhãn |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Người đúng. “Anh check giúp em” và “nha” hơi quá trớn trong phản hồi hoàn tiền của LogiX. | Nêu chuẩn xưng hô CS và thêm ví dụ phân biệt thân thiện với quá trớn. |
| H-017 | PASS | FAIL | Người đúng theo bối cảnh khách lớn tuổi trong ghi chú. “Bạn ơi … rồi nha” chưa phù hợp. | Thêm ví dụ chọn cách xưng hô theo ngữ cảnh khách hàng. |
| H-029 | PASS | FAIL | Người đúng. “Không cần nhắn thêm” mang giọng ra lệnh dù mở đầu bằng “Dạ, vui lòng”. | Chấm toàn câu và thêm ví dụ về cách đề nghị khách chờ. |
| H-042 | FAIL | PASS | Người đúng. Câu trả lời ngắn nhưng lịch sự, nêu số tiền và thời gian dự kiến. | Chỉ yêu cầu lời xin lỗi khi ngữ cảnh cần. |
| H-051 | FAIL | PASS | Người đúng theo quy ước CS LogiX cho phép thuật ngữ “refund”. | Thêm ví dụ dùng thuật ngữ được chấp nhận trong câu tiếng Việt lịch sự. |
| H-081 | FAIL | PASS | Judge đúng theo ghi chú CSV, trong đó người gắn nhãn đã đọc nhầm ticket. CSV chỉ có reply và ghi chú nên cần ticket gốc để xác minh lại. | Gửi ca cho người gắn nhãn thứ hai cùng ticket gốc. Giữ kết quả calibration công khai theo nhãn hiện có. |
| HL-015 | PASS | FAIL | Người đúng theo ghi chú ledger. Reply báo 55.000đ, ledger ghi 40.000đ. | Chấm tính đúng đắn của số tiền bằng code đối chiếu ledger. |
| HL-016 | PASS | FAIL | Người đúng theo ghi chú ledger. Lời xin lỗi dài bao quanh thông báo 55.000đ, ledger ghi 35.000đ. | Thêm ví dụ reply lịch sự nhưng sai nội dung. Chấm lỗi tiền bằng code. |
| HL-047 | PASS | FAIL | Người đúng theo rubric CS. “Ok bạn” thiếu trang trọng và “xử lý rồi” bỏ qua kết quả cụ thể khách cần biết. | Yêu cầu câu trả lời nêu kết quả hoặc bước tiếp theo và cho ví dụ về cách xưng hô phù hợp. |

## Rubric đề xuất sau audit

Các quy tắc dưới đây là bản đề xuất rút ra từ các bất đồng. M2 đã chạy calibration trên verdict replay hiện có. Các quy tắc mới chưa được áp dụng vào prompt judge, CSV hoặc ngưỡng gate, nên số liệu phía trên vẫn là của lần replay ban đầu.

### Giọng văn — `tone_ok`

- **Xưng hô phù hợp với ngữ cảnh CS.** Mặc định dùng “anh/chị” và quyết định theo toàn câu. FAIL khi cách xưng hô quá suồng sã trong ngữ cảnh khiếu nại, như “Anh check giúp em … nha” (H-008) hoặc “bạn ơi … rồi nha” với khách lớn tuổi (H-017). Có thể PASS với “Dạ, anh/chị vui lòng kiểm tra giao dịch ạ.”
- **Chấm cả câu, kể cả mệnh đề cuối.** FAIL nếu phản hồi ra lệnh hoặc gạt yêu cầu của khách, như “không cần nhắn thêm” (H-029), dù mở đầu lịch sự. Có thể PASS với “Dạ, yêu cầu đang được xử lý. LogiX sẽ cập nhật khi có kết quả ạ.”
- **Chấp nhận câu ngắn và thuật ngữ được đội CS cho phép.** Xác nhận đã hoàn tiền có thể PASS khi câu lịch sự, rõ ràng và đủ thông tin, dù thiếu lời xin lỗi (H-042) hoặc dùng từ “refund” (H-051). Chỉ yêu cầu lời xin lỗi khi tình huống có bất tiện cần ghi nhận.

### Mức hữu ích — `helpful`

- **Ưu tiên kết quả hoặc bước tiếp theo cụ thể.** Nếu khách cần bổ sung thông tin, yêu cầu đúng dữ liệu còn thiếu, chẳng hạn mã đơn. Nếu yêu cầu đã được xử lý, nêu kết quả thay vì chỉ báo “xử lý rồi” (HL-047).
- **Đối chiếu tiền hoàn bằng code.** Một câu báo đã hoàn 55.000đ trong khi ledger ghi 40.000đ phải bị đánh lỗi số tiền (HL-015). Lời xin lỗi và độ dài câu không ảnh hưởng phép đối chiếu (HL-016). Khi thiếu ledger, đánh dấu chưa đủ bằng chứng để xác nhận số tiền. Giữ `helpful` ngoài gate ở M2, phần metric đối chiếu reply với ledger thuộc M3.

### Xử lý bất đồng do nhãn

Với H-081, ghi chú CSV cho biết người gắn nhãn đã đọc nhầm ticket. Cần lấy ticket gốc và nhờ người thứ hai chấm độc lập trước khi sửa nhãn. Giữ nhãn hiện tại cho lần đo M2. Để đánh giá các sửa đổi rubric, cần chạy judge với rubric mới trên tập held-out có nhãn người và tính lại ma trận nhầm lẫn, κ, precision và recall.

## Giới hạn

Các verdict được phát lại từ CSV công khai. Cần tập held-out có nhãn người mới và đủ ngữ cảnh gốc để kiểm tra judge sau khi sửa rubric. Các tiêu chí về tiền và phê duyệt dùng grader bằng code.

Chạy lại từ `src/`:

```bash
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 21
```

Lệnh thứ nhất trả exit 0. Lệnh thứ hai trả exit 1 vì không đạt ngưỡng calibration.
