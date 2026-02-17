import http from "k6/http";
import { check, sleep } from "k6";
import { Counter } from "k6/metrics";

// Custom metrics: see exactly how many 201 vs 429 you got (limiter working = many 429s)
const count201 = new Counter("responses_201_created");
const count429 = new Counter("responses_429_rate_limited");

export const options = {
    vus: 25,              // virtual users hitting your API at once
    duration: "30s",      // run for 30 seconds
    thresholds: {
        "http_req_failed": ["rate<=1"],
        "checks": ["rate>=0.99"],
        // Limiter is working if we get a lot of 429s (only 5/min per IP allowed)
        "responses_429_rate_limited": ["count>50"],
    },
};

export default function () {
    const url = "http://127.0.0.1:5000/service-tickets/"; // adjust if your route differs

    // Use a route you rate-limited (POST usually)
    const payload = JSON.stringify({
        // ⚠️ Put real fields your POST expects (example placeholders)
        description: "Stress test ticket",
        customer_id: 1,
    });

    const params = {
        headers: { "Content-Type": "application/json" },
    };

    const res = http.post(url, payload, params);

    if (res.status === 201) count201.add(1);
    if (res.status === 429) count429.add(1);

    check(res, {
        "status is 201/200/429": (r) => [200, 201, 429].includes(r.status),
    });

    sleep(0.1);
}
