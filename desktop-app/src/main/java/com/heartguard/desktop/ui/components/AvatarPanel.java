package com.heartguard.desktop.ui.components;

import javax.imageio.ImageIO;
import javax.swing.*;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.net.URL;
import java.util.concurrent.ExecutionException;

/**
 * Panel circular para mostrar avatares de usuario
 * Puede mostrar una foto de perfil o iniciales por defecto
 */
public class AvatarPanel extends JPanel {
    private static final Color DEFAULT_BACKGROUND = new Color(33, 150, 243);
    private static final Color DEFAULT_TEXT = Color.WHITE;
    
    private final int size;
    private final String name;
    private BufferedImage photo;
    private String photoUrl;
    private boolean loadingPhoto = false;
    
    public AvatarPanel(String name, int size) {
        this(name, null, size);
    }
    
    public AvatarPanel(String name, String photoUrl, int size) {
        this.name = name != null ? name : "?";
        this.size = size;
        this.photoUrl = photoUrl;
        
        setPreferredSize(new Dimension(size, size));
        setMinimumSize(new Dimension(size, size));
        setMaximumSize(new Dimension(size, size));
        setOpaque(false);
        
        if (photoUrl != null && !photoUrl.trim().isEmpty()) {
            loadPhotoAsync(photoUrl);
        }
    }
    
    /**
     * Establece una nueva URL de foto y la carga
     */
    public void setPhotoUrl(String photoUrl) {
        this.photoUrl = photoUrl;
        this.photo = null;
        
        if (photoUrl != null && !photoUrl.trim().isEmpty()) {
            loadPhotoAsync(photoUrl);
        } else {
            repaint();
        }
    }
    
    /**
     * Carga la foto de forma asíncrona desde una URL
     */
    private void loadPhotoAsync(String urlString) {
        if (loadingPhoto) return;
        loadingPhoto = true;
        
        SwingWorker<BufferedImage, Void> worker = new SwingWorker<>() {
            @Override
            protected BufferedImage doInBackground() throws Exception {
                try {
                    URL url = new URL(urlString);
                    return ImageIO.read(url);
                } catch (IOException e) {
                    System.err.println("Error al cargar foto desde URL: " + urlString + " - " + e.getMessage());
                    return null;
                }
            }
            
            @Override
            protected void done() {
                loadingPhoto = false;
                try {
                    photo = get();
                    repaint();
                } catch (InterruptedException | ExecutionException e) {
                    System.err.println("Error al procesar foto: " + e.getMessage());
                    photo = null;
                    repaint();
                }
            }
        };
        worker.execute();
    }
    
    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        
        if (photo != null) {
            // Dibujar foto circular
            Ellipse2D clip = new Ellipse2D.Float(0, 0, size, size);
            g2.setClip(clip);
            g2.drawImage(photo, 0, 0, size, size, null);
            g2.setClip(null);
            
            // Borde opcional
            g2.setColor(new Color(229, 234, 243));
            g2.setStroke(new BasicStroke(2));
            g2.drawOval(1, 1, size - 2, size - 2);
        } else {
            // Dibujar círculo con iniciales
            g2.setColor(DEFAULT_BACKGROUND);
            g2.fillOval(0, 0, size, size);
            
            // Iniciales
            String initials = getInitials(name);
            g2.setColor(DEFAULT_TEXT);
            g2.setFont(new Font("Inter", Font.BOLD, size / 3));
            FontMetrics fm = g2.getFontMetrics();
            int x = (size - fm.stringWidth(initials)) / 2;
            int y = ((size - fm.getHeight()) / 2) + fm.getAscent();
            g2.drawString(initials, x, y);
        }
        
        g2.dispose();
    }
    
    @Override
    public Dimension getPreferredSize() {
        return new Dimension(size, size);
    }
    
    @Override
    public Dimension getMinimumSize() {
        return new Dimension(size, size);
    }
    
    @Override
    public Dimension getMaximumSize() {
        return new Dimension(size, size);
    }
    
    /**
     * Obtiene las iniciales de un nombre
     */
    private String getInitials(String name) {
        if (name == null || name.trim().isEmpty()) return "?";
        String[] parts = name.trim().split("\\s+");
        if (parts.length >= 2) {
            return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
        }
        return parts[0].substring(0, Math.min(2, parts[0].length())).toUpperCase();
    }
}
