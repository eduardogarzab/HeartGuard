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
            new JFXPanel(); // Esto inicializa implícitamente Platform.startup()
            Platform.setImplicitExit(false); // Importante: evitar que JavaFX cierre la aplicación
            System.out.println("[Main] JavaFX toolkit inicializado correctamente");
        });
    }
}
