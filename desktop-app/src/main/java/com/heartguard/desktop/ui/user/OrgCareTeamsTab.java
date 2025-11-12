package com.heartguard.desktop.ui.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.heartguard.desktop.api.ApiClient;
import com.heartguard.desktop.models.user.OrgMembership;
import com.heartguard.desktop.ui.components.AvatarPanel;

import javax.swing.*;
import javax.swing.border.CompoundBorder;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * Tab de Care Teams de una organización.
 * Layout: Sidebar izquierdo (30%) con lista de care teams + Panel derecho (70%) con detalle
 */
public class OrgCareTeamsTab extends JPanel {
    // Colores
    private static final Color GLOBAL_BACKGROUND = new Color(247, 249, 251);
    private static final Color CARD_BACKGROUND = Color.WHITE;
    private static final Color PRIMARY_BLUE = new Color(0, 120, 215);
    private static final Color SECONDARY_GREEN = new Color(40, 167, 69);
    private static final Color DANGER_RED = new Color(220, 53, 69);
    private static final Color TEXT_PRIMARY = new Color(46, 58, 89);
    private static final Color TEXT_SECONDARY = new Color(96, 103, 112);
    private static final Color BORDER_LIGHT = new Color(223, 227, 230);
    private static final Color HOVER_BG = new Color(240, 242, 245);
    
    private final ApiClient apiClient;
    private final String accessToken;
    private final OrgMembership organization;
    private final Consumer<Exception> exceptionHandler;
    private final BiConsumer<String, Boolean> snackbarHandler;
    
    private final JPanel teamsListPanel = new JPanel();
    private final JPanel detailContainer = new JPanel(new BorderLayout());
    
    private JsonArray careTeams;
    private String selectedTeamId;
    
    public OrgCareTeamsTab(
            ApiClient apiClient,
            String accessToken,
            OrgMembership organization,
            Consumer<Exception> exceptionHandler,
            BiConsumer<String, Boolean> snackbarHandler
    ) {
        this.apiClient = apiClient;
        this.accessToken = accessToken;
        this.organization = organization;
        this.exceptionHandler = exceptionHandler;
        this.snackbarHandler = snackbarHandler;
        
        setLayout(new BorderLayout());
        setOpaque(false);
        setBorder(new EmptyBorder(24, 24, 24, 24));
        
        initUI();
    }
    
    private void initUI() {
        // Sidebar izquierdo (30%)
        JPanel sidebar = new JPanel(new BorderLayout());
        sidebar.setPreferredSize(new Dimension(420, 0));
        sidebar.setBackground(CARD_BACKGROUND);
        sidebar.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        
        // Header del sidebar
        JLabel sidebarTitle = new JLabel("Care Teams");
        sidebarTitle.setFont(new Font("Inter", Font.BOLD, 18));
        sidebarTitle.setForeground(TEXT_PRIMARY);
        sidebarTitle.setBorder(new EmptyBorder(0, 0, 16, 0));
        sidebar.add(sidebarTitle, BorderLayout.NORTH);
        
        // Lista de teams
        teamsListPanel.setLayout(new BoxLayout(teamsListPanel, BoxLayout.Y_AXIS));
        teamsListPanel.setOpaque(false);
        
        JScrollPane teamsScroll = new JScrollPane(teamsListPanel);
        teamsScroll.setBorder(null);
        teamsScroll.getVerticalScrollBar().setUnitIncrement(12);
        teamsScroll.setOpaque(false);
        teamsScroll.getViewport().setOpaque(false);
        sidebar.add(teamsScroll, BorderLayout.CENTER);
        
        add(sidebar, BorderLayout.WEST);
        
        // Panel derecho (70%) - Detalle
        detailContainer.setOpaque(false);
        detailContainer.setBorder(new EmptyBorder(0, 16, 0, 0));
        
        // Estado inicial vacío
        showEmptyState();
        
        add(detailContainer, BorderLayout.CENTER);
    }
    
