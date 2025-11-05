window.ORG_ADMIN_CONFIG = Object.assign(
    {
        gatewayBaseUrl: "http://localhost:8080",
        authLoginPath: "/auth/login/user",
        authMePath: "/auth/me",
        adminBasePath: "/admin",
        requestTimeoutMs: 15000,
    },
    window.ORG_ADMIN_CONFIG || {}
);
