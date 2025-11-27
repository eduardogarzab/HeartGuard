package com.heartguard.desktop.util;

import java.awt.*;

/**
 * Utilidades para hacer la UI responsive y adaptable a diferentes tamaños de pantalla
 */
public class ResponsiveUtils {
    
    /**
     * Obtiene el tamaño de la pantalla
     */
    public static Dimension getScreenSize() {
        GraphicsEnvironment ge = GraphicsEnvironment.getLocalGraphicsEnvironment();
        GraphicsDevice gd = ge.getDefaultScreenDevice();
        DisplayMode dm = gd.getDisplayMode();
        return new Dimension(dm.getWidth(), dm.getHeight());
    }
    
    /**
     * Calcula un tamaño responsive basado en porcentaje de la pantalla
     * @param widthPercent Porcentaje del ancho de la pantalla (0.0 a 1.0)
     * @param heightPercent Porcentaje de la altura de la pantalla (0.0 a 1.0)
     * @param minWidth Ancho mínimo en píxeles
     * @param minHeight Altura mínima en píxeles
     * @return Dimension calculada
     */
    public static Dimension getResponsiveSize(double widthPercent, double heightPercent, 
                                             int minWidth, int minHeight) {
        Dimension screen = getScreenSize();
        int width = Math.max(minWidth, (int)(screen.width * widthPercent));
        int height = Math.max(minHeight, (int)(screen.height * heightPercent));
        return new Dimension(width, height);
    }
    
    /**
     * Calcula un tamaño responsive con máximos
     * @param widthPercent Porcentaje del ancho de la pantalla
     * @param heightPercent Porcentaje de la altura de la pantalla
     * @param maxWidth Ancho máximo en píxeles
     * @param maxHeight Altura máxima en píxeles
     * @return Dimension calculada
     */
    public static Dimension getResponsiveSizeWithMax(double widthPercent, double heightPercent,
                                                    int maxWidth, int maxHeight) {
        Dimension screen = getScreenSize();
        int width = Math.min(maxWidth, (int)(screen.width * widthPercent));
        int height = Math.min(maxHeight, (int)(screen.height * heightPercent));
        return new Dimension(width, height);
    }
    
    /**
     * Verifica si la pantalla es pequeña (< 1366x768)
     */
    public static boolean isSmallScreen() {
        Dimension screen = getScreenSize();
        return screen.width < 1366 || screen.height < 768;
    }
    
    /**
     * Verifica si la pantalla es muy pequeña (< 1280x720)
     */
    public static boolean isTinyScreen() {
        Dimension screen = getScreenSize();
        return screen.width < 1280 || screen.height < 720;
    }
    
    /**
     * Obtiene un factor de escala basado en el tamaño de la pantalla
     * Retorna 1.0 para pantallas normales, valores menores para pantallas pequeñas
     */
    public static double getScaleFactor() {
        Dimension screen = getScreenSize();
        if (screen.width >= 1920) {
            return 1.0; // Full HD o mayor
        } else if (screen.width >= 1600) {
            return 0.9;
        } else if (screen.width >= 1366) {
            return 0.8;
        } else {
            return 0.7; // Pantallas pequeñas
        }
    }
}
