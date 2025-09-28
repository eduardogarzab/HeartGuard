// settings.gradle.kts

pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // --- AÑADE ESTA LÍNEA ---
        maven { url = uri("https://jitpack.io") }
    }
}
rootProject.name = "HeartGuard"
include(":app")