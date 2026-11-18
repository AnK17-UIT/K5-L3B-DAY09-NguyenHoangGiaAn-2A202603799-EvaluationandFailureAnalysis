# Trace case — C-002@11

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11` (item `E-002`), run ID `E-seeded_regression-20261118-4c6e` trong `src/reports/m1_seeded_regression.json` |
| Triệu chứng | Lab 8 `trial_pass` báo `status resolved != denied`. Ledger ghi 20.000đ với một khoản hoàn, nhãn là 0đ và không có khoản hoàn. Event 6 báo đã hoàn 20.000đ. |
| Bước sai đầu tiên | Event 3 `model_override` — `{"delay_days": 5}`. Ticket ghi 5 ngày, dữ liệu đơn từ DB ghi 2 ngày. |
| Vì sao là bước đầu tiên | Event 1 `handoff` chuyển claim cho investigator với phạm vi `owner_order`. Event 2 `investigator` đọc đúng đơn O-202 và lấy `delay_days = 2`. Dữ liệu mẫu cố tình đặt ticket C-002 ghi trễ 5 ngày và bản ghi đơn O-202 trong hệ thống ghi trễ 2 ngày để kiểm tra nguồn agent dùng khi tính hoàn tiền. Ở event 3, `seeded_regression` dùng 5 ngày từ ticket trên bản sao dữ liệu đơn trong bộ nhớ, dẫn đến quote 20.000đ tại event 4. Bản ghi SQLite vẫn giữ 2 ngày. |
| Failure mode | FM-03 (`ticket_trust`), xem [taxonomy](failure_taxonomy.md). |
| Đối chứng | `fixed C-002@11`, run ID `E-fixed-20261118-4c6e`. Sau cùng kết quả tra cứu, event 3 là `quote` với `amount_vnd = 0`, lý do `no_entitlement`. Ledger ghi 0đ, Lab 8 PASS. |
| Regression test | `test_ticket_delay_conflict_does_not_create_refund` đối chiếu số tiền ledger với nhãn. Hai tham số chạy cùng claim và seed. `fixed` phải pass, `seeded_regression` phải fail assertion và được đánh dấu strict xfail cho fixture cố ý lỗi. |
| Chưa chắc chắn | Trace ghi override dưới MockLLM. Ca này chưa bao phủ lỗi dùng dữ kiện sai mà không ghi event override, hoặc tần suất xuất hiện trên LLM thật. |

Chạy lại từ `src/`:

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q -o addopts= tests/test_lab9_trace_case.py
```

Các report M1 được sinh bởi `lab9.eval` từ eval set v1 (SHA `4c6e1e3ed1d4`) bằng spec tạm chỉ chứa các metric đã triển khai. Hai grader M3 chưa tham gia lần chạy này.
