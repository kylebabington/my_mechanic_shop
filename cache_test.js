import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    stages: [
        { duration: "10s", target: 10 },
        { duration: "20s", target: 50 },
        { duration: "10s", target: 0 },
    ],
};

export default function () {
    const url = "http://127.0.0.1:5000/service-tickets/"; // cached GET endpoint

    const res = http.get(url);

    check(res, {
        "status is 200": (r) => r.status === 200,
        "response not empty": (r) => r.body && r.body.length > 2,
    });

    sleep(0.05);
}
