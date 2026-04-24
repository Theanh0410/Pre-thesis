# Xử lý lỗi trong hệ thống nhà thông minh

Việc phân phối nhiệm vụ trong smart home không chỉ dừng lại ở việc gán nhiệm vụ – nó còn bao gồm khả năng **phản hồi khi có sự cố**.

## Ví dụ lỗi phổ biến:

- Thiết bị không phản hồi (mất kết nối)
- Hành động thất bại (không bật được đèn)
- Thiết bị bị lỗi phần cứng

## Chiến lược xử lý:

1. **Retry:** thử lại hành động sau vài giây
2. **Fallback:** gán nhiệm vụ đó cho thiết bị khác (nếu có)
3. **Notify:** gửi cảnh báo đến người dùng hoặc hệ thống trung tâm

Kết hợp hệ thống phân phối nhiệm vụ với **fail-safe logic** sẽ giúp đảm bảo độ tin cậy và tính bền vững trong vận hành.
