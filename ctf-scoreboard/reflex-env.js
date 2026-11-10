const origin =
  typeof window !== "undefined"
    ? window.location.origin
    : "http://localhost:8080";
const wsOrigin = origin.replace(/^http/, "ws");
const env = {
  PING: origin + "/ping",
  EVENT: wsOrigin + "/_event",
  UPLOAD: origin + "/_upload",
  AUTH_CODESPACE: origin + "/auth-codespace",
  HEALTH: origin + "/_health",
  ALL_ROUTES: origin + "/_all_routes",
  TRANSPORT: "websocket",
  TEST_MODE: false,
};
export { env as t };
