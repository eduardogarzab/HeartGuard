package com.heartguard.desktop;

import com.formdev.flatlaf.FlatLightLaf;
import com.heartguard.desktop.ui.LoginFrame;
import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;

import javax.swing.*;

/**
 * Clase principal de la aplicación HeartGuard Desktop
 */
public class Main {
    
    public static void main(String[] args) {
        // Configurar propiedades del sistema para JavaFX WebView en Java 21
        // Estas propiedades deben establecerse ANTES de inicializar JavaFX
        System.setProperty("prism.order", "sw");
        System.setProperty("prism.verbose", "false");
        System.setProperty("javafx.animation.fullspeed", "true");
        System.setProperty("prism.lcdtext", "false");
        System.setProperty("prism.subpixeltext", "false");
        
        // Inicializar el toolkit de JavaFX de forma explícita
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
     * Inicializa el toolkit de JavaFX de forma explícita.
     * Esto asegura que el toolkit esté listo antes de crear cualquier JFXPanel.
     */
    private static void initializeJavaFX() {
        // Crear un JFXPanel dummy para forzar la inicialización del toolkit de JavaFX
        // Este panel no se usa, solo dispara la inicialización
        SwingUtilities.invokeLater(() -> {
            try {
                new JFXPanel(); // Esto inicializa implícitamente Platform.startup()
                Platform.setImplicitExit(false); // Importante: evitar que JavaFX cierre la aplicación
                
                // En Java 21, forzar que el renderizador use software en lugar de hardware
                // Esto previene problemas de renderizado de tiles en WebView
                Platform.runLater(() -> {
                    System.setProperty("prism.order", "sw");
                    System.setProperty("prism.text", "t2k");
                });
                
                System.out.println("[Main] JavaFX toolkit inicializado correctamente para Java 21");
            } catch (Exception e) {
                System.err.println("[Main] Error al inicializar JavaFX: " + e.getMessage());
                e.printStackTrace();
            }
        });
    }
}
