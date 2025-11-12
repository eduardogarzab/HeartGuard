package com.heartguard.desktop.ui.user;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.google.gson.JsonObject;

import javax.imageio.ImageIO;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.filechooser.FileNameExtensionFilter;
import java.awt.*;
import java.awt.geom.Ellipse2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;

/**
 * Panel para mostrar y gestionar la foto de perfil del usuario
 * Incluye funcionalidades para subir, editar y eliminar la foto
 */
public class UserProfilePhotoPanel extends JPanel {
    private static final Color PRIMARY_COLOR = new Color(33, 150, 243);
    private static final Color PRIMARY_DARK = new Color(25, 118, 210);
    private static final Color SURFACE_COLOR = Color.WHITE;
    private static final Color TEXT_PRIMARY_COLOR = new Color(35, 52, 70);
    private static final Color TEXT_SECONDARY_COLOR = new Color(104, 120, 138);
    private static final Color DANGER_COLOR = new Color(231, 76, 60);
    private static final int PHOTO_SIZE = 150;
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final String userId;
    
    private JLabel photoLabel;
    private BufferedImage currentPhoto;
    private String currentPhotoUrl;
    private JButton uploadButton;
    private JButton deleteButton;
    private Runnable onPhotoChangedCallback;
    
    public UserProfilePhotoPanel(ApiClient apiClient, String accessToken, String userId) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.userId = userId;
        