    private void showEmptyState() {
        detailContainer.removeAll();
        
        JPanel emptyPanel = new JPanel();
        emptyPanel.setLayout(new BoxLayout(emptyPanel, BoxLayout.Y_AXIS));
        emptyPanel.setBackground(CARD_BACKGROUND);
        emptyPanel.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(80, 20, 80, 20)
        ));
        
        JLabel icon = new JLabel("👥", SwingConstants.CENTER);
        icon.setFont(new Font("Segoe UI Emoji", Font.PLAIN, 56));
        icon.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel title = new JLabel("Selecciona un Care Team");
        title.setFont(new Font("Inter", Font.BOLD, 20));
        title.setForeground(TEXT_PRIMARY);
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel subtitle = new JLabel("Elige un equipo de la lista para ver sus detalles");
        subtitle.setFont(new Font("Inter", Font.PLAIN, 14));
        subtitle.setForeground(TEXT_SECONDARY);
        subtitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        emptyPanel.add(Box.createVerticalGlue());
        emptyPanel.add(icon);
        emptyPanel.add(Box.createVerticalStrut(16));
        emptyPanel.add(title);
        emptyPanel.add(Box.createVerticalStrut(8));
        emptyPanel.add(subtitle);
        emptyPanel.add(Box.createVerticalGlue());
        
        detailContainer.add(emptyPanel, BorderLayout.CENTER);
        detailContainer.revalidate();
        detailContainer.repaint();
    }
    
    /**
     * Carga lista de care teams
     */
    public void loadData() {
        SwingWorker<JsonArray, Void> worker = new SwingWorker<>() {
            @Override
            protected JsonArray doInBackground() throws Exception {
                JsonObject response = apiClient.getOrganizationCareTeams(accessToken, organization.getOrgId());
                System.out.println("[OrgCareTeamsTab] Response: " + response.toString());
                
                // Backend retorna: {data: {organization: {...}, care_teams: [...]}}
                if (response.has("data") && response.get("data").isJsonObject()) {
                    JsonObject data = response.getAsJsonObject("data");
                    if (data.has("care_teams") && data.get("care_teams").isJsonArray()) {
                        return data.getAsJsonArray("care_teams");
                    }
                }
                
                return new JsonArray();
            }
            
            @Override
            protected void done() {
                try {
                    careTeams = get();
                    System.out.println("[OrgCareTeamsTab] Care teams loaded: " + careTeams.size());
                    updateTeamsList();
                } catch (Exception ex) {
                    ex.printStackTrace();
                    exceptionHandler.accept(ex);
                }
            }
        };
        worker.execute();
    }
    
    private void updateTeamsList() {
        teamsListPanel.removeAll();
        
        if (careTeams == null || careTeams.size() == 0) {
            JLabel emptyLabel = new JLabel("No hay care teams disponibles");
            emptyLabel.setFont(new Font("Inter", Font.PLAIN, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            teamsListPanel.add(Box.createVerticalGlue());
            teamsListPanel.add(emptyLabel);
            teamsListPanel.add(Box.createVerticalGlue());
        } else {
            for (int i = 0; i < careTeams.size(); i++) {
                JsonObject team = careTeams.get(i).getAsJsonObject();
                JPanel teamRow = createTeamRow(team);
                teamRow.setAlignmentX(Component.LEFT_ALIGNMENT);
                teamsListPanel.add(teamRow);
                
                if (i < careTeams.size() - 1) {
                    teamsListPanel.add(Box.createVerticalStrut(8));
                }
            }
        }
        
        teamsListPanel.revalidate();
        teamsListPanel.repaint();
    }
    
    private JPanel createTeamRow(JsonObject team) {
        String teamId = team.has("id") ? team.get("id").getAsString() : "";
        String teamName = team.has("name") ? team.get("name").getAsString() : "Sin nombre";
        
        JPanel row = new JPanel(new BorderLayout(12, 0));
        row.setBackground(CARD_BACKGROUND);
        row.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(16, 16, 16, 16)
        ));
        row.setMaximumSize(new Dimension(Integer.MAX_VALUE, 80));
        row.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        
        // Panel izquierdo con el contenido
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setOpaque(false);
        
        // Nombre del team
        JLabel nameLabel = new JLabel(teamName);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 15));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Contar miembros (si están disponibles)
        int membersCount = 0;
        if (team.has("members") && team.get("members").isJsonArray()) {
            membersCount = team.getAsJsonArray("members").size();
        }
        
        JLabel membersLabel = new JLabel(membersCount + " miembro" + (membersCount != 1 ? "s" : ""));
        membersLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        membersLabel.setForeground(TEXT_SECONDARY);
        membersLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        leftPanel.add(nameLabel);
        leftPanel.add(Box.createVerticalStrut(4));
        leftPanel.add(membersLabel);
        
        row.add(leftPanel, BorderLayout.CENTER);
        
        // Flecha indicadora
        JLabel arrowLabel = new JLabel("→");
        arrowLabel.setFont(new Font("Segoe UI Symbol", Font.PLAIN, 20));
        arrowLabel.setForeground(PRIMARY_BLUE);
        row.add(arrowLabel, BorderLayout.EAST);
        
        // Efecto hover
        row.addMouseListener(new java.awt.event.MouseAdapter() {
            @Override
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                row.setBackground(HOVER_BG);
            }
            
            @Override
            public void mouseExited(java.awt.event.MouseEvent evt) {
                row.setBackground(CARD_BACKGROUND);
            }
            
            @Override
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                selectTeam(teamId, teamName);
            }
        });
        
        return row;
    }
    
    private void selectTeam(String teamId, String teamName) {
        selectedTeamId = teamId;
        
        // Buscar el team completo en los datos cargados
        JsonObject selectedTeam = null;
        if (careTeams != null) {
            for (int i = 0; i < careTeams.size(); i++) {
                JsonObject team = careTeams.get(i).getAsJsonObject();
                String id = team.has("id") ? team.get("id").getAsString() : "";
                if (id.equals(teamId)) {
                    selectedTeam = team;
                    break;
                }
            }
        }
        
        if (selectedTeam == null) {
            snackbarHandler.accept("Error: No se encontró el care team", false);
            return;
        }
        
        // Crear panel de detalle
        detailContainer.removeAll();
        JPanel detailPanel = createTeamDetailPanel(selectedTeam);
        detailContainer.add(detailPanel, BorderLayout.CENTER);
        detailContainer.revalidate();
        detailContainer.repaint();
        
        snackbarHandler.accept("Detalle de " + teamName + " cargado", true);
    }
    
    private JPanel createTeamDetailPanel(JsonObject team) {
        String teamName = team.has("name") ? team.get("name").getAsString() : "Sin nombre";
        String teamId = team.has("id") ? team.get("id").getAsString() : "";
        String createdAt = team.has("created_at") ? team.get("created_at").getAsString() : "N/A";
        
        JPanel mainPanel = new JPanel(new BorderLayout());
        mainPanel.setBackground(GLOBAL_BACKGROUND);
        
        // Header del panel FUERA del scroll
        JPanel headerCard = new JPanel(new BorderLayout());
        headerCard.setBackground(PRIMARY_BLUE);
        headerCard.setBorder(new EmptyBorder(32, 32, 32, 32));
        headerCard.setPreferredSize(new Dimension(Integer.MAX_VALUE, 110));
        
        JPanel headerContent = new JPanel();
        headerContent.setLayout(new BoxLayout(headerContent, BoxLayout.Y_AXIS));
        headerContent.setOpaque(false);
        
        JLabel titleLabel = new JLabel("👥 " + teamName);
        titleLabel.setFont(new Font("Inter", Font.BOLD, 28));
        titleLabel.setForeground(Color.WHITE);
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel dateLabel = new JLabel("📅 Creado el " + formatDate(createdAt));
        dateLabel.setFont(new Font("Inter", Font.PLAIN, 14));
        dateLabel.setForeground(new Color(220, 230, 255));
        dateLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        headerContent.add(titleLabel);
        headerContent.add(Box.createVerticalStrut(8));
        headerContent.add(dateLabel);
        
        headerCard.add(headerContent, BorderLayout.WEST);
        
        // Agregar header al mainPanel NORTH (no dentro del scroll)
        mainPanel.add(headerCard, BorderLayout.NORTH);
        
        // Contenido que SI va en scroll
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBackground(GLOBAL_BACKGROUND);
        contentPanel.setBorder(new EmptyBorder(32, 0, 0, 0));
        
        // Panel con padding para el contenido
        JPanel membersContainer = new JPanel();
        membersContainer.setLayout(new BoxLayout(membersContainer, BoxLayout.Y_AXIS));
        membersContainer.setBackground(GLOBAL_BACKGROUND);
        membersContainer.setBorder(new EmptyBorder(0, 32, 32, 32));
        
        // Sección: Miembros del equipo
        JLabel membersTitle = new JLabel("Miembros del Equipo");
        membersTitle.setFont(new Font("Inter", Font.BOLD, 20));
        membersTitle.setForeground(TEXT_PRIMARY);
        membersTitle.setAlignmentX(Component.LEFT_ALIGNMENT);
        membersTitle.setBorder(new EmptyBorder(0, 0, 20, 0));
        membersContainer.add(membersTitle);
        
        // Lista de miembros
        if (team.has("members") && team.get("members").isJsonArray()) {
            JsonArray members = team.getAsJsonArray("members");
            
            if (members.size() > 0) {
                for (int i = 0; i < members.size(); i++) {
                    JsonObject member = members.get(i).getAsJsonObject();
                    JPanel memberCard = createMemberCard(member);
                    memberCard.setAlignmentX(Component.LEFT_ALIGNMENT);
                    membersContainer.add(memberCard);
                    membersContainer.add(Box.createVerticalStrut(16));
                }
            } else {
                JLabel emptyLabel = new JLabel("No hay miembros en este equipo");
                emptyLabel.setFont(new Font("Inter", Font.ITALIC, 14));
                emptyLabel.setForeground(TEXT_SECONDARY);
                emptyLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
                membersContainer.add(emptyLabel);
            }
        } else {
            JLabel emptyLabel = new JLabel("No hay miembros en este equipo");
            emptyLabel.setFont(new Font("Inter", Font.ITALIC, 14));
            emptyLabel.setForeground(TEXT_SECONDARY);
            emptyLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
            membersContainer.add(emptyLabel);
        }
        
        contentPanel.add(membersContainer);
        contentPanel.add(Box.createVerticalGlue());
        
        // Envolver en scroll pane
        JScrollPane scrollPane = new JScrollPane(contentPanel);
        scrollPane.setBorder(null);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        scrollPane.setHorizontalScrollBarPolicy(ScrollPaneConstants.HORIZONTAL_SCROLLBAR_NEVER);
        scrollPane.setOpaque(false);
        scrollPane.getViewport().setOpaque(false);
        
        mainPanel.add(scrollPane, BorderLayout.CENTER);
        
        return mainPanel;
    }
    
    private JPanel createMemberCard(JsonObject member) {
        String userId = member.has("user_id") ? member.get("user_id").getAsString() : "";
        String name = member.has("name") ? member.get("name").getAsString() : "Sin nombre";
        String email = member.has("email") ? member.get("email").getAsString() : "N/A";
        String roleText = "Miembro";
        String roleCode = "";
        
        if (member.has("role") && member.get("role").isJsonObject()) {
            JsonObject role = member.getAsJsonObject("role");
            if (role.has("label")) {
                roleText = role.get("label").getAsString();
            }
            if (role.has("code")) {
                roleCode = role.get("code").getAsString();
            }
        }
        
        JPanel card = new JPanel(new BorderLayout(16, 0));
        card.setBackground(CARD_BACKGROUND);
        card.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        card.setMinimumSize(new Dimension(Integer.MAX_VALUE, 110));
        card.setPreferredSize(new Dimension(Integer.MAX_VALUE, 110));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 110));
        card.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        
        // Avatar circular - con contenedor para asegurar tamaño
        String photoUrl = member.has("profile_photo_url") && !member.get("profile_photo_url").isJsonNull()
                ? member.get("profile_photo_url").getAsString() : null;
        
        JPanel avatarContainer = new JPanel(new BorderLayout());
        avatarContainer.setOpaque(false);
        avatarContainer.setPreferredSize(new Dimension(64, 64));
        avatarContainer.setMinimumSize(new Dimension(64, 64));
        avatarContainer.setMaximumSize(new Dimension(64, 64));
        AvatarPanel avatarPanel = new AvatarPanel(name, photoUrl, 64);
        avatarContainer.add(avatarPanel, BorderLayout.CENTER);
        card.add(avatarContainer, BorderLayout.WEST);
        
        // Información del miembro
        JPanel infoPanel = new JPanel();
        infoPanel.setLayout(new BoxLayout(infoPanel, BoxLayout.Y_AXIS));
        infoPanel.setOpaque(false);
        
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 16));
        nameLabel.setForeground(TEXT_PRIMARY);
        
        JLabel emailLabel = new JLabel("✉️ " + email);
        emailLabel.setFont(new Font("Inter", Font.PLAIN, 13));
        emailLabel.setForeground(TEXT_SECONDARY);
        
        infoPanel.add(nameLabel);
        infoPanel.add(Box.createVerticalStrut(6));
        infoPanel.add(emailLabel);
        
        card.add(infoPanel, BorderLayout.CENTER);
        
        // Panel derecho: Badge de rol + ícono de ver más
        JPanel rightPanel = new JPanel();
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));
        rightPanel.setOpaque(false);
        
        // Badge de rol con colores según tipo
        Color badgeBg = getRoleBadgeColor(roleCode);
        JLabel roleLabel = new JLabel(roleText);
        roleLabel.setFont(new Font("Inter", Font.BOLD, 11));
        roleLabel.setForeground(Color.WHITE);
        roleLabel.setOpaque(true);
        roleLabel.setBackground(badgeBg);
        roleLabel.setBorder(new EmptyBorder(6, 12, 6, 12));
        roleLabel.setAlignmentX(Component.RIGHT_ALIGNMENT);
        
        // Ícono de ver detalles
        JLabel detailIcon = new JLabel("→");
        detailIcon.setFont(new Font("Segoe UI Symbol", Font.BOLD, 20));
        detailIcon.setForeground(PRIMARY_BLUE);
        detailIcon.setAlignmentX(Component.RIGHT_ALIGNMENT);
        
        rightPanel.add(roleLabel);
        rightPanel.add(Box.createVerticalGlue());
        rightPanel.add(detailIcon);
        
        card.add(rightPanel, BorderLayout.EAST);
        
        // Efecto hover
        card.addMouseListener(new java.awt.event.MouseAdapter() {
            private final Color originalBg = CARD_BACKGROUND;
            
            @Override
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                card.setBackground(HOVER_BG);
                card.setBorder(new CompoundBorder(
                        new LineBorder(PRIMARY_BLUE, 2, true),
                        new EmptyBorder(19, 19, 19, 19)
                ));
            }
            
            @Override
            public void mouseExited(java.awt.event.MouseEvent evt) {
                card.setBackground(originalBg);
                card.setBorder(new CompoundBorder(
                        new LineBorder(BORDER_LIGHT, 1, true),
                        new EmptyBorder(20, 20, 20, 20)
                ));
            }
            
            @Override
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                showMemberDetail(member);
            }
        });
        
        return card;
    }
    
    /**
     * Crea un avatar circular con iniciales
     */
    private JPanel createAvatarPanel(String name, int size) {
        JPanel avatarPanel = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                
                // Círculo de fondo
                g2.setColor(PRIMARY_BLUE);
                g2.fillOval(0, 0, size, size);
                
                // Iniciales
                String initials = getInitials(name);
                g2.setColor(Color.WHITE);
                g2.setFont(new Font("Inter", Font.BOLD, size / 3));
                FontMetrics fm = g2.getFontMetrics();
                int x = (size - fm.stringWidth(initials)) / 2;
                int y = ((size - fm.getHeight()) / 2) + fm.getAscent();
                g2.drawString(initials, x, y);
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
        };
        avatarPanel.setPreferredSize(new Dimension(size, size));
        avatarPanel.setMinimumSize(new Dimension(size, size));
        avatarPanel.setMaximumSize(new Dimension(size, size));
        avatarPanel.setOpaque(false);
        return avatarPanel;
    }
    
    private String getInitials(String name) {
        if (name == null || name.trim().isEmpty()) return "?";
        String[] parts = name.trim().split("\\s+");
        if (parts.length >= 2) {
            return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
        }
        return parts[0].substring(0, Math.min(2, parts[0].length())).toUpperCase();
    }
    
    private Color getRoleBadgeColor(String roleCode) {
        switch (roleCode) {
            case "admin":
                return DANGER_RED;
            case "specialist":
                return PRIMARY_BLUE;
            case "caregiver":
                return SECONDARY_GREEN;
            default:
                return TEXT_SECONDARY;
        }
    }
    
    /**
     * Muestra el detalle completo de un miembro del equipo
     */
    private void showMemberDetail(JsonObject member) {
        String name = member.has("name") ? member.get("name").getAsString() : "Sin nombre";
        String email = member.has("email") ? member.get("email").getAsString() : "N/A";
        String userId = member.has("user_id") ? member.get("user_id").getAsString() : "";
        String roleText = "Miembro";
        
        if (member.has("role") && member.get("role").isJsonObject()) {
            JsonObject role = member.getAsJsonObject("role");
            if (role.has("label")) {
                roleText = role.get("label").getAsString();
            }
        }
        
        // Crear diálogo modal con detalles del miembro
        Window parentWindow = SwingUtilities.getWindowAncestor(this);
        JDialog dialog = new JDialog(parentWindow, "Detalle del Miembro", Dialog.ModalityType.APPLICATION_MODAL);
        dialog.setSize(500, 450);
        dialog.setLocationRelativeTo(parentWindow); // Centrar respecto a la ventana padre
        
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBackground(GLOBAL_BACKGROUND);
        contentPanel.setBorder(new EmptyBorder(24, 24, 24, 24));
        
        // Avatar grande con foto o iniciales
        String photoUrl = member.has("profile_photo_url") && !member.get("profile_photo_url").isJsonNull()
                ? member.get("profile_photo_url").getAsString() : null;
        AvatarPanel avatarPanel = new AvatarPanel(name, photoUrl, 120);
        avatarPanel.setAlignmentX(Component.CENTER_ALIGNMENT);
        contentPanel.add(avatarPanel);
        contentPanel.add(Box.createVerticalStrut(20));
        
        // Nombre
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Inter", Font.BOLD, 24));
        nameLabel.setForeground(TEXT_PRIMARY);
        nameLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        contentPanel.add(nameLabel);
        contentPanel.add(Box.createVerticalStrut(8));
        
        // Rol
        JLabel roleLabel = new JLabel(roleText);
        roleLabel.setFont(new Font("Inter", Font.PLAIN, 16));
        roleLabel.setForeground(PRIMARY_BLUE);
        roleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        contentPanel.add(roleLabel);
        contentPanel.add(Box.createVerticalStrut(24));
        
        // Detalles en card
        JPanel detailsCard = new JPanel();
        detailsCard.setLayout(new BoxLayout(detailsCard, BoxLayout.Y_AXIS));
        detailsCard.setBackground(CARD_BACKGROUND);
        detailsCard.setBorder(new CompoundBorder(
                new LineBorder(BORDER_LIGHT, 1, true),
                new EmptyBorder(20, 20, 20, 20)
        ));
        detailsCard.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        // Email
        JPanel emailRow = createDetailRow("📧 Email", email);
        detailsCard.add(emailRow);
        detailsCard.add(Box.createVerticalStrut(12));
        
        // User ID
        String shortId = userId.length() > 12 ? userId.substring(0, 12) + "..." : userId;
        JPanel idRow = createDetailRow("🆔 User ID", shortId);
        detailsCard.add(idRow);
        
        contentPanel.add(detailsCard);
        contentPanel.add(Box.createVerticalGlue());
        
        // Botón cerrar
        JButton closeButton = new JButton("Cerrar");
        closeButton.setFont(new Font("Inter", Font.BOLD, 14));
        closeButton.setForeground(Color.WHITE);
        closeButton.setBackground(PRIMARY_BLUE);
        closeButton.setBorderPainted(false);
        closeButton.setFocusPainted(false);
        closeButton.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        closeButton.setAlignmentX(Component.CENTER_ALIGNMENT);
        closeButton.addActionListener(e -> dialog.dispose());
        contentPanel.add(closeButton);
        
        dialog.add(contentPanel);
        dialog.setVisible(true);
    }
    
    private JPanel createDetailRow(String label, String value) {
        JPanel row = new JPanel(new BorderLayout(12, 0));
        row.setOpaque(false);
        row.setMaximumSize(new Dimension(Integer.MAX_VALUE, 30));
        
        JLabel labelComp = new JLabel(label);
        labelComp.setFont(new Font("Inter", Font.PLAIN, 13));
        labelComp.setForeground(TEXT_SECONDARY);
        
        JLabel valueComp = new JLabel(value);
        valueComp.setFont(new Font("Inter", Font.BOLD, 13));
        valueComp.setForeground(TEXT_PRIMARY);
        
        row.add(labelComp, BorderLayout.WEST);
        row.add(valueComp, BorderLayout.EAST);
        
        return row;
    }
    
    private String formatDate(String timestamp) {
        if (timestamp == null || timestamp.equals("N/A")) {
            return "N/A";
        }
        // Formato simple: YYYY-MM-DD HH:MM
        try {
            if (timestamp.length() >= 19) {
                return timestamp.substring(0, 10) + " " + timestamp.substring(11, 16);
            }
            return timestamp;
        } catch (Exception e) {
            return timestamp;
        }
    }
}
