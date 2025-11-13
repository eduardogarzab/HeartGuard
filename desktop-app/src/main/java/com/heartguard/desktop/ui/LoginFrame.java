package com.heartguard.desktop.ui;

import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.api.ApiException;
import com.heartguard.desktop.models.LoginResponse;
import com.heartguard.desktop.ui.user.UserDashboardFrame;
import com.heartguard.desktop.util.ResponsiveUtils;

import javax.swing.*;
import java.awt.*;
import java.util.Calendar;

/**
 * Pantalla principal que maneja login y registro en una sola ventana
 */
public class LoginFrame extends JFrame {
    private final ApiClient apiClient;
    private JPanel mainPanel;
    private CardLayout cardLayout;
    
    // Estados de la ventana
    private static final String LOGIN_VIEW = "login";
    private static final String REGISTER_USER_VIEW = "register_user";
    private static final String REGISTER_PATIENT_VIEW = "register_patient";

    public LoginFrame() {
        this.apiClient = new ApiClient();
        initComponents();
    }

    private void initComponents() {
        setTitle("HeartGuard - Sistema de Monitoreo Cardíaco");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        // Usar altura responsive, máximo 700px
        Dimension loginSize = ResponsiveUtils.getResponsiveSizeWithMax(0.4, 0.8, 550, 700);
        setSize(loginSize);
        setLocationRelativeTo(null);
        setResizable(false);

        // Usar CardLayout para cambiar entre vistas
        cardLayout = new CardLayout();
        mainPanel = new JPanel(cardLayout);

        // Crear las tres vistas
        mainPanel.add(createLoginPanel(), LOGIN_VIEW);
        mainPanel.add(createRegisterUserPanel(), REGISTER_USER_VIEW);
        mainPanel.add(createRegisterPatientPanel(), REGISTER_PATIENT_VIEW);

        add(mainPanel);
        
        // Mostrar la vista de login inicialmente
        cardLayout.show(mainPanel, LOGIN_VIEW);
    }

