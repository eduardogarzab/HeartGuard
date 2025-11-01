package com.heartguard.portal.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.ClientHttpRequestExecution;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

@Configuration
@EnableConfigurationProperties(GatewayProperties.class)
public class AppConfig {

    @Bean
    public RestTemplate restTemplate() {
        RestTemplate restTemplate = new RestTemplate();
        
        // Agregar interceptor de logging
        List<ClientHttpRequestInterceptor> interceptors = new ArrayList<>(restTemplate.getInterceptors());
        interceptors.add(new LoggingInterceptor());
        restTemplate.setInterceptors(interceptors);
        
        // Agregar error handler personalizado
        restTemplate.setErrorHandler(new DetailedErrorHandler());
        
        restTemplate.getMessageConverters().add(new MappingJackson2HttpMessageConverter());
        return restTemplate;
    }
    
    private static class LoggingInterceptor implements ClientHttpRequestInterceptor {
        @Override
        public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
            System.out.println("\n>>> REQUEST TO GATEWAY <<<");
            System.out.println("URI: " + request.getURI());
            System.out.println("Method: " + request.getMethod());
            System.out.println("Headers: " + request.getHeaders());
            if (body.length > 0) {
                System.out.println("Body: " + new String(body, StandardCharsets.UTF_8));
            }
            
            ClientHttpResponse response = execution.execute(request, body);
            
            System.out.println("\n<<< RESPONSE FROM GATEWAY <<<");
            System.out.println("Status: " + response.getStatusCode());
            System.out.println("Headers: " + response.getHeaders());
            
            return response;
        }
    }
    
    private static class DetailedErrorHandler extends DefaultResponseErrorHandler {
        @Override
        public void handleError(ClientHttpResponse response) throws IOException {
            System.out.println("\n!!! ERROR RESPONSE FROM GATEWAY !!!");
            System.out.println("Status: " + response.getStatusCode());
            System.out.println("Status Text: " + response.getStatusText());
            System.out.println("Headers: " + response.getHeaders());
            
            byte[] body = getResponseBody(response);
            if (body != null && body.length > 0) {
                String bodyStr = new String(body, StandardCharsets.UTF_8);
                System.out.println("Error Body: " + bodyStr);
            }
            System.out.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
            
            super.handleError(response);
        }
    }
}
