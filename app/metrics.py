from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_requests_total", "HTTP requests", ["path", "code"]
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
tokens_processed_total = Counter("tokens_processed_total", "Tokens processed")
pii_detected_total = Counter("pii_detected_total", "PII detected", ["type"])
store_errors_total = Counter("store_errors_total", "Store errors")