        initComponents();
    }
    
    private void initComponents() {
        setLayout(new BorderLayout(0, 16));
        setOpaque(false);
        setBorder(new EmptyBorder(8, 0, 0, 0));
        
        // Panel superior con la foto
        JPanel photoContainer = new JPanel(new FlowLayout(FlowLayout.CENTER, 0, 0));
        photoContainer.setOpaque(false);
        
        photoLabel = new JLabel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
                
                // Dibujar sombra sutil
                g2.setColor(new Color(0, 0, 0, 20));
                g2.fillOval(3, 3, PHOTO_SIZE, PHOTO_SIZE);
                
                // Dibujar círculo de fondo
                if (currentPhoto == null) {
                    // Sin foto - mostrar placeholder con iniciales
                    g2.setColor(PRIMARY_COLOR);
                    g2.fillOval(0, 0, PHOTO_SIZE, PHOTO_SIZE);
                    
                    g2.setColor(Color.WHITE);
                    g2.setFont(new Font("Segoe UI", Font.BOLD, 48));
                    FontMetrics fm = g2.getFontMetrics();
                    String initials = "?";
                    int x = (PHOTO_SIZE - fm.stringWidth(initials)) / 2;
                    int y = ((PHOTO_SIZE - fm.getHeight()) / 2) + fm.getAscent();
                    g2.drawString(initials, x, y);
                } else {
                    // Con foto - dibujar imagen circular
                    Ellipse2D clip = new Ellipse2D.Float(0, 0, PHOTO_SIZE, PHOTO_SIZE);
                    g2.setClip(clip);
                    g2.drawImage(currentPhoto, 0, 0, PHOTO_SIZE, PHOTO_SIZE, null);
                }
                
                // Dibujar borde
                g2.setClip(null);
                g2.setColor(PRIMARY_COLOR);
                g2.setStroke(new BasicStroke(3));
                g2.drawOval(1, 1, PHOTO_SIZE - 2, PHOTO_SIZE - 2);
                
                g2.dispose();
                super.paintComponent(g);
            }
        };
        photoLabel.setPreferredSize(new Dimension(PHOTO_SIZE + 4, PHOTO_SIZE + 4));
        photoLabel.setOpaque(false);
        photoContainer.add(photoLabel);
        
        add(photoContainer, BorderLayout.CENTER);
        
        // Panel inferior con botones
        JPanel buttonsPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 8, 0));
        buttonsPanel.setOpaque(false);
        
        uploadButton = new RoundedButton(
                "Cambiar Foto",
                PRIMARY_COLOR,
                null,
                Color.WHITE
        );
        uploadButton.setPreferredSize(new Dimension(120, 36));
        uploadButton.addActionListener(e -> handleUploadPhoto());
        
        deleteButton = new RoundedButton(
                "Eliminar",
                DANGER_COLOR,
                null,
                Color.WHITE
        );
        deleteButton.setPreferredSize(new Dimension(100, 36));
        deleteButton.addActionListener(e -> handleDeletePhoto());
        deleteButton.setEnabled(false); // Deshabilitado hasta que haya una foto
        
        buttonsPanel.add(uploadButton);
        buttonsPanel.add(deleteButton);
        
        add(buttonsPanel, BorderLayout.SOUTH);
    }
    
    /**
     * Establece la URL de la foto de perfil y la carga
     */
    public void setPhotoUrl(String photoUrl) {
        this.currentPhotoUrl = photoUrl;
        
        if (photoUrl != null && !photoUrl.trim().isEmpty()) {
            loadPhotoFromUrl(photoUrl);
            deleteButton.setEnabled(true);
        } else {
            currentPhoto = null;
            deleteButton.setEnabled(false);
            photoLabel.repaint();
        }
    }
    
    /**
     * Establece un callback que se ejecuta cuando la foto cambia
     */
    public void setOnPhotoChangedCallback(Runnable callback) {
        this.onPhotoChangedCallback = callback;
    }
    
    /**
     * Carga una foto desde una URL
     */
    private void loadPhotoFromUrl(String urlString) {
        SwingWorker<BufferedImage, Void> worker = new SwingWorker<>() {
            @Override
            protected BufferedImage doInBackground() throws Exception {
                URL url = new URL(urlString);
                return ImageIO.read(url);
            }
            
            @Override
            protected void done() {
                try {
                    currentPhoto = get();
                    photoLabel.repaint();
                } catch (InterruptedException | ExecutionException e) {
                    System.err.println("Error al cargar foto desde URL: " + e.getMessage());
                    currentPhoto = null;
                    photoLabel.repaint();
                }
            }
        };
        worker.execute();
    }
    
    /**
     * Maneja la subida o actualización de la foto
     */
    private void handleUploadPhoto() {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Seleccionar Foto de Perfil");
        fileChooser.setFileFilter(new FileNameExtensionFilter(
                "Archivos de Imagen (*.jpg, *.jpeg, *.png)", 
                "jpg", "jpeg", "png"
        ));
        
        int result = fileChooser.showOpenDialog(this);
        if (result == JFileChooser.APPROVE_OPTION) {
            File selectedFile = fileChooser.getSelectedFile();
            
            // Validar tamaño del archivo (máximo 5 MB)
            long fileSizeInMB = selectedFile.length() / (1024 * 1024);
            if (fileSizeInMB > 5) {
                JOptionPane.showMessageDialog(
                        this,
                        "El archivo es demasiado grande. El tamaño máximo es 5 MB.",
                        "Error",
                        JOptionPane.ERROR_MESSAGE
                );
                return;
            }
            
            // Mostrar diálogo de progreso
            JDialog progressDialog = new JDialog(
                    (Window) SwingUtilities.getWindowAncestor(this),
                    "Subiendo foto...",
                    Dialog.ModalityType.APPLICATION_MODAL
            );
            progressDialog.setSize(300, 100);
            progressDialog.setLocationRelativeTo(this);
            progressDialog.setLayout(new BorderLayout(10, 10));
            
            JLabel progressLabel = new JLabel("Subiendo foto de perfil...", SwingConstants.CENTER);
            JProgressBar progressBar = new JProgressBar();
            progressBar.setIndeterminate(true);
            
            JPanel contentPanel = new JPanel(new BorderLayout(10, 10));
            contentPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
            contentPanel.add(progressLabel, BorderLayout.CENTER);
            contentPanel.add(progressBar, BorderLayout.SOUTH);
            
            progressDialog.setContentPane(contentPanel);
            
            // Subir la foto en background
            boolean isUpdate = currentPhotoUrl != null && !currentPhotoUrl.trim().isEmpty();
            
            apiClient.uploadUserPhotoAsync(accessToken, userId, selectedFile, isUpdate)
                    .thenAccept(response -> SwingUtilities.invokeLater(() -> {
                        progressDialog.dispose();
                        
                        // Extraer la URL de la foto de la respuesta
                        if (response.has("data")) {
                            JsonObject data = response.getAsJsonObject("data");
                            if (data.has("photo_url")) {
                                String newPhotoUrl = data.get("photo_url").getAsString();
                                
                                // Primero, cargar la imagen localmente desde el archivo seleccionado
                                // para mostrarla inmediatamente sin esperar la descarga desde la URL
                                try {
                                    currentPhoto = ImageIO.read(selectedFile);
                                    currentPhotoUrl = newPhotoUrl;
                                    deleteButton.setEnabled(true);
                                    photoLabel.repaint();
                                } catch (IOException e) {
                                    // Si falla la carga local, cargar desde URL
                                    setPhotoUrl(newPhotoUrl);
                                }
                                
                                JOptionPane.showMessageDialog(
                                        this,
                                        "Foto de perfil actualizada correctamente",
                                        "Éxito",
                                        JOptionPane.INFORMATION_MESSAGE
                                );
                                
                                // Notificar cambio para actualizar el resto del dashboard
                                if (onPhotoChangedCallback != null) {
                                    onPhotoChangedCallback.run();
                                }
                            }
                        }
                    }))
                    .exceptionally(ex -> {
                        SwingUtilities.invokeLater(() -> {
                            progressDialog.dispose();
                            handleAsyncError(ex, "Error al subir la foto de perfil");
                        });
                        return null;
                    });
            
            progressDialog.setVisible(true);
        }
    }
    
    /**
     * Maneja la eliminación de la foto
     */
    private void handleDeletePhoto() {
        int confirm = JOptionPane.showConfirmDialog(
                this,
                "¿Está seguro que desea eliminar su foto de perfil?",
                "Confirmar eliminación",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
        );
        
        if (confirm != JOptionPane.YES_OPTION) {
            return;
        }
        
        // Mostrar diálogo de progreso
        JDialog progressDialog = new JDialog(
                (Window) SwingUtilities.getWindowAncestor(this),
                "Eliminando foto...",
                Dialog.ModalityType.APPLICATION_MODAL
        );
        progressDialog.setSize(300, 100);
        progressDialog.setLocationRelativeTo(this);
        progressDialog.setLayout(new BorderLayout(10, 10));
        
        JLabel progressLabel = new JLabel("Eliminando foto de perfil...", SwingConstants.CENTER);
        JProgressBar progressBar = new JProgressBar();
        progressBar.setIndeterminate(true);
        
        JPanel contentPanel = new JPanel(new BorderLayout(10, 10));
        contentPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
        contentPanel.add(progressLabel, BorderLayout.CENTER);
        contentPanel.add(progressBar, BorderLayout.SOUTH);
        
        progressDialog.setContentPane(contentPanel);
        
        // Eliminar la foto en background
        apiClient.deleteUserPhotoAsync(accessToken, userId)
                .thenAccept(response -> SwingUtilities.invokeLater(() -> {
                    progressDialog.dispose();
                    
                    setPhotoUrl(null);
                    
                    JOptionPane.showMessageDialog(
                            this,
                            "Foto de perfil eliminada correctamente",
                            "Éxito",
                            JOptionPane.INFORMATION_MESSAGE
                    );
                    
                    // Notificar cambio
                    if (onPhotoChangedCallback != null) {
                        onPhotoChangedCallback.run();
                    }
                }))
                .exceptionally(ex -> {
                    SwingUtilities.invokeLater(() -> {
                        progressDialog.dispose();
                        handleAsyncError(ex, "Error al eliminar la foto de perfil");
                    });
                    return null;
                });
        
        progressDialog.setVisible(true);
    }
    
    /**
     * Maneja errores asincrónicos
     */
    private void handleAsyncError(Throwable throwable, String fallbackMessage) {
        Throwable cause = unwrapCompletionException(throwable);
        
        if (cause instanceof ApiException apiException) {
            JOptionPane.showMessageDialog(
                    this,
                    apiException.getMessage(),
                    "Error",
                    JOptionPane.ERROR_MESSAGE
            );
            return;
        }
        
        String message = (cause != null && cause.getMessage() != null && !cause.getMessage().isBlank())
                ? cause.getMessage()
                : fallbackMessage;
        
        JOptionPane.showMessageDialog(
                this,
                message,
                "Error",
                JOptionPane.ERROR_MESSAGE
        );
    }
    
    /**
     * Desenvuelve excepciones de CompletableFuture
     */
    private Throwable unwrapCompletionException(Throwable throwable) {
        if (throwable instanceof CompletionException completion && completion.getCause() != null) {
            return completion.getCause();
        }
        if (throwable instanceof ExecutionException execution && execution.getCause() != null) {
            return execution.getCause();
        }
        return throwable;
    }
    
    /**
     * Clase interna para botones redondeados
     */
    private static class RoundedButton extends JButton {
        private final Color baseColor;
        
        RoundedButton(String text, Color baseColor, Color borderColor, Color textColor) {
            super(text);
            this.baseColor = baseColor;
            setFont(new Font("Segoe UI", Font.BOLD, 13));
            setForeground(textColor);
            setFocusPainted(false);
            setContentAreaFilled(false);
            setOpaque(false);
            setBorder(new EmptyBorder(8, 20, 8, 20));
            setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            
            int arc = 24;
            Color fill = baseColor;
            if (!isEnabled()) {
                fill = new Color(baseColor.getRed(), baseColor.getGreen(), baseColor.getBlue(), 100);
            } else if (getModel().isPressed()) {
                fill = blendColor(fill, Color.BLACK, 0.15);
            } else if (getModel().isRollover()) {
                fill = blendColor(fill, Color.WHITE, 0.12);
            }
            
            g2.setColor(fill);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), arc, arc);
            
            g2.dispose();
            super.paintComponent(g);
        }
        
        private Color blendColor(Color color1, Color color2, double ratio) {
            double clamped = Math.max(0, Math.min(1, ratio));
            int red = (int) Math.round(color1.getRed() * (1 - clamped) + color2.getRed() * clamped);
            int green = (int) Math.round(color1.getGreen() * (1 - clamped) + color2.getGreen() * clamped);
            int blue = (int) Math.round(color1.getBlue() * (1 - clamped) + color2.getBlue() * clamped);
            return new Color(red, green, blue);
        }
    }
}
