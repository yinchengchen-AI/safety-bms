// 运行时环境变量（由 nginx entrypoint 在生产环境替换）
window.__ENV__ = {
  API_BASE_URL: "/api/v1",
};
