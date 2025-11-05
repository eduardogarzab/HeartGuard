package com.heartguard.desktop.api;

/**
 * Excepción personalizada para errores de API
 */
public class ApiException extends Exception {
    private final int statusCode;
    private final String error;
    private final String responseBody;

    public ApiException(String message) {
        super(message);
        this.statusCode = 0;
        this.error = null;
        this.responseBody = null;
    }

    public ApiException(String message, int statusCode, String error, String responseBody) {
        super(message);
        this.statusCode = statusCode;
        this.error = error;
        this.responseBody = responseBody;
    }

    public ApiException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 0;
        this.error = null;
        this.responseBody = null;
    }

    public int getStatusCode() {
        return statusCode;
    }

    public String getError() {
        return error;
    }

    public String getResponseBody() {
        return responseBody;
    }

    @Override
    public String toString() {
        if (statusCode > 0) {
            return "ApiException{" +
                    "statusCode=" + statusCode +
                    ", error='" + error + '\'' +
                    ", message='" + getMessage() + '\'' +
                    '}';
        }
        return super.toString();
    }
}
