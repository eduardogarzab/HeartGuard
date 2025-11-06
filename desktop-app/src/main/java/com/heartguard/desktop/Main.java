package com.heartguard.desktop;

import com.formdev.flatlaf.FlatLightLaf;
import com.heartguard.desktop.ui.LoginFrame;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;

import javax.swing.*;
import java.util.concurrent.CountDownLatch;

/**
 * Clase principal de la aplicación HeartGuard Desktop
 */
public class Main {
    
    public static void main(String[] args) {
        // Configurar propiedades del sistema para JavaFX WebView en Java 21
        // Estas propiedades deben establecerse ANTES de cualquier inicialización de JavaFX
        configureJavaFXProperties();
        
        // Inicializar el toolkit de JavaFX de forma explícita y ESPERAR a que esté listo
        // Esto es crítico para Java 17+ con JFXPanel
        initializeJavaFX();
        
        // Configurar Look and Feel moderno
        try {
            UIManager.setLookAndFeel(new FlatLightLaf());
        } catch (Exception e) {
            System.err.println("Failed to initialize FlatLaf Look and Feel");
            e.printStackTrace();
            // Fallback al Look and Feel del sistema
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ex) {
                ex.printStackTrace();
            }
        }

        // Ejecutar la aplicación en el Event Dispatch Thread
        SwingUtilities.invokeLater(() -> {
            LoginFrame loginFrame = new LoginFrame();
            loginFrame.setVisible(true);
        });
    }
    
    /**
     * Configura las propiedades del sistema para JavaFX.
     * DEBE llamarse antes de inicializar JavaFX.
     */
    private static void configureJavaFXProperties() {
        // Usar software rendering para máxima estabilidad con WebView
        System.setProperty("prism.order", "sw");
        System.setProperty("prism.text", "t2k");
        System.setProperty("prism.verbose", "false");
        System.setProperty("javafx.animation.fullspeed", "false");
        System.setProperty("prism.lcdtext", "false");
        System.setProperty("prism.subpixeltext", "false");
        
        // Configuración específica para WebView
        System.setProperty("prism.allowhidpi", "false");
        System.setProperty("prism.vsync", "false");
        
        System.out.println("[Main] Propiedades de JavaFX configuradas");
    }
    
    /**
     * Inicializa el toolkit de JavaFX de forma explícita y ESPERA a que esté completamente listo.
     * Esto asegura que el toolkit esté listo antes de crear cualquier JFXPanel.
     */
    private static void initializeJavaFX() {
        final CountDownLatch latch = new CountDownLatch(1);
        
        SwingUtilities.invokeLater(() -> {
            try {
                // Crear un JFXPanel dummy para forzar la inicialización del toolkit de JavaFX
                new JFXPanel();
                
                // Configurar JavaFX para que no cierre la aplicación automáticamente
                Platform.setImplicitExit(false);
                
                // Esperar a que el toolkit esté completamente inicializado
                Platform.runLater(() -> {
                    System.out.println("[Main] JavaFX toolkit inicializado correctamente");
                    latch.countDown();
                });
            } catch (Exception e) {
                System.err.println("[Main] Error al inicializar JavaFX: " + e.getMessage());
                e.printStackTrace();
                latch.countDown();
            }
        });
        
        // Esperar a que JavaFX esté listo
        try {
            latch.await();
            Thread.sleep(200); // Pequeña pausa adicional para asegurar estabilidad
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
