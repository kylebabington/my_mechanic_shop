import http from "k6/http";
import { check, sleep } from "k6";

export const options = { vus: 1, iterations: 10 };

export default function () {
    const listUrl = "http://127.0.0.1:5000/customers/"; // cached list endpoint
    const createUrl = "http://127.0.0.1:5000/customers/"; // POST endpoint that clears cache

    // 1) GET list (may be cached)
    const before = http.get(listUrl);

    // 2) POST new customer (should clear cache)
    const payload = JSON.stringify({
        name: `LoadTest_${__ITER}`,
        email: `loadtest_${__ITER}@example.com`,
        phone: "317-555-0000",
    });

    const postRes = http.post(createUrl, payload, {
        headers: { "Content-Type": "application/json" },
    });

    check(postRes, {
        "post is 201/200": (r) => [200, 201].includes(r.status),
    });

    // 3) GET list again — should reflect the new customer if cache was cleared
    const after = http.get(listUrl);
    check(after, {
        "list is 200": (r) => r.status === 200,
    });

    sleep(0.2);
}
