# Eval card — LogiX-VN refund agent

- **Eval set** — v1, SHA `4c6e1e3ed1d4`, 14 item × 5 seed (11, 22, 33, 44, 55),
  nguồn `lab8_public`. Nhãn lưu riêng trong [labels_v1.json](../src/data/eval/labels_v1.json).
- **Môi trường** — MockLLM, Python 3.12.3, metric spec `1.0`.
  Source Day 8 từ clone tại `034c6c4`. Code và grader Day 9 là bản local M4 trên `starter/d09`, dựa trên HEAD `9e1549a`.
  Các thay đổi dùng cho lượt chạy đang chờ commit nên chưa có commit SHA riêng.
- **Gate owner đề xuất** — người duy trì bộ eval kiểm tra metric và trial fail khi gate exit 1. Người phụ trách sản phẩm xác nhận phạm vi ticket pilot.
- **Phạm vi pilot** — ticket CS tiếng Việt cho một đơn LogiX-VN, xử lý phí giao trễ hoặc bồi thường hàng hỏng đã xác minh. Xem [phạm vi và điều kiện release](PRD_v1.1.md).

## Report và kết quả

| Lượt chạy | Run ID | Gate |
|---|---|---|
| [Baseline swarm](../src/reports/baseline_v1.json) | `E-swarm-20261118-4c6e` | Đối chứng |
| [Swarm chạy lại](../src/reports/eval_pr.json) | `E-swarm-20261118-4c6e` | Exit 0 |
| [Fixed](../src/reports/eval_fixed.json) | `E-fixed-20261118-4c6e` | Exit 0 |
| [Seeded regression](../src/reports/eval_seeded_regression.json) | `E-seeded_regression-20261118-4c6e` | Exit 1 |

| Metric | Baseline swarm | Fixed | Seeded regression |
|---|---:|---:|---:|
| `approval_bypass` | 0 | 0 | 0 |
| `secret_leak` | 0 | 0 | 0 |
| `db_fact_kept` | 0.9857 | 1 | 0.9286 |
| `refund_amount_correct` | 0.9857 | 1 | 0.8571 |
| `pass_rate` | 0.9857 | 1 | 0.7143 |
| `pass_5` | 0.9286 | 1 | 0.7143 |
| `cost_per_success` | 49.567 | 48.7157 | 81.202 |
| `proposal_amount_correct` | 0.9857 | 1 | 0.7857 |
| `reply_amount_correct` | 1 | 1 | 0.785714 |

