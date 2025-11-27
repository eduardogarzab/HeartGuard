package com.heartguard.desktop.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Utilidades comunes para manejo de JSON dentro de la aplicación desktop.
 */
public final class JsonUtils {
    public static final Gson GSON = new GsonBuilder()
            .setDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX")
            .create();

    private JsonUtils() {
    }
}
