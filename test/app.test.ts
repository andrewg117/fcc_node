import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import app from "../api/server/app.ts";

let baseUrl: string;
const server = app.listen(0);

before(() => {
    const { port } = server.address() as AddressInfo;
    baseUrl = `http://localhost:${port}`;
});

after(() => {
    server.close();
});

test("GET /server returns the home message", async () => {
    const res = await fetch(`${baseUrl}/server`);
    assert.equal(res.status, 200);
    assert.equal(await res.text(), "Server home\n");
});

test("GET /server/user/:id returns the user for a numeric id", async () => {
    const res = await fetch(`${baseUrl}/server/user/42`);
    assert.equal(res.status, 200);
    assert.equal(await res.text(), "User ID: 42");
});

test("GET /server/user/:id 404s for a non-numeric id", async () => {
    const res = await fetch(`${baseUrl}/server/user/abc`);
    assert.equal(res.status, 404);
    const body = await res.json();
    assert.equal(body.message, "Id given is not a number");
});

test("unknown routes fall through to the 404 page", async () => {
    const res = await fetch(`${baseUrl}/does-not-exist`);
    assert.equal(res.status, 404);
    assert.match(await res.text(), /Route does not exist/);
});
