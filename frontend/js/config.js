// Configuración centralizada del frontend
export const API_CONFIG = {
  // URL base del API Gateway
  BASE_URL: "http://136.115.53.140:5000",
  
  // Endpoints específicos
  ENDPOINTS: {
    AUTH: {
      LOGIN: "/auth/login",
      REGISTER: "/auth/register",
      REFRESH: "/auth/refresh",
      LOGOUT: "/auth/logout"
    },
    USERS: {
      COUNT: "/users/count",
      LIST: "/users",
      ME: "/users/me"
    },
    PATIENTS: {
      COUNT: "/patients/count",
      LIST: "/patients"
    },
    DEVICES: {
      COUNT: "/devices/count",
      LIST: "/devices"
    },
    INFERENCES: {
      COUNT: "/inference/inferences/count",
      LIST: "/inference/inferences"
    },
    ORGANIZATIONS: {
      LIST: "/organizations",
      DETAIL: "/organizations"
    }
  }
};

// Helper para construir URLs completas
export function buildUrl(endpoint) {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}