Ngưỡng lấy từ [metric spec v1](../src/config/metric_spec.yaml) và được liệt kê trong [PRD v1.1](PRD_v1.1.md#3-định-nghĩa-chạy-đúng). `approval_bypass` và `secret_leak` là số trial bị đánh dấu. `reply_amount_correct` là tỷ lệ trial vượt qua kiểm tra số tiền trong reply so với ledger.

`proposal_amount_correct` đối chiếu số tiền agent đề xuất với nhãn. Metric này dùng để chẩn đoán, với quyết định gate giữ theo các metric blocking hiện có. Trên v1, `lab9.mutation --detect` phát hiện 20/20 trial mà `seeded_regression` fail và báo nhầm 0/70 trial trên `fixed`. Trong 5 ca được bổ sung phát hiện, proposal sai nhưng ledger vẫn ghi đúng 0đ.

## So sánh ghép cặp

Paired bootstrap percentile 95% trên 14 cặp item, mỗi item lấy trung bình qua 5 seed. Δ = kết quả variant − baseline. Lượt `swarm` chạy lại có Δ = 0 và CI [0, 0] cho hai metric dưới đây.

| Variant | Metric | Δ | CI 95% |
|---|---|---:|---|
| `fixed` | `pass_rate` | +0.014 | [+0.000, +0.043] |
| `fixed` | `refund_amount_correct` | +0.014 | [+0.000, +0.043] |
| `seeded_regression` | `pass_rate` | -0.271 | [-0.500, -0.057] |
| `seeded_regression` | `refund_amount_correct` | -0.129 | [-0.315, +0.000] |

Gate chặn `seeded_regression` ở `pass_rate` vì tụt dưới sàn và toàn bộ CI nằm dưới 0. `refund_amount_correct` tụt dưới sàn. `reply_amount_correct` tụt dưới sàn 1,00. Kết quả gate và các bước kiểm tra Core đã xác minh local. GitHub Actions chờ chạy trên PR.

## Judge và trace

- `tone_ok` đạt ngưỡng trên CSV replay với κ = 0,757, precision = 0,857, recall = 0,800.
- `helpful` bị loại khỏi gate vì κ = 0,375 và recall = 0,300, bỏ sót 21/30 lỗi theo nhãn người. Xem [judge audit và rubric đề xuất](judge_audit.md).
- [Trace C-002@11](trace_case.md) ghi event 3 `model_override` là bước sai đầu tiên. [Regression test](../src/tests/test_lab9_trace_case.py) kiểm tra ledger 0đ, pass trên `fixed` và bắt lỗi 20.000đ trên `seeded_regression`.

## Giới hạn và quản lý phiên bản

MockLLM và các ticket mẫu chưa đo được hành vi trên người dùng thật. 14 item cho khoảng tin cậy rộng và khả năng phát hiện lỗi hiếm còn hạn chế. Judge replay dùng verdict công khai. Cần tập held-out có nhãn người để kiểm tra rubric sửa đổi. Eval card mô tả kết quả trong phạm vi v1.

Tăng `eval_set_version` khi thay đổi tập item hoặc nhãn, ví dụ bổ sung ca từ trace mới. Sinh lại baseline bằng cùng tập và seed dùng cho PR. Khi đổi metric hoặc ngưỡng, tăng `metric_spec_version` và ghi lý do.

## Eval set v2 — M5

[Baseline v2](../src/reports/baseline_v2.json) có run ID `E-swarm-20261118-5e53`, SHA `5e536f408dd2` và 28 item × 5 seed. Tập gồm 14 claim v1 và 14 claim từ adversarial pack. [Metric spec v2](../src/config/metric_spec_v2.yaml) giữ FM-08 làm metric blocking và đánh giá riêng từng slice.

| Phạm vi `pass_rate` | Baseline | Slice regression | Sàn | Paired CI 95% | Gate |
|---|---:|---:|---:|---|---|
| Toàn bộ | 0,9786 | 0,9357 | 0,85 | [−0,121, +0,029] | Qua |
| `money_movement` | 1,0000 | 0,8500 | 0,95 | [−0,300, 0,000] | Chặn |
| `adversarial` | 0,9714 | 0,9143 | 0,85 | [−0,186, +0,057] | Qua |
| `denial` | 0,9455 | 1,0000 | 0,90 | [+0,018, +0,109] | Qua |

[Slice regression](../src/reports/eval_slice_regression.json) có run ID `E-slice_regression-20261118-5e53`. Lỗi cộng điều khoản làm suy giảm tỷ lệ pass của các claim có giao dịch hoàn. Sàn `money_movement` đặt cao hơn sàn chung để bảo vệ nhóm có tiền thực ghi vào ledger. Hai biến thể `fixed` và `honest_refactor` đều qua gate v2 tại M5.


### Độ ổn định qua nhiều lần chạy — M6

`pass@k` ước lượng xác suất có ít nhất một lần pass trong k lần lấy mẫu. `pass^k` ước lượng xác suất cả k lần đều pass. Ví dụ một item pass 4/5 lần có `pass@5 = 1` và `pass^5 = 0`. Report lưu hai dạng lần lượt theo tên `pass_at_k` và `pass_hat_k` với k cụ thể.

A/A chạy cùng shape `swarm` và cùng eval set v2 trên hai nhóm seed. Kết quả lấy từ `lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110`.

| Metric | Seed 11/22/33/44/55 | Seed 66/77/88/99/110 | Δ |
|---|---:|---:|---:|
| `pass_rate` | 0,9786 | 0,9786 | 0 |
| `pass_at_5` | 1,0000 | 1,0000 | 0 |
| `pass_hat_5` | 0,8929 | 0,8929 | 0 |

Hai bộ seed có cùng số seed chia hết cho 5, nên điểm yếu đã biết của swarm xuất hiện cùng tần suất. Tất cả metric trong lần chạy A/A này có Δ = 0. Chọn sàn blocking `pass_hat_5 ≥ 0,80`, thấp hơn mức quan sát A/A 0,8929 khoảng 9,29 điểm phần trăm và đạt sàn tối thiểu của đề. Baseline so với chính nó vẫn qua gate. Với LLM thật, sampling và biến động backend có thể làm kết quả khác nhau giữa các lần chạy. Cần lặp A/A để ước lượng dải dao động trước khi đặt ngưỡng vận hành.

[Flaky regression](../src/reports/eval_flaky_regression.json), run ID `E-flaky_regression-20261118-5e53`, có `pass_hat_5 = 0,5714` và `pass_rate = 0,9143`. Tỷ lệ pass tổng vẫn trên sàn 0,85. Trong lượt này, CI của `pass_rate` cũng nằm dưới 0 và slice `money_movement` dưới sàn, nên gate ghi cả hai lý do cùng với `pass_hat_5`. Sàn `pass_hat_5` tự nó đủ để chặn biến thể này.

Năm seed chỉ cho một mẫu nhỏ. Một lỗi phụ thuộc vào khoảng 1/3 seed có thể không xuất hiện ổn định giữa các nhóm 5 seed, đặc biệt khi chỉ ảnh hưởng ít item. Cần thêm lần chạy hoặc ca nhắm vào điều kiện kích hoạt để đánh giá khả năng phát hiện.

### Kiểm tra tính toàn vẹn — M7

Gate đối chiếu lưới item × seed và slice tags với baseline, kiểm tra evaluator failures cùng điểm thiếu hoặc không hữu hạn. Trên PR, workflow lấy metric spec từ commit đích và truyền qua `--base-spec` để kiểm tra ratchet. Với cùng eval-set version, gate từ chối xóa metric hoặc slice, nới ngưỡng hay bỏ đánh dấu blocking hoặc kiểm định suy giảm đã có.

| Trap công khai | Kết quả gate | Bằng chứng bị phát hiện |
|---|---|---|
| `evaluator_errors_as_nan` | Exit 1 | Điểm từng trial bị thiếu |
| `dropped_failing_rows` | Exit 1 | Thiếu dòng và thiếu cặp item/seed |
| `cherry_picked_seeds` | Exit 1 | Tập cặp item/seed khác baseline |
| `loosened_spec` | Exit 1 | Nới ngưỡng và bỏ slice trên cùng eval-set version |

Các trap được sinh từ run `E-slice_regression-20261118-5e53` bằng `lab9.traps`. Runner trả exit 0 vì cả bốn trap đều bị chặn. Kiểm tra local bổ sung xác nhận gate chặn dòng trùng, evaluator failure trên report vốn qua gate và sửa slice tags. Bộ chấm ẩn và GitHub Actions chờ xác minh.

Mutation scorecard v2 đạt **3/3 regression bị chặn, 0 báo nhầm**. Gate chặn `seeded_regression`, `slice_regression` và `flaky_regression`, đồng thời cho qua `fixed` và `honest_refactor`.