    // ========== VISTA DE LOGIN ==========
    private JPanel createLoginPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BorderLayout(10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 40, 20, 40));

        // Panel de título
        JPanel titlePanel = new JPanel();
        titlePanel.setLayout(new BoxLayout(titlePanel, BoxLayout.Y_AXIS));
        JLabel titleLabel = new JLabel("HeartGuard");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 32));
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        JLabel subtitleLabel = new JLabel("Sistema de Monitoreo Cardíaco");
        subtitleLabel.setFont(new Font("Arial", Font.PLAIN, 14));
        subtitleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        subtitleLabel.setForeground(Color.GRAY);
        titlePanel.add(titleLabel);
        titlePanel.add(Box.createVerticalStrut(5));
        titlePanel.add(subtitleLabel);
        titlePanel.add(Box.createVerticalStrut(30));

        // Panel de formulario
        JPanel formPanel = new JPanel();
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.insets = new Insets(5, 5, 5, 5);

        // Selector de tipo de cuenta
        JLabel typeLabel = new JLabel("Tipo de cuenta:");
        typeLabel.setFont(new Font("Arial", Font.BOLD, 12));
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 2;
        formPanel.add(typeLabel, gbc);

        JPanel radioPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JRadioButton userRadio = new JRadioButton("Usuario (Staff)", true);
        JRadioButton patientRadio = new JRadioButton("Paciente");
        ButtonGroup group = new ButtonGroup();
        group.add(userRadio);
        group.add(patientRadio);
        radioPanel.add(userRadio);
        radioPanel.add(patientRadio);
        gbc.gridy = 1;
        formPanel.add(radioPanel, gbc);

        // Email
        JLabel emailLabel = new JLabel("Email:");
        gbc.gridy = 2;
        gbc.gridwidth = 1;
        formPanel.add(emailLabel, gbc);

        JTextField emailField = new JTextField(20);
        gbc.gridx = 1;
        formPanel.add(emailField, gbc);

        // Password
        JLabel passwordLabel = new JLabel("Contraseña:");
        gbc.gridx = 0;
        gbc.gridy = 3;
        formPanel.add(passwordLabel, gbc);

        JPasswordField passwordField = new JPasswordField(20);
        gbc.gridx = 1;
        formPanel.add(passwordField, gbc);

        // Label de estado
        JLabel statusLabel = new JLabel(" ");
        statusLabel.setHorizontalAlignment(SwingConstants.CENTER);
        statusLabel.setForeground(Color.RED);

        // Panel de botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 10));
        JButton loginButton = new JButton("Iniciar Sesión");
        loginButton.setPreferredSize(new Dimension(140, 35));
        loginButton.setBackground(new Color(0, 123, 255));
        loginButton.setForeground(Color.WHITE);
        loginButton.setFocusPainted(false);
        
        JButton registerButton = new JButton("Registrarse");
        registerButton.setPreferredSize(new Dimension(140, 35));
        registerButton.setBackground(new Color(40, 167, 69));
        registerButton.setForeground(Color.WHITE);
        registerButton.setFocusPainted(false);
        
        buttonPanel.add(loginButton);
        buttonPanel.add(registerButton);

        // Acciones de botones
        loginButton.addActionListener(e -> handleLogin(emailField, passwordField, userRadio, statusLabel, loginButton, registerButton, emailField, passwordField, userRadio, patientRadio));
        
        registerButton.addActionListener(e -> {
            if (userRadio.isSelected()) {
                cardLayout.show(mainPanel, REGISTER_USER_VIEW);
            } else {
                cardLayout.show(mainPanel, REGISTER_PATIENT_VIEW);
            }
        });

        // Ensamblar
        panel.add(titlePanel, BorderLayout.NORTH);
        panel.add(formPanel, BorderLayout.CENTER);
        
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.add(buttonPanel, BorderLayout.NORTH);
        bottomPanel.add(statusLabel, BorderLayout.CENTER);
        panel.add(bottomPanel, BorderLayout.SOUTH);

        // Enter key para login
        getRootPane().setDefaultButton(loginButton);

        return panel;
    }

    private void handleLogin(JTextField emailField, JPasswordField passwordField, JRadioButton userRadio, 
                            JLabel statusLabel, JButton loginButton, JButton registerButton,
                            JTextField emailFieldRef, JPasswordField passwordFieldRef, 
                            JRadioButton userRadioRef, JRadioButton patientRadioRef) {
        String email = emailField.getText().trim();
        String password = new String(passwordField.getPassword());

        if (email.isEmpty() || password.isEmpty()) {
            statusLabel.setText("Por favor complete todos los campos");
            statusLabel.setForeground(Color.RED);
            return;
        }

        // Deshabilitar botones durante la petición
        loginButton.setEnabled(false);
        registerButton.setEnabled(false);
        emailField.setEnabled(false);
        passwordField.setEnabled(false);
        userRadioRef.setEnabled(false);
        patientRadioRef.setEnabled(false);
        
        statusLabel.setText("Iniciando sesión...");
        statusLabel.setForeground(Color.BLUE);

        // Ejecutar en un hilo separado
        SwingWorker<LoginResponse, Void> worker = new SwingWorker<>() {
            @Override
            protected LoginResponse doInBackground() throws Exception {
                if (userRadio.isSelected()) {
                    return apiClient.loginUser(email, password);
                } else {
                    return apiClient.loginPatient(email, password);
                }
            }

            @Override
            protected void done() {
                loginButton.setEnabled(true);
                registerButton.setEnabled(true);
                emailField.setEnabled(true);
                passwordField.setEnabled(true);
                userRadioRef.setEnabled(true);
                patientRadioRef.setEnabled(true);
                
                try {
                    LoginResponse response = get();
                    statusLabel.setText("¡Inicio de sesión exitoso!");
                    statusLabel.setForeground(new Color(40, 167, 69));
                    
                    String accountType = response.getAccountType();
                    String fullName = response.getFullName();
                    
                    // Si es paciente, abrir dashboard
                    if (accountType.equals("patient")) {
                        openPatientDashboard(response);
                    } else {
                        openUserDashboard(response);
                    }
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    if (cause instanceof ApiException) {
                        ApiException apiEx = (ApiException) cause;
                        statusLabel.setText("Error: " + apiEx.getMessage());
                    } else {
                        statusLabel.setText("Error de conexión: " + ex.getMessage());
                    }
                    statusLabel.setForeground(Color.RED);
                }
            }
        };
        worker.execute();
    }

    // ========== VISTA DE REGISTRO DE USUARIO ==========
    private JPanel createRegisterUserPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BorderLayout(10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 40, 20, 40));

        // Título
        JPanel titlePanel = new JPanel();
        JLabel titleLabel = new JLabel("Registro de Usuario (Staff)");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 24));
        titlePanel.add(titleLabel);

        // Formulario
        JPanel formPanel = new JPanel();
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.insets = new Insets(5, 5, 5, 5);

        int row = 0;

        // Email
        JTextField emailField = new JTextField(20);
        addFormField(formPanel, gbc, row++, "*Email:", emailField);

        // Password
        JPasswordField passwordField = new JPasswordField(20);
        addFormField(formPanel, gbc, row++, "*Contraseña:", passwordField);

        // Confirm Password
        JPasswordField confirmPasswordField = new JPasswordField(20);
        addFormField(formPanel, gbc, row++, "*Confirmar Contraseña:", confirmPasswordField);

        // Nombre Completo
        JTextField nameField = new JTextField(20);
        nameField.setToolTipText("Ej: Dr. Juan Pérez López");
        addFormField(formPanel, gbc, row++, "*Nombre Completo:", nameField);

        // Nota informativa
        gbc.gridx = 0;
        gbc.gridy = row++;
        gbc.gridwidth = 2;
        JLabel noteLabel = new JLabel("<html><i>Nota: Se unirá a organizaciones mediante invitaciones</i></html>");
        noteLabel.setForeground(Color.GRAY);
        formPanel.add(noteLabel, gbc);
        gbc.gridwidth = 1;

        // Label de estado
        JLabel statusLabel = new JLabel(" ");
        statusLabel.setHorizontalAlignment(SwingConstants.CENTER);

        // Panel de botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 10));
        
        JButton registerButton = new JButton("Registrar");
        registerButton.setPreferredSize(new Dimension(120, 35));
        registerButton.setBackground(new Color(40, 167, 69));
        registerButton.setForeground(Color.WHITE);
        registerButton.setFocusPainted(false);
        
        JButton backButton = new JButton("Volver");
        backButton.setPreferredSize(new Dimension(120, 35));
        backButton.setBackground(new Color(108, 117, 125));
        backButton.setForeground(Color.WHITE);
        backButton.setFocusPainted(false);
        backButton.addActionListener(e -> cardLayout.show(mainPanel, LOGIN_VIEW));
        
        buttonPanel.add(registerButton);
        buttonPanel.add(backButton);

        registerButton.addActionListener(e -> handleRegisterUser(
            emailField, passwordField, confirmPasswordField, nameField,
            statusLabel, registerButton, backButton
        ));

        // Ensamblar
        panel.add(titlePanel, BorderLayout.NORTH);
        
        JScrollPane scrollPane = new JScrollPane(formPanel);
        scrollPane.setBorder(null);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.add(buttonPanel, BorderLayout.NORTH);
        bottomPanel.add(statusLabel, BorderLayout.CENTER);
        panel.add(bottomPanel, BorderLayout.SOUTH);

        return panel;
    }

    private void handleRegisterUser(JTextField emailField, JPasswordField passwordField,
                                   JPasswordField confirmPasswordField, JTextField nameField,
                                   JLabel statusLabel, JButton registerButton, JButton backButton) {
        String email = emailField.getText().trim();
        String password = new String(passwordField.getPassword());
        String confirmPassword = new String(confirmPasswordField.getPassword());
        String name = nameField.getText().trim();

        // Validaciones - Solo campos obligatorios (email, password, name)
        if (email.isEmpty() || password.isEmpty() || name.isEmpty()) {
            statusLabel.setText("Por favor complete todos los campos obligatorios (*)");
            statusLabel.setForeground(Color.RED);
            return;
        }

        if (!password.equals(confirmPassword)) {
            statusLabel.setText("Las contraseñas no coinciden");
            statusLabel.setForeground(Color.RED);
            return;
        }

        if (password.length() < 8) {
            statusLabel.setText("La contraseña debe tener al menos 8 caracteres");
            statusLabel.setForeground(Color.RED);
            return;
        }

        registerButton.setEnabled(false);
        backButton.setEnabled(false);
        statusLabel.setText("Registrando usuario...");
        statusLabel.setForeground(Color.BLUE);

        SwingWorker<LoginResponse, Void> worker = new SwingWorker<>() {
            @Override
            protected LoginResponse doInBackground() throws Exception {
                // Registro de usuario: solo requiere name, email, password
                return apiClient.registerUser(email, password, name);
            }

            @Override
            protected void done() {
                registerButton.setEnabled(true);
                backButton.setEnabled(true);
                try {
                    LoginResponse response = get();
                    statusLabel.setText("¡Registro exitoso!");
                    statusLabel.setForeground(new Color(40, 167, 69));
                    
                    JOptionPane.showMessageDialog(
                        LoginFrame.this,
                        "Usuario registrado exitosamente!\n\n" +
                        "Email: " + email + "\n" +
                        "Nombre: " + name + "\n\n" +
                        "Ahora puedes iniciar sesión.",
                        "Registro Exitoso",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                    
                    // Limpiar los campos después del registro exitoso
                    emailField.setText("");
                    passwordField.setText("");
                    confirmPasswordField.setText("");
                    nameField.setText("");
                    
                    cardLayout.show(mainPanel, LOGIN_VIEW);
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    if (cause instanceof ApiException) {
                        ApiException apiEx = (ApiException) cause;
                        statusLabel.setText("Error: " + apiEx.getMessage());
                    } else {
                        statusLabel.setText("Error de conexión: " + ex.getMessage());
                    }
                    statusLabel.setForeground(Color.RED);
                }
            }
        };
        worker.execute();
    }

    // ========== VISTA DE REGISTRO DE PACIENTE ==========
    private JPanel createRegisterPatientPanel() {
        JPanel panel = new JPanel();
        panel.setLayout(new BorderLayout(10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 40, 20, 40));

        // Título
        JPanel titlePanel = new JPanel();
        JLabel titleLabel = new JLabel("Registro de Paciente");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 24));
        titlePanel.add(titleLabel);

        // Formulario
        JPanel formPanel = new JPanel();
        formPanel.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.insets = new Insets(5, 5, 5, 5);

        int row = 0;

        // === CAMPOS OBLIGATORIOS ===
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 4;
        JLabel requiredLabel = new JLabel("Campos Obligatorios:");
        requiredLabel.setFont(new Font("Arial", Font.BOLD, 12));
        formPanel.add(requiredLabel, gbc);
        row++;

        // Email *
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        formPanel.add(new JLabel("*Email:"), gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        JTextField emailField = new JTextField(20);
        formPanel.add(emailField, gbc);
        row++;

        // Password *
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        formPanel.add(new JLabel("*Contraseña:"), gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        JPasswordField passwordField = new JPasswordField(20);
        formPanel.add(passwordField, gbc);
        row++;

        // Confirm Password *
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        formPanel.add(new JLabel("*Confirmar Contraseña:"), gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        JPasswordField confirmPasswordField = new JPasswordField(20);
        formPanel.add(confirmPasswordField, gbc);
        row++;

        // Name * (Nombre completo)
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        formPanel.add(new JLabel("*Nombre Completo:"), gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        JTextField nameField = new JTextField(20);
        nameField.setToolTipText("Ej: María González López");
        formPanel.add(nameField, gbc);
        row++;

        // Organization ID * (UUID o Código)
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        formPanel.add(new JLabel("*Organización:"), gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        JTextField orgIdField = new JTextField(20);
        orgIdField.setText("FAM-001");
        orgIdField.setToolTipText("UUID (ej: 550e8400-...) o Código (ej: CLIN-001, FAM-001)");
        formPanel.add(orgIdField, gbc);
        row++;

        // === CAMPOS OPCIONALES ===
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 4;
        JLabel optionalLabel = new JLabel("Campos Opcionales:");
        optionalLabel.setFont(new Font("Arial", Font.BOLD, 12));
        optionalLabel.setForeground(Color.GRAY);
        formPanel.add(optionalLabel, gbc);
        row++;

        // Fecha de Nacimiento (birthdate) - OPCIONAL
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        JLabel birthdateLabel = new JLabel("Fecha de Nacimiento:");
        birthdateLabel.setForeground(Color.GRAY);
        formPanel.add(birthdateLabel, gbc);
        
        // Día
        gbc.gridx = 1;
        gbc.gridwidth = 1;
        Integer[] days = new Integer[31];
        for (int i = 0; i < 31; i++) days[i] = i + 1;
        JComboBox<Integer> dayCombo = new JComboBox<>(days);
        dayCombo.setSelectedIndex(0);
        formPanel.add(dayCombo, gbc);
        
        // Mes
        gbc.gridx = 2;
        String[] months = {"Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                          "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"};
        JComboBox<String> monthCombo = new JComboBox<>(months);
        monthCombo.setSelectedIndex(0);
        formPanel.add(monthCombo, gbc);
        
        // Año
        gbc.gridx = 3;
        Integer[] years = new Integer[100];
        int currentYear = Calendar.getInstance().get(Calendar.YEAR);
        for (int i = 0; i < 100; i++) years[i] = currentYear - i;
        JComboBox<Integer> yearCombo = new JComboBox<>(years);
        yearCombo.setSelectedItem(1990);
        formPanel.add(yearCombo, gbc);
        row++;

        // Género (sex_code) - OPCIONAL
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        JLabel genderLabel = new JLabel("Género:");
        genderLabel.setForeground(Color.GRAY);
        formPanel.add(genderLabel, gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        
        String[] genderLabels = {"Masculino", "Femenino", "Otro"};
        String[] genderCodes = {"M", "F", "O"};
        JComboBox<String> genderComboBox = new JComboBox<>(genderLabels);
        formPanel.add(genderComboBox, gbc);
        row++;

        // Nivel de Riesgo (risk_level_code) - OPCIONAL
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        JLabel riskLabel = new JLabel("Nivel de Riesgo:");
        riskLabel.setForeground(Color.GRAY);
        formPanel.add(riskLabel, gbc);
        gbc.gridx = 1;
        gbc.gridwidth = 3;
        String[] riskLevels = {"Bajo (low)", "Medio (medium)", "Alto (high)"};
        String[] riskLevelCodes = {"low", "medium", "high"};
        JComboBox<String> riskLevelComboBox = new JComboBox<>(riskLevels);
        riskLevelComboBox.setSelectedIndex(1); // medium por defecto
        formPanel.add(riskLevelComboBox, gbc);
        row++;

        // Label de estado
        JLabel statusLabel = new JLabel(" ");
        statusLabel.setHorizontalAlignment(SwingConstants.CENTER);

        // Panel de botones
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 10));
        
        JButton registerButton = new JButton("Registrar");
        registerButton.setPreferredSize(new Dimension(120, 35));
        registerButton.setBackground(new Color(40, 167, 69));
        registerButton.setForeground(Color.WHITE);
        registerButton.setFocusPainted(false);
        
        JButton backButton = new JButton("Volver");
        backButton.setPreferredSize(new Dimension(120, 35));
        backButton.setBackground(new Color(108, 117, 125));
        backButton.setForeground(Color.WHITE);
        backButton.setFocusPainted(false);
        backButton.addActionListener(e -> cardLayout.show(mainPanel, LOGIN_VIEW));
        
        buttonPanel.add(registerButton);
        buttonPanel.add(backButton);

        registerButton.addActionListener(e -> handleRegisterPatient(
            emailField, passwordField, confirmPasswordField, nameField,
            orgIdField, dayCombo, monthCombo, yearCombo,
            genderComboBox, riskLevelComboBox, statusLabel, registerButton, backButton
        ));

        // Ensamblar
        panel.add(titlePanel, BorderLayout.NORTH);
        
        JScrollPane scrollPane = new JScrollPane(formPanel);
        scrollPane.setBorder(null);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        JPanel bottomPanel = new JPanel(new BorderLayout());
        bottomPanel.add(buttonPanel, BorderLayout.NORTH);
        bottomPanel.add(statusLabel, BorderLayout.CENTER);
        panel.add(bottomPanel, BorderLayout.SOUTH);

        return panel;
    }

    private void handleRegisterPatient(JTextField emailField, JPasswordField passwordField,
                                      JPasswordField confirmPasswordField, JTextField nameField,
                                      JTextField orgIdField, JComboBox<Integer> dayCombo, 
                                      JComboBox<String> monthCombo, JComboBox<Integer> yearCombo,
                                      JComboBox<String> genderComboBox, JComboBox<String> riskLevelComboBox,
                                      JLabel statusLabel, JButton registerButton, JButton backButton) {
        String email = emailField.getText().trim();
        String password = new String(passwordField.getPassword());
        String confirmPassword = new String(confirmPasswordField.getPassword());
        String name = nameField.getText().trim();
        String orgId = orgIdField.getText().trim();
        
        // Campos opcionales
        int day = (Integer) dayCombo.getSelectedItem();
        int month = monthCombo.getSelectedIndex() + 1; // 1-12
        int year = (Integer) yearCombo.getSelectedItem();
        String birthdate = String.format("%04d-%02d-%02d", year, month, day);
        
        // Convertir el índice del género al código correcto: M, F, O
        String[] genderCodes = {"M", "F", "O"};
        String sexCode = genderCodes[genderComboBox.getSelectedIndex()];
        
        // Risk level code
        String[] riskLevelCodes = {"low", "medium", "high"};
        String riskLevelCode = riskLevelCodes[riskLevelComboBox.getSelectedIndex()];

        // Validaciones - Solo campos obligatorios
        if (email.isEmpty() || password.isEmpty() || name.isEmpty() || orgId.isEmpty()) {
            statusLabel.setText("Por favor complete todos los campos obligatorios (*)");
            statusLabel.setForeground(Color.RED);
            return;
        }

        if (!password.equals(confirmPassword)) {
            statusLabel.setText("Las contraseñas no coinciden");
            statusLabel.setForeground(Color.RED);
            return;
        }

        if (password.length() < 8) {
            statusLabel.setText("La contraseña debe tener al menos 8 caracteres");
            statusLabel.setForeground(Color.RED);
            return;
        }

        registerButton.setEnabled(false);
        backButton.setEnabled(false);
        statusLabel.setText("Registrando paciente...");
        statusLabel.setForeground(Color.BLUE);

        SwingWorker<LoginResponse, Void> worker = new SwingWorker<>() {
            @Override
            protected LoginResponse doInBackground() throws Exception {
                // Llamar a la API con todos los campos (obligatorios y opcionales)
                return apiClient.registerPatient(email, password, name, orgId, 
                                                birthdate, sexCode, riskLevelCode);
            }

            @Override
            protected void done() {
                registerButton.setEnabled(true);
                backButton.setEnabled(true);
                try {
                    LoginResponse response = get();
                    statusLabel.setText("¡Registro exitoso!");
                    statusLabel.setForeground(new Color(40, 167, 69));
                    
                    JOptionPane.showMessageDialog(
                        LoginFrame.this,
                        "Paciente registrado exitosamente!\n\n" +
                        "Email: " + email + "\n" +
                        "Nombre: " + name + "\n\n" +
                        "Ahora puedes iniciar sesión.",
                        "Registro Exitoso",
                        JOptionPane.INFORMATION_MESSAGE
                    );
                    
                    // Limpiar los campos después del registro exitoso
                    emailField.setText("");
                    passwordField.setText("");
                    confirmPasswordField.setText("");
                    nameField.setText("");
                    orgIdField.setText("");
                    dayCombo.setSelectedIndex(0);
                    monthCombo.setSelectedIndex(0);
                    yearCombo.setSelectedIndex(0);
                    genderComboBox.setSelectedIndex(0);
                    riskLevelComboBox.setSelectedIndex(1); // medium
                    
                    cardLayout.show(mainPanel, LOGIN_VIEW);
                } catch (Exception ex) {
                    Throwable cause = ex.getCause();
                    if (cause instanceof ApiException) {
                        ApiException apiEx = (ApiException) cause;
                        statusLabel.setText("Error: " + apiEx.getMessage());
                    } else {
                        statusLabel.setText("Error de conexión: " + ex.getMessage());
                    }
                    statusLabel.setForeground(Color.RED);
                }
            }
        };
        worker.execute();
    }

    private void addFormField(JPanel panel, GridBagConstraints gbc, int row, String label, JComponent field) {
        gbc.gridx = 0;
        gbc.gridy = row;
        gbc.gridwidth = 1;
        panel.add(new JLabel(label), gbc);

        gbc.gridx = 1;
        panel.add(field, gbc);
    }
    
    /**
     * Abre la ventana del dashboard del paciente
     */
    private void openPatientDashboard(LoginResponse loginResponse) {
        // Crear nueva ventana para el dashboard
        JFrame dashboardFrame = new JFrame("HeartGuard - Dashboard del Paciente");
        dashboardFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        dashboardFrame.setSize(1000, 800);
        dashboardFrame.setLocationRelativeTo(null);
        
        // Crear panel del dashboard
        PatientDashboardPanel dashboardPanel = new PatientDashboardPanel(
            apiClient,
            loginResponse.getAccessToken(),
            loginResponse.getPatientId()
        );
        
        dashboardFrame.add(dashboardPanel);
        dashboardFrame.setVisible(true);

        // Cerrar la ventana de login
        this.dispose();
    }

    private void openUserDashboard(LoginResponse loginResponse) {
        // Crear un nuevo ApiClient para cada sesión para evitar contaminación de datos
        ApiClient newApiClient = new ApiClient();
        UserDashboardFrame frame = new UserDashboardFrame(newApiClient, loginResponse);
        frame.setVisible(true);
        this.dispose();
    }
}